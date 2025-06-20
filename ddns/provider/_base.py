# coding=utf-8

"""
BaseDNSProvider 抽象基类
定义所有 DNS 服务商 API 类应继承的抽象基类，统一接口，便于扩展适配多服务商。

Abstract base class for DNS provider APIs.
Defines a unified interface to support extension and adaptation across providers.


┌──────────────────────────────────────────────────┐
│        用户调用 set_record(domain, value...)      │
└──────────────────────────────────────────────────┘
                      │
                      ▼
     ┌──────────────────────────────────────┐
     │   快速解析 是否包含 ~ 或 + 分隔符？    │
     └──────────────────────────────────────┘
            │                         │
       [是，拆解成功]             [否，无法拆解]
 sub 和 main│                         │ domain
            ▼                         ▼
┌────────────────────────┐   ┌──────────────────────────┐
│ 查询 zone_id           │   │ 自动循环解析   while:     │
│  _query_zone_id(main)  │   │  _query_zone_id(...)     │
└────────────────────────┘   └──────────────────────────┘
            │                         │
            ▼                         ▼
      zone_id ←──────────────┬─── sub
                             ▼
        ┌─────────────────────────────────────┐
        │ 查询 record_id:                     │
        │ _query_record_id(zone_id, sub, ...) │
        └─────────────────────────────────────┘
                          │
            ┌─────────────┴────────────────┐
            │    record_id 是否存在？       │
            └────────────┬─────────────────┘
                         │
          ┌──────────────┴─────────────┐
          │                            │
          ▼                            ▼
┌─────────────────────┐      ┌─────────────────────┐
│ 更新记录             │      │ 创建记录            │
│ _update_record(...) │      │ _create_record(...) │
└─────────────────────┘      └─────────────────────┘
          │                            │
          ▼                            ▼
        ┌───────────────────────────────┐
        │         返回操作结果           │
        └───────────────────────────────┘
"""

