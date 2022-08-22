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
                AddIndex("use"). 
                AddIndex("status"). 
                AddIndex('md5')
        )
        self.pptb = self.db.Table("proxypool")
    
    def Has(self, url:str) -> bool:
        return self.pptb.Where("url", "=", url).Exists()
    
    def Size(self) -> int:
        return self.pptb.Where("status", "=", "alive").Count()
    
    def Append(self, url:str):
        self.pptb.Data({
            "url": url,
            "use": 0,
            "status": "alive",
        }).Insert()
    
    def Pop(self) -> str:
        p = self.pptb.OrderBy("id").First()
        self.pptb.Where("id", "=", p['id']).Delete()
        return p['url']
    
    def Remove(self, url:str):
        self.pptb.Where("url", "=", url).Delete()

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

    proxypool = ProxyPool()

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
            if proxypool.Has(u):
                Lg.Trace(f"Server not exists")
                if checkAlive(u):
                    Lg.Trace(f"Server alive")
                    if len(proxypool) > psize:
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
                    if u in proxypool:
                        proxypool.Remove(u)
                        pgppc.Set(len(proxypool))
                        pgppnd.Add()
        
        def removeUnAliveProxy():
            gap = 1800
            while True:
                stime = Time.Now()
                for u in proxypool:
                    if not checkAlive(u):
                        Lg.Trace(f"The server inside the pool is not alive, remove: {u}")
                        if u in proxypool:
                            proxypool.Remove(u)
                            pgppc.Set(len(proxypool))
                            pgpped.Add()
                etime = Time.Now()
                if etime - stime < gap:
                    Time.Sleep(gap - (etime - stime))
        
        Thread(removeUnAliveProxy)

        while True:
            if len(proxypool) > 10:
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
        return Random.Choice(proxypool)

    w.Run("0.0.0.0", 8879)