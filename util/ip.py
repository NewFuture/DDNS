#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
import os
import socket
import logging as logger
try:
    # python2
    from urllib2 import urlopen
except ImportError:
    # python3
    from urllib.request import urlopen


def default_v4():  # 默认连接外网的ipv4
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("1.1.1.1", 53))
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
    info = socket.getaddrinfo(socket.gethostname(), 0, socket.AF_INET6)
    logger.debug(info)
    return info[int(i)][4][0]


def local_v4(i=0):  # 本地ipv4地址
    info = socket.getaddrinfo(socket.gethostname(), 0, socket.AF_INET)
    logger.debug(info)
    return info[int(i)][-1][0]


def public_v4(url="http://v4.ipv6-test.com/api/myip.php"):  # 公网IPV4地址
    try:
        return urlopen(url, timeout=60).read().decode('utf8')
    except Exception as e:
        logger.error(e)


def public_v6(url="http://v6.ipv6-test.com/api/myip.php"):  # 公网IPV6地址
    try:
        return urlopen(url, timeout=60).read().decode('utf8')
    except Exception as e:
        logger.error(e)


def ip_regex_match(parrent_regex, match_regex):

    ip_pattern = re.compile(parrent_regex)
    matcher = re.compile(match_regex)

    if os.name == 'nt':  # windows:
        cmd = 'ipconfig'
    else:
        cmd = 'ifconfig || ip address'

    for s in os.popen(cmd).readlines():
        addr = ip_pattern.search(s)
        if addr and matcher.match(addr.group(1)):
            return addr.group(1)


def regex_v4(reg):  # ipv4 正则提取
    if os.name == 'nt':  # Windows: IPv4 xxx: 192.168.1.2
        regex_str = r'IPv4 .*: ((?:\d{1,3}\.){3}\d{1,3})\W'
    else:
        regex_str = r'inet (?:addr\:)?((?:\d{1,3}\.){3}\d{1,3})\s'
    return ip_regex_match(regex_str, reg)


def regex_v6(reg):  # ipv6 正则提取
    if os.name == 'nt':  # Windows: IPv4 xxx: ::1
        regex_str = r'IPv6 .*: ([\:\dabcdef]*)?\W'
    else:
        regex_str = r'inet6 (?:addr\:)?([\:\dabcdef]*)?\s'
    return ip_regex_match(regex_str, reg)
