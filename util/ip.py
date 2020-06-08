#!/usr/bin/env python
# -*- coding:utf-8 -*-
from re import compile
from os import name as os_name, popen
from socket import socket, getaddrinfo, gethostname, AF_INET, AF_INET6, SOCK_DGRAM
from logging import info, debug, error
try:
    # python2
    from urllib2 import urlopen, Request
except ImportError:
    # python3
    from urllib.request import urlopen, Request

# IPV4正则
IPV4_REG = r'((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])'
# IPV6正则
# https://community.helpsystems.com/forums/intermapper/miscellaneous-topics/5acc4fcf-fa83-e511-80cf-0050568460e4
IPV6_REG = r'((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))'


def default_v4():  # 默认连接外网的ipv4
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(("1.1.1.1", 53))
    ip = s.getsockname()[0]
    s.close()
    return ip


def default_v6():  # 默认连接外网的ipv6
    s = socket(AF_INET6, SOCK_DGRAM)
    s.connect(('1:1:1:1:1:1:1:1', 8))
    ip = s.getsockname()[0]
    s.close()
    return ip


def local_v6(i=0):  # 本地ipv6地址
    info = getaddrinfo(gethostname(), 0, AF_INET6)
    debug(info)
    return info[int(i)][4][0]


def local_v4(i=0):  # 本地ipv4地址
    info = getaddrinfo(gethostname(), 0, AF_INET)
    debug(info)
    return info[int(i)][-1][0]


def _open(url, reg):
    try:
        debug("open: %s", url)
        res = urlopen(
            Request(url, headers={'User-Agent': 'curl/7.63.0-ddns'}),  timeout=60
        ).read().decode('utf8')
        debug("response: %s",  res)
        return compile(reg).search(res).group()
    except Exception as e:
        error(e)


def public_v4(url="https://pv.sohu.com/cityjson?ie=utf-8", reg=IPV4_REG):  # 公网IPV4地址
    return _open(url, reg)


def public_v6(url="https://ipv6-test.com/api/myip.php", reg=IPV6_REG):  # 公网IPV6地址
    return _open(url, reg)


def _ip_regex_match(parrent_regex, match_regex):

    ip_pattern = compile(parrent_regex)
    matcher = compile(match_regex)

    if os_name == 'nt':  # windows:
        cmd = 'ipconfig'
    else:
        cmd = 'ifconfig 2>/dev/null || ip address'

    for s in popen(cmd).readlines():
        addr = ip_pattern.search(s)
        if addr and matcher.match(addr.group(1)):
            return addr.group(1)


def regex_v4(reg):  # ipv4 正则提取
    if os_name == 'nt':  # Windows: IPv4 xxx: 192.168.1.2
        regex_str = r'IPv4 .*: ((?:\d{1,3}\.){3}\d{1,3})\W'
    else:
        regex_str = r'inet (?:addr\:)?((?:\d{1,3}\.){3}\d{1,3})[\s/]'
    return _ip_regex_match(regex_str, reg)


def regex_v6(reg):  # ipv6 正则提取
    if os_name == 'nt':  # Windows: IPv4 xxx: ::1
        regex_str = r'IPv6 .*: ([\:\dabcdef]*)?\W'
    else:
        regex_str = r'inet6 (?:addr\:)?([\:\dabcdef]*)?[\s/%]'
    return _ip_regex_match(regex_str, reg)
