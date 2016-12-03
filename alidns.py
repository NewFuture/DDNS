# coding=utf-8
"""
AliDNS API
阿里DNS解析操作库
https://help.aliyun.com/document_detail/29739.html
@author: New Future
"""

import hashlib
import hmac
import httplib
import json
import urllib
import uuid
from datetime import datetime

import debug

__author__ = 'New Future'
# __all__ = ["request", "ID", "TOKEN", "PROXY"]
debug.ENABLE = False

ID = "id"
TOKEN = "TOKEN"
DEBUG = debug.log()
PROXY = None  # 代理设置
API_SITE = "alidns.aliyuncs.com"
API_METHOD = "POST"


def signature(params):
    """
    计算签名,返回签名后的查询参数
    """
    params.update({
        'Format': 'json',
        'Version': '2015-01-09',
        'AccessKeyId': ID,
        'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'SignatureMethod': 'HMAC-SHA1',
        'SignatureNonce': uuid.uuid4(),
        'SignatureVersion': "1.0",
    })
    query = urllib.urlencode(sorted(params.items()))
    DEBUG(query)
    sign = API_METHOD + "&" + \
        urllib.quote_plus("/") + "&" + urllib.quote(query, safe='')
    DEBUG("signString: %s" % sign)

    sign = hmac.new(str(TOKEN + "&"), sign, hashlib.sha1).digest()
    params["Signature"] = sign.encode("base64").strip()
    return params


def request(param=None, **params):
    """
    发送请求数据
    """
    if param:
        params.update(param)
    params = signature(params)
    DEBUG("params:%s" % (params))

    if PROXY:
        conn = httplib.HTTPSConnection(PROXY)
        conn.set_tunnel(API_SITE, 443)
    else:
        conn = httplib.HTTPSConnection(API_SITE)

    conn.request(API_METHOD, '/', urllib.urlencode(params),
                 {"Content-type": "application/x-www-form-urlencoded"})
    response = conn.getresponse()
    data = response.read()
    conn.close()

    if response.status < 200 or response.status >= 300:
        raise Exception(data)
    else:
        data = json.loads(data)
        DEBUG(data)
        return data


def get_domain_info(domain):
    """
    切割域名获取主域名和对应ID
    https://help.aliyun.com/document_detail/29755.html
    http://alidns.aliyuncs.com/?Action=GetMainDomainName&InputString=www.example.com
    """
    res = request(Action="GetMainDomainName", InputString=domain)
    sub, main = res.get('RR'), res.get('DomainName')
    return sub, main


def get_records(domain, **conditions):
    """
        获取记录ID
        返回满足条件的所有记录[]
        https://help.aliyun.com/document_detail/29776.html
        TODO 大于500翻页
    """
    if not hasattr(get_records, "records"):
        get_records.records = {}  # "静态变量"存储已查询过的id
        get_records.keys = ("RecordId", "RR", "Type", "Line",
                            "Locked", "Status", "Priority", "Value")

    if not domain in get_records.records:
        get_records.records[domain] = {}
        data = request(Action="DescribeDomainRecords",
                       DomainName=domain, PageSize=500)
        if data:
            for record in data.get('DomainRecords').get('Record'):
                get_records.records[domain][record["RecordId"]] = {
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
        update
        https://help.aliyun.com/document_detail/29774.html
        add
        https://help.aliyun.com/document_detail/29772.html?
    """
    DEBUG(">>>>>%s(%s)" % (domain, record_type))
    sub, main = get_domain_info(domain)
    if not sub:
        raise Exception("invalid domain: [ %s ] " % domain)

    records = get_records(main, RR=sub, Type=record_type)
    result = {}

    if records:
        for (rid, record) in records.items():
            if record["Value"] != value:
                DEBUG(sub, record)
                res = request(Action="UpdateDomainRecord", RecordId=rid,
                              Value=value, RR=sub, Type=record_type)
                if res:
                    # update records
                    get_records.records[main][rid]["Value"] = value
                    result[rid] = res
                else:
                    result[rid] = "update fail!\n" + str(res)
    else:  # https://help.aliyun.com/document_detail/29772.html
        res = request(Action="AddDomainRecord", DomainName=main,
                      Value=value, RR=sub, Type=record_type)
        if res:
            # update records INFO
            rid = res.get('RecordId')
            get_records.records[main][rid] = {
                'Value': value,
                "RecordId": rid,
                "RR": sub,
                "Type": record_type
            }
            result = res
        else:
            result = domain + " created fail!"
    return result

if __name__ == '__main__':
    print update_record('dns.newfuture.win', '6.6.6.6')
