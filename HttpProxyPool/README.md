由于下游应用只能设置一个代理服务器, 而上游却给了一堆的代理服务器, 所以需要这个代理池来自动转发请求.

它会请求上游的url, 返回结果是一堆的代理, 一行一个.