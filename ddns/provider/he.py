# coding=utf-8
"""
Hurricane Electric (he.net) API
https://dns.he.net/docs.html
@author: NN708, NewFuture
"""

import logging
from ._base import BaseProvider, TYPE_FORM


class HeProvider(BaseProvider):
    API = "https://dyn.dns.he.net"
    ContentType = TYPE_FORM
    DecodeResponse = False  # he.net response is plain text, not JSON

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        """
        使用 POST API 更新或创建 DNS 记录。
        Update or create DNS record with POST API.
        """
        logging.info("start update %s(%s) => %s", domain, record_type, value)
        params = {
            "hostname": domain,  # he.net requires full domain name
            "myip": value,  # IP address to update
            "password": self.auth_token,  # Use auth_token as password
        }
        logging.debug("HE Params: %s", params)
        res = self._http("POST", "/nic/update", body=params)
        if not res:
            raise Exception("empty response")
        elif res[:5] == "nochg" or res[:4] == "good":  # No change or success
            return res
        else:
            logging.error("HE API error: %s", res)
            raise Exception(res)
