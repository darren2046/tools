#!/opt/homebrew/bin/python3
import re 
import os 
import sys
import time
import subprocess 

fversion = open("version").read()
print("current version:",fversion)

sversion = fversion.split(".")[0] + '.' + fversion.split(".")[1] + '.'
version = int(fversion.split(".")[-1])

nfversion = input("Next version ["+sversion+str(version+1)+"]: ")

if nfversion.strip() == "":
    nfversion = sversion+str(version+1)

print("Next version: " + nfversion)

open("version", "w").write(nfversion)

if os.system("""
docker buildx build --platform linux/amd64,linux/arm64 . -t darren2046/http-proxy-pool:"""+nfversion+""" --push 
docker buildx build --platform linux/amd64,linux/arm64 . -t darren2046/http-proxy-pool:latest --push 
""") != 0:
    sys.exit(0)
