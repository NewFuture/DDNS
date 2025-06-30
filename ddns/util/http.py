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

try:  # python 3
    from http.client import HTTPSConnection, HTTPConnection, HTTPException
    from urllib.parse import urlparse
except ImportError:  # python 2
    from httplib import HTTPSConnection, HTTPConnection, HTTPException  # type: ignore[no-redef]
    from urlparse import urlparse  # type: ignore[no-redef]

__all__ = ["send_http_request", "HttpResponse"]

logger = getLogger().getChild(__name__)


class HttpResponse(object):
    """HTTP响应封装类"""

    def __init__(self, status, reason, headers, body):
        # type: (int, str, list[tuple[str, str]], str) -> None
        """
        初始化HTTP响应对象

        Args:
            status (int): HTTP状态码
            reason (str): 状态原因短语
            headers (list[tuple[str, str]]): 响应头列表，保持原始格式和顺序
            body (str): 响应体内容
        """
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

    def get_header(self, name, default=None):
        # type: (str, str | None) -> str | None
        """
        获取指定名称的头部值（不区分大小写）

        Args:
            name (str): 头部名称

        Returns:
            str | None: 头部值，如果不存在则返回None
        """
        name_lower = name.lower()
        for header_name, header_value in self.headers:
            if header_name.lower() == name_lower:
                return header_value
        return default


def _create_connection(hostname, port, is_https, proxy, verify_ssl):
    # type: (str, int | None, bool, str | None, bool | str) -> HTTPConnection | HTTPSConnection
    """创建HTTP/HTTPS连接"""
    target = proxy or hostname

    if not is_https:
        conn = HTTPConnection(target, port)
    else:
        ssl_context = ssl.create_default_context()

        if verify_ssl is False:
            # 禁用SSL验证
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        elif hasattr(verify_ssl, "lower") and verify_ssl.lower() not in ("auto", "true"):  # type: ignore[union-attr]
            # 使用自定义CA证书 lower 判断 str/unicode 兼容 python2
            try:
                ssl_context.load_verify_locations(verify_ssl)  # type: ignore[arg-type]
            except Exception as e:
                logger.error("Failed to load CA certificate from %s: %s", verify_ssl, e)
        else:
            # 默认验证，尝试加载系统证书
            _load_system_ca_certs(ssl_context)
        conn = HTTPSConnection(target, port, context=ssl_context)

    # 设置代理隧道
    if proxy:
        conn.set_tunnel(hostname, port)  # type: ignore[attr-defined]

    return conn


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
                logger.debug("Failed to load CA certificates from %s: %s", ca_path, e)

    if loaded_count > 0:
        logger.debug("Successfully loaded CA certificates from %d locations", loaded_count)


def _close_connection(conn):
    # type: (HTTPConnection | HTTPSConnection) -> None
    """关闭HTTP/HTTPS连接"""
    try:
        conn.close()
    except Exception as e:
        logger.warning("Failed to close connection: %s", e)


def send_http_request(method, url, body=None, headers=None, proxy=None, max_redirects=5, verify_ssl=True):
    # type: (str, str, str | bytes | None, dict[str, str] | None, str | None, int, bool | str) -> HttpResponse
    """
    发送HTTP/HTTPS请求，支持重定向跟随和灵活的SSL验证
    Send HTTP/HTTPS request with support for redirect following and flexible SSL verification.
    Args:
        method (str): HTTP方法，如GET、POST等
        url (str): 请求的URL
        body (str | bytes | None): 请求体
        headers (dict[str, str] | None): 请求头
        proxy (str | None): 代理地址
        max_redirects (int): 最大重定向次数
        verify_ssl (bool | str): 是否验证SSL证书
    Returns:
        HttpResponse: 响应对象，包含状态码、头部和解码后的内容
    Raises:
        HTTPException: 如果请求失败或重定向次数超过限制
        ssl.SSLError: 如果SSL验证失败
    """
    if max_redirects <= 0:
        raise HTTPException("Too many redirects")

    # 解析URL
    url_obj = urlparse(url)
    is_https = url_obj.scheme == "https"
    hostname = url_obj.hostname or url_obj.netloc.split(":")[0]
    request_path = "{}?{}".format(url_obj.path, url_obj.query) if url_obj.query else url_obj.path
    headers = headers or {}

    # 创建连接
    actual_verify_ssl = verify_ssl
    conn = _create_connection(hostname, url_obj.port, is_https, proxy, verify_ssl)

    # 执行请求，处理SSL错误
    try:
        conn.request(method, request_path, body, headers)
        response = conn.getresponse()
    except ssl.SSLError:
        _close_connection(conn)
        if verify_ssl == "auto" and is_https:
            logger.warning("SSL verification failed, switching to unverified connection %s", url)
            # 重新连接，忽略SSL验证
            conn = _create_connection(hostname, url_obj.port, is_https, proxy, False)
            conn.request(method, request_path, body, headers)
            response = conn.getresponse()
            actual_verify_ssl = False
        else:
            raise

    # 检查重定向
    status = response.status
    if 300 <= status < 400:
        location = response.getheader("Location")
        _close_connection(conn)
        if not location:
            # 无Location头的重定向
            logger.warning("Redirect status %d but no Location header", status)
            location = ""

        # 构建重定向URL
        redirect_url = _build_redirect_url(location, "{}://{}".format(url_obj.scheme, url_obj.netloc), url_obj.path)

        # 如果重定向URL没有查询字符串，但原始URL有，则附加
        if url_obj.query and "?" not in redirect_url:
            redirect_url += "?" + url_obj.query

        # 确定重定向方法：303或302+POST转为GET，其他保持原方法
        if status == 303 or (status == 302 and method == "POST"):
            method, body = "GET", None
            # 如果从POST转为GET，移除相关的头部
            if headers:
                headers = {k: v for k, v in headers.items() if k.lower() not in ("content-length", "content-type")}

        logger.info("Redirecting [%d] to: %s", status, redirect_url)
        # 递归处理重定向
        return send_http_request(method, redirect_url, body, headers, proxy, max_redirects - 1, actual_verify_ssl)

    # 处理最终响应
    content_type = response.getheader("Content-Type")
    response_headers = response.getheaders()
    raw_body = response.read()
    _close_connection(conn)

    # 解码响应体并创建响应对象
    decoded_body = _decode_response_body(raw_body, content_type)
    return HttpResponse(status, response.reason, response_headers, decoded_body)


def _build_redirect_url(location, base, path):
    # type: (str, str, str) -> str
    """构建重定向URL，使用简单的字符串操作"""
    if location.startswith("http"):
        return location

    if location.startswith("/"):
        # 绝对路径：使用base的scheme和netloc
        base_url = urlparse(base)
        return "{}://{}{}".format(base_url.scheme, base_url.netloc, location)
    else:
        base_path = path.rsplit("/", 1)[0] if "/" in path else ""
        if not base_path.endswith("/"):
            base_path += "/"
        return base + base_path + location


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
