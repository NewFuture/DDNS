# coding=utf-8
"""
Hurricane Electric (he.net) API
https://dns.he.net/docs.html
@author: NN708, NewFuture
"""

from ._base import BaseProvider, TYPE_FORM


class HeProvider(BaseProvider):
    API = "https://dyn.dns.he.net"
    ContentType = TYPE_FORM
    DecodeResponse = False  # he.net response is plain text, not JSON

    def _validate(self):
        pass

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        """
        使用 POST API 更新或创建 DNS 记录。
        Update or create DNS record with POST API.
        """
        self.logger.info("start update %s(%s) => %s", domain, record_type, value)
        params = {
            "hostname": domain,  # he.net requires full domain name
            "myip": value,  # IP address to update
            "password": self.auth_token,  # Use auth_token as password
        }
        self.logger.debug("HE Params: %s", params)
        res = self._http("POST", "/nic/update", body=params)
        if not res:
            raise Exception("empty response")
        elif res[:5] == "nochg" or res[:4] == "good":  # No change or success
            return res
        else:
            self.logger.error("HE API error: %s", res)
            raise Exception(res)

    def _query_zone_id(self, domain):
        return domain

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line=None, extra=None):
        pass

    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra=None):
        return self.set_record(self._join_domain(sub_domain, main_domain), value, record_type)

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra=None):
        return self.set_record(zone_id, value, record_type)
