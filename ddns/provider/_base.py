# coding=utf-8
"""
## SimpleProvider 简单DNS抽象基类

* set_record()

## BaseProvider 标准DNS抽象基类
定义所有 DNS 服务商 API 类应继承的抽象基类，统一接口，便于扩展适配多服务商。

Abstract base class for DNS provider APIs.
Defines a unified interface to support extension and adaptation across providers.
* _query_zone_id
* _query_record
* _update_record
* _create_record
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

from abc import ABCMeta, abstractmethod
from hashlib import sha256
from hmac import HMAC
from json import loads as jsondecode, dumps as jsonencode
from logging import Logger, getLogger  # noqa:F401 # type: ignore[no-redef]
from os import environ
from ..util.http import send_http_request

try:  # python 3
    from urllib.parse import quote, urlencode
except ImportError:  # python 2
    from urllib import urlencode, quote  # type: ignore[no-redef,import-untyped]

TYPE_FORM = "application/x-www-form-urlencoded"
TYPE_JSON = "application/json"


def hmac_sha256(key, message):
    # type: (str | bytes, str | bytes) -> HMAC
    """
    计算 HMAC-SHA256 签名对象

    Compute HMAC-SHA256 signature object.

    Args:
        key (str | bytes): 签名密钥 / Signing key
        message (str | bytes): 待签名消息 / Message to sign

    Returns:
        HMAC: HMAC签名对象，可调用.digest()获取字节或.hexdigest()获取十六进制字符串
              HMAC signature object, call .digest() for bytes or .hexdigest() for hex string
    """
    # Python 2/3 compatible encoding - avoid double encoding in Python 2
    if not isinstance(key, bytes):
        key = key.encode("utf-8")
    if not isinstance(message, bytes):
        message = message.encode("utf-8")
    return HMAC(key, message, sha256)


def sha256_hash(data):
    # type: (str | bytes) -> str
    """
    计算 SHA256 哈希值

    Compute SHA256 hash.

    Args:
        data (str | bytes): 待哈希数据 / Data to hash

    Returns:
        str: 十六进制哈希字符串 / Hexadecimal hash string
    """
    # Python 2/3 compatible encoding - avoid double encoding in Python 2
    if not isinstance(data, bytes):
        data = data.encode("utf-8")
    return sha256(data).hexdigest()


def hmac_sha256_authorization(
    secret_key,  # type: str | bytes
    method,  # type: str
    path,  # type: str
    query,  # type: str
    headers,  # type: dict[str, str]
    body_hash,  # type: str
    signing_string_format,  # type: str
    authorization_format,  # type: str
):
    # type: (...) -> str
    """
    HMAC-SHA256 云服务商通用认证签名生成器

    Universal cloud provider authentication signature generator using HMAC-SHA256.

    通用的云服务商API认证签名生成函数，使用HMAC-SHA256算法生成符合各云服务商规范的Authorization头部。

    模板变量格式：{HashedCanonicalRequest}, {SignedHeaders}, {Signature}

    Args:
        secret_key (str | bytes): 签名密钥，已经过密钥派生处理 / Signing key (already derived if needed)
        method (str): HTTP请求方法 / HTTP request method (GET, POST, etc.)
        path (str): API请求路径 / API request path
        query (str): URL查询字符串 / URL query string
        headers (dict[str, str]): HTTP请求头部 / HTTP request headers
        body_hash (str): 请求体的SHA256哈希值 / SHA256 hash of request payload
        signing_string_format (str): 待签名字符串模板，包含 {HashedCanonicalRequest} 占位符
        authorization_format (str): Authorization头部模板，包含 {SignedHeaders}, {Signature} 占位符

    Returns:
        str: 完整的Authorization头部值 / Complete Authorization header value
    """
    # 1. 构建规范化头部 - 所有传入的头部都参与签名
    headers_to_sign = {k.lower(): str(v).strip() for k, v in headers.items()}
    signed_headers_list = sorted(headers_to_sign.keys())

    # 2. 构建规范请求字符串
    canonical_headers = ""
    for header_name in signed_headers_list:
        canonical_headers += "{}:{}\n".format(header_name, headers_to_sign[header_name])

    # 构建完整的规范请求字符串
    signed_headers = ";".join(signed_headers_list)
    canonical_request = "\n".join([method.upper(), path, query, canonical_headers, signed_headers, body_hash])

    # 3. 构建待签名字符串 - 只需要替换 HashedCanonicalRequest
    hashed_canonical_request = sha256_hash(canonical_request)
    string_to_sign = signing_string_format.format(HashedCanonicalRequest=hashed_canonical_request)

    # 4. 计算最终签名
    signature = hmac_sha256(secret_key, string_to_sign).hexdigest()

    # 5. 构建Authorization头部 - 只需要替换 SignedHeaders 和 Signature
    authorization = authorization_format.format(SignedHeaders=signed_headers, Signature=signature)

    return authorization


class SimpleProvider(object):
    """
    简单DNS服务商接口的抽象基类, 必须实现 `set_record` 方法。

    Abstract base class for all simple DNS provider APIs.
    Subclasses must implement `set_record`.

    * set_record(domain, value, record_type="A", ttl=None, line=None, **extra)
    """

    __metaclass__ = ABCMeta

    # API endpoint domain (to be defined in subclass)
    API = ""  # type: str # https://exampledns.com
    # Content-Type for requests (to be defined in subclass)
    content_type = TYPE_FORM  # type: Literal["application/x-www-form-urlencoded"] | Literal["application/json"]
    # 默认 accept 头部, 空则不设置
    accept = TYPE_JSON  # type: str | None
    # Decode Response as JSON by default
    decode_response = True
    # 是否验证 SSL 证书，默认为 True
    verify_ssl = "auto"  # type: bool | str

    # 版本
    version = environ.get("DDNS_VERSION", "0.0.0")
    # Description
    remark = "Managed by [DDNS v{}](https://ddns.newfuture.cc)".format(version)

    def __init__(self, auth_id, auth_token, logger=None, verify_ssl=None, **options):
        # type: (str, str, Logger | None, bool|str| None, **object) -> None
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
        self.logger = (logger or getLogger()).getChild(name)
        self.proxy = None  # type: str | None
        if verify_ssl is not None:
            self.verify_ssl = verify_ssl
        self._zone_map = {}  # type: dict[str, str]
        self.logger.debug("%s initialized with: %s", self.__class__.__name__, auth_id)
        self._validate()  # 验证身份认证信息

    @abstractmethod
    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        # type: (str, str, str, str | int | None, str | None, **object) -> bool
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
        raise NotImplementedError("This set_record should be implemented by subclasses")

    def set_proxy(self, proxy_str):
        # type: (str | None) -> SimpleProvider
        """
        设置代理服务器

        Set HTTPS proxy string.

        Args:
            proxy_str (str): 代理地址

        Returns:
            Self: 自身
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
            headers (dict): 头部，可选

        Returns:
            Any: 解析后的响应内容

        Raises:
            RuntimeError: 当响应状态码为400/401或5xx(服务器错误)时抛出异常
        """
        method = method.upper()

        # 简化参数处理逻辑
        query_params = queries or {}
        if params:
            if method in ("GET", "DELETE"):
                if isinstance(params, dict):
                    query_params.update(params)
                else:
                    # params是字符串，直接作为查询字符串
                    url += ("&" if "?" in url else "?") + str(params)
                    params = None
            elif body is None:
                body = params

        # 构建查询字符串
        if len(query_params) > 0:
            url += ("&" if "?" in url else "?") + self._encode(query_params)

        # 构建完整URL
        if not url.startswith("http://") and not url.startswith("https://"):
            if not url.startswith("/") and self.API.endswith("/"):
                url = "/" + url
            url = self.API + url

        # 记录请求日志
        self.logger.info("%s %s", method, self._mask_sensitive_data(url))

        # 处理请求体
        body_data, headers = None, headers or {}
        if body:
            if "content-type" not in headers:
                headers["content-type"] = self.content_type
            if isinstance(body, (str, bytes)):
                body_data = body
            elif self.content_type == TYPE_FORM:
                body_data = self._encode(body)
            else:
                body_data = jsonencode(body)
            self.logger.debug("body:\n%s", self._mask_sensitive_data(body_data))

        # 处理headers
        if self.accept and "accept" not in headers and "Accept" not in headers:
            headers["accept"] = self.accept
        if len(headers) > 2:
            self.logger.debug("headers:\n%s", {k: self._mask_sensitive_data(v) for k, v in headers.items()})

        response = send_http_request(
            url=url,
            method=method,
            body=body_data,
            headers=headers,
            proxy=self.proxy,
            max_redirects=5,
            verify_ssl=self.verify_ssl,
        )

        # 处理响应
        status_code = response.status
        if not (200 <= status_code < 300):
            self.logger.warning("response status: %s %s", status_code, response.reason)

        res = response.body
        # 针对客户端错误、认证/授权错误和服务器错误直接抛出异常
        if status_code >= 500 or status_code in (400, 401, 403):
            self.logger.error("HTTP error:\n%s", res)
            if status_code == 400:
                raise RuntimeError("请求参数错误 [400]: " + response.reason)
            elif status_code == 401:
                raise RuntimeError("认证失败 [401]: " + response.reason)
            elif status_code == 403:
                raise RuntimeError("权限不足 [403]: " + response.reason)
            else:
                raise RuntimeError("服务器错误 [{}]: {}".format(status_code, response.reason))

        self.logger.debug("response:\n%s", res)
        if not self.decode_response:
            return res

        try:
            return jsondecode(res)
        except Exception as e:
            self.logger.error("fail to decode response: %s", e)
        return res

    @staticmethod
    def _encode(params):
        # type: (dict|list|str|bytes|None) -> str
        """
        编码参数为 URL 查询字符串

        Args:
            params (dict|list|str|bytes|None): 参数字典、列表或字符串
        Returns:
            str: 编码后的查询字符串
        """
        if not params:
            return ""
        elif isinstance(params, (str, bytes)):
            return params  # type: ignore[return-value]
        return urlencode(params, doseq=True)

    @staticmethod
    def _quote(data, safe="/"):
        # type: (str, str) -> str
        """
        对字符串进行 URL 编码

        Args:
            data (str): 待编码字符串

        Returns:
            str: 编码后的字符串
        """
        return quote(data, safe=safe)

    def _mask_sensitive_data(self, data):
        # type: (str | bytes | None) -> str | bytes | None
        """
        对敏感数据进行打码处理，用于日志输出，支持URL编码的敏感信息

        Args:
            data (str | bytes | None): 需要处理的数据
        Returns:
            str | bytes | None: 打码后的字符串
        """
        if not data or not self.auth_token:
            return data

        # 生成打码后的token
        token_masked = self.auth_token[:2] + "***" + self.auth_token[-2:] if len(self.auth_token) > 4 else "***"
        token_encoded = quote(self.auth_token, safe="")

        if isinstance(data, bytes):  # 处理字节数据
            return data.replace(self.auth_token.encode(), token_masked.encode()).replace(
                token_encoded.encode(), token_masked.encode()
            )
        if hasattr(data, "replace"):  # 处理字符串数据
            return data.replace(self.auth_token, token_masked).replace(token_encoded, token_masked)
        return data


class BaseProvider(SimpleProvider):
    """
    标准DNS服务商接口的抽象基类

    Abstract base class for all standard DNS provider APIs.
    Subclasses must implement the abstract methods to support various providers.

    * _query_zone_id()
    * _query_record_id()
    * _update_record()
    * _create_record()
    """

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        # type: (str, str, str, str | int | None, str | None, **Any) -> bool
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
            bool: 执行结果
        """
        domain = domain.lower()
        self.logger.info("%s => %s(%s)", domain, value, record_type)
        sub, main = split_custom_domain(domain)
        try:
            if sub is not None:
                # 使用自定义分隔符格式
                zone_id = self.get_zone_id(main)
            else:
                # 自动分析域名
                zone_id, sub, main = self._split_zone_and_sub(domain)

            self.logger.info("sub: %s, main: %s(id=%s)", sub, main, zone_id)
            if not zone_id or sub is None:
                self.logger.critical("找不到 zone_id 或 subdomain: %s", domain)
                return False

            # 查询现有记录
            record = self._query_record(zone_id, sub, main, record_type=record_type, line=line, extra=extra)

            # 更新或创建记录
            if record:
                self.logger.info("Found existing record: %s", record)
                return self._update_record(zone_id, record, value, record_type, ttl=ttl, line=line, extra=extra)
            else:
                self.logger.warning("No existing record found, creating new one")
                return self._create_record(zone_id, sub, main, value, record_type, ttl=ttl, line=line, extra=extra)
        except Exception as e:
            self.logger.exception("Error setting record for %s: %s", domain, e)
            return False

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
    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> Any
        """
        查询 DNS 记录 ID

        Args:
            zone_id (str): 区域 ID
            subdomain (str): 子域名
            main_domain (str): 主域名
            record_type (str): 记录类型，例如 A、AAAA
            line (str | None): 线路选项，可选
            extra (dict): 额外参数
        Returns:
            Any | None: 记录
        """
        raise NotImplementedError("This _query_record should be implemented by subclasses")

    @abstractmethod
    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | str | None, str | None, dict) -> bool
        """
        创建新 DNS 记录

        Args:
            zone_id (str): 区域 ID
            subdomain (str): 子域名
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
    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
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
            bool: 操作结果
        """
        raise NotImplementedError("This _update_record should be implemented by subclasses")

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


def split_custom_domain(domain):
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


def join_domain(sub, main):
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
