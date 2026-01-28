# coding=utf-8
"""
HTTP请求工具模块,SSL 代理，重试，basic-auth
HTTP utilities module, including ssl, proxies, retry and basicAuth.

@author: NewFuture
"""

from logging import getLogger
from re import compile
import ssl
import os
import time
import socket

from .. import __version__

try:  # python 3
    from urllib.request import (
        BaseHandler,
        build_opener,
        HTTPBasicAuthHandler,
        HTTPDefaultErrorHandler,
        HTTPPasswordMgrWithDefaultRealm,
        HTTPSHandler,
        ProxyHandler,
        Request,
    )
    from urllib.parse import quote, urlencode, unquote
    from http.client import HTTPSConnection
except ImportError:  # python 2
    from urllib2 import (  # type: ignore[no-redef]
        BaseHandler,
        build_opener,
        HTTPBasicAuthHandler,
        HTTPDefaultErrorHandler,
        HTTPPasswordMgrWithDefaultRealm,
        HTTPSHandler,
        ProxyHandler,
        Request,
    )
    from urllib import urlencode, quote, unquote  # type: ignore[no-redef]
    from httplib import HTTPSConnection  # type: ignore[no-redef]

__all__ = ["request", "HttpResponse", "quote", "urlencode", "USER_AGENT"]
# Default user-agent for DDNS requests
USER_AGENT = "DDNS/{} (ddns@newfuture.cc)".format(__version__ if __version__ != "${BUILD_VERSION}" else "dev")

logger = getLogger().getChild("http")
_AUTH_URL_RE = compile(r"^(https?://)([^:/?#]+):([^@]+)@(.+)$")


def _proxy_handler(proxy):
    # type: (str | None) -> ProxyHandler | None
    """标准化代理格式并返回ProxyHandler对象"""
    if not proxy or proxy.upper() in ("SYSTEM", "DEFAULT"):
        return ProxyHandler()  # 系统代理
    elif proxy.upper() in ("DIRECT"):
        return ProxyHandler({})  # 不使用代理
    elif "://" not in proxy:
        # 检查是否是 host:port 格式
        logger.warning("Legacy proxy format '%s' detected, converting to 'http://%s'", proxy, proxy)
        proxy = "http://" + proxy

    return ProxyHandler({"http": proxy, "https": proxy})


def request(method, url, data=None, headers=None, proxies=None, verify=True, auth=None, retries=1):
    # type: (str, str, str | bytes | None, dict[str, str] | None, list[str] | None, bool | str, BaseHandler | None, int) -> HttpResponse # noqa: E501
    """
    发送HTTP/HTTPS请求，支持自动重试和类似requests.request的参数接口

    Args:
        method (str): HTTP方法，如GET、POST等
        url (str): 请求的URL，支持嵌入式认证格式 https://user:pass@domain.com
        data (str | bytes | None): 请求体数据
        headers (dict[str, str] | None): 请求头字典
        proxies (list[str | None] | None): 代理列表，支持以下格式：
                                         - "http://host:port" - 具体代理地址
                                         - "DIRECT" - 直连，不使用代理
                                         - "SYSTEM" - 使用系统默认代理设置
        verify (bool | str): SSL验证配置
                            - True: 启用标准SSL验证
                            - False: 禁用SSL验证
                            - "auto": 启用验证，失败时自动回退到不验证
                            - str: 自定义CA证书文件路径
        auth (BaseHandler | None): 自定义认证处理器
        retries (int): 最大重试次数，默认1次

    Returns:
        HttpResponse: 响应对象

    Raises:
        URLError: 如果请求失败
        ssl.SSLError: 如果SSL验证失败
        ValueError: 如果参数无效
    """
    # 解析URL以检查是否包含嵌入式认证信息
    m = _AUTH_URL_RE.match(url)
    if m:
        protocol, username, password, rest = m.groups()
        url = protocol + rest
        auth = HTTPBasicAuthHandler(HTTPPasswordMgrWithDefaultRealm())
        auth.add_password(None, url, unquote(username), unquote(password))  # type: ignore[no-untyped-call]

    # 准备请求
    if isinstance(data, str):
        data = data.encode("utf-8")

    if headers is None:
        headers = {}
    if not any(k.lower() == "user-agent" for k in headers.keys()):
        headers["User-Agent"] = USER_AGENT  # 设置默认User-Agent

    handlers = [NoHTTPErrorHandler(), AutoSSLHandler(verify), RetryHandler(retries)]
    handlers += [auth] if auth else []

    def run(proxy_handler):
        req = Request(url, data=data, headers=headers)
        req.get_method = lambda: method.upper()  # python 2 兼容
        h = handlers + ([proxy_handler] if proxy_handler else [])
        return build_opener(*h).open(req, timeout=60 if method == "GET" else 120)  # 创建处理器链

    if not proxies:
        response = run(None)  # 默认
    else:
        last_err = None  # type: Exception # type: ignore[assignment]
        for p in proxies:
            logger.debug("Trying proxy: %s", p)
            try:
                response = run(_proxy_handler(p))  # 尝试使用代理
                break  # 成功后退出循环
            except Exception as e:
                last_err = e
        else:
            logger.error("All proxies failed")
            raise last_err  # 如果所有代理都失败，抛出最后一个错误

    # 处理响应
    response_headers = response.info()
    raw_body = response.read()
    decoded_body = _decode_response_body(raw_body, response_headers.get("Content-Type"))
    status_code = response.getcode()
    reason = getattr(response, "msg", "")

    return HttpResponse(status_code, reason, response_headers, decoded_body)


