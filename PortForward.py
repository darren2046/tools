#!/opt/homebrew/opt/python@3.10/libexec/bin/python
from bagbag import * 

def copy(s, c):
    try:
        while True:
            s.SendBytes(c.RecvBytes(4096))
    except:
        pass 
    # Lg.Trace("Close")
    s.Close()
    c.Close()

Lg.Trace("Started..")
for s in Socket.TCP.Listen("0.0.0.0", 80).Accept():
    Lg.Trace("New connection from:", s)
    c = Socket.TCP.Connect("ifconfig.me", 80)
    Thread(copy, s, c)
    Thread(copy, c, s)

# $ curl localhost  -v -H 'Host: ifconfig.me'
# *   Trying 127.0.0.1:80...
# * Connected to localhost (127.0.0.1) port 80 (#0)
# > GET / HTTP/1.1
# > Host: ifconfig.me
# > User-Agent: curl/7.84.0
# > Accept: */*
# > 
# * Mark bundle as not supporting multiuse
# < HTTP/1.1 200 OK
# < access-control-allow-origin: *
# < content-type: text/plain; charset=utf-8
# < content-length: 13
# < date: Wed, 30 Nov 2022 11:39:19 GMT
# < x-envoy-upstream-service-time: 1
# < strict-transport-security: max-age=2592000; includeSubDomains
# < server: istio-envoy
# < Via: 1.1 google
# < 
# * Connection #0 to host localhost left intact
# 11.11.111.111