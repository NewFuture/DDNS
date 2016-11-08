# coding=utf-8

# ali DNS API
import httplib
import urllib
import json

import hashlib
import hmac
import uuid
from datetime import datetime

#https://help.aliyun.com/document_detail/29739.html
ID="AccessKeyId"
TOKEN="AccessKey"
DEBUG =True
PROXY = None  # 代理设置
API_SITE = "alidns.aliyuncs.com"
API_METHOD="POST"

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
    queryString = urllib.urlencode(sorted(params.items()))
    if DEBUG: print(queryString)
    signString = API_METHOD + "&" + urllib.quote_plus("/") + "&" + urllib.quote(queryString,safe='')
    if DEBUG: print("signString: %s"%signString)

    signature = hmac.new(TOKEN+"&", signString, hashlib.sha1).digest()
    params["Signature"] = signature.encode("base64").strip()
    return params


def request(param={},**params):
    """
    发送请求数据
    """
    params.update(param)
    params=signature(params)
    if DEBUG: print("params:%s"%(params))
    
    if PROXY:
        conn = httplib.HTTPSConnection(PROXY)
        conn.set_tunnel(API_SITE, 443)
    else:
        conn = httplib.HTTPSConnection(API_SITE)

    conn.request(API_METHOD, '/', urllib.urlencode(params), {"Content-type": "application/x-www-form-urlencoded"})
    response = conn.getresponse()
    data = response.read()
    conn.close()

    if response.status < 200 or response.status >= 300:
        raise Exception(data)
    else:
        data = json.loads(data)
        return data

print request(Action="DescribeDomainRecords",DomainName="newfuture.xyz")
