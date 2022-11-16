from bagbag import * 

args = ( 
    Tools.Argparser().
        Add("srcdbhost"). 
        Add("dstdbhost"). 
        Add("srctable"). 
        Get()
)

sdb = Tools.MySQL(args.srcdbhost)
ddb = Tools.MySQL(args.dstdbhost)
stb = sdb.Table(args.srctable)
dtb = ddb.Table(args.srctable)

ldb = Tools.SQLite("MergeMySQLDataFormOneToAnother.db")
kv = ldb.KeyValue("kv").Namespace(args.srcdbhost).Namespace(args.dstdbhost).Namespace(args.srctable)

idx = kv.Get("id_seek", 0)

total = stb.Where("id", ">", idx).Count()
pg = Tools.ProgressBar(total=total)

while True:
    Lg.Trace(idx)
    res = stb.Where("id", ">", idx).OrderBy("id").Limit(100).Get()

    if len(res) == 0:
        Lg.Trace("")
        break 

    for r in res:
        Lg.Trace("")
        pg.Add()
        if r["id"] > idx:
            idx = r["id"]
            kv.Set("id_seek", idx)
        
        del(r["id"])

        dtb.Data(r).Insert()