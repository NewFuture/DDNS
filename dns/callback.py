# coding=utf-8
"""
Custom Callback API
自定义回调接口解析操作库

@author: 老周部落
"""

from json import loads as jsondecode, dumps as jsonencode
from logging import debug, info, warning
from time import time

try:
    # python 2
    from httplib import HTTPSConnection, HTTPConnection
    from urlparse import urlparse, parse_qsl
    from urllib import urlencode
except ImportError:
    # python 3
    from http.client import HTTPSConnection, HTTPConnection
    from urllib.parse import urlencode, urlparse, parse_qsl

__author__ = '老周部落'

class Config:
    ID = None # 自定义回调 URL
    TOKEN = None # 使用 JSON 编码的 POST 参数
    PROXY = None  # 代理设置
    TTL = None

def request(method, action, param=None, **params):
    """
    发送请求数据
    """
    if param:
        params.update(param)

    URLObj = urlparse(Config.ID)
    params = dict((k, params[k]) for k in params if params[k] is not None)
    info("%s/%s : %s", URLObj.netloc, action, params)

    if Config.PROXY:
        if URLObj.netloc == "http":
            conn = HTTPConnection(Config.PROXY)
        else:
            conn = HTTPSConnection(Config.PROXY)
        conn.set_tunnel(URLObj.netloc, URLObj.port)
    else:
        if URLObj.netloc == "http":
            conn = HTTPConnection(URLObj.netloc, URLObj.port)
        else:
            conn = HTTPSConnection(URLObj.netloc, URLObj.port)

    headers = {}

    if method == "GET":
        if params:
            action += '?' + urlencode(params)
        params = ""
    else:
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    params = urlencode(params)

    conn.request(method, action, params, headers)
    response = conn.getresponse()
    res = response.read().decode('utf8')
    conn.close()
    if response.status < 200 or response.status >= 300:
        warning('%s : error[%d]:%s', action, response.status, res)
        raise Exception(res)
    else:
        debug('%s : result:%s', action, res)
        return data

def replace_params(domain, record_type, ip, params):
    """
    替换定义常量为实际值
    """
    dict = {"__DOMAIN__": domain, "__RECORDTYPE__": record_type, "__TTL__": Config.TTL, "__TIMESTAMP__": time(), "__IP__": ip}
    for key, value in params.items():
        if dict.get(value):
            params[key] = dict.get(value)
    return params

def update_record(domain, value, record_type="A"):
    """
    更新记录
    """
    info(">>>>>%s(%s)", domain, record_type)

    result = {}

    if not Config.TOKEN: # 此处使用 TOKEN 参数透传 POST 参数所用的 JSON
        method = "GET"
        URLObj = urlparse(Config.ID)
        path = URLObj.path
        query = dict(parse_qsl(URLObj.query))
        params = replace_params(domain, record_type, value, query)
    else:
        method = "POST"
        URLObj = urlparse(Config.ID)
        path = URLObj.path
        params = replace_params(domain, record_type, value, jsondecode(Config.TOKEN))

    res = request(method, path, params)

    if res:
        result = "Callback Request Success!\n" + res
    else:
        result = "Callback Request Fail!\n"

    return result
