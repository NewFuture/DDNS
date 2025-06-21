# coding=utf-8
"""
AliDNS API
阿里DNS解析操作库
@author: NewFuture
"""

import logging
from hashlib import sha1
from hmac import new as hmac
from base64 import b64encode
from datetime import datetime

from ._base import BaseProvider, TYPE_FORM

try:  # python 3
    from urllib.parse import urlencode, quote_plus, quote
except ImportError:  # python 2
    from urllib import urlencode, quote_plus, quote  # type: ignore[no-redef,import-untyped]


class AlidnsProvider(BaseProvider):
    API = "alidns.aliyuncs.com"
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
                "SignatureNonce": hex(now.__hash__())[4:],
                "SignatureVersion": "1.0",
            }
        )
        query = urlencode(sorted(params.items()))
        query = query.replace("+", "%20")
        logging.debug("query: %s", query)
        sign = "POST&" + quote_plus("/") + "&" + quote(query, safe="")
        logging.debug("sign: %s", sign)
        sign = hmac((self.auth_token + "&").encode("utf-8"), sign.encode("utf-8"), sha1).digest()
        sign = b64encode(sign).strip().decode()
        params["Signature"] = sign
        return params

    def _request(self, action, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict
        params = {k: v for k, v in params.items() if v is not None}
        params["Action"] = action
        params = self._signature(params)
        return self._https("POST", "/", {}, **params)

    def _query_zone_id(self, domain):
        """
        https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-getmaindomainname
        """
        res = self._request("GetMainDomainName", InputString=domain)
        return res.get("DomainName")

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line=None, extra={}):
        """
        https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-describedomainrecords
        """
        data = self._request(
            "DescribeDomainRecords",
            DomainName=zone_id,
            RRKeyWord=sub_domain,
            Type=record_type,
            Line=line,
            PageSize=500,
            Lang=extra.get("Lang"),  # 默认中文
            Status=extra.get("Status"),  # 默认查询启用状态的记录
        )
        records = data.get("DomainRecords", {}).get("Record", [])
        if not records:
            logging.warning(
                "No records found for [%s] with sub %s + type %s (line: %s)",
                zone_id,
                sub_domain,
                record_type,
                line,
            )
        elif not isinstance(records, list):
            logging.error("Invalid records format: %s", records)
        else:
            return next((r for r in records if r.get("RR") == sub_domain), None)

        return None

    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra={}):
        """
        https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-adddomainrecord
        """
        data = self._request(
            "AddDomainRecord",
            DomainName=zone_id,
            RR=sub_domain,
            Value=value,
            Type=record_type,
            TTL=ttl,
            Line=line,
            **extra,
        )
        if data and data.get("RecordId"):
            logging.info("Record created: %s", data)
            return True
        logging.error("Failed to create record: %s", data)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra={}):
        """
        https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-updatedomainrecord
        """
        data = self._request(
            "UpdateDomainRecord",
            RecordId=old_record.get("RecordId"),
            Value=value,
            RR=old_record.get("RR"),
            Type=record_type,
            TTL=ttl,
            Line=line or old_record.get("Line"),
            **extra,
        )
        if data and data.get("RecordId"):
            logging.info("Record updated: %s", data)
            return True
        logging.error("Failed to update record: %s", data)
        return False
