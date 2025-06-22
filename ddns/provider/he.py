# coding=utf-8
"""
Hurricane Electric (he.net) API
https://dns.he.net/docs.html
@author: NN708, NewFuture
"""

import logging
from ._base import BaseProvider, TYPE_FORM


class HeProvider(BaseProvider):
    API = "dyn.dns.he.net"
    ContentType = TYPE_FORM
    DecodeResponse = False  # he.net response is plain text, not JSON

    def _request(self, **params):
        params.update({"password": "***"})
        logging.debug("%s: %s", self.API, params)
        params["password"] = self.auth_token  # Use auth_token as password
        res = self._https("POST", "/nic/update", body=params)
        if not res:
            raise Exception("empty response")
        elif res[:5] == "nochg" or res[:4] == "good":  # No change or success
            return res
        else:
            raise Exception(res)

    def _query_zone_id(self, domain):
        return domain

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line=None, extra={}):
        """
        he.net 动态 DNS 不支持查询记录，直接返回。
        he.net dynamic DNS does not support querying records, always return.
        """
        return {"name": self._join_domain(sub_domain, main_domain)}

    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra={}):
        return self._request(hostname=self._join_domain(sub_domain, main_domain), myip=value)

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra={}):
        """
        更新或创建 DNS 记录，仅支持 A/AAAA 类型。
        Update or create DNS record, only supports A/AAAA type.
        https://dns.he.net/docs.html
        """
        domain = old_record.get("name") or (zone_id)
        return self._request(hostname=domain, myip=value)
