#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
自动更新DNS
@author: New Future
@modified: rufengsuixing
"""
from __future__ import print_function
import argparse
import json
import time
import os
import sys
import tempfile

from util import ip
from util.cache import Cache

CACHE_FILE = os.path.join(tempfile.gettempdir(), 'ddns.cache')


def get_config(key=None, default=None, path="config.json"):
    """
    读取配置
    """
    if not hasattr(get_config, "config"):
        try:
            with open(path) as configfile:
                get_config.config = json.load(configfile)
                get_config.time = os.stat(path).st_mtime
        except IOError:
            print('Config file %s does not appear to exist.' % path)
            with open(path, 'w') as configfile:
                configure = {
                    "id": "your id",
                    "token": "your token",
                    "dns": "dnspod",
                    "ipv4": [
                        "your.domain",
                        "ipv4.yours.domain"
                    ],
                    "ipv6": [
                        "your.domain",
                        "ipv6.your.domain"
                    ],
                    "index4": "default",
                    "index6": "default",
                    "proxy": None
                }
                json.dump(configure, configfile, indent=2, sort_keys=True)
            sys.exit("New template configure file is created!")
        except:
            sys.exit('fail to load config from file: %s' % path)
    if key:
        return get_config.config.get(key, default)
    else:
        return get_config.config


def update_ip(ip_type, cache, dns):
    """
    更新IP
    """
    ipname = 'ipv' + ip_type
    domains = get_config(ipname)
    if not domains:
        return None
    if get_config('re'+ip_type):
        value=getattr(ip, "reip" + ip_type)(get_config('re'+ip_type))
    else:
        index = get_config('index' + ip_type) or "default"
        if str(index).isdigit():
            value = getattr(ip, "local_v" + ip_type)(index)
        else:
            value = getattr(ip, index + "_v" + ip_type)()
    if value is None:
        return False
    elif cache and value == cache[ipname]:
        print('.', end=" ")
    else:
        print ('update %s to: %s' % (ipname, value))
        record_type = (ip_type == '4') and 'A' or 'AAAA'
        for domain in domains:
            print (dns.update_record(domain, value, record_type=record_type))
        if cache is not False:
            cache[ipname] = value


def main():
    """
    更新
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', default="config.json")
    get_config(path=parser.parse_args().c)
    # Dynamicly import the dns module as configuration
    dns_provider = str(get_config('dns', 'dnspod').lower())
    dns = getattr(__import__('dns', fromlist=[dns_provider]), dns_provider)
    dns.ID, dns.TOKEN = get_config('id'), get_config('token')
    dns.PROXY = get_config('proxy')

    ip.DEBUG = get_config('debug')

    cache = get_config('cache', True) and Cache(CACHE_FILE)
    if cache is False:
        print("Cache is disabled!")
    elif len(cache) < 1 or get_config.time >= cache.time:
        cache.clear()
        print ("=" * 25, time.ctime(), "=" * 25, sep=' ')
    try:
        update_ip('4', cache, dns)
        update_ip('6', cache, dns)
    except:
        if dns.PROXY and get_config('no_proxy_try'):
            dns.PROXY=None
            update_ip('4', cache, dns)
            update_ip('6', cache, dns)

if __name__ == '__main__':
    main()
