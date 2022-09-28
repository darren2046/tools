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
    Get()
)

stataistic = {}

if str(args.Tables) != "":
    tbs = [i.strip() for i in str(args.Tables).split(",")]
else:
    tbs = None

db = Tools.MySQL(args.MySQLHost, args.MySQLPort, args.MySQLUser, args.MySQLPass, args.MySQLDatabase)

seekdb = Tools.SQLite(args.SeekDB)

stb = (seekdb.Table("seek").
    AddColumn("table", "string"). 
    AddColumn("seek", "int"). 
    AddColumn("exported", "int").
    AddIndex("table"))

w = Tools.WebServer()

@w.Route("/<tbname>")
def getData(tbname:str):
    if tbs and tbname not in tbs:
        return Json.Dumps({})
    
    if tbname not in stataistic:
        if not stb.Where("table", "=", tbname).Exists():
            stb.Data({
                "table": tbname,
                "seek": 0,
                "exported": 0,
            }).Insert()
            stataistic[tbname] = 0 
        else:
            stataistic[tbname] = stb.Where("table", "=", tbname).First()["exported"]

    seek = stb.Where("table", "=", tbname).First()["seek"]

    res = db.Table(tbname).Where("id", ">", seek).Limit(args.Batch).OrderBy("id").Get()
    if len(res) != 0:
        seek = res[-1]["id"]
        stataistic[tbname] += len(res)
        Lg.Trace(f"Total export for table `{tbname}`: {stataistic[tbname]}")
        stb.Where("table", "=", tbname).Data({
            "seek": seek,
            "exported": stataistic[tbname],
        }).Update()
        return Json.Dumps([dict(r) for r in res])
    else:
        return Json.Dumps({})

@w.Route("/reset/<tbname>")
def resetCounter(tbname:str):
    if tbs and tbname not in tbs:
        w.Response.Abort(404)
    
    if tbname not in stataistic:
        if not stb.Where("table", "=", tbname).Exists():
            stb.Data({
                "table": tbname,
                "seek": 0,
                "exported": 0,
            }).Insert()
            stataistic[tbname] = 0 
        else:
            stataistic[tbname] = stb.Where("table", "=", tbname).First()["exported"]

    stataistic[tbname] = 0
    
    stb.Where("table", "=", tbname).Data({
        "seek": 0,
        "exported": 0,
    }).Update()

    return ""

w.Run(port=args.Port)
