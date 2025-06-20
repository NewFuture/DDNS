# coding=utf-8

"""
BaseDNSProvider 抽象基类
本模块定义了所有DNS服务商API类应继承的抽象基类，统一接口规范，便于后续扩展和多服务商适配。

Abstract base class for all DNS provider APIs.
This module defines the abstract base class that all DNS provider API classes should inherit from,
ensuring a unified interface for easy extension and adaptation to multiple providers.
"""
from abc import ABC, abstractmethod, abstractproperty
from json import jsondecode
import logging
try:  # python 3
    from http.client import HTTPSConnection
    from urllib.parse import urlencode
except ImportError:  # python 2
    from httplib import HTTPSConnection
    from urllib import urlencode
    
__author__ = 'New Future'
__all__ = ["BaseProvider"]

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

    def __init__(self, auth_id, auth_token, **options): # type: (string, string, **Any) -> None
        """
        初始化，传入配置参数（如API密钥、域名等）
        Initialize with configuration parameters (e.g., API keys, domain info).
        :param auth_id: string, 认证ID
        :param auth_token: string, 认证Key/Token
        :param options: dict, 其它信息
        """
        self.auth_id = auth_id  # type: string
        self.auth_token = auth_token  # type: string
        self.options = options
        self._zone_map={} # type: dict[str, str]
        self.proxy = None # type: str
        
    def get_zone_id(self, domain):
        # type: (string) -> str
        """
        获取域名zone_id
        Get domain zone_id
        :param domain: 需要操作的完整域名
                       The full domain name to operate on.
        :return: zoneid.
        """
        if hasattr(self._zone_map, domain):
            return self._zone_map.get(domain)
        zone_id = self._query_zone_id(domain)
        if zone_id:
            setattrself._zone_map[domain]=zone_id
        return zone_id

    @abstractmethod
    def _create_record_with_zone_id(self,zone_id,sub,value,record_type,ttl=None, line=None, extra=None):
        pass

    @abstractmethod
    def _update_record_with_zone_id(self,zone_id,record_id ,value,record_type,ttl=None,line=None,extra=None):
        pass
    
    @abstractmethod
    def _query_zone_id(self, domain):
        # type: (str) -> str
        pass

    @abstractmethod
    def _query_record_id(self, zoneId, sub, record_type, line=None):
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
        pass

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        
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
        domain = domain.lower()
        logging.info("start update %s(%s) => %s", domain, record_type, value)

        sub, main = self._split_custom_domain(domain)
        zone_id = None  # type: str
        if sub is not None:
            zone_id = self.get_zone_id(main)
        else:
            zone_id, sub = self._split_zone_and_sub(domain)
        record_id = self._query_record_id(zone_id,sub)
        if record_id:
           return self._update_record_with_zone_id(zone_id=zone_id,record_id=record_id, record_type=record_type, value=value,ttl=ttl,line=line, extra=extra)
        else:
           return self._create_record_with_zone_id(zone_id=zone_id,sub=sub, record_type=record_type, value=value,ttl=ttl,line=line, extra=extra)
        
    def set_proxy(self, proxy_str):
        self.proxy = proxy_str
        return self

    def _split_zone_and_sub(self, domain):
        domain_split = domain.split('.')
        zone_id = None
        index = 2
        # ddns.example.com => example.com; ddns.example.eu.org => example.eu.org
        while (not zoneid) and (index <= len(domain_slice)):
            main = '.'.join(domain_slice[-index:])
            zone_id = self.get_zone_id(main)
            index += 1
        if zone_id:
            sub = ".".join(domain_split[:-index]) or '@'
            logging.info("zone_id: %s, sub: %s", zone_id, sub)
            return zone_id, sub
        return None,None


    def _split_custom_domain(self, domain):
        # type: (str) -> (str, str)
        """
        将形如 'sub~main.com' 或 'sub+main.com' 的域名拆分为 (子域, 主域)。
        若没有分隔符，则返回 (None, domain)
        """
        for sep in ('~', '+'):
            if sep in domain:
                sub, main = domain.split(sep, 1)
                return sub, main
        return None, domain


    def _https(self, method, url, _headers=None, **params):
        # type: (str, str, Dict[str, str], **Dict[str, Any]) -> Any
        """
        发送请求数据
        """
        method = method.upper()
        logging.info("[%s]%s : %s", method, url, params)
        if self.proxy:
            conn = HTTPSConnection(self.proxy)
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
            logging.warning('%s : error[%d]:%s', url, response.status, response.reason)
            logging.info(res)
            raise Exception(res)
        try:
            data = jsondecode(res)
            logging.debug('response:%s', data)
            return data
        except Exception as e:
            logging.error('fail to decode %s', e)
            raise e
