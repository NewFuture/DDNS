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
        │ 查询 record:                        │
        │   _query_record(zone_id, sub, ...)  │
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
@author: NewFuture
"""

from os import environ
from abc import ABCMeta, abstractmethod
from json import loads as jsondecode, dumps as jsonencode
from logging import Logger

try:  # python 3
    from http.client import HTTPSConnection, HTTPConnection, HTTPException
    from urllib.parse import quote, urlencode, urlparse
except ImportError:  # python 2
    from httplib import HTTPSConnection, HTTPConnection, HTTPException  # type: ignore[no-redef,import-untyped]
    from urllib import urlencode, quote  # type: ignore[no-redef,import-untyped]
    from urlparse import urlparse  # type: ignore[no-redef,import-untyped]

TYPE_FORM = "application/x-www-form-urlencoded"
TYPE_JSON = "application/json"


class BaseProvider(object):
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
    API = ""  # type: str # https://exampledns.com
    # Content-Type for requests (to be defined in subclass)
    ContentType = TYPE_FORM  # type: Literal["application/x-www-form-urlencoded"] | Literal["application/json"]
    # Decode Response as JSON by default
    DecodeResponse = True

    # 版本
    Version = environ.get("DDNS_VERSION", "0.0.0")
    # Description
    Remark = "Managed by [DDNS v{}](https://ddns.newfuture.cc)".format(Version)

    def __init__(self, auth_id, auth_token, logger=None, **options):
        # type: (str, str, Logger | None, **object) -> None
        """
        初始化服务商对象

        Initialize provider instance.

        Args:
            auth_id (str): 身份认证 ID / Authentication ID
            auth_token (str): 密钥 / Authentication Token
            options (dict): 其它参数，如代理、调试等 / Additional options
        """
        self.auth_id = auth_id  # type: str
        self.auth_token = auth_token  # type: str
        self.options = options
        name = self.__class__.__name__
        self.logger = logger.getChild(name) if logger else Logger(name)
        self.proxy = None  # type: str | None
        self._zone_map = {}  # type: dict[str, str]
        self.logger.debug("%s initialized with auth_id: %s", self.__class__.__name__, auth_id)
        self._validate()  # 验证身份认证信息

    def get_zone_id(self, domain):
        # type: (str) -> str | None
        """
        查询指定域名对应的 zone_id

        Get zone_id for the domain.

        Args:
            domain (str): 主域名 / main name

        Returns:
            str | None: 区域 ID / Zone identifier
        """
        if domain in self._zone_map:
            return self._zone_map[domain]
        zone_id = self._query_zone_id(domain)
        if zone_id:
            self._zone_map[domain] = zone_id
        return zone_id

    @abstractmethod
    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """
        查询主域名的 zone ID

        Args:
            domain (str): 主域名

        Returns:
            str | None: Zone ID
        """
        return domain

    @abstractmethod
    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line=None, extra=None):
        # type: (str, str, str, str, str | None, dict | None) -> Any
        """
        查询 DNS 记录 ID

        Args:
            zone_id (str): 区域 ID
            sub_domain (str): 子域名
            main_domain (str): 主域名
            record_type (str): 记录类型，例如 A、AAAA
            line (str | None): 线路选项，可选
            extra (dict): 额外参数
        Returns:
            Any | None: 记录
        """
        raise NotImplementedError("This _query_record should be implemented by subclasses")

    @abstractmethod
    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, str, str, str, str, int | str | None, str | None, dict | None) -> bool
        """
        创建新 DNS 记录

        Args:
            zone_id (str): 区域 ID
            sub_domain (str): 子域名
            main_domain (str): 主域名
            value (str): 记录值
            record_type (str): 类型，如 A
            ttl (int | None): TTL 可选
            line (str | None): 线路选项
            extra (dict | None): 额外字段

        Returns:
            Any: 操作结果
        """
        raise NotImplementedError("This _create_record should be implemented by subclasses")

    @abstractmethod
    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, dict, str, str, int | str | None, str | None, dict | None) -> bool
        """
        更新已有 DNS 记录

        Args:
            zone_id (str): 区域 ID
            old_record (dict): 旧记录信息
            value (str): 新的记录值
            record_type (str): 类型
            ttl (int | None): TTL
            line (str | None): 线路
            extra (dict | None): 额外参数

        Returns:
            Any: 操作结果
        """
        pass

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        # type: (str, str, str, str | int | None, str | None, **dict) -> bool
        """
        设置 DNS 记录（创建或更新）

        Set or update DNS record.

        Args:
            domain (str): 完整域名
            value (str): 新记录值
            record_type (str): 记录类型
            ttl (int | None): TTL 值，可选
            line (str | None): 线路信息
            extra (dict): 额外参数

        Returns:
            Any: 执行结果
        """
        domain = domain.lower()
        self.logger.info("%s => %s(%s)", domain, value, record_type)

        sub, main = self._split_custom_domain(domain)
        if sub:
            zone_id = self.get_zone_id(main)
        else:
            zone_id, sub, main = self._split_zone_and_sub(domain)
        self.logger.info("sub: %s, main: %s(id=%s)", sub, main, zone_id)
        if not zone_id or sub is None:
            self.logger.critical("查询 zone_id 或 subdomain失败: %s", domain)
            raise ValueError("Cannot resolve zone_id or subdomain for " + domain)

        record = self._query_record(
            zone_id, sub_domain=sub, main_domain=main, record_type=record_type, line=line, extra=extra
        )
        if record:
            self.logger.info("Found existing record:\n  %s", record)
            return self._update_record(
                zone_id, old_record=record, value=value, record_type=record_type, ttl=ttl, line=line, extra=extra
            )
        else:
            self.logger.warning("No existing record found, creating new one")
            return self._create_record(
                zone_id,
                sub_domain=sub,
                main_domain=main,
                value=value,
                record_type=record_type,
                ttl=ttl,
                line=line,
                extra=extra,
            )

    def set_proxy(self, proxy_str):
        # type: (str | None) -> BaseProvider
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

    def _validate(self):
        # type: () -> None
        """
        验证身份认证信息是否填写

        Validate authentication credentials.
        """
        if not self.auth_id:
            raise ValueError("id must be configured")
        if not self.auth_token:
            raise ValueError("token must be configured")
        if not self.API:
            raise ValueError("API endpoint must be defined in {}".format(self.__class__.__name__))

    def _split_zone_and_sub(self, domain):
        # type: (str) -> tuple[str | None, str | None, str ]
        """
        从完整域名拆分主域名和子域名

        Args:
            domain (str): 完整域名

        Returns:
            (zone_id, sub): 元组
        """
        domain_split = domain.split(".")
        zone_id = None
        index = 2
        main = ""
        while not zone_id and index <= len(domain_split):
            main = ".".join(domain_split[-index:])
            zone_id = self.get_zone_id(main)
            index += 1
        if zone_id:
            sub = ".".join(domain_split[: -index + 1]) or "@"
            self.logger.debug("zone_id: %s, sub: %s", zone_id, sub)
            return zone_id, sub, main
        return None, None, main

    def _send_request(self, url, method="GET", body=None, headers=None):
        # type: (str, str, str | None, dict[str, str] | None) -> str
        """
        创建 HTTP/HTTPS 连接对象。
        Create HTTP/HTTPS connection object.
        """
        url_obj = urlparse(url)
        isHttps = url_obj.scheme == "https"
        hostname = url_obj.hostname  # type: str # type: ignore[assignment]
        ConnectionClass = HTTPSConnection if isHttps else HTTPConnection
        if self.proxy:
            conn = ConnectionClass(self.proxy)
            conn.set_tunnel(hostname, url_obj.port)
        else:
            conn = ConnectionClass(hostname, url_obj.port)
        url = "{}?{}".format(url_obj.path, url_obj.query) if url_obj.query else url_obj.path
        conn.request(method, url, body, headers=headers or {})
        response = conn.getresponse()
        res = response.read().decode("utf-8")
        conn.close()
        if not (response.status >= 200 and response.status < 300):
            self.logger.warning("%s : error[%d]: %s", url, response.status, response.reason)
            self.logger.info(res)
            raise HTTPException(res)
        return res

    def _http(self, method, url, params=None, body=None, queries=None, headers=None):  # noqa: C901
        # type: (str, str, dict[str,Any]|str|None, dict[str,Any]|str|None, dict[str,Any]|None, dict|None) -> Any
        """
        发送 HTTP/HTTPS 请求，自动根据 API/url 选择协议。

        Args:
            method (str): 请求方法，如 GET、POST
            url (str): 请求路径
            params (dict[str, Any] | None): 请求参数,自动处理 query string 或者body
            body (dict[str, Any] | str | None): 请求体内容
            queries (dict[str, Any] | None): 查询参数，自动处理为 URL 查询字符串
            headers (dict): 头部，可选        Returns:
            Any: 解析后的响应内容
        """
        method = method.upper()

        # 自动处理参数
        query_str = ""
        if params:
            if method in ("GET", "DELETE"):
                # 如果是 GET 或 DELETE 方法，参数放在查询字符串中
                if not isinstance(params, str):
                    # 如果 params 已经是字符串，则直接使用
                    queries = queries.update(params) if queries else params
                elif queries is None:
                    query_str = params
                else:
                    self.logger.error("params should not be used with queries for %s method", method)
            elif body is None:
                body = params
            else:
                self.logger.error("params should not be used with body for %s method", method)
        query_str = query_str or self._encode(queries)

        # 拼接URL
        if query_str:
            url += ("&" if "?" in url else "?") + query_str
        if not url.startswith("http://") and not url.startswith("https://"):
            if not url.startswith("/") and self.API.endswith("/"):
                url = "/" + url
            url = "{}{}".format(self.API, url)
        # 对URL进行打码处理后输出日志
        self.logger.info("%s %s", method, self._mask_sensitive_data(url))  # 主体
        bodyData = None
        if body:
            headers = headers or {}
            if "content-type" not in headers:
                headers["content-type"] = self.ContentType
            if isinstance(body, str):
                # 如果 body 已经是字符串，则不需要再次编码
                bodyData = body
            elif self.ContentType == TYPE_FORM:
                bodyData = self._encode(body)
            else:
                bodyData = jsonencode(body)
            # 对body进行打码处理后输出日志
            self.logger.debug("body: %s", self._mask_sensitive_data(bodyData))

        res = self._send_request(method=method, url=url, body=bodyData, headers=headers)
        if not self.DecodeResponse:
            # 如果不需要解码响应，则直接返回原始字符串
            self.logger.debug("response: %s", res)
            return res
        try:
            data = jsondecode(res)
            self.logger.debug("response: \n%s", data)
            return data
        except Exception as e:
            self.logger.error("fail to decode response: %s", e)
            raise e

    @staticmethod
    def _split_custom_domain(domain):
        # type: (str) -> tuple[str | None, str]
        """
        拆分支持 ~ 或 + 的自定义格式域名为 (子域, 主域)

        如 sub~example.com => ('sub', 'example.com')

        Returns:
            (sub, main): 子域 + 主域
        """
        for sep in ("~", "+"):
            if sep in domain:
                sub, main = domain.split(sep, 1)
                return sub, main
        return None, domain

    @staticmethod
    def _join_domain(sub, main):
        # type: (str | None, str) -> str
        """
        合并子域名和主域名为完整域名

        Args:
            sub (str | None): 子域名
            main (str): 主域名

        Returns:
            str: 完整域名
        """
        sub = sub and sub.strip(".").strip().lower()
        main = main and main.strip(".").strip().lower()
        if not sub or sub == "@":
            if not main:
                raise ValueError("Both sub and main cannot be empty")
            return main
        if not main:
            return sub
        return "{}.{}".format(sub, main)

    @staticmethod
    def _encode(params):
        # type: (dict|list|str|None) -> str
        """
        编码参数为 URL 查询字符串

        Args:
            params (dict|list): 参数字典或列表        Returns:
            str: 编码后的查询字符串
        """
        if not params or isinstance(params, str):
            return ""
        return urlencode(params, doseq=True)

    @staticmethod
    def _quote(data, safe="/", encoding=None, errors=None):
        # type: (str, str, str|None, str|None) -> str
        """
        对字符串进行 URL 编码

        Args:
            data (str): 待编码字符串

        Returns:
            str: 编码后的字符串
        """
        return quote(data, safe=safe, encoding=encoding, errors=errors)

    def _mask_sensitive_data(self, data):
        # type: (str | None) -> str
        """
        对敏感数据进行打码处理，用于日志输出

        Args:
            data (str | dict | None): 需要处理的数据
            is_url (bool): 是否为URL数据        Returns:
            str: 打码后的字符串
        """
        if not data or not self.auth_token:
            return data  # type: ignore[return-value]

        token_masked = "***"
        if self.auth_token and len(self.auth_token) > 4:
            token_masked = self.auth_token[:2] + "***" + self.auth_token[-2:]
        return data.replace(self.auth_token, token_masked)
