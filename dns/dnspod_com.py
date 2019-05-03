# coding=utf-8
"""
DNSPOD API
DNSPOD 接口解析操作库
http://www.dnspod.com/docs/domains.html
@author: New Future
"""

from json import loads as jsondecode
from logging import debug, info, warning
try:
    # python 2
    from httplib import HTTPSConnection
    from urllib import urlencode
except ImportError:
    # python 3
    from http.client import HTTPSConnection
    from urllib.parse import urlencode


__author__ = 'New Future'


ID = "token id"
TOKEN = "token key"
PROXY = None  # 代理设置
API_SITE = "api.dnspod.com"
API_METHOD = "POST"


def request(action, param=None, **params):
    """
    发送请求数据
    """
    if param:
        params.update(param)

    params.update({'login_token': '***', 'format': 'json'})
    info("%s : params:%s", action, params)
    params['user_token'] = "%s,%s" % (ID, TOKEN)

    if PROXY:
        conn = HTTPSConnection(PROXY)
        conn.set_tunnel(API_SITE, 443)
    else:
        conn = HTTPSConnection(API_SITE)

    conn.request(API_METHOD, '/' + action, urlencode(params),
                 {
                     "Content-type": "application/x-www-form-urlencoded",
                     "User-Agent": "DDNS Client/1.0"
    })
    response = conn.getresponse()
    res = response.read()
    conn.close()

    if response.status < 200 or response.status >= 300:
        warning('%s : error:%s', action, res)
        raise Exception(res)
    else:
        data = jsondecode(res.decode('utf8'))
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
    if len(domain_split) == 3:  # 长度为3
        sub, main = domain_split[0], domain_split[1] + '.' + domain_split[2]
        did = get_domain_id(main)
    else:  # 长度大于三通过API判断,最后两个，三个递增
        main = domain_split.pop()
        while domain_split:
            main = domain_split.pop() + '.' + main
            did = get_domain_id(main)
            if did:
                sub = ".".join(domain_split)
                break
        else:
            warning('domain_id: %s, sub: %s', did, sub)
            return None, None
        if not sub:  # root domain根域名https://github.com/NewFuture/DDNS/issues/9
            sub = '@'
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
        info = request('Domain.Info', domain=domain)
        if info and info.get('status', {}).get('code') == "1":
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
                line = record["line"].replace(
                    "Default", "default").encode("utf-8")
                res = request('Record.Modify', record_id=did, record_line=line, value=value,
                              sub_domain=sub, domain_id=domainid, record_type=record_type)
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
                      sub_domain=sub, record_type=record_type, record_line="default", ttl=600)
        if res:
            did = res.get("record")["id"]
            get_records.records[domainid][did] = res.get("record")
            get_records.records[domainid][did].update(
                value=value, sub_domain=sub, record_type=record_type)
            result = res.get("record")
        else:
            result = domain + " created fail!"
    return result
