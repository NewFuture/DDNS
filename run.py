#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
自动更新DNS
@author: New Future
"""
import argparse
import json
import time

import dnspod
import alidns
import ip

DNS = dnspod


def get_config(key=None, default=None, file="config.json"):
    if not hasattr(get_config, "config"):
        try:
            with open(file) as configfile:
                get_config.config = json.load(configfile)
        except:
            exit('fail to load config from file: %s' % file)
    if key:
        return get_config.config.get(key, default)
    else:
        return get_config.config


def update():
    print "=" * 25 + " " + time.ctime() + " " + "=" * 25
    index4 = get_config('index4') or "default"
    if str(index4).isdigit():
        ipv4 = ip.local_v4(index4)
    else:
        ipv4 = getattr(ip, index4 + "_v4")()
    print 'update ipv4 to:', ipv4
    if ipv4 != None:
        for domain in get_config('ipv4'):
            print DNS.update_record(domain, ipv4, 'A')

    v6_domains = get_config("ipv6") or "default"
    if len(v6_domains) > 0:
        index6 = get_config('index6')
        if str(index6).isdigit():
            ipv6 = ip.local_v6(index6)
        else:
            ipv6 = getattr(ip, index6 + "_v6")()
        print 'update ipv6 to:', ipv6
        if ipv6 != None:
            for domain in v6_domains:
                print DNS.update_record(domain, ipv6, 'AAAA')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', default="config.json")
    get_config(file=parser.parse_args().c)
    if get_config('dns', 'dnspod').startswith('ali'):
        DNS = alidns
    DNS.ID, DNS.TOKEN = get_config('id'), get_config('token')
    DNS.PROXY = get_config('proxy')
    ip.DEBUG = get_config('debug')
    update()
