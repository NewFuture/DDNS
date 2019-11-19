# coding=utf-8
"""
DNSCOM API
DNS.COM 接口解析操作库
http://open.dns.com/
@author: Bigjin
@mailto: i@bigjin.com
"""

from hashlib import md5
from json import loads as jsondecode
from logging import debug, info, warning
from time import mktime
from datetime import datetime

try:
    # python 2
    from httplib import HTTPSConnection
    from urllib import urlencode
except ImportError:
    # python 3
    from http.client import HTTPSConnection
    from urllib.parse import urlencode


__author__ = 'Bigjin'
# __all__ = ["request", "ID", "TOKEN", "PROXY"]


class Config:
    ID = "id"
    TOKEN = "TOKEN"
    PROXY = None  # 代理设置
    TTL = None


class API:
    # API 配置
    SITE = "www.dns.com"  # API endpoint
    METHOD = "POST"  # 请求方法


def signature(params):
    """
    计算签名,返回签名后的查询参数
    """
    params.update({
        'apiKey': Config.ID,
        'timestamp': mktime(datetime.now().timetuple()),
    })
    query = urlencode(sorted(params.items()))
    debug(query)
    sign = query
    debug("signString: %s", sign)

    sign = md5((sign + Config.TOKEN).encode('utf-8')).hexdigest()
    params["hash"] = sign

    return params


def request(action, param=None, **params):
    """
    发送请求数据
    """
    if param:
        params.update(param)
    params = dict((k, params[k]) for k in params if params[k] is not None)
    params = signature(params)
    info("%s/api/%s/ : params:%s", API.SITE, action, params)

    if Config.PROXY:
        conn = HTTPSConnection(Config.PROXY)
        conn.set_tunnel(API.SITE, 443)
    else:
        conn = HTTPSConnection(API.SITE)

    conn.request(API.METHOD, '/api/' + action + '/', urlencode(params),
                 {"Content-type": "application/x-www-form-urlencoded"})
    response = conn.getresponse()
    result = response.read().decode('utf8')
    conn.close()

    if response.status < 200 or response.status >= 300:
        warning('%s : error[%d]:%s', action, response.status, result)
        raise Exception(result)
    else:
        data = jsondecode(result)
        debug('%s : result:%s', action, data)
        if data.get('code') != 0:
            raise Exception("api error:", data.get('message'))
        data = data.get('data')
        if data is None:
            raise Exception('response data is none')
        return data


def get_domain_info(domain):
    """
    切割域名获取主域名和对应ID
    """
    if len(domain.split('.')) > 2:
        domains = domain.split('.', 1)
        sub = domains[0]
        main = domains[1]
    else:
        sub = ''  # 接口有bug 不能传 @ * 作为主机头，但是如果为空，默认为 @
        main = domain

    res = request("domain/getsingle", domainID=main)
    domain_id = res.get('domainID')
    return sub, main, domain_id


def get_records(domain, domain_id, **conditions):
    """
        获取记录ID
        返回满足条件的所有记录[]
        TODO 大于500翻页
    """
    if not hasattr(get_records, "records"):
        get_records.records = {}  # "静态变量"存储已查询过的id
        get_records.keys = ("recordID", "record", "type", "viewID",
                            "TTL", "state", "value")

    if not domain in get_records.records:
        get_records.records[domain] = {}
        data = request("record/list",
                       domainID=domain_id, pageSize=500)
        if data.get('data'):
            for record in data.get('data'):
                get_records.records[domain][record["recordID"]] = {
                    k: v for (k, v) in record.items() if k in get_records.keys}
    records = {}
    for (rid, record) in get_records.records[domain].items():
        for (k, value) in conditions.items():
            if record.get(k) != value:
                break
        else:  # for else push
            records[rid] = record
    return records


def update_record(domain, value, record_type='A'):
    """
        更新记录
    """
    info(">>>>>%s(%s)", domain, record_type)
    sub, main, domain_id = get_domain_info(domain)

    records = get_records(main, domain_id, record=sub, type=record_type)
    result = {}

    if records:
        for (rid, record) in records.items():
            if record["value"] != value:
                debug(sub, record)
                res = request("record/modify", domainID=domain_id,
                              recordID=rid, newvalue=value, newTTL=Config.TTL)
                if res:
                    # update records
                    get_records.records[main][rid]["value"] = value
                    result[rid] = res
                else:
                    result[rid] = "update fail!\n" + str(res)
            else:
                result[rid] = domain
    else:
        res = request("record/create", domainID=domain_id,
                      value=value, host=sub, type=record_type, TTL=Config.TTL)
        if res:
            # update records INFO
            rid = res.get('recordID')
            get_records.records[main][rid] = {
                'value': value,
                "recordID": rid,
                "record": sub,
                "type": record_type
            }
            result = res
        else:
            result = domain + " created fail!"
    return result
