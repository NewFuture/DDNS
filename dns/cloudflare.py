# coding=utf-8
"""
CloudFlare API
CloudFlare 接口解析操作库
https://api.cloudflare.com/#dns-records-for-a-zone-properties
@author: TongYifan
"""

import json
import logging as logger

try:
    # python 2
    from httplib import HTTPSConnection
    import urllib
except ImportError:
    # python 3
    from http.client import HTTPSConnection
    import urllib.parse as urllib

__author__ = 'TongYifan'

ID = "AUTH EMAIL"  # CloudFlare 验证的是用户Email，等同于其他平台的userID
TOKEN = "API KEY"
PROXY = None  # 代理设置
API_SITE = "api.cloudflare.com"


def request(method, action, param=None, **params):
    """
        发送请求数据
    """
    if param:
        params.update(param)

    logger.debug("$s %s : params:%s", action, params)
    if PROXY:
        conn = HTTPSConnection(PROXY)
        conn.set_tunnel(API_SITE, 443)
    else:
        conn = HTTPSConnection(API_SITE)

    if method in ['PUT', 'POST']:
        # 从public_v(4,6)获取的IP是bytes类型，在json.dumps时会报TypeError
        params['content'] = str(params.get('content'))
        params = json.dumps(params)
    else:
        params = urllib.urlencode(params)
    if method == 'GET':
        action = action + '?' + params
    conn.request(method, '/client/v4/zones' + action, params,
                 {"Content-type": "application/json",
                  "X-Auth-Email": ID,
                  "X-Auth-Key": TOKEN})
    response = conn.getresponse()
    res = response.read()
    conn.close()
    if response.status < 200 or response.status >= 300:
        raise Exception(res)
    else:
        data = json.loads(res.decode('utf8'))
        if not data:
            raise Exception("Empty Response")
        elif data.get('success'):
            return data.get('result', [{}])
        else:
            raise Exception(data.get('errors', [{}]))


def get_zone_id(domain):
    """
        切割域名获取主域名ID(Zone_ID)
        https://api.cloudflare.com/#zone-list-zones
    """
    zones = request('GET', '', per_page=50)
    zone = next((z for z in zones if domain.endswith(z.get('name'))), None)
    zoneid = zone and zone['id']
    return zoneid


def get_records(zoneid, **conditions):
    """
           获取记录ID
           返回满足条件的所有记录[]
           TODO 大于100翻页
    """
    if not hasattr(get_records, 'records'):
        get_records.records = {}  # "静态变量"存储已查询过的id
        get_records.keys = ('id', 'type', 'name', 'content', 'proxied', 'ttl')

    if not zoneid in get_records.records:
        get_records.records[zoneid] = {}
        data = request('GET', '/' + zoneid + '/dns_records', per_page=100, **conditions)
        if data:
            for record in data:
                get_records.records[zoneid][record['id']] = {
                    k: v for (k, v) in record.items() if k in get_records.keys}

    records = {}
    for (zid, record) in get_records.records[zoneid].items():
        for (k, value) in conditions.items():
            if record.get(k) != value:
                break
        else:  # for else push
            records[zid] = record
    return records


def update_record(domain, value, record_type="A"):
    """
    更新记录
    """
    logger.debug(">>>>>%s(%s)", domain, record_type)
    zoneid = get_zone_id(domain)
    if not zoneid:
        raise Exception("invalid domain: [ %s ] " % domain)

    records = get_records(zoneid, name=domain, type=record_type)
    result = {}
    if records:  # update
        # https://api.cloudflare.com/#dns-records-for-a-zone-update-dns-record
        for (rid, record) in records.items():
            if record['content'] != value:
                res = request('PUT', '/' + zoneid + '/dns_records/' + record['id'],
                              type=record_type, content=value, name=domain)
                if res:
                    get_records.records[zoneid][rid]['content'] = value
                    result[rid] = res.get("record")
                else:
                    result[rid] = "Update fail!\n" + str(res)
            else:
                result[rid] = domain
    else:  # create
        # https://api.cloudflare.com/#dns-records-for-a-zone-create-dns-record
        res = request('POST', '/' + zoneid + '/dns_records',
                      type=record_type, name=domain, content=value, proxied=False, ttl=600)
        if res:
            get_records.records[zoneid][res['id']] = res
            get_records.records[zoneid][res['id']].update(
                value=value, type=record_type)
            result = res
        else:
            result = domain + " created fail!"
    return result