from abc import ABCMeta, abstractmethod, ABC
from json import loads as jsondecode, dumps as jsonencode
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
    DNS服务商接口的抽象基类

    Abstract base class for all DNS provider APIs.
    Subclasses must implement the abstract methods to support various providers.

    * _query_zone_id()
    * _query_record_id()
    * _update_record()
    * _create_record()
    """

    __metaclass__ = ABCMeta

    # API endpoint domain (to be defined in subclass)
    API = ''
    # 默认 Content-Type
    ContentType = TYPE_FORM

    def __init__(self, auth_id, auth_token, **options):
        # type: (str, str, **any) -> None
        """
        初始化服务商对象

        Initialize provider instance.

        Args:
            auth_id (str): 身份认证 ID / Authentication ID
            auth_token (str): 密钥 / Authentication Token
            options (dict): 其它参数，如代理、调试等 / Additional options
        """
        self.auth_id = auth_id  # type: string
        self.auth_token = auth_token  # type: string
        self.options = options
        self._zone_map={} # type: dict[str, str]
        self.proxy = None # type: str
        
    def get_zone_id(self, domain):
        # type: (str) -> str or None
        """
        查询指定域名对应的 zone_id

        Get zone_id for the domain.

        Args:
            domain (str): 主域名 / main name

        Returns:
            str or None: 区域 ID / Zone identifier
        """
        if domain in self._zone_map:
            return self._zone_map[domain]
        zone_id = self._query_zone_id(domain)
        if zone_id:
            self._zone_map[domain] = zone_id
        return zone_id

    @abstractmethod
    def _query_zone_id(self, domain):
        # type: (str) -> str or None
        """
        查询主域名的 zone ID

        Args:
            domain (str): 主域名

        Returns:
            str or None: Zone ID
        """
        return domain

    @abstractmethod
    def _query_record_id(self, zone_id, sub, record_type, line=None):
        # type: (str, str, str, str or None) -> str or None
        """
        查询 DNS 记录 ID

        Args:
            zone_id (str): 区域 ID
            sub (str): 子域名
            record_type (str): 记录类型，例如 A、AAAA
            line (str or None): 线路选项，可选

        Returns:
            str or None: 记录 ID
        """
        return sub

    @abstractmethod
    def _create_record(self, zone_id, sub, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, str, str, str, int or None, str or None, dict or None) -> Any
        """
        创建新 DNS 记录

        Args:
            zone_id (str): 区域 ID
            sub (str): 子域名
            value (str): 记录值
            record_type (str): 类型，如 A
            ttl (int or None): TTL 可选
            line (str or None): 线路选项
            extra (dict or None): 额外字段

        Returns:
            Any: 操作结果
        """
        pass

    @abstractmethod
    def _update_record(self, zone_id, record_id, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, str, str, str, int or None, str or None, dict or None) -> Any
        """
        更新已有 DNS 记录

        Args:
            zone_id (str): 区域 ID
            record_id (str): 要更新的记录 ID
            value (str): 新的记录值
            record_type (str): 类型
            ttl (int or None): TTL
            line (str or None): 线路
            extra (dict or None): 额外参数

        Returns:
            Any: 操作结果
        """
        pass

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        # type: (str, str, str, int or None, str or None, **dict) -> Any
        """
        设置 DNS 记录（创建或更新）

        Set or update DNS record.

        Args:
            domain (str): 完整域名
            value (str): 新记录值
            record_type (str): 记录类型
            ttl (int or None): TTL 值，可选
            line (str or None): 线路信息
            extra (dict): 额外参数

        Returns:
            Any: 执行结果
        """
        domain = domain.lower()
        logging.info("start update %s(%s) => %s", domain, record_type, value)

        sub, main = self._split_custom_domain(domain)
        if sub:
            zone_id = self.get_zone_id(main)
        else:
            zone_id, sub = self._split_zone_and_sub(domain)

        if not zone_id or not sub:
            raise ValueError("Cannot resolve zone_id or subdomain for " + domain)

        record_id = self._query_record_id(zone_id, sub, record_type, line)
        if record_id:
            return self._update_record(zone_id, record_id, value, record_type, ttl, line, extra)
        else:
            return self._create_record(zone_id, sub, value, record_type, ttl, line, extra)

    def set_proxy(self, proxy_str):
        # type: (str) -> BaseProvider
        """
        设置代理服务器

        Set HTTPS proxy string.

        Args:
            proxy_str (str): 代理地址

        Returns:
            BaseProvider: 自身
        """
        self.proxy = proxy_str
        return self

    def _split_zone_and_sub(self, domain):
        # type: (str) -> (str or None, str or None)
        """
        从完整域名拆分主域名和子域名

        Args:
            domain (str): 完整域名

        Returns:
            (zone_id, sub): 元组
        """
        domain_split = domain.split('.')
        zone_id = None
        index = 2
        while not zone_id and index <= len(domain_split):
            main = '.'.join(domain_split[-index:])
            zone_id = self.get_zone_id(main)
            index += 1
        if zone_id:
            sub = '.'.join(domain_split[:-index + 1]) or '@'
            logging.info("zone_id: %s, sub: %s", zone_id, sub)
            return zone_id, sub
        return None, None

    def _split_custom_domain(self, domain):
        # type: (str) -> (str or None, str)
        """
        拆分支持 ~ 或 + 的自定义格式域名为 (子域, 主域)

        如 sub~example.com => ('sub', 'example.com')

        Returns:
            (sub, main): 子域 + 主域
        """
        for sep in ('~', '+'):
            if sep in domain:
                sub, main = domain.split(sep, 1)
                return sub, main
        return None, domain

    def _https(self, method, url, _headers=None, **params):
        # type: (str, str, dict, **dict) -> Any
        """
        发送 HTTPS 请求

        Args:
            method (str): 请求方法，如 GET、POST
            url (str): 请求路径
            _headers (dict): 头部，可选
            params (dict): 请求参数

        Returns:
            Any: 解析后的响应内容
        """
        method = method.upper()
        logging.info("[%s] %s : %s", method, url, params)

        if self.proxy:
            conn = HTTPSConnection(self.proxy)
            conn.set_tunnel(self.API, 443)
        else:
            conn = HTTPSConnection(self.API)

        if method in ['GET', 'DELETE'] and params:
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
        res = response.read().decode('utf-8')
        conn.close()

        if response.status < 200 or response.status >= 300:
            logging.warning('%s : error[%d]: %s', url, response.status, response.reason)
            logging.info(res)
            raise Exception(res)

        try:
            data = jsondecode(res)
            logging.debug('response: %s', data)
            return data
        except Exception as e:
            logging.error('fail to decode response: %s', e)
            raise
