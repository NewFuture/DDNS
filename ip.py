#!/usr/bin/env python
#-*- coding:utf-8 -*-

import socket
DEBUG = False


def local_v6(i=0):  # 本地ipv6地址
    info = socket.getaddrinfo(socket.gethostname(), 0, socket.AF_INET6)
    if DEBUG: print(info)
    return info[i][4][0]


def local_v4(i=0):  # 本地ipv4地址
    info = socket.getaddrinfo(socket.gethostname(), 0, socket.AF_INET)
    if DEBUG: print(info)
    return info[i][-1][0]
