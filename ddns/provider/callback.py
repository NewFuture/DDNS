# coding=utf-8
"""
Custom Callback API
自定义回调接口解析操作库

@author: 老周部落, NewFuture
"""

from ._base import TYPE_JSON, BaseProvider
from json import loads as jsondecode
from time import time

try:  # python 3
    from urllib.parse import urlparse
except ImportError:  # python 2
    from urlparse import urlparse  # type: ignore[no-redef,import]


class CallbackProvider(BaseProvider):
    """
    通用自定义回调 Provider，支持 GET/POST 任意接口。
    Generic custom callback provider, supports GET/POST arbitrary API.
    """

    ContentType = TYPE_JSON
    DecodeResponse = False  # Callback response is not JSON, it's a custom response

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        """
        发送自定义回调请求，支持 GET/POST
        Send custom callback request, support GET/POST
        """
        self.logger.info("start update %s(%s) => %s", domain, record_type, value)
        url = self.auth_id  # 直接用 auth_id 作为 url
        token = self.auth_token
        headers = {}
        if not token:
            # GET 方式，URL query 传参
            method = "GET"
            query = urlparse(url).query
            params = self._replace_params(query, domain, record_type, value, ttl)
        else:
            # POST 方式，token 作为 POST 参数
            method = "POST"
            params = token if isinstance(token, dict) else jsondecode(token)
            params = self._replace_params(params, domain, record_type, value, ttl)

        try:
            res = self._http(method, url, params=params, headers=headers)
        except Exception as e:
            self.logger.error("Callback error: %s", e)
            return False
        if res:
            self.logger.info("Callback result: %s", res)
            return True
        else:
            self.logger.warning("Callback No Response")
            return False

    def _replace_params(self, params, domain, record_type, ip, ttl=None, line=None, extra=None):
        # type: (dict|str, str, str, str, int | None, str | None, dict | None) -> dict
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
        if isinstance(params, str):
            for rk, rv in extra.items():
                params = params.replace(rk, rv)
        else:
            for k, v in params.items():
                if isinstance(v, str):
                    for rk, rv in extra.items():
                        params[k] = v.replace(rk, rv)
        return params
