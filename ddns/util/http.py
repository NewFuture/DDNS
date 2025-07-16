# coding=utf-8
"""
HTTP请求工具模块

HTTP utilities module for DDNS project.
Provides common HTTP functionality including redirect following support.

@author: NewFuture
"""

from logging import getLogger
import ssl
import os
import re

try:  # python 3
    from urllib.request import HTTPBasicAuthHandler, BaseHandler, OpenerDirector  # noqa: F401
    from urllib.request import HTTPPasswordMgrWithDefaultRealm, Request, HTTPSHandler, ProxyHandler, build_opener
    from urllib.parse import quote, urlencode, unquote
    from urllib.error import HTTPError, URLError
except ImportError:  # python 2
    from urllib2 import Request, HTTPSHandler, ProxyHandler, build_opener, HTTPError, URLError  # type: ignore[no-redef]
    from urllib2 import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler  # type: ignore[no-redef]
    from urllib import urlencode, quote, unquote  # type: ignore[no-redef]


__all__ = [
    "send_http_request",
    "HttpResponse",
    "quote",
    "urlencode",
    "URLError",
]

logger = getLogger().getChild(__name__)
_AUTH_URL_RE = re.compile(r"^(https?://)([^:/?#]+):([^@]+)@(.+)$")


class HttpResponse(object):
    """HTTP响应封装类"""

    def __init__(self, status, reason, headers, body):
        # type: (int, str, object, str) -> None
        """
        初始化HTTP响应对象

        Args:
            status (int): HTTP状态码
            reason (str): 状态原因短语
            headers (object): 响应头对象，直接使用 response.info()
            body (str): 响应体内容
        """
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

    def get_header(self, name, default=None):
        # type: (str, str | None) -> str | None
        """
        获取指定名称的头部值

        Args:
            name (str): 头部名称
            default (str | None): 默认值

        Returns:
            str | None: 头部值，如果不存在则返回默认值
        """
        return self.headers.get(name, default)  # type: ignore[union-attr]


# 移除了自定义重定向处理器，使用urllib2/urllib.request的内置重定向处理


def _create_ssl_context(verify_ssl):
    # type: (bool | str) -> ssl.SSLContext | None
    """创建SSL上下文"""
    ssl_context = ssl.create_default_context()

    if verify_ssl is False:
        # 禁用SSL验证
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    elif hasattr(verify_ssl, "lower") and verify_ssl.lower() not in ("auto", "true"):  # type: ignore[union-attr]
        # 使用自定义CA证书
        try:
            ssl_context.load_verify_locations(verify_ssl)  # type: ignore[arg-type]
        except Exception as e:
            logger.error("Failed to load CA certificate from %s: %s", verify_ssl, e)
            return None
    else:
        # 默认验证，尝试加载系统证书
        _load_system_ca_certs(ssl_context)

    return ssl_context


def _load_system_ca_certs(ssl_context):
    # type: (ssl.SSLContext) -> None
    """加载系统CA证书"""
    # 常见CA证书路径
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

    # Windows额外路径
    if os.name == "nt":
        ca_paths.append("C:\\Program Files\\Git\\mingw64\\ssl\\cert.pem")
        ca_paths.append("C:\\Program Files\\OpenSSL\\ssl\\cert.pem")

    loaded_count = 0
    for ca_path in ca_paths:
        if os.path.isfile(ca_path):
            try:
                ssl_context.load_verify_locations(ca_path)
                loaded_count += 1
                logger.debug("Loaded CA certificates from: %s", ca_path)
            except Exception as e:
                logger.info("Failed to load CA certificates from %s: %s", ca_path, e)


def _create_opener(proxy, verify_ssl, auth_handler=None):
    # type: (str | None, bool | str, BaseHandler | None) -> OpenerDirector
    """创建URL打开器，支持代理和SSL配置"""
    handlers = []

    if proxy:
        handlers.append(ProxyHandler({"http": proxy, "https": proxy}))

    if auth_handler:
        handlers.append(auth_handler)

    ssl_context = _create_ssl_context(verify_ssl)
    if ssl_context:
        handlers.append(HTTPSHandler(context=ssl_context))

    return build_opener(*handlers)


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

    # 使用正则表达式直接提取用户名和密码
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
    opener = _create_opener(proxy, verify_ssl, auth_handler)

    try:
        response = opener.open(req)
        response_headers = response.info()
        raw_body = response.read()
        decoded_body = _decode_response_body(raw_body, response_headers.get("Content-Type"))
        return HttpResponse(response.getcode(), getattr(response, "msg", ""), response_headers, decoded_body)
    except HTTPError as e:
        # 记录HTTP错误并读取响应体用于调试
        response_headers = getattr(e, "headers", {})
        raw_body = e.read()
        decoded_body = _decode_response_body(raw_body, response_headers.get("Content-Type"))
        logger.error("HTTP error %s: %s for %s", e.code, getattr(e, "reason", str(e)), url)
        return HttpResponse(e.code, getattr(e, "reason", str(e)), response_headers, decoded_body)
    except ssl.SSLError:
        if verify_ssl == "auto":
            logger.warning("SSL verification failed, switching to unverified connection %s", url)
            return send_http_request(method, url, body, headers, proxy, False, auth_handler)
        else:
            raise


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
        charsets.insert(0, charset)
        # 处理常见别名
        if charset == "gb2312":
            charsets.remove("gbk")
            charsets.insert(0, "gbk")
        elif charset == "iso-8859-1":
            charsets.remove("latin-1")
            charsets.insert(0, "latin-1")

    # 按优先级尝试解码
    for encoding in charsets:
        try:
            return raw_body.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue

    # 最终后备：UTF-8替换错误字符
    return raw_body.decode("utf-8", errors="replace")
