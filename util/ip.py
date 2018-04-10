#!/usr/bin/env python
#-*- coding:utf-8 -*-
import psutil
import socket
try:
    # python2
    from urllib2 import urlopen
except ImportError:
    # python3
    from urllib.request import urlopen

DEBUG = False  # 是否打印错误

ipv4=[]
ipv6=[]
info=psutil.net_if_addrs()
for k,v in info.items():  
    for item in v:
        try:
            #windows
            fam=item.family.value 
        except:
            #linux
            fam=item.family
        if fam == 2 and not item[1]=='127.0.0.1':
            ipv4.append(item[1])
        elif fam == 10 and not item[1]=='::1':
            ipv6.append(item[1])
def default_v4():  # 默认连接外网的ipv4
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 8))
    ip = s.getsockname()[0]
    s.close()
    return ip


def default_v6():  # 默认连接外网的ipv6
    s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    s.connect(('8:8:8:8:8:8:8:8', 8))
    ip = s.getsockname()[0]
    s.close()
    return ip


def local_v6(i=0):  # 本地ipv6地址
    return ipv6[i]


def local_v4(i=0):  # 本地ipv4地址
    return ipv4[i]


def public_v4(url="http://v4.ipv6-test.com/api/myip.php"):  # 公网IPV4地址
    try:
        return urlopen(url, timeout=60).read()
    except Exception as e:
        if DEBUG:
            print(e)


def public_v6(url="http://v6.ipv6-test.com/api/myip.php"):  # 公网IPV6地址
    try:
        return urlopen(url, timeout=60).read()
    except Exception as e:
        if DEBUG:
            print(e)


def nku_v4():  # nku 内网ipv4地址
    host = ['http://202.113.18.106']
    for url in host:
        try:
            html = urlopen(url, timeout=60).read()
            p = html.find("v4ip='")
            if p > 0:
                html = html[p + 6:]
                result = html[:html.find("'")].strip()
                if result != None:
                    return result
        except Exception as e:
            if DEBUG:
                print(e)
            continue
def reip4(re_ex4):
    import re
    for ip in ipv4:
        if re.match(re_ex4, ip):
            return ip
    
def reip6(re_ex6):
    import re
    for ip in ipv6:
        if re.match(re_ex6, ip):
            return ip
    
