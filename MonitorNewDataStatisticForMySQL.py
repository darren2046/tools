from bagbag import *

args = (Tools.Argparser().Add("MySQL_HOST").AddOpt("TABLES", "", "tb1,tb2,tb3").Add("TGAPI").AddInt("TGID").Get())

db = Tools.MySQL(args.MySQL_HOST)

tgbot = Tools.TelegramBot(args.TGAPI).SetChatID(args.TGID)

if args.TABLES == "":
    tables = None
else:
    tables = str(args.TABLES).split(",")

statistics = {}

if tables:
    tbs = tables 
else:
    tbs = db.Tables()

for tbname in tbs:
    Lg.Trace(f"Checking table: {tbname}")
    res = db.Table(tbname).OrderBy("id", "desc").First()
    if res:
        statistics[tbname] = res["id"]
    else:
        Lg.Trace("No data")
        statistics[tbname] = 0
    Lg.Trace(f"Current count for table {tbname}: {statistics[tbname]}")

def send():
    global statistics
    msg = ["New added:"]
    if tables:
        tbs = tables 
    else:
        tbs = db.Tables()

    for tbname in tbs:
        Lg.Trace(f"Checking table: {tbname}")
        res = db.Table(tbname).OrderBy("id", "desc").First()
        if res:
            current = res["id"]
        else:
            current = 0

        if tbname not in statistics:
            statistics[tbname] = 0 

        step = current - statistics[tbname]
        Lg.Trace(f"For table {tbname}: {current} - {statistics[tbname]} = {step}")
        msg.append(tbname + ": " + str(step))
        statistics[tbname] = current

    Lg.Trace('\n'.join(msg))
    tgbot.SendMsg('\n'.join(msg))

c = Tools.Crontab()

c.Every().Day().At("00:00").Do(send)

Time.Sleep()