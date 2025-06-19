# coding=utf-8

"""
BaseDNSProvider 抽象基类
本模块定义了所有DNS服务商API类应继承的抽象基类，统一接口规范，便于后续扩展和多服务商适配。

Abstract base class for all DNS provider APIs.
This module defines the abstract base class that all DNS provider API classes should inherit from,
ensuring a unified interface for easy extension and adaptation to multiple providers.
"""
from abc import ABC, abstractmethod, abstractproperty
import logging
try:  # python 3
    from http.client import HTTPSConnection
    from urllib.parse import urlencode
except ImportError:  # python 2
    from httplib import HTTPSConnection
    from urllib import urlencode
    
__author__ = 'New Future'
__all__ = ["BaseProvider"]

class ProviderOption:
    ID = None
    TOKEN = None
    PROXY = None
    TTL = None

TYPE_FORM = "application/x-www-form-urlencoded"
TYPE_JSON = "application/json"

class BaseProvider(ABC):
    """
    所有DNS服务商API的抽象基类
    子类需实现以下方法以适配不同DNS服务商的API。

    Abstract base class for all DNS provider APIs.
    Subclasses must implement the following methods to adapt to different DNS provider APIs.
    """
    # API 域名 API endpoint doamin 
    API = ''
    ContentType = TYPE_FORM

    def __init__(self, option):
        """
        初始化，传入配置参数（如API密钥、域名等）
        Initialize with configuration parameters (e.g., API keys, domain info).
        :param config: dict类型，包含API认证信息、域名等
                       dict, contains API credentials, domain, etc.
        """
        self.option = option

    @abstractmethod
    def get_domain_info(self, domain):
        """
        获取域名信息（如主域名、zone_id等）
        Get domain information (e.g., main domain, zone_id, etc.)
        :param domain: 需要操作的完整域名
                       The full domain name to operate on.
        :return: 域名相关信息（如主域名、zone_id等），具体结构由子类定义
                 Domain info (such as main domain, zone_id, etc.), defined by subclass.
        """

    @abstractmethod
    def get_records(self, domain, record_type=None):
        """
        查询DNS记录
        Query DNS records.
        :param domain: 域名
                       Domain name.
        :param record_type: 记录类型（如A、AAAA等），可选
                           Record type (e.g., A, AAAA), optional.
        :return: 记录列表，结构由子类定义
                 List of records, structure defined by subclass.
        """

    @abstractmethod
    def update_record(self, domain, value, record_type="A"):
        """
        更新DNS记录（如IP变更）
        Update DNS record (e.g., IP change).
        :param domain: 域名
                       Domain name.
        :param value: 新的记录值（如新的IP地址）
                      New record value (e.g., IP address).
        :param record_type: 记录类型，默认"A"
                           Record type, default is "A".
        :return: 操作结果，结构由子类定义
                 Operation result, structure defined by subclass.
        """

    def https(self, method, url, _headers=None, _proxy=None, **params):
        """
        发送请求数据
        """
        method = method.upper()
        logging.info("[%s]%s : %s", method, url, params)
        if _proxy:
            conn = HTTPSConnection(_proxy)
            conn.set_tunnel(self.API, 443)
        else:
            conn = HTTPSConnection(self.API)

        if method in  ['GET','DELETE'] and params:
            url += '?' + urlencode(params)
            logging.debug("url: %s", url)
            params = None
        
        body = None
        if params:
            if _headers is None:
                _headers = {}
            _headers['content-type'] = self.ContentType
            if self.ContentType == TYPE_FORM:
                body = urlencode(params)            
            else:
                body = jsonencode(params)
            logging.debug("encoded: %s", body)

        conn.request(method, url, body, _headers)
        response = conn.getresponse()
        res = response.read().decode('utf8')
        conn.close()

        if response.status < 200 or response.status >= 300:
            logging.warning('%s : error[%d]:%s', action, response.status, response.reason)
            logging.info(res)
            raise Exception(res)
        try:
            data = jsondecode(res)
            logging.debug('%s : result:%s', action, data)
            return data
        except Exception as e:
            logging.exception(e)
            raise
