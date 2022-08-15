from tabnanny import check
from weakref import proxy
from bagbag import *

if len(Os.Args) < 2:
    print("Usage: " + Os.Args[0] + " [URL to get proxy servers]")
    Os.Exit(0)

psurl = Os.Args[1]

w = Tools.WebServer()

proxypool = []

@w.Route("/")
def index():
    return Random.Choice(proxypool)

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
        if u not in proxypool:
            Lg.Trace(f"Server not exists")
            if checkAlive(u):
                Lg.Trace(f"Server alive")
                if len(proxypool) > 100:
                    uu = proxypool.pop(0)
                    Lg.Trace(f"Pop server: {uu}")
                proxypool.append(u)
                Lg.Trace(f"Append server")
            else:
                Lg.Trace("Server not alive")
        else:
            Lg.Trace("Server exists")
            if not checkAlive(u):
                Lg.Trace("Server not alive, remove")
                proxypool.remove(u)

    while True:
        for u in [i.strip() for i in Http.Get(psurl).Content.splitlines()]:
            Lg.Trace(f"Checking: {u}")
            Thread(checkAndAppend, u)
            Time.Sleep(1)
            
Thread(updateProxy)

w.Run("0.0.0.0", 8879)