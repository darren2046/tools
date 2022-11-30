from bagbag import * 

from cfg import sghcfg

import yaml 

languages = Http.Get("https://raw.githubusercontent.com/github/linguist/master/lib/linguist/languages.yml").Content
languages = yaml.safe_load(languages)

db = Tools.MySQL("192.168.1.230")

(
    db.Table("binance_api"). 
        AddColumn("source", "string"). 
        AddColumn("pattern", "string").
        AddColumn("url", "text"). 
        AddColumn("rawurl", "text"). 
        AddColumn("content", "text").
        AddColumn("info", "text"). 
        AddColumn("md5", "string").
        AddIndex("md5")
)

tbba = db.Table("binance_api")

g = Tools.Github(sghcfg.token, ratelimit = "60/m")

for k in languages:
    v = languages[k]
    if 'codemirror_mode' in v and 'extensions' in v:
        for i in v['extensions']:
            pattern = "extension:" + i.lstrip('.') + " " + sys.argv[1]
            Lg.Trace(f"Searching: {pattern}")
            for r in g.Search(pattern):
                Lg.Trace("Found:", r)
                md5 = Hash.Md5sum(r.url)
                if tbba.Where("md5", "=", md5).NotExists():
                    tbba.Data({
                        "source": "github",
                        "pattern": pattern, 
                        "url": r.url, 
                        "rawurl": r.rawurl,
                        "content": r.content, 
                        "md5": md5
                    }).Insert()
    
