# coding=utf-8
"""
DNSCOM/51dns API 接口解析操作库
www.51dns.com (原dns.com)
@author: Bigjin<i@bigjin.com>, NewFuture
"""

from time import mktime
from datetime import datetime
import logging
from hashlib import md5

from ._base import BaseProvider, TYPE_FORM


class DnscomProvider(BaseProvider):
    """
    DNSCOM/51dns API Provider
    https://www.51dns.com/document/api/index.html
    """

    API = "https://www.51dns.com"
    ContentType = TYPE_FORM

    def _signature(self, params):
        """
        https://www.51dns.com/document/api/70/72.html
        """
        params = {k: v for k, v in params.items() if v is not None}
        params.update(
            {
                "apiKey": self.auth_id,
                "timestamp": mktime(datetime.now().timetuple()),
            }
        )
        query = self._encode(sorted(params.items()))
        sign = md5((query + self.auth_token).encode("utf-8")).hexdigest()
        params["hash"] = sign
        return params

    def _request(self, action, **params):
        params = self._signature(params)
        data = self._http("POST", "/api/{}/".format(action), body=params)
        if data is None or not isinstance(data, dict):
            raise Exception("response data is none")
        if data.get("code", 0) != 0:
            raise Exception("api error: " + str(data.get("message")))
        return data.get("data")

    def _query_zone_id(self, domain):
        """
        https://www.51dns.com/document/api/74/31.html
        """
        res = self._request("domain/getsingle", domainID=domain)
        logging.debug("Queried domain: %s", res)
        if res:
            return res.get("domainID")
        return None

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line=None, extra={}):
        """
        https://www.51dns.com/document/api/4/47.html
        """
        records = self._request("record/list", domainID=zone_id, host=sub_domain, pageSize=500)
        records = records.get("data", []) if records else []
        for record in records:
            if (
                record.get("record") == sub_domain
                and record.get("type") == record_type
                and (line is None or record.get("viewID") == line)
            ):
                return record
        return None

    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra={}):
        """
        https://www.51dns.com/document/api/4/12.html
        """
        extra["remark"] = extra.get("remark", self.Remark)
        res = self._request(
            "record/create",
            domainID=zone_id,
            value=value,
            host=sub_domain,
            type=record_type,
            TTL=ttl,
            viewID=line,
            **extra
        )
        if res and res.get("recordID"):
            logging.info("Record created: %s", res)
            return True
        logging.error("Failed to create record: %s", res)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra={}):
        """
        https://www.51dns.com/document/api/4/45.html
        """
        extra["remark"] = old_record.get("remark", extra.get("remark", self.Remark))
        res = self._request(
            "record/modify", domainID=zone_id, recordID=old_record.get("recordID"), newvalue=value, newTTL=ttl
        )
        if res:
            logging.info("Record updated: %s", res)
            return True
        logging.error("Failed to update record: %s", res)
        return False
