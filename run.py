#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
DDNS
@author: New Future
@modified: rufengsuixing
"""
from __future__ import print_function
from argparse import ArgumentParser, RawTextHelpFormatter
from json import load as loadjson, dump as dumpjson
from time import ctime
from os import path, environ, stat, name as os_name
from tempfile import gettempdir
from logging import DEBUG, basicConfig, info, warning, error

import sys

from util import ip
from util.cache import Cache

__version__ = "${BUILD_SOURCEBRANCHNAME}@${BUILD_DATE}"  # CI 时会被Tag替换
__description__ = "automatically update DNS records to dynamic local IP [自动更新DNS记录指向本地IP]"
__doc__ = """
ddns[%s]
(i) homepage or docs [文档主页]: https://ddns.newfuture.cc/
(?) issues or bugs [问题和帮助]: https://github.com/NewFuture/DDNS/issues
Copyright (c) New Future (MIT License)
""" % (__version__)

if getattr(sys, 'frozen', False):
    # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-OpenSSL-Certificate
    environ['SSL_CERT_FILE'] = path.join(
        getattr(sys, '_MEIPASS'), 'lib', 'cert.pem')

CACHE_FILE = path.join(gettempdir(), 'ddns.cache')


def get_config(key=None, default=None, path="config.json"):
    """
    读取配置
    """
    if not hasattr(get_config, "config"):
        try:
            with open(path) as configfile:
                get_config.config = loadjson(configfile)
                get_config.time = stat(path).st_mtime
        except IOError:
            error(' Config file `%s` does not exist!' % path)
            with open(path, 'w') as configfile:
                configure = {
                    "$schema": "https://ddns.newfuture.cc/schema/v2.json",
                    "id": "YOUR ID or EAMIL for DNS Provider",
                    "token": "YOUR TOKEN or KEY for DNS Provider",
                    "dns": "dnspod",
                    "ipv4": [
                        "newfuture.cc",
                        "ddns.newfuture.cc"
                    ],
                    "ipv6": [
                        "newfuture.cc",
                        "ipv6.ddns.newfuture.cc"
                    ],
                    "index4": "default",
                    "index6": "default",
                    "proxy": None,
                    "debug": False,
                }
                dumpjson(configure, configfile, indent=2, sort_keys=True)
            sys.exit("New template configure file `%s` is generated." % path)
        except:
            sys.exit('fail to load config from file: %s' % path)
    if key:
        return get_config.config.get(key, default)
    else:
        return get_config.config


def get_ip(ip_type):
    """
    get IP address
    """
    index = get_config('index' + ip_type, "default")
    if index is False:  # disabled
        return False
    elif str(index).isdigit():  # local eth
        value = getattr(ip, "local_v" + ip_type)(index)
    elif any((c in index) for c in '*.:'):  # regex
        value = getattr(ip, "regex_v" + ip_type)(index)
    else:
        value = getattr(ip, index + "_v" + ip_type)()

    return value


def change_dns_record(dns, proxy_list, **kw):
    for proxy in proxy_list:
        if not proxy or (proxy.upper() in ['DIRECT', 'NONE']):
            dns.PROXY = None
        else:
            dns.PROXY = proxy
        record_type, domain = kw['record_type'], kw['domain']
        print('\n%s(%s) ==> %s [via %s]' %
              (domain, record_type, kw['ip'], proxy))
        try:
            return dns.update_record(domain, kw['ip'], record_type=record_type)
        except Exception as e:
            error(e)
    return False


def update_ip(ip_type, cache, dns, proxy_list):
    """
    更新IP
    """
    ipname = 'ipv' + ip_type
    domains = get_config('ipv' + ip_type)
    if not domains:
        return None
    address = get_ip(ip_type)
    if not address:
        return False
    elif cache and (address == cache[ipname]):
        print('.', end=" ")  # 缓存命中
        return True
    record_type = (ip_type == '4') and 'A' or 'AAAA'
    update_fail = False  # https://github.com/NewFuture/DDNS/issues/16
    for domain in domains:
        if change_dns_record(dns, proxy_list, domain=domain, ip=address, record_type=record_type):
            update_fail = True
    if cache is not False:
        # 如果更新失败删除缓存
        cache[ipname] = update_fail and address


def main():
    """
    更新
    """
    parser = ArgumentParser(description=__description__,
                            epilog=__doc__, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-v', '--version',
                        action='version', version=__version__)
    parser.add_argument('-c', '--config',
                        default="config.json", help="run with config file [配置文件路径]")
    get_config(path=parser.parse_args().config)
    # Dynamicly import the dns module as configuration
    dns_provider = str(get_config('dns', 'dnspod').lower())
    dns = getattr(__import__('dns', fromlist=[dns_provider]), dns_provider)
    dns.ID, dns.TOKEN = get_config('id'), get_config('token')
    if get_config('debug'):
        ip.DEBUG = get_config('debug')
        basicConfig(
            level=DEBUG,
            format='%(asctime)s <%(module)s.%(funcName)s> %(lineno)d@%(pathname)s \n[%(levelname)s] %(message)s')
        info("DDNS[%s] run: %s,%s", __version__, os_name, sys.platform)

    proxy = get_config('proxy') or 'DIRECT'
    proxy_list = proxy.strip('; ') .split(';')

    cache = get_config('cache', True) and Cache(CACHE_FILE)
    if cache is False:
        warning("Cache is disabled!")
    elif len(cache) < 1 or get_config.time >= cache.time:
        cache.clear()
        print("=" * 25, ctime(), "=" * 25, sep=' ')
    update_ip('4', cache, dns, proxy_list)
    update_ip('6', cache, dns, proxy_list)


if __name__ == '__main__':
    main()
