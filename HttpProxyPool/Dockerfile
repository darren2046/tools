FROM darren2046/bagbag:0.40.6

WORKDIR /app

COPY proxy_pool.py /app/proxy_pool.py

RUN pip install types-requests requests; \
    apt update;\
    apt install wget;\
    wget https://files.pythonhosted.org/packages/86/22/069e14dc6367b8f688b42f78793c7dd5c65228d107fa78d466f61334d495/proxy.py-2.4.3.tar.gz -O /tmp/proxy.py-2.4.3.tar.gz; \
    cd /tmp;\
    tar xvf /tmp/proxy.py-2.4.3.tar.gz; \ 
    cp /app/proxy_pool.py /tmp/proxy.py-2.4.3/proxy/plugin; \
    pip install ./proxy.py-2.4.3

COPY HttpProxyPool.py /app/HttpProxyPool.py
COPY run.py /app/run.py

EXPOSE 8899 9105

ENTRYPOINT [ "python", "/app/run.py" ]
