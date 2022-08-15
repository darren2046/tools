from bagbag import *

if not Os.Getenv("POOL_SERVER"):
    Lg.Error("需要设置代理池的URL用环境变量: POOL_SERVER")
    Os.Exit(0)

def runProxy():
    Os.System("proxy --plugins proxy.plugin.ProxyPoolPlugin --proxy-url-server http://127.0.0.1:8879 --hostname 0.0.0.0")

Thread(runProxy)

Os.System("python /app/HttpProxyPool.py '" + Os.Getenv("POOL_SERVER") + "'")
