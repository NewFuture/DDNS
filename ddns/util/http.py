# coding=utf-8
"""
HTTP请求工具模块

HTTP utilities module for DDNS project.
Provides common HTTP functionality including ssl, proxy, and basicauth.

@author: NewFuture
"""

from logging import getLogger
from re import compile
import ssl
import os
import time
import socket

try:  # python 3
    from urllib.request import (  # noqa: F401
        HTTPBasicAuthHandler,
        HTTPSHandler,
        BaseHandler,
        Request,
        HTTPPasswordMgrWithDefaultRealm,
        HTTPDefaultErrorHandler,
        ProxyHandler,
        build_opener,
    )
    from urllib.parse import quote, urlencode, unquote
    from urllib.error import URLError, HTTPError
    import http.client
    # Python 3 specific exceptions
    RETRY_EXCEPTIONS = (
        URLError,
        socket.timeout,
        TimeoutError,
        http.client.RemoteDisconnected,
        ConnectionResetError,
    )
except ImportError:  # python 2
    from urllib2 import (  # type: ignore[no-redef]
        Request,
        HTTPSHandler,
        ProxyHandler,
        HTTPDefaultErrorHandler,
        HTTPPasswordMgrWithDefaultRealm,
        HTTPBasicAuthHandler,
        build_opener,
        URLError,
        HTTPError,
    )
    from urllib import urlencode, quote, unquote  # type: ignore[no-redef]
    import httplib  # type: ignore[import]
    # Python 2 specific exceptions (some may not exist)
    RETRY_EXCEPTIONS = (
        URLError,
        socket.timeout,
    )
    # Add exceptions that exist in Python 2
    try:
        # ConnectionResetError exists in Python 2.7 on some systems
        RETRY_EXCEPTIONS += (ConnectionResetError,)  # type: ignore[name-defined]
    except NameError:
        pass
    try:
        # Some systems may have httplib equivalents
        RETRY_EXCEPTIONS += (httplib.BadStatusLine,)
    except AttributeError:
        pass


__all__ = ["send_http_request", "request", "HttpResponse", "quote", "urlencode"]

logger = getLogger().getChild(__name__)
_AUTH_URL_RE = compile(r"^(https?://)([^:/?#]+):([^@]+)@(.+)$")

# Default retry status codes that should trigger retries
RETRY_STATUS_CODES = (408, 429, 500, 502, 503, 504)


class NoHTTPErrorProcessor(HTTPDefaultErrorHandler):  # type: ignore[misc]
    """自定义HTTP错误处理器，处理所有HTTP错误状态码，返回响应而不抛出异常"""

    def http_error_default(self, req, fp, code, msg, hdrs):
        """处理所有HTTP错误状态码，返回响应而不抛出异常"""
        logger.warning("HTTP error %s: %s", code, msg)
        return fp


class SSLAutoFallbackHandler(HTTPSHandler):  # type: ignore[misc]
    """SSL自动降级处理器，处理 unable to get local issuer certificate 错误"""

    # 类级别的SSL上下文缓存
    _ssl_cache = {}  # type: dict[str, ssl.SSLContext]

    def __init__(self, verify_ssl):
        # type: (bool | str) -> None
        self._verify_ssl = verify_ssl
        ssl_context = self._get_ssl_context()
        # 兼容性：优先使用context参数，失败时降级
        try:  # python 3 / python 2.7.9+
            HTTPSHandler.__init__(self, context=ssl_context)
        except (TypeError, AttributeError):  # python 2.7.8-
            HTTPSHandler.__init__(self)

    def _get_ssl_context(self):
        # type: () -> ssl.SSLContext | None
        """创建或获取缓存的SSLContext"""
        # 缓存键
        cache_key = "default"
        if not self._verify_ssl:
            if not hasattr(ssl, "_create_unverified_context"):
                return None
            cache_key = "unverified"
            if cache_key not in self._ssl_cache:
                self._ssl_cache[cache_key] = ssl._create_unverified_context()
        elif hasattr(self._verify_ssl, "lower") and self._verify_ssl.lower() not in ("auto", "true"):  # type: ignore
            cache_key = str(self._verify_ssl)
            if cache_key not in self._ssl_cache:
                self._ssl_cache[cache_key] = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cache_key)
        elif cache_key not in self._ssl_cache:
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            if not ssl_context.get_ca_certs():
                logger.warning("No system CA certificates found, loading default CA certificates")
                _load_system_ca_certs(ssl_context)
            self._ssl_cache[cache_key] = ssl_context

        return self._ssl_cache[cache_key]

    def https_open(self, req):
        """处理HTTPS请求，自动处理SSL错误"""
        try:
            return HTTPSHandler.https_open(self, req)
        except Exception as e:
            # SSL auto模式：只处理 unable to get local issuer certificate 错误
            if self._verify_ssl == "auto" and "unable to get local issuer certificate" in str(e).lower():
                msg = "unable to get local issuer certificate, switching to unverified connection for %s"
                logger.warning(msg, req.get_full_url())
                self._verify_ssl = False
                # 创建不验证SSL的临时处理器重试
                try:  # python 3 / python 2.7.9+
                    temp_handler = HTTPSHandler(context=self._get_ssl_context())
                except (TypeError, AttributeError):  # python 2.7.8-
                    temp_handler = HTTPSHandler()
                return temp_handler.https_open(req)
            else:
                raise


