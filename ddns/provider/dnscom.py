# coding=utf-8
"""
DNSCOM/51dns API 接口解析操作库
www.51dns.com (原dns.com)
@author: Bigjin<i@bigjin.com>, NewFuture
"""

from hashlib import md5
from time import time

from ._base import TYPE_FORM, BaseProvider, encode_params


class DnscomProvider(BaseProvider):
    """
    DNSCOM/51dns API Provider
    https://www.51dns.com/document/api/index.html
    """

    endpoint = "https://www.51dns.com"
    content_type = TYPE_FORM

    def _validate(self):
        self.logger.warning(
            "DNS.COM 缺少充分的真实环境测试，请及时在 GitHub Issues 中反馈: %s",
            "https://github.com/NewFuture/DDNS/issues",
        )
        super(DnscomProvider, self)._validate()

    def _signature(self, params):
        """https://www.51dns.com/document/api/70/72.html"""
        params = {k: v for k, v in params.items() if v is not None}
        params.update(
            {
                "apiKey": self.id,
                "timestamp": time(),  # 时间戳
            }
        )
        query = encode_params(params)
        sign = md5((query + self.token).encode("utf-8")).hexdigest()
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
        """https://www.51dns.com/document/api/74/31.html"""
        res = self._request("domain/getsingle", domainID=domain)
        self.logger.debug("Queried domain: %s", res)
        if res:
            return res.get("domainID")
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        """https://www.51dns.com/document/api/4/47.html"""
        records = self._request("record/list", domainID=zone_id, host=subdomain, pageSize=500)
        records = records.get("data", []) if records else []
        for record in records:
            if (
                record.get("record") == subdomain
                and record.get("type") == record_type
                and (line is None or record.get("viewID") == line)
            ):
                return record
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        """https://www.51dns.com/document/api/4/12.html"""
        extra["remark"] = extra.get("remark", self.remark)
        res = self._request(
            "record/create",
            domainID=zone_id,
            value=value,
            host=subdomain,
            type=record_type,
            TTL=ttl,
            viewID=line,
            **extra
        )  # fmt: skip
        if res and res.get("recordID"):
            self.logger.info("Record created: %s", res)
            return True
        self.logger.error("Failed to create record: %s", res)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        """https://www.51dns.com/document/api/4/45.html"""
        extra["remark"] = extra.get("remark", self.remark)
        res = self._request(
            "record/modify", domainID=zone_id, recordID=old_record.get("recordID"), newvalue=value, newTTL=ttl
        )
        if res:
            self.logger.info("Record updated: %s", res)
            return True
        self.logger.error("Failed to update record: %s", res)
        return False
