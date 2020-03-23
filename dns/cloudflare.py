# coding=utf-8
"""
CloudFlare API
CloudFlare 接口解析操作库
https://api.cloudflare.com/#dns-records-for-a-zone-properties
@author: TongYifan
"""

from json import loads as jsondecode, dumps as jsonencode
from logging import debug, info, warning

try:
    # python 2
    from httplib import HTTPSConnection
    from urllib import urlencode
except ImportError:
    # python 3
    from http.client import HTTPSConnection
    from urllib.parse import urlencode

__author__ = 'TongYifan'


class Config:
    ID = "AUTH EMAIL"  # CloudFlare 验证的是用户Email，等同于其他平台的userID
    TOKEN = "API KEY"
    PROXY = None  # 代理设置
    TTL = None


class API:
    # API 配置
    SITE = "api.cloudflare.com"  # API endpoint


def request(method, action, param=None, **params):
    """
        发送请求数据
    """
    if param:
        params.update(param)
    
    params = dict((k, params[k]) for k in params if params[k] is not None)
    info("%s/%s : %s", API.SITE, action, params)
    if Config.PROXY:
        conn = HTTPSConnection(Config.PROXY)
        conn.set_tunnel(API.SITE, 443)
    else:
        conn = HTTPSConnection(API.SITE)

    if method in ['PUT', 'POST', 'PATCH']:
        # 从public_v(4,6)获取的IP是bytes类型，在json.dumps时会报TypeError
        params['content'] = str(params.get('content'))
        params = jsonencode(params)
    else:  # (GET, DELETE) where DELETE doesn't require params in Cloudflare
        if params:
            action += '?' + urlencode(params)
        params = None
    if not Config.ID:
        headers = {"Content-type": "application/json", "Authorization": "Bearer " + Config.TOKEN}
    else:
        headers = {"Content-type": "application/json", "X-Auth-Email": Config.ID, "X-Auth-Key": Config.TOKEN}
    conn.request(method, '/client/v4/zones' + action, params, headers)
    response = conn.getresponse()
    res = response.read().decode('utf8')
    conn.close()
    if response.status < 200 or response.status >= 300:
        warning('%s : error[%d]:%s', action, response.status, res)
        raise Exception(res)
    else:
        data = jsondecode(res)
        debug('%s : result:%s', action, data)
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
    cache_key = zoneid + "_" + \
        conditions.get('name', "") + "_" + conditions.get('type', "")
    if not hasattr(get_records, 'records'):
        get_records.records = {}  # "静态变量"存储已查询过的id
        get_records.keys = ('id', 'type', 'name', 'content', 'proxied', 'ttl')

    if not zoneid in get_records.records:
        get_records.records[cache_key] = {}
        data = request('GET', '/' + zoneid + '/dns_records',
                       per_page=100, **conditions)
        if data:
            for record in data:
                get_records.records[cache_key][record['id']] = {
                    k: v for (k, v) in record.items() if k in get_records.keys}

    records = {}
    for (zid, record) in get_records.records[cache_key].items():
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
    info(">>>>>%s(%s)", domain, record_type)
    zoneid = get_zone_id(domain)
    if not zoneid:
        raise Exception("invalid domain: [ %s ] " % domain)

    records = get_records(zoneid, name=domain, type=record_type)
    cache_key = zoneid + "_" + domain + "_" + record_type
    result = {}
    if records:  # update
        # https://api.cloudflare.com/#dns-records-for-a-zone-update-dns-record
        for (rid, record) in records.items():
            if record['content'] != value:
                res = request('PUT', '/' + zoneid + '/dns_records/' + record['id'],
                              type=record_type, content=value, name=domain, ttl=Config.TTL)
                if res:
                    get_records.records[cache_key][rid]['content'] = value
                    result[rid] = res.get("name")
                else:
                    result[rid] = "Update fail!\n" + str(res)
            else:
                result[rid] = domain
    else:  # create
        # https://api.cloudflare.com/#dns-records-for-a-zone-create-dns-record
        res = request('POST', '/' + zoneid + '/dns_records',
                      type=record_type, name=domain, content=value, proxied=False, ttl=Config.TTL)
        if res:
            get_records.records[cache_key][res['id']] = res
            result = res
        else:
            result = domain + " created fail!"
    return result
