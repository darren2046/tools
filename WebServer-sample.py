from bagbag import *

if __name__ == "__main__":
    w = Tools.WebServer()

    @w.Route("/")
    def index():
        return "Hello World!"

    @w.Route("/json")
    def json():
        return {"key": "value"}

    @w.Route("/param/<pname>")
    def param(pname):
        return pname

    @w.Route('/method', methods=['GET', 'POST'])
    def login():
        return w.Request.Method()

    # curl 'http://localhost:8080/getArg?key=value'
    @w.Route("/getArg")
    def getArg():
        return w.Request.Args.Get("key", "")

    # curl -XPOST -F "key=value" http://localhost:8080/form
    @w.Route("/form", methods=["POST"])
    def postForm():
        return w.Request.Form.Get("key")

    # curl -XPOST -d '{"key":"value"}' http://localhost:8080/postjson
    @w.Route("/postjson", methods=["POST"])
    def postJson():
        return w.Request.Json()

    # curl -XPOST -d 'Hello World!' http://localhost:8080/postData
    @w.Route("/postData", methods=["POST"])
    def postData():
        return w.Request.Data()

    w.Run("0.0.0.0", 8080, block=False)

    w2 = Tools.WebServer()

    @w2.Route("/")
    def index2():
        return "Hello World 2!"
    
    w2.Run("0.0.0.0", 8081) # Block here