class RetryHandler(BaseHandler):  # type: ignore[misc]
    """HTTP重试处理器，自动重试指定状态码和网络错误"""

    def __init__(self, retries=3, retry_codes=None):
        # type: (int, tuple | None) -> None
        """
        初始化重试处理器
        
        Args:
            retries (int): 最大重试次数
            retry_codes (tuple | None): 需要重试的HTTP状态码，默认为RETRY_STATUS_CODES
        """
        self.retries = retries
        self.retry_codes = retry_codes or RETRY_STATUS_CODES

    def http_open(self, req):
        """处理HTTP请求，实现自动重试逻辑"""
        return self._retry_request(req, 'http')

    def https_open(self, req):
        """处理HTTPS请求，实现自动重试逻辑"""
        return self._retry_request(req, 'https')

    def _retry_request(self, req, protocol):
        """实际的重试逻辑"""
        last_err = None
        for i in range(self.retries + 1):
            try:
                # 移除自己，让其他处理器处理请求
                parent = self.parent
                # 创建一个临时opener，不包含RetryHandler
                temp_handlers = [h for h in parent.handlers if not isinstance(h, RetryHandler)]
                temp_opener = build_opener(*temp_handlers)
                
                resp = temp_opener.open(req)
                if hasattr(resp, 'getcode') and resp.getcode() in self.retry_codes:
                    # 对于需要重试的状态码，抛出HTTPError以触发重试
                    try:
                        # Python 3
                        from urllib.error import HTTPError as UrllibHTTPError
                        raise UrllibHTTPError(req.get_full_url(), resp.getcode(), "Retryable", resp.headers, resp)
                    except ImportError:
                        # Python 2
                        from urllib2 import HTTPError as Urllib2HTTPError  # type: ignore[import]
                        raise Urllib2HTTPError(req.get_full_url(), resp.getcode(), "Retryable", resp.headers, resp)
                return resp
            except Exception as e:
                # 首先检查是否为HTTPError，处理状态码逻辑
                if hasattr(e, 'code'):
                    if e.code in self.retry_codes:
                        last_err = e
                        if i < self.retries:
                            wait_time = 2 ** i
                            logger.warning("HTTP %d error, retrying in %d seconds: %s", e.code, wait_time, str(e))
                            time.sleep(wait_time)
                            continue  # 重试
                        else:
                            logger.error("Request failed after %d retries with HTTP %d: %s", self.retries, e.code, str(e))
                            raise
                    else:
                        # 不重试的HTTP状态码直接抛出
                        raise
                
                # 然后检查是否为网络异常
                if isinstance(e, RETRY_EXCEPTIONS):
                    last_err = e
                    if i < self.retries:
                        wait_time = 2 ** i
                        logger.warning("Request failed, retrying in %d seconds: %s", wait_time, str(e))
                        time.sleep(wait_time)
                        continue  # 重试
                    else:
                        logger.error("Request failed after %d retries: %s", self.retries, str(e))
                        raise
                
                # 其他异常直接抛出
                raise


class HttpResponse(object):
    """HTTP响应封装类"""

    def __init__(self, status, reason, headers, body):
        # type: (int, str, Any, str) -> None
        """
        初始化HTTP响应对象

        Args:
            status (int): HTTP状态码
            reason (str): 状态原因短语
            headers (Any): 响应头对象，直接使用 response.info()
            body (str): 响应体内容
        """
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body


def _load_system_ca_certs(ssl_context):
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


