# coding=utf-8
"""
DDNS Tests Package
"""

import errno
import os
import socket
import ssl
import sys
import unittest

TEST_HTTP_TIMEOUT = 5

try:
    _TIMEOUT_ERRORS = (socket.timeout, TimeoutError)
except NameError:  # Python 2
    _TIMEOUT_ERRORS = (socket.timeout,)

_NETWORK_ERRNOS = {
    value
    for value in (
        getattr(errno, "ECONNABORTED", None),
        getattr(errno, "ECONNREFUSED", None),
        getattr(errno, "ECONNRESET", None),
        getattr(errno, "EHOSTDOWN", None),
        getattr(errno, "EHOSTUNREACH", None),
        getattr(errno, "ENETDOWN", None),
        getattr(errno, "ENETRESET", None),
        getattr(errno, "ENETUNREACH", None),
        getattr(errno, "EPIPE", None),
        getattr(errno, "ETIMEDOUT", None),
        10060,  # WSAETIMEDOUT
    )
    if value is not None
}


def is_network_error(error, include_ssl=False):
    """Return whether an exception represents an unavailable test endpoint."""
    if isinstance(error, _TIMEOUT_ERRORS):
        return True

    reason = getattr(error, "reason", None)
    if reason is not None and reason is not error and is_network_error(reason, include_ssl):
        return True

    if isinstance(error, (socket.gaierror, socket.herror)):
        return True

    if getattr(error, "errno", None) in _NETWORK_ERRNOS:
        return True

    if include_ssl and isinstance(error, ssl.SSLError):
        return True

    error_msg = str(error).lower()
    network_keywords = ["timeout", "timed out", "connection", "resolution", "unreachable", "network"]
    if include_ssl:
        network_keywords.extend(["ssl", "certificate"])
    return any(keyword in error_msg for keyword in network_keywords)


try:
    from unittest import mock  # type: ignore
    from unittest.mock import patch, MagicMock, call
except ImportError:  # Python 2
    from mock import patch, MagicMock, call  # type: ignore
    import mock  # type: ignore

__all__ = ["patch", "MagicMock", "unittest", "call", "mock", "TEST_HTTP_TIMEOUT", "is_network_error"]

# 添加当前目录到 Python 路径，这样就可以直接导入 test_base
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 添加上级目录到 Python 路径，这样就可以导入 ddns 模块
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
