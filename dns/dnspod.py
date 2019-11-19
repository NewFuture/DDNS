# coding=utf-8
"""
DNSPOD API
DNSPOD 接口解析操作库
http://www.dnspod.cn/docs/domains.html
@author: New Future
"""

from json import loads as jsondecode
from logging import debug, info, warning
from os import environ
try:
    # python 2
    from httplib import HTTPSConnection
    from urllib import urlencode
except ImportError:
    # python 3
    from http.client import HTTPSConnection
    from urllib.parse import urlencode

__author__ = 'New Future'


class Config:
    ID = "token id"
    TOKEN = "token key"
    PROXY = None  # 代理设置
    TTL = None


class API:
    # API 配置
    SITE = "dnsapi.cn"  # API endpoint
    METHOD = "POST"  # 请求方法
    TOKEN_PARAM = "login_token"  # token参数
    DEFAULT = "默认"  # 默认线路名


def request(action, param=None, **params):
    """
    发送请求数据
    """
    if param:
        params.update(param)
    params = dict((k, params[k]) for k in params if params[k] is not None)
    params.update({API.TOKEN_PARAM: '***', 'format': 'json'})
    info("%s/%s : %s", API.SITE, action, params)
    params[API.TOKEN_PARAM] = "%s,%s" % (Config.ID, Config.TOKEN)
    if Config.PROXY:
        conn = HTTPSConnection(Config.PROXY)
        conn.set_tunnel(API.SITE, 443)
    else:
        conn = HTTPSConnection(API.SITE)

    conn.request(API.METHOD, '/' + action, urlencode(params), {
        "Content-type": "application/x-www-form-urlencoded",
        "User-Agent": "DDNS/%s (ddns@newfuture.cc)" % environ.get("DDNS_VERSION", "1.0.0")
    })
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
            raise Exception("empty response")
        elif data.get("status", {}).get("code") == "1":
            return data
        else:
            raise Exception(data.get('status', {}))


def get_domain_info(domain):
    """
    切割域名获取主域名和对应ID
    """
    domain_split = domain.split('.')
    sub, did = None, None
    main = domain_split.pop()
    while domain_split:  # 通过API判断,最后两个，三个递增
        main = domain_split.pop() + '.' + main
        did = get_domain_id(main)
        if did:
            sub = ".".join(domain_split) or '@'
            # root domain根域名https://github.com/NewFuture/DDNS/issues/9
            break
    info('domain_id: %s, sub: %s', did, sub)
    return did, sub


def get_domain_id(domain):
    """
        获取域名ID
        http://www.dnspod.cn/docs/domains.html#domain-info
    """
    if not hasattr(get_domain_id, "domain_list"):
        get_domain_id.domain_list = {}  # "静态变量"存储已查询过的id

    if domain in get_domain_id.domain_list:
        # 如果已经存在直接返回防止再次请求
        return get_domain_id.domain_list[domain]
    else:
        try:
            info = request('Domain.Info', domain=domain)
        except Exception:
            return
        did = info.get("domain", {}).get("id")
        if did:
            get_domain_id.domain_list[domain] = did
            return did


def get_records(did, **conditions):
    """
        获取记录ID
        返回满足条件的所有记录[]
        TODO 大于3000翻页
        http://www.dnspod.cn/docs/records.html#record-list
    """
    if not hasattr(get_records, "records"):
        get_records.records = {}  # "静态变量"存储已查询过的id
        get_records.keys = ("id", "name", "type", "line",
                            "line_id", "enabled", "mx", "value")

    if not did in get_records.records:
        get_records.records[did] = {}
        data = request('Record.List', domain_id=did)
        if data:
            for record in data.get('records'):
                get_records.records[did][record["id"]] = {
                    k: v for (k, v) in record.items() if k in get_records.keys}

    records = {}
    for (did, record) in get_records.records[did].items():
        for (k, value) in conditions.items():
            if record.get(k) != value:
                break
        else:  # for else push
            records[did] = record
    return records


def update_record(domain, value, record_type="A"):
    """
    更新记录
    """
    info(">>>>>%s(%s)", domain, record_type)
    domainid, sub = get_domain_info(domain)
    if not domainid:
        raise Exception("invalid domain: [ %s ] " % domain)

    records = get_records(domainid, name=sub, type=record_type)
    result = {}
    if records:  # update
        # http://www.dnspod.cn/docs/records.html#record-modify
        for (did, record) in records.items():
            if record["value"] != value:
                debug(sub, record)
                res = request('Record.Modify', record_id=did, record_line=record["line"].replace("Default", "default").encode(
                    "utf-8"), value=value, sub_domain=sub, domain_id=domainid, record_type=record_type, ttl=Config.TTL)
                if res:
                    get_records.records[domainid][did]["value"] = value
                    result[did] = res.get("record")
                else:
                    result[did] = "update fail!\n" + str(res)
            else:
                result[did] = domain
    else:  # create
        # http://www.dnspod.cn/docs/records.html#record-create
        res = request("Record.Create", domain_id=domainid, value=value,
                      sub_domain=sub, record_type=record_type, record_line=API.DEFAULT, ttl=Config.TTL)
        if res:
            did = res.get("record")["id"]
            get_records.records[domainid][did] = res.get("record")
            get_records.records[domainid][did].update(
                value=value, sub_domain=sub, record_type=record_type)
            result = res.get("record")
        else:
            result = domain + " created fail!"
    return result