def send_http_request(method, url, body=None, headers=None, proxy=None, verify_ssl=True, auth_handler=None):
    # type: (str, str, str | bytes | None, dict[str, str] | None, str | None, bool | str, BaseHandler | None) -> HttpResponse # noqa: E501
    """
    发送HTTP/HTTPS请求，支持重定向跟随和灵活的SSL验证

    Args:
        method (str): HTTP方法，如GET、POST等
        url (str): 请求的URL，支持嵌入式认证格式 https://user:pass@domain.com
        body (str | bytes | None): 请求体
        headers (dict[str, str] | None): 请求头
        proxy (str | None): 代理地址，格式为 http://proxy:port
        verify_ssl (bool | str): SSL验证配置
                                - True: 启用标准SSL验证
                                - False: 禁用SSL验证
                                - "auto": 启用验证，失败时自动回退到不验证
                                - str: 自定义CA证书文件路径
        auth_handler (BaseHandler | None): 自定义认证处理器

    Returns:
        HttpResponse: 响应对象

    Raises:
        URLError: 如果请求失败
        ssl.SSLError: 如果SSL验证失败
    """
    # 解析URL以检查是否包含嵌入式认证信息
    m = _AUTH_URL_RE.match(url)
    if m:
        protocol, username, password, rest = m.groups()
        clean_url = protocol + rest
        password_mgr = HTTPPasswordMgrWithDefaultRealm()  # 使用urllib的内置认证机制
        password_mgr.add_password(None, clean_url, unquote(username), unquote(password))
        auth_handler = HTTPBasicAuthHandler(password_mgr)
        url = clean_url

    # 准备请求
    if isinstance(body, str):
        body = body.encode("utf-8")

    req = Request(url, data=body)
    req.get_method = lambda: method  # type: ignore[attr-defined]

    if headers:
        for key, value in headers.items():
            req.add_header(key, value)

    # 创建opener并发送请求
    handlers = [NoHTTPErrorProcessor(), SSLAutoFallbackHandler(verify_ssl=verify_ssl)]  # type: list[BaseHandler]
    if proxy:
        handlers.append(ProxyHandler({"http": proxy, "https": proxy}))
    if auth_handler:
        handlers.append(auth_handler)
    opener = build_opener(*handlers)
    response = opener.open(req)

    # 处理响应
    response_headers = response.info()
    raw_body = response.read()
    decoded_body = _decode_response_body(raw_body, response_headers.get("Content-Type"))
    status_code = response.getcode()
    reason = getattr(response, "msg", "")

    return HttpResponse(status_code, reason, response_headers, decoded_body)


def request(method, url, data=None, headers=None, proxies=None, verify=True, auth=None, retries=3):
    # type: (str, str, str | bytes | None, dict[str, str] | None, dict[str, str] | None, bool | str, BaseHandler | None, int) -> HttpResponse # noqa: E501
    """
    发送HTTP/HTTPS请求，支持自动重试和类似requests.request的参数接口
    
    Args:
        method (str): HTTP方法，如GET、POST等
        url (str): 请求的URL，支持嵌入式认证格式 https://user:pass@domain.com
        data (str | bytes | None): 请求体数据
        headers (dict[str, str] | None): 请求头字典
        proxies (dict[str, str] | None): 代理配置，格式为 {'http': 'proxy_url', 'https': 'proxy_url'}
        verify (bool | str): SSL验证配置
                            - True: 启用标准SSL验证
                            - False: 禁用SSL验证
                            - "auto": 启用验证，失败时自动回退到不验证
                            - str: 自定义CA证书文件路径
        auth (BaseHandler | None): 自定义认证处理器
        retries (int): 最大重试次数，默认3次
        
    Returns:
        HttpResponse: 响应对象
        
    Raises:
        URLError: 如果请求失败
        ssl.SSLError: 如果SSL验证失败
    """
    # 解析URL以检查是否包含嵌入式认证信息
    m = _AUTH_URL_RE.match(url)
    if m:
        protocol, username, password, rest = m.groups()
        clean_url = protocol + rest
        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, clean_url, unquote(username), unquote(password))
        auth = HTTPBasicAuthHandler(password_mgr)
        url = clean_url

    # 准备请求
    if isinstance(data, str):
        data = data.encode("utf-8")

    req = Request(url, data=data)
    req.get_method = lambda: method  # type: ignore[attr-defined]

    if headers:
        for key, value in headers.items():
            req.add_header(key, value)

    # 处理代理配置，兼容requests格式
    proxy = None
    if proxies:
        # 优先使用https代理，然后是http代理
        proxy = proxies.get('https') or proxies.get('http')

    # 创建opener并发送请求，包括重试处理器
    handlers = [NoHTTPErrorProcessor(), SSLAutoFallbackHandler(verify_ssl=verify), RetryHandler(retries=retries)]  # type: list[BaseHandler]
    if proxy:
        handlers.append(ProxyHandler({"http": proxy, "https": proxy}))
    if auth:
        handlers.append(auth)
    opener = build_opener(*handlers)
    response = opener.open(req)

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

    # 最终后备：UTF-8替换错误字符
    return raw_body.decode("utf-8", errors="replace")
