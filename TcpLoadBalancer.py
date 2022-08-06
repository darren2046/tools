from bagbag import *

def forward(tconn:Socket.TCP.StreamConnection, tuconn:Socket.TCP.StreamConnection):
    Lg.Trace(f"Forward from {tconn.PeerAddress().Host}:{tconn.PeerAddress().Port} to {tuconn.PeerAddress().Host}:{tuconn.PeerAddress().Port}")
    try:
        while True:
            buf = tconn.RecvBytes(1024)
            tuconn.SendBytes(buf)
    except:
        pass

    Lg.Trace(f"Forwarder for {tconn.PeerAddress().Host}:{tconn.PeerAddress().Port} to {tuconn.PeerAddress().Host}:{tuconn.PeerAddress().Port} exit")

def connHandler(tconn:Socket.TCP.StreamConnection):
    Lg.Trace(f"Thread started for: {tconn.PeerAddress().Host}:{tconn.PeerAddress().Port}")
    
    uip = Funcs.Int2IP(
        Random.Choice(
            Range(
                Funcs.IP2Int("172.19.0.3"),
                Funcs.IP2Int("172.19.0.252")
            )
        )
    )
    Lg.Trace(f"Connect to upstream: {uip}")
    tuconn = Socket.TCP.Connect(uip, 65400)

    Thread(forward, tconn, tuconn)

    forward(tuconn, tconn)

if __name__ == "__main__":
    Lg.Info("Listen on: 65401")
    tserver = Socket.TCP.Listen("0.0.0.0", 65401)
    for tconn in tserver.Accept():
        Lg.Trace(f"Connection from: {tconn.PeerAddress().Host}:{tconn.PeerAddress().Port}")
        Thread(connHandler, tconn)
