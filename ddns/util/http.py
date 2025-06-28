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

__all__ = ["send_http_request"]

logger = getLogger().getChild(__name__)


def _create_connection(hostname, port, is_https, proxy, verify_ssl):
    # type: (str, int | None, bool, str | None, bool | str) -> HTTPConnection | HTTPSConnection
    """创建HTTP/HTTPS连接，合并SSL上下文创建逻辑"""
    target = proxy or hostname
    if not is_https:
        conn = HTTPConnection(target, port)
    else:
        # 根据verify_ssl参数创建SSL上下文
        ssl_context = None
        if verify_ssl is False:
            # 禁用SSL验证
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        elif isinstance(verify_ssl, str) and verify_ssl != "auto" and verify_ssl != "true":
            # 使用自定义CA证书
            ssl_context = ssl.create_default_context()
            try:
                ssl_context.load_verify_locations(verify_ssl)
            except Exception as e:
                logger.error("Failed to load CA certificate from %s: %s", verify_ssl, e)
        else:
            # verify_ssl为True或"auto"时，创建默认SSL上下文并尝试加载系统证书
            ssl_context = ssl.create_default_context()
            _load_system_ca_certs(ssl_context)

        # 创建HTTPS连接
        conn = HTTPSConnection(target, port, context=ssl_context) if ssl_context else HTTPSConnection(target, port)

    # 设置代理隧道
    if proxy:
        conn.set_tunnel(hostname, port)  # type: ignore[attr-defined]

    return conn


def _load_system_ca_certs(ssl_context):
    # type: (ssl.SSLContext) -> None
    """加载系统常用CA证书路径以提高兼容性"""
    # 常用的系统CA证书路径
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

    # Windows会使用系统证书存储，不需要额外的文件路径
    # 但可以尝试一些常见的第三方安装路径
    if os.name == "nt":
        ca_paths.extend(
            [
                "C:\\Program Files\\Git\\mingw64\\ssl\\cert.pem",
                "C:\\Program Files\\OpenSSL\\ssl\\cert.pem",
            ]
        )

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
    # type: (str, str, str | bytes | None, dict[str, str] | None, str | None, int, bool | str) -> str
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
        str: 响应内容 (decoded to UTF-8)
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

        # 确定重定向方法：303或302+POST转为GET，其他保持原方法
        if status == 303 or (status == 302 and method == "POST"):
            method, body = "GET", None

        logger.debug("Redirecting [%d] to: %s", status, redirect_url)
        # 递归处理重定向
        return send_http_request(method, redirect_url, body, headers, proxy, max_redirects - 1, actual_verify_ssl)

    # 处理最终响应
    res = response.read().decode("utf-8")
    _close_connection(conn)

    if not (200 <= status < 300):
        logger.warning("%s : error[%d]: %s", url, status, response.reason)
        logger.info(res)
        raise HTTPException("HTTP Error {}: {}\n{}".format(status, response.reason, res))

    return res


def _build_redirect_url(location, base, path):
    # type: (str, str, str) -> str
    """构建重定向URL"""
    if location.startswith("http"):
        return location
    elif location.startswith("/"):
        return "{}{}".format(base, location)
    else:
        base_path = path.rsplit("/", 1)[0] if "/" in path else ""
        if not base_path.endswith("/"):
            base_path += "/"

        return "{}{}{}".format(base, base_path, location)
