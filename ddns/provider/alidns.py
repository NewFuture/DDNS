# coding=utf-8
"""
AliDNS API
阿里DNS解析操作库
@author: NewFuture
"""

from ._base import BaseProvider, TYPE_FORM
from hashlib import sha1
from hmac import new as hmac
from base64 import b64encode
from datetime import datetime


class AlidnsProvider(BaseProvider):
    API = "https://alidns.aliyuncs.com"
    ContentType = TYPE_FORM

    def _signature(self, params):
        # type: (dict[str, Any]) -> dict[str, Any]
        """
        签名请求参数 (v2 RPC)
        https://help.aliyun.com/zh/sdk/product-overview/rpc-mechanism
        @todo: [v3](https://help.aliyun.com/zh/sdk/product-overview/v3-request-structure-and-signature)
        Sign the request parameters for AliDNS API.
        :param params: 请求参数/Request parameters
        :return: 签名后的参数/Signed parameters
        """
        now = datetime.utcnow()
        params.update(
            {
                "Format": "json",
                "Version": "2015-01-09",
                "AccessKeyId": self.auth_id,
                "Timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "SignatureMethod": "HMAC-SHA1",
                "SignatureNonce": hex(now.__hash__())[2:],
                "SignatureVersion": "1.0",
            }
        )
        query = self._encode(sorted(params.items()))
        query = query.replace("+", "%20")
        self.logger.debug("query: %s", query)
        # sign = "POST&" + quote_plus("/") + "&" + quote(query, safe="")
        sign = "POST&%2F&" + self._quote(query, safe="")

        self.logger.debug("sign: %s", sign)
        sign = hmac((self.auth_token + "&").encode("utf-8"), sign.encode("utf-8"), sha1).digest()
        sign = b64encode(sign).strip().decode()
        params["Signature"] = sign
        return params

    def _request(self, action, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict
        params = {k: v for k, v in params.items() if v is not None}
        params["Action"] = action
        params = self._signature(params)
        return self._http("POST", "/", body=params)

    def _query_zone_id(self, domain):
        """
        https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-getmaindomainname
        """
        res = self._request("GetMainDomainName", InputString=domain)
        return res.get("DomainName")

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line=None, extra=None):
        """
        https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-describedomainrecords
        """
        extra = extra or {}
        data = self._request(
            "DescribeDomainRecords",
            DomainName=zone_id,
            RRKeyWord=sub_domain,
            Type=record_type,
            Line=line,
            PageSize=500,
            Lang=extra.get("Lang"),  # 默认中文
            Status=extra.get("Status"),  # 默认全部状态
        )
        records = data.get("DomainRecords", {}).get("Record", [])
        if not records:
            self.logger.warning(
                "No records found for [%s] with sub %s + type %s (line: %s)", zone_id, sub_domain, record_type, line
            )
        elif not isinstance(records, list):
            self.logger.error("Invalid records format: %s", records)
        else:
            return next((r for r in records if r.get("RR") == sub_domain), None)

        return None

    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra=None):
        """
        https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-adddomainrecord
        """
        extra = extra or {}
        data = self._request(
            "AddDomainRecord",
            DomainName=zone_id,
            RR=sub_domain,
            Value=value,
            Type=record_type,
            TTL=ttl,
            Line=line,
            **extra
        )
        if data and data.get("RecordId"):
            self.logger.info("Record created: %s", data)
            return True
        self.logger.error("Failed to create record: %s", data)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra=None):
        """
        https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-updatedomainrecord
        """
        extra = extra or {}
        data = self._request(
            "UpdateDomainRecord",
            RecordId=old_record.get("RecordId"),
            Value=value,
            RR=old_record.get("RR"),
            Type=record_type,
            TTL=ttl,
            Line=line or old_record.get("Line"),
            **extra
        )
        if data and data.get("RecordId"):
            self.logger.info("Record updated: %s", data)
            return True
        self.logger.error("Failed to update record: %s", data)
        return False
