from bagbag import *

class ProxyPool():
    def __init__(self) -> None:
        self.db = Tools.SQLite("/data/proxypool.db")
        (
            self.db.Table("proxypool").
                AddColumn("md5", "string"). # 代理地址可能会很长, 所以这是md5
                AddColumn("url", "string"). # 代理的地址 
                AddColumn("use", "int"). # 使用过的次数
                AddColumn("status", "string"). # 状态, alive, pop, dead
                AddColumn("time", "int"). # 添加的时间
                AddIndex("use"). 
                AddIndex("status"). 
                AddIndex('md5'). 
                AddIndex("time"). 
                AddIndex("use", "time")
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
        r = pptb.Where("use", "!=", -1).OrderBy("use").OrderBy("time", "desc").First()
        if not r:
            return None
        
        pptb.Where("id", "=", r['id']).Data({
            "use": r['use'] + 1,
        }).Update()

        return r['url']
    
    def Has(self, url:str) -> bool:
        pptb = self.db.Table("proxypool")
        return pptb.Where("md5", "=", Hash.Md5sum(url)).Exists()
    
    def Size(self) -> int:
        pptb = self.db.Table("proxypool")
        return pptb.Where("status", "=", "alive").Count()
    
    def Append(self, url:str):
        pptb = self.db.Table("proxypool")
        pptb.Data({
            "url": url,
            "use": 0,
            "status": "alive",
            "md5": Hash.Md5sum(url),
            "time": int(Time.Now()),
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
        print("Usage: " + Os.Args[0] + " [URL to get proxy servers] [Pool Size]")
        Os.Exit(0)

    psurl = Os.Args[1]
    psize = int(Os.Args[2])

    serving = Time.Now()

    Lg.Trace(f"代理池的服务器URL:{psurl}")

    pg = Tools.PrometheusMetricServer()
    pgppa = pg.NewCounter("proxy_pool_add", "新加入代理池的代理个数")
    pgppe = pg.NewCounter("proxy_pool_exists", "从上游获取到的代理已存在代理池的个数")
    pgppc = pg.NewGauge("proxy_pool_count", "代理池的代理个数")
    pgppnd = pg.NewCounter("proxy_pool_new_dead", "从上游获取到的代理测试为无效的个数")
    pgpped = pg.NewCounter("proxy_pool_exists_dead", "代理池内的代理测试为无效的个数")
    pgppu = pg.NewGaugeWithLabel("proxy_pool_usage", ["use"], "代理池里面的代理的使用情况")

    proxypool = ProxyPool()

    def updateMetrics():
        while True:
            for i in Range(10):
                pgppu.Set({'use': i}, proxypool.db.Table("proxypool").Where("use", "=", i).Count())
            Time.Sleep(15)
    
    Thread(updateMetrics)

    # 循环更新代理池
    def updateProxy():
        def checkAlive(url:str):
            try:
                resp = Http.Get("https://ifconfig.me", HttpProxy=url)
                if resp.StatusCode != 200:
                    raise Exception("status code not 200")
                return True
            except:
                try:
                    resp = Http.Get("https://aws.amazon.com/", HttpProxy=url)
                    if resp.StatusCode != 200:
                        return False
                    return True
                except:
                    try:
                        resp = Http.Get("https://aws.amazon.com/", HttpProxy=url)
                        if resp.StatusCode != 200:
                            return False
                        return True
                    except:
                        return False 
        
        def checkAndAppend(u:str):
            if not proxypool.Has(u):
                Lg.Trace(f"Server not exists")
                if checkAlive(u):
                    Lg.Trace(f"Server alive")
                    while proxypool.Size() > psize:
                        uu = proxypool.Pop()
                        Lg.Trace(f"Pop server: {uu}")
                    proxypool.Append(u)
                    Lg.Trace(f"Append server")
                    pgppa.Add()
                    pgppc.Set(proxypool.Size())
                else:
                    Lg.Trace("Server not alive")
                    pgppnd.Add()
            else:
                Lg.Trace("Server exists")
                pgppe.Add()
                if not checkAlive(u):
                    Lg.Trace("Server not alive, remove")
                    if proxypool.Has(u):
                        proxypool.Remove(u)
                        pgppc.Set(proxypool.Size())
                        pgppnd.Add()
        
        def removeUnAliveProxy():
            gap = 1800
            while True:
                stime = Time.Now()
                for u in proxypool:
                    if not checkAlive(u):
                        Lg.Trace(f"The server inside the pool is not alive, remove: {u}")
                        if proxypool.Has(u):
                            proxypool.Remove(u)
                            pgppc.Set(proxypool.Size())
                            pgpped.Add()
                etime = Time.Now()
                if etime - stime < gap:
                    Time.Sleep(gap - (etime - stime))
        
        Thread(removeUnAliveProxy)

        while True:
            if proxypool.Size() > 10:
                sec = Time.Now() - serving
                Lg.Trace(f"如果代理池有10个以上链接, 且1分钟没有提供给其他人调用, 那么1小时更新一次, Time.Now() - serving: {sec}")
                if Time.Now() - serving > 60 and 3600 > Time.Now() - serving:
                    Time.Sleep(1)
                    continue
            
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

    w.Run("0.0.0.0", 8879)