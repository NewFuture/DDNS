# coding=utf-8
"""
Custom Callback API
自定义回调接口解析操作库

@author: 老周部落, NewFuture
"""

import logging
from json import loads as jsondecode
from time import time
from ._base import TYPE_FORM, TYPE_JSON, BaseProvider

try:  # python 3
    from urllib.parse import urlparse, parse_qsl
except ImportError:  # python 2
    from urlparse import urlparse, parse_qsl  # type: ignore[no-redef,import]


class CallbackProvider(BaseProvider):
    """
    通用自定义回调 Provider，支持 GET/POST 任意接口。
    Generic custom callback provider, supports GET/POST arbitrary API.
    """

    DecodeResponse = False  # Callback response is not JSON, it's a custom response

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        """
        发送自定义回调请求，支持 GET/POST
        Send custom callback request, support GET/POST
        """
        logging.info("start update %s(%s) => %s", domain, record_type, value)
        url = self.auth_id  # 直接用 auth_id 作为 url
        token = self.auth_token
        if not token:
            # GET 方式，URL query 透传
            method = "GET"
            self.ContentType = TYPE_FORM  # 设置 Content-Type 为 FORM
            query = dict(parse_qsl(urlparse(url).query))
            params = self._replace_params(query, domain, record_type, value, ttl)
        else:
            # POST 方式，token 作为 POST 参数
            method = "POST"
            self.ContentType = TYPE_JSON  # 设置 Content-Type 为 JSON
            params = self._replace_params(jsondecode(token), domain, record_type, value, ttl)

        try:
            res = self._http(method, url, params)
        except Exception as e:
            logging.error("Callback error: %s", e)
            return False
        if res:
            logging.info("Callback result: %s", res)
            return True
        else:
            logging.warning("Callback No Response")
            return False

    def _replace_params(self, params, domain, record_type, ip, ttl=None, line=None, extra=None):
        # type: (dict, str, str, str, int | None, str | None, dict | None) -> dict
        """
        替换参数中的特殊变量为实际值
        Replace special variables in params with actual values
        """
        if extra is None:
            extra = {}
        extra.update(
            {
                "__DOMAIN__": domain,
                "__RECORDTYPE__": record_type,
                "__TTL__": ttl,
                "__IP__": ip,
                "__TIMESTAMP__": time(),
                "__LINE__": line,
            }
        )
        for k, v in params.items():
            if isinstance(v, str) and v in extra:
                params[k] = extra[v]
        return params
