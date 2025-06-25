# coding=utf-8
"""
Custom Callback API
自定义回调接口解析操作库

@author: 老周部落, NewFuture
"""

from ._base import TYPE_JSON, BaseProvider
from json import loads as jsondecode
from time import time


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
        token = self.auth_token  # auth_token 作为 POST 参数
        extra.update(
            {
                "__DOMAIN__": domain,
                "__RECORDTYPE__": record_type,
                "__TTL__": ttl,
                "__IP__": value,
                "__TIMESTAMP__": time(),
                "__LINE__": line,
            }
        )
        if not token:
            # GET 方式，URL query 传参
            method = "GET"
            url = self._replace_vars(url, extra)
            res = self._http(method, url)
        else:
            # POST 方式，token 作为 POST 参数
            method = "POST"
            params = token if isinstance(token, dict) else jsondecode(token)
            for k, v in params.items():
                if isinstance(v, str):
                    params[k] = self._replace_vars(v, extra)
            res = self._http(method, url, params=params)
        if res:
            self.logger.info("Callback result: %s", res)
            return True
        else:
            self.logger.warning("Callback No Response")
            return False

    def _replace_vars(self, str, mapping):
        # type: (str, dict) -> str
        """
        替换字符串中的变量为实际值
        Replace variables in string with actual values
        """
        for k, v in mapping.items():
            str = str.replace(k, v)
        return str

    def _validate(self):
        if not self.auth_id:
            raise ValueError("id must be configured")
