from bagbag import *

if __name__ == "__main__":
    # Local 
    # se = Selenium()

    # Remote 
    #se = Selenium("http://127.0.0.1:4444")

    # With PAC 
    se = Tools.Selenium(PACFileURL="http://192.168.1.135:8000/pac")
    # se = Selenium("http://127.0.0.1:4444", PACFileURL="http://192.168.1.135:8000/pac")

    # Example of PAC file
    # function FindProxyForURL(url, host)
    # {
    #     if (shExpMatch(host, "*.onion"))
    #     {
    #         return "SOCKS5 192.168.1.135:9150";
    #     }
    #     if (shExpMatch(host, "ipinfo.io"))
    #     {
    #         return "SOCKS5 192.168.1.135:7070";
    #     }
    #     return "DIRECT";
    # }
    
    # PAC test 
    # Access through 192.168.1.135:7070
    se.Get("http://ipinfo.io/ip")
    print(se.PageSource())
    
    # Direct access
    se.Get("https://ifconfig.me/ip")
    print(se.PageSource())
    
    # Access Onion domain with 192.168.1.135:9150
    se.Get("http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/")
    print(se.PageSource())

    # Function test
    se.Get("https://find-and-update.company-information.service.gov.uk/")
    # Find the input bar and input "ade"
    se.Find("/html/body/div[1]/main/div[3]/div/form/div/div/input").Input("ade")
    # Find the search button and click
    se.Find('//*[@id="search-submit"]').Click()
    
    # Get the page source of the search result
    print(se.PageSource())

    se.Close()