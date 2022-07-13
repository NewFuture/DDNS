# coding=utf-8
"""
DNSPOD API
DNSPOD 接口解析操作库
http://www.dnspod.com/docs/domains.html
@author: New Future
"""

from dns.dnspod import *  # noqa: F403

API.SITE = "api.dnspod.com"  # noqa: F405
API.DEFAULT = "default"  # noqa: F405

# https://github.com/NewFuture/DDNS/issues/286
# API.TOKEN_PARAM = "user_token"  # noqa: F405
