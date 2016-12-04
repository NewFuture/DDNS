#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
自动更新DNS
@author: New Future
"""
import argparse
import json
import time
import os
import tempfile

from dns import alidns, dnspod
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
        except IOError:
            exit('fail to load config from file: %s' % path)
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

    index = get_config('index' + ip_type) or "default"
    if str(index).isdigit():
        value = getattr(ip, "local_v" + ip_type)(index)

    else:
        value = getattr(ip, index + "_v" + ip_type)()

    if value is None:
        return False
    elif value == cache[ipname]:
        print '.',
    else:
        cache[ipname] = value
        print 'update %s to: %s' % (ipname, value)
        record_type = (ip_type == '4') and 'A' or 'AAAA'
        for domain in domains:
            print dns.update_record(domain, value, record_type=record_type)


def main():
    """
    更新
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', default="config.json")
    get_config(path=parser.parse_args().c)
    if get_config('dns', 'dnspod').startswith('ali'):
        dns = alidns
    else:
        dns = dnspod
    dns.ID, dns.TOKEN = get_config('id'), get_config('token')
    dns.PROXY = get_config('proxy')
    ip.DEBUG = get_config('debug')

    cache = Cache(CACHE_FILE)
    if len(cache) < 1:
        print "=" * 25 + " " + time.ctime() + " " + "=" * 25

    update_ip('4', cache, dns)
    update_ip('6', cache, dns)


if __name__ == '__main__':
    main()
