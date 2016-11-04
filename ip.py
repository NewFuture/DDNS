#!/usr/bin/env python
#-*- coding:utf-8 -*-

import socket
import urllib2
DEBUG = False  # 是否打印错误


def local_v6(i=0):  # 本地ipv6地址
    info = socket.getaddrinfo(socket.gethostname(), 0, socket.AF_INET6)
    if DEBUG:
        print(info)
    return info[i][4][0]


def local_v4(i=0):  # 本地ipv4地址
    info = socket.getaddrinfo(socket.gethostname(), 0, socket.AF_INET)
    if DEBUG:
        print(info)
    return info[i][-1][0]


def public_v4(url="http://v4.ipv6-test.com/api/myip.php"):  # 公网IPV4地址
    try:
        return urllib2.urlopen(url, timeout=60).read()
    except Exception, e:
        if DEBUG:
            print(e)


def public_v6(url="http://v6.ipv6-test.com/api/myip.php"):  # 公网IPV6地址
    try:
        return urllib2.urlopen(url, timeout=60).read()
    except Exception, e:
        if DEBUG:
            print(e)


def nku_v4():  # nku 内网ipv4地址
    host = ['http://202.113.18.106']
    for url in host:
        try:
            html = urllib2.urlopen(url, timeout=60).read()
            p = html.find("v4ip='")
            if p > 0:
                html = html[p + 6:]
                result = html[:html.find("'")].strip()
                if result != None:
                    return result
        except Exception, e:
            if DEBUG:
                print(p)
            continue
