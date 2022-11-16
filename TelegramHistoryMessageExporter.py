from bagbag import * 
from cfg import thmecfg

tg = Tools.Telegram(thmecfg.telegram_appid, thmecfg.telegram_apphash, thmecfg.telegram_session)

peer = tg.PeerByUsername(thmecfg.telegram_username_to_export)

jfd = open("telegram_history.json", "w")
tfd = open("telegram_history.txt", "w")

for m in Tools.ProgressBar(peer.MessagesAll()):
    jfd.write(Json.Dumps({"message": m.MessageRaw}) + "\n")
    tfd.write(str(m.MessageRaw) + "\n\n----------\n\n")