def _decode_response_body(raw_body, content_type):
    # type: (bytes, str | None) -> str
    """解码HTTP响应体，优先使用UTF-8"""
    if not raw_body:
        return ""

    # 从Content-Type提取charset
    charsets = ["utf-8", "gbk", "ascii", "latin-1"]
    if content_type and "charset=" in content_type.lower():
        start = content_type.lower().find("charset=") + 8
        end = content_type.find(";", start)
        if end == -1:
            end = len(content_type)
        charset = content_type[start:end].strip("'\" ").lower()

        # 处理常见别名映射
        charset_aliases = {"gb2312": "gbk", "iso-8859-1": "latin-1"}
        charset = charset_aliases.get(charset, charset)
        if charset in charsets:
            charsets.remove(charset)
        charsets.insert(0, charset)

    # 按优先级尝试解码
    for encoding in charsets:
        try:
            return raw_body.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue

    return raw_body.decode("utf-8", errors="replace")  # 最终后备：UTF-8替换错误字符


class HttpResponse(object):
    """HTTP响应封装类"""

    def __init__(self, status, reason, headers, body):
        # type: (int, str, Any, str) -> None
        """初始化HTTP响应对象"""
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body


class NoHTTPErrorHandler(HTTPDefaultErrorHandler):  # type: ignore[misc]
    """自定义HTTP错误处理器，处理所有HTTP错误状态码，返回响应而不抛出异常"""

    def http_error_default(self, req, fp, code, msg, hdrs):
        """处理所有HTTP错误状态码，返回响应而不抛出异常"""
        logger.info("HTTP error %s: %s", code, msg)
        return fp


