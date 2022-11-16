from bagbag import *

args = (
    Tools.Argparser().
    Add("MySQLHost"). 
    AddInt("MySQLPort").
    Add("MySQLUser").
    Add("MySQLPass").
    Add("MySQLDatabase").
    AddOpt("Tables", "", "逗号分割的可以访问的表, 例如: tb1,tb2,tb3"). 
    AddOptInt("Port", 6676, "监听http服务的端口").
    AddOptInt("Batch", 100, "每次给多少数据"). 
    AddOpt("SeekDB", "seek.db").
    AddOpt("TelegramToken", "", "是否每天发送export多少数据出来, 有设定这个值就会启用"). 
    AddOptInt("TelegramChatID", "").
    Get()
)

Lg.SetFile("log/DatabaseExporter.log")
Lg.Trace("程序启动")

stataistic = {}

if str(args.Tables) != "":
    tbs = [i.strip() for i in str(args.Tables).split(",")]
else:
    tbs = None

db = Tools.MySQL(args.MySQLHost, args.MySQLPort, args.MySQLUser, args.MySQLPass, args.MySQLDatabase)

seekdb = Tools.SQLite(args.SeekDB)

(seekdb.Table("seek").
    AddColumn("table", "string"). 
    AddColumn("seek", "int"). 
    AddColumn("exported", "int").
    AddIndex("table"))

w = Tools.WebServer()

@w.Route("/<tbname>")
def getData(tbname:str):
    stb = seekdb.Table("seek")

    Lg.Trace(f"请求导出数据表: {tbname}")
    if tbs and tbname not in tbs:
        Lg.Trace(f"表{tbname}不在{tbs}中, 跳过")
        return Json.Dumps({})
    
    if tbname not in stataistic:
        Lg.Trace(f"表{tbname}不在stataistic中")
        if not stb.Where("table", "=", tbname).Exists():
            Lg.Trace(f"表{tbname}不在seek数据库中, 添加")
            stb.Data({
                "table": tbname,
                "seek": 0,
                "exported": 0,
            }).Insert()
            stataistic[tbname] = 0 
        else:
            Lg.Trace(f"表{tbname}在seek数据库中, 添加数据库的值到stataistic中")
            stataistic[tbname] = stb.Where("table", "=", tbname).First()["exported"]

    Lg.Trace(f"获取表{tbname}的seek")
    seek = stb.Where("table", "=", tbname).First()["seek"]
    Lg.Trace(f"seek为{seek}")

    res = db.Table(tbname).Where("id", ">", seek).Limit(args.Batch).OrderBy("id").Get()
    if len(res) != 0:
        seek = res[-1]["id"]
        stataistic[tbname] += len(res)
        Lg.Trace(f"表{tbname}已导出数据量: {stataistic[tbname]}, id偏移量: {seek}")
        stb.Where("table", "=", tbname).Data({
            "seek": seek,
            "exported": stataistic[tbname],
        }).Update()
        return Json.Dumps([dict(r) for r in res])
    else:
        Lg.Trace(f"表{tbname}没有更多的数据, 返回空")
        return Json.Dumps({})

@w.Route("/reset/<tbname>")
def resetCounter(tbname:str):
    stb = seekdb.Table("seek")
    
    Lg.Trace(f"请求重置表{tbname}")
    if tbs and tbname not in tbs:
        Lg.Trace(f"表{tbname}不在{tbs}中, 跳过")
        w.Response.Abort(404)
    
    if tbname not in stataistic:
        Lg.Trace(f"表{tbname}不在stataistic中")
        if not stb.Where("table", "=", tbname).Exists():
            Lg.Trace(f"表{tbname}不在seek数据库中, 添加")
            stb.Data({
                "table": tbname,
                "seek": 0,
                "exported": 0,
            }).Insert()
        else:
            Lg.Trace(f"表{tbname}在seek数据库中, 重置数据库的值")
            stb.Where("table", "=", tbname).Data({
                "seek": 0,
                "exported": 0,
            }).Update()
        stataistic[tbname] = 0 
    else:
        Lg.Trace(f"表{tbname}在stataistic中")

        Lg.Trace(f"重置stataistic里面表{tbname}的值为0")
        stataistic[tbname] = 0

        Lg.Trace(f"重置数据库的表{tbname}的值")
        stb.Where("table", "=", tbname).Data({
            "seek": 0,
            "exported": 0,
        }).Update()

    return ""

w.Run(port=args.Port, block=False)

seeks = {}
exporteds = {}
todayseek = 0
todayexported = 0

for i in seekdb.Table("seek").Get():
    seeks[i["table"]] = i["seek"]
    exporteds[i["table"]] = i["exported"]

def SendStatistic():
    global args
    global seeks
    global exporteds
    global todayseek
    global todayexported 

    stb = seekdb.Table("seek")

    msg = "New exported in Server side:\n"
    for i in stb.Get():
        if i["table"] not in seeks:
            seeks[i["table"]] = 0

        todayseek = i["seek"] - seeks[i["table"]]
        seeks[i["table"]] = i["seek"]

        if i["table"] not in exporteds:
            exporteds[i["table"]] = 0

        todayexported = i["exported"] - exporteds[i["table"]]
        exporteds[i["table"]] = i["exported"]

        msg += i["table"] + f": seek: {todayseek}, exported: {todayexported}\n"
    
    Lg.Trace(msg)
    
    if args.TelegramToken != "":
        Lg.Trace("Send msg to telegram...")
        tgbot = Tools.TelegramBot(args.TelegramToken).SetChatID(args.TelegramChatID)
        tgbot.SendMsg(msg)

c = Tools.Crontab()
c.Every().Day().At("00:00").Do(SendStatistic)

Time.Sleep()
