#!/usr/bin/env python
#-*- coding:utf-8 -*-
# DNSPOD API 接口
import httplib
import urllib
import json

TOKEN = "yourid,yourkey"  # token
PROXY = None  # 代理设置

_domain_id_list = {}


def get_domain_info(domain):  # 切割域名
    domain_split = domain.split('.')
    domain_split_len = len(domain_split)
    maindomain = domain_split[domain_split_len - 2] + '.' + domain_split[domain_split_len - 1]
    return maindomain, domain


def request(action, params, method='POST'):  # 发送请求
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/json"}
    API_SITE = "dnsapi.cn"
    if PROXY:
        conn = httplib.HTTPSConnection(PROXY)
        conn.set_tunnel(API_SITE, 443)
    else:
        conn = httplib.HTTPSConnection(API_SITE)
    conn.request(method, '/' + action, urllib.urlencode(params), headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    if response.status == 200:
        return data
    else:
        return None


def get_domain_id():  # 获取域名ID
    if len(_domain_id_list) > 0:
        return _domain_id_list
    else:
        params = {'login_token': TOKEN, 'format': 'json'}
        data = request('Domain.List', params)
        data = json.loads(data)
        domainlist = data.get('domains')
        for d in domainlist:
            _domain_id_list[d.get('name')] = d.get('id')
        return _domain_id_list


def get_domain_record_id(domain_id, domain_type="A"):  # 获取记录ID
    params = {'login_token': TOKEN, 'domain_id': domain_id, 'format': 'json'}
    data = request('Record.List', params)
    data = json.loads(data)
    if data.get('code') == '10':
        return None

    # print(domain_id, data)
    domain = data.get('domain')
    if not domain:
        return None
    domainname = domain.get('name')
    record_list = data.get('records')
    record = {}
    # print record_list[0]
    for r in record_list:
        # print(r.get('id'), r.get('name'), r.get('type'),r.get('value'))
        if r.get('type') == domain_type:
            key = r.get('name') != '@' and r.get('name') + '.' + domainname or domainname
            record[key] = {'id': int(r.get('id')), 'value': r.get('value'), 'sub': r.get('name')}
    return record


def update_domain_info(domain, domain_type="A"):  # 更新域名信息
    m, sub_m = get_domain_info(domain)
    domain_id = get_domain_id().get(m)
    record_list = get_domain_record_id(domain_id, domain_type)
    # print(record_list)
    if record_list == None:
        return None

    record_info = record_list.get(sub_m)
    if record_info == None:
        return None
    record_info['did'] = domain_id
    return record_info


def change_record(domain, value, record_type="A"):  # 更改记录
    info = update_domain_info(domain, record_type)
    if info == None:
        return None
    elif info['value'] == value:
        return domain, value
    params = {'login_token': TOKEN, 'value': value, 'sub_domain': info['sub'],
              'domain_id': info['did'], 'record_id': info['id'], 'record_type': record_type,
              'format': 'json', 'ttl': 600, 'record_line': '默认', }
    return request('Record.Modify', params)
