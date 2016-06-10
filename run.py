#!/usr/bin/env python
#-*- coding:utf-8 -*-

import dnspod
import ip
import json


def get_config(key=None, file="config.json"):
    if not hasattr(get_config, "config"):
        try:
            with open(file) as configfile:
                get_config.config = json.load(configfile)
        except:
            exit('fail to load config from file: %s' % file)
    if key:
        return get_config.config.get(key)
    else:
        return get_config.config


def update():
    ipv4 = ip.local_v4(get_config('index4'))
    print 'update ipv4 to:', ipv4
    if ipv4 != None:
        for domain in get_config('ipv4'):
            print dnspod.change_record(domain, ipv4, 'A')

    ipv6 = ip.local_v6(get_config('index6'))
    print 'update ipv6 to:', ipv6
    if ipv6 != None:
        for domain in get_config('ipv6'):
            print dnspod.change_record(domain, ipv6, 'AAAA')

if __name__ == '__main__':
    dnspod.TOKEN = "%s,%s" % (get_config('id'), get_config('token'))
    dnspod.PROXY = get_config('proxy')
    update()
