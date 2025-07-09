# coding=utf-8
"""
DNS Provider 签名和哈希算法模块

Signature and hash algorithms module for DNS providers.
Provides common cryptographic functions for cloud provider authentication.

@author: NewFuture
"""

from hashlib import sha256
from hmac import HMAC


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
