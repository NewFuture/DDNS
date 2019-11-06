# coding=utf-8
"""
Hurricane Electric (he.net) API
Hurricane Electric (he.net) 接口解析操作库
https://dns.he.net/docs.html
@author: NN708
"""

from logging import debug, info, warning

try:
    # python 2
    from httplib import HTTPSConnection
    from urllib import urlencode
except ImportError:
    # python 3
    from http.client import HTTPSConnection
    from urllib.parse import urlencode

__author__ = 'NN708'


class Config:
    TOKEN = "password"
    PROXY = None  # 代理设置


class API:
    # API 配置
    SITE = "dyn.dns.he.net"
    METHOD = "POST"
    ACTION = "nic/update"
    TOKEN_PARAM = "password"  # key name of token param


def request(param=None, **params):
    """
    发送请求数据
    """
    if param:
        params.update(param)

    params.update({API.TOKEN_PARAM: '***'})
    info("%s/%s : %s", API.SITE, API.ACTION, params)
    params[API.TOKEN_PARAM] = Config.TOKEN

    if Config.PROXY:
        conn = HTTPSConnection(Config.PROXY)
        conn.set_tunnel(API.SITE, 443)
    else:
        conn = HTTPSConnection(API.SITE)

    conn.request(API.METHOD, '/' + API.ACTION, urlencode(params), {
        "Content-type": "application/x-www-form-urlencoded"
    })
    response = conn.getresponse()
    res = response.read().decode('utf8')
    conn.close()

    if response.status < 200 or response.status >= 300:
        warning('%s : error[%d]:%s', API.ACTION, response.status, res)
        raise Exception(res)
    else:
        debug('%s : result:%s', API.ACTION, res)
        if not res:
            raise Exception("empty response")
        elif res[:5] == "nochg" or res[:4] == "good": # No change or success
            return res
        else:
            raise Exception(res)


def update_record(domain, value, record_type="A"):
    """
    更新记录
    """
    info(">>>>>%s(%s)", domain, record_type)
    res = request(hostname=domain, myip=value)
    if res[:4] == "good":
        result = "Record updated. New IP is: " + res[5:-1]
    elif res[:5] == "nochg":
        result = "IP not changed. IP is: " + res[6:-1]
    else:
        result = "Record update failed."
    return result
