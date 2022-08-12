from bagbag import *

if __name__ == "__main__":
    w = Tools.CSV.Writer("test.csv")

    w.SetHeaders("h1", "h2")

    w.Write({"h1": "v1", "h2": '"v2,kkk|'})
    w.Write({"h1": "v,1", "h2": '"v222'})
    w.Write({"h1": "3", "h2": '"99kkk'})

    w.Close()

    # test.csv
    # h1,h2
    # v1,"\"v2,kkk|"
    # "v,1",\"v222
    # 3,\"99kkk

    r = Tools.CSV.Reader("test.csv")
    print(r.Read()) # {'h1': 'v1', 'h2': '"v2,kkk|'}

    for row in r:
        print(row) 
        # {'h1': 'v,1', 'h2': '"v222'}
        # {'h1': '3', 'h2': '"99kkk'}
    
    w = Tools.CSV.Writer("test.csv", "a")
    w.Write({"h1": "4", "h2": '5'}) 
    w.Write({"h1": "6", "h3": '7'}) # 6,