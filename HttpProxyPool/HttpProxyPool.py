from bagbag import *

class ProxyPool():
    def __init__(self) -> None:
        self.db = Tools.SQLite("/data/proxypool.db")
        (
            self.db.Table("proxypool").
                AddColumn("md5", "string"). # 代理地址可能会很长, 所以这是md
                AddColumn("url", "string"). # 代理的地址 
                AddColumn("use", "int"). # 使用过的次数
                AddColumn("status", "string"). # 状态, alive, pop, dead
                AddColumn("time", "int"). # 添加的时间
                AddColumn("ip", "string"). # 代理的公网IP 
                AddColumn("location", "string"). # 公网IP的国家
                AddIndex("use"). 
                AddIndex("ip"). 
                AddIndex("status").
                AddIndex("time"). 
                AddIndex("use", "time"). 
                AddIndex("country")
        )
    #     self.pptb = self.db.Table("proxypool")
    #     self.lock = Tools.Lock()

    # def wrap(func): # func是被包装的函数
    #     def ware(self, *args, **kwargs): # self是类的实例
    #         self.lock.Acquire()
    #         res = func(self, *args, **kwargs)
    #         self.lock.Release()
    #         return res

    #     return ware
    
    def Get(self) -> str | None:
        pptb = self.db.Table("proxypool")
        r = pptb.Where("use", ">", -1).OrderBy("use").OrderBy("time", "desc").First()
        if not r:
            return None
        
        pptb.Where("id", "=", r['id']).Data({
            "use": r['use'] + 1,
        }).Update()

        return r['url']
    
    def Has(self, PublicIP:str) -> bool:
        pptb = self.db.Table("proxypool")
        return pptb.Where("ip", "=", PublicIP).Exists()
    
    def Size(self) -> int:
        pptb = self.db.Table("proxypool")
        return pptb.Where("status", "=", "alive").Count()
    
    def Append(self, url:str, pip:str):
        try:
            location = Json.Loads(Http.Get("https://ip.svc.ltd/" + pip).Content)["results"]["qqwry"]["Country"]
        except Exception as e:
            Lg.Trace("查询地区出错:", e)
            Time.Sleep(1)
            try:
                location = Json.Loads(Http.Get("https://ip.svc.ltd/" + pip).Content)["results"]["qqwry"]["Country"]
            except Exception as e:
                Lg.Trace("查询地区出错:", e)
                location = ""

        pptb = self.db.Table("proxypool")
        pptb.Data({
            "url": url,
            "use": 0,
            "status": "alive",
            "md5": Hash.Md5sum(url),
            "time": int(Time.Now()),
            "ip": pip, 
            "location": location,
        }).Insert()
    
    def Pop(self) -> str:
        pptb = self.db.Table("proxypool")
        p = pptb.OrderBy("id").First()
        pptb.Where("id", "=", p['id']).Data({
            "status": "pop",
            "use": -1,
        }).Update()
        return p['url']
    
    def Remove(self, url:str):
        pptb = self.db.Table("proxypool")
        pptb.Where("md5", "=", Hash.Md5sum(url)).Data({
            "status": "remove",
            "use": -1,
        }).Update()
    
    def __iter__(self) -> str:
        pptb = self.db.Table("proxypool")
        sid = 0

        while True:
            res = pptb.Where("id", ">", sid).Limit(100).Get()
            if len(res) == 0:
                return 
            
            for r in res:
                if r['id'] > sid:
                    sid = r['id']

                yield r['url'] 