class AutoSSLHandler(HTTPSHandler):  # type: ignore[misc]
    """SSL自动降级处理器，处理 unable to get local issuer certificate 错误"""

    _ssl_cache = {}  # type: dict[str, ssl.SSLContext|None]

    def __init__(self, verify):
        # type: (bool | str) -> None
        self._verify = verify
        self._context = self._ssl_context()
        # 兼容性：优先使用context参数，失败时降级
        try:  # python 3 / python 2.7.9+
            HTTPSHandler.__init__(self, context=self._context)
        except (TypeError, AttributeError):  # python 2.7.8-
            HTTPSHandler.__init__(self)

    def https_open(self, req):
        """处理HTTPS请求，自动处理SSL错误"""
        try:
            return self._open(req)
        except OSError as e:  # SSL auto模式：处理本地证书错误
            ssl_errors = ("unable to get local issuer certificate", "Basic Constraints of CA cert not marked critical")
            if self._verify == "auto" and any(err in str(e) for err in ssl_errors):
                logger.warning("SSL error (%s), switching to unverified connection", str(e))
                self._verify = False  # 不验证SSL
                self._context = self._ssl_context()  # 确保上下文已更新
                return self._open(req)  # 重试请求
            else:
                logger.debug("error: (%s)", e)
                raise

    def _open(self, req):
        try:  # python 3
            return self.do_open(HTTPSConnection, req, context=self._context)
        except (TypeError, AttributeError):  # python 2.7.6- Fallback for older Python versions
            logger.info("Falling back to parent https_open method for compatibility")
            return HTTPSHandler.https_open(self, req)

    def _ssl_context(self):
        # type: () -> ssl.SSLContext | None
        """创建或获取缓存的SSLContext"""
        cache_key = "default"  # 缓存键
        if not self._verify:
            cache_key = "unverified"
            if cache_key not in self._ssl_cache:
                self._ssl_cache[cache_key] = (
                    ssl._create_unverified_context() if hasattr(ssl, "_create_unverified_context") else None
                )
        elif hasattr(self._verify, "lower") and self._verify.lower() not in ("auto", "true"):  # type: ignore
            cache_key = str(self._verify)
            if cache_key not in self._ssl_cache:
                self._ssl_cache[cache_key] = ssl.create_default_context(cafile=cache_key)
        elif cache_key not in self._ssl_cache:
            self._ssl_cache[cache_key] = ssl.create_default_context()
            if not self._ssl_cache[cache_key].get_ca_certs():  # type: ignore
                logger.info("No system CA certificates found, loading default CA certificates")
                self._load_system_ca_certs(self._ssl_cache[cache_key])  # type: ignore

        return self._ssl_cache[cache_key]

    def _load_system_ca_certs(self, ssl_context):
        # type: (ssl.SSLContext) -> None
        """加载系统CA证书"""
        ca_paths = [
            # Linux/Unix常用路径
            "/etc/ssl/certs/ca-certificates.crt",  # Debian/Ubuntu
            "/etc/pki/tls/certs/ca-bundle.crt",  # RedHat/CentOS
            "/etc/ssl/ca-bundle.pem",  # OpenSUSE
            "/etc/ssl/cert.pem",  # OpenBSD
            "/usr/local/share/certs/ca-root-nss.crt",  # FreeBSD
            "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",  # Fedora/RHEL
            # macOS路径
            "/usr/local/etc/openssl/cert.pem",  # macOS with Homebrew
            "/opt/local/etc/openssl/cert.pem",  # macOS with MacPorts
        ]

        for ca_path in ca_paths:
            if os.path.isfile(ca_path):
                try:
                    ssl_context.load_verify_locations(ca_path)
                    logger.info("Loaded CA certificates from: %s", ca_path)
                    return  # 成功加载后立即返回
                except Exception as e:
                    logger.warning("Failed to load CA certificates from %s: %s", ca_path, e)


class RetryHandler(BaseHandler):  # type: ignore[misc]
    """HTTP重试处理器，自动重试指定状态码和网络错误"""

    handler_order = 100
    RETRY_CODES = (408, 429, 500, 502, 503, 504)

    def __init__(self, retries=3):
        # type: (int) -> None
        """初始化重试处理器"""
        self._in_retry = False  # 防止递归调用的标志
        self.retries = retries  # 始终设置retries属性
        if retries > 0:
            self.default_open = self._open

    def _open(self, req):
        """实际的重试逻辑，处理所有协议"""
        if self._in_retry:
            return None  # 防止递归调用

        self._in_retry = True

        try:
            for attempt in range(1, self.retries + 1):
                try:
                    res = self.parent.open(req, timeout=req.timeout)
                    if not hasattr(res, "getcode") or res.getcode() not in self.RETRY_CODES:
                        return res  # 成功响应直接返回
                    logger.warning("HTTP %d error, retrying in %d seconds", res.getcode(), 2**attempt)
                except (socket.timeout, socket.gaierror, socket.herror) as e:
                    logger.warning("Request failed, retrying in %d seconds: %s", 2**attempt, str(e))

                time.sleep(2**attempt)
                continue
            return self.parent.open(req, timeout=req.timeout)  # 最后一次尝试
        finally:
            self._in_retry = False
