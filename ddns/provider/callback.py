# coding=utf-8
"""
Custom Callback API
自定义回调接口解析操作库

@author: 老周部落, NewFuture
"""

from ._base import TYPE_JSON, SimpleProvider
from time import time
from json import loads as jsondecode


class CallbackProvider(SimpleProvider):
    """
    通用自定义回调 Provider，支持 GET/POST 任意接口。
    Generic custom callback provider, supports GET/POST arbitrary API.
    """

    endpoint = ""  # CallbackProvider uses id as URL, no fixed API endpoint
    content_type = TYPE_JSON
    decode_response = False  # Callback response is not JSON, it's a custom response

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        """
        发送自定义回调请求，支持 GET/POST
        Send custom callback request, support GET/POST
        """
        self.logger.info("%s => %s(%s)", domain, value, record_type)
        url = self.id  # 直接用 id 作为 url
        token = self.token  # token 作为 POST 参数
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
        url = self._replace_vars(url, extra)
        method, params = "GET", None
        if token:
            # 如果有 token，使用 POST 方法
            method = "POST"
            # POST 方式，token 作为 POST 参数
            params = token if isinstance(token, dict) else jsondecode(token)
            for k, v in params.items():
                if hasattr(v, "replace"):  # 判断是否支持字符串替换, 兼容py2,py3
                    params[k] = self._replace_vars(v, extra)

        try:
            res = self._http(method, url, body=params)
            if res is not None:
                self.logger.info("Callback result: %s", res)
                return True
            else:
                self.logger.warning("Callback received empty response.")
        except Exception as e:
            self.logger.error("Callback failed: %s", e)
        return False

    def _replace_vars(self, string, mapping):
        # type: (str, dict) -> str
        """
        替换字符串中的变量为实际值
        Replace variables in string with actual values
        """
        for k, v in mapping.items():
            string = string.replace(k, str(v))
        return string

    def _validate(self):
        # CallbackProvider uses id as URL, not as regular ID
        if self.endpoint or (not self.id or "://" not in self.id):
            # 如果 endpoint 已经设置，或者 id 不是有效的 URL，则抛出异常
            self.logger.critical("endpoint [%s] or id [%s] 必须是有效的URL", self.endpoint, self.id)
            raise ValueError("endpoint or id must be configured with URL")