if __name__ == "__main__":
    if len(Os.Args) < 2:
        print("Usage: " + Os.Args[0] + " [URL to get proxy servers] [Pool Size] [Check Alive]")
        Os.Exit(0)

    psurl = Os.Args[1]
    psize = int(Os.Args[2])
    checkalive = Os.Args[3] == "True"

    serving = Time.Now()

    Lg.Trace(f"代理池的服务器URL:{psurl}")

    pg = Tools.PrometheusMetricServer()
    pgppa = pg.NewCounter("proxy_pool_add", "新加入代理池的代理个数")
    pgppe = pg.NewCounter("proxy_pool_exists", "从上游获取到的代理已存在代理池的个数")
    pgppc = pg.NewGauge("proxy_pool_count", "代理池的代理个数")
    pgppnd = pg.NewCounter("proxy_pool_new_dead", "从上游获取到的代理测试为无效的个数")
    pgpped = pg.NewCounter("proxy_pool_exists_dead", "代理池内的代理测试为无效的个数")
    pgppu = pg.NewGaugeWithLabel("proxy_pool_usage", ["use"], "代理池里面的代理的使用情况")
    pgppl = pg.NewGaugeWithLabel("proxy_pool_location", ["location"], "代理池里面的地区分布情况")

    proxypool = ProxyPool()

    def updateMetrics():
        maxuseo = 0
        while True:
            try:
                # 不用Group By是因为要清除一些之前留下的痕迹
                maxuse = proxypool.db.Table("proxypool").OrderBy("use", "desc").First()["use"]
                if maxuse > maxuseo:
                    maxuseo = maxuse
                for i in Range(maxuseo + 1):
                    pgppu.Set({'use': i}, proxypool.db.Table("proxypool").Where("use", "=", i).Count())
                
                for i in proxypool.db.Execute("select count(id) as `count`, `location` from `proxypool` group by `location`"):
                    pgppl.Set({"location": i["location"]}, i["count"])

                pgppc.Set(proxypool.Size())
            except:
                Lg.Error("Update Metrics错误")
            Time.Sleep(15)

    Thread(updateMetrics)

    # 循环更新代理池
    def updateProxy():
        def checkIP(url:str) -> str:
            try:
                return Funcs.GetPublicIP(url)
            except:
                return None
        
        def checkAndAppend(u:str):
            pip = checkIP(u)
            if pip != None:
                Lg.Trace(f"Server alive")
                if not proxypool.Has(pip):
                    Lg.Trace(f"Server not exists")
                    while proxypool.Size() > psize:
                        uu = proxypool.Pop()
                        Lg.Trace(f"Pop server: {uu}")
                    proxypool.Append(u, pip)
                    Lg.Trace(f"Append server")
                    pgppa.Add()
                    
                else:
                    Lg.Trace("Server exists")
                    pgppe.Add()
            else:
                Lg.Trace("Server not alive")
                pgppnd.Add()
                Lg.Trace("remove")
                proxypool.Remove(u)
                pgppnd.Add()

        def removeUnAliveProxy():
            gap = 1800
            while True:
                stime = Time.Now()
                for u in proxypool:
                    if not checkIP(u):
                        Lg.Trace(f"The server inside the pool is not alive, remove: {u}")
                        proxypool.Remove(u)
                        pgpped.Add()
                etime = Time.Now()
                if etime - stime < gap:
                    Time.Sleep(gap - (etime - stime))
        
        Thread(removeUnAliveProxy)

        while True:
            if proxypool.db.Table("proxypool").Where("use", "=", 0).Count() > 100:
                Lg.Trace("代理池内未使用的代理超过100个, 不更新")
                Time.Sleep(3) 
            else:
                if proxypool.db.Table("proxypool").Where("use", "=", 0).Count() > 30:
                    Lg.Trace("代理池内未使用的代理超过30个")
                    sec = Time.Now() - serving
                    if Time.Now() - serving > 60 and 3600 > Time.Now() - serving:
                        Lg.Trace(f"且1分钟没有提供给其他人调用, 不更新, Time.Now() - serving: {sec}")
                        Time.Sleep(3)
                    else:
                        Lg.Trace("有提供使用, 更新")
                        try:
                            for u in [i.strip() for i in Http.Get(psurl).Content.splitlines()]:
                                Lg.Trace(f"Checking: {u}")
                                Thread(checkAndAppend, u)
                                Time.Sleep(1)
                        except:
                            pass
                else:
                    Lg.Trace("代理池内未使用的代理不足30个, 更新")
                    try:
                        for u in [i.strip() for i in Http.Get(psurl).Content.splitlines()]:
                            Lg.Trace(f"Checking: {u}")
                            Thread(checkAndAppend, u)
                            Time.Sleep(1)
                    except:
                        pass
    Thread(updateProxy)

    # 给proxy_pool.py去调用
    w = Tools.WebServer()

    @w.Route("/")
    def index():
        global serving
        serving = Time.Now()
        while True:
            url = proxypool.Get()
            if not url:
                Time.Sleep(1)
            else:
                return url
    
    @w.Route("/add", methods=["POST"])
    def add():
        data = w.Request.Json()
        if not proxypool.Has(data["ip"]):
            Lg.Trace("HTTP Post上来的代理不存在:", data["ip"])
            proxypool.Append(data["url"], data["ip"])
            return "HTTP Post上来的代理不存在:" + data["ip"]
        else:
            Lg.Trace("HTTP Post上来的代理已存在:", data["ip"])
            return "HTTP Post上来的代理已存在:" + data["ip"]

    w.Run("0.0.0.0", 8879)