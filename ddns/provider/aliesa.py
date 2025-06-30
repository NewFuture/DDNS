# coding=utf-8
"""
AliESA API
阿里云边缘安全加速(Edge Security Acceleration) DNS解析操作库
@author: Github Copilot
"""

from ._base import BaseProvider, TYPE_FORM
from hashlib import sha1
from hmac import new as hmac
from base64 import b64encode
from time import time, strftime


class AliESAProvider(BaseProvider):
    API = "https://esa.aliyuncs.com"
    content_type = TYPE_FORM

    def _signature(self, params):
        # type: (dict[str, Any]) -> dict[str, Any]
        """
        签名请求参数 (v2 RPC)
        https://help.aliyun.com/zh/sdk/product-overview/rpc-mechanism
        Sign the request parameters for AliESA API.
        :param params: 请求参数/Request parameters
        :return: 签名后的参数/Signed parameters
        """
        params.update(
            {
                "Format": "json",
                "Version": "2024-09-10",
                "AccessKeyId": self.auth_id,
                "Timestamp": strftime("%Y-%m-%dT%H:%M:%SZ"),
                "SignatureMethod": "HMAC-SHA1",
                "SignatureNonce": hex(hash(time()))[2:],
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
        查询站点ID
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-listsites
        """
        res = self._request("ListSites", SiteName=domain)
        sites = res.get("Sites", [])
        if not sites:
            self.logger.warning("No sites found for domain: %s", domain)
            return None
        
        # 查找完全匹配的站点
        site = next((s for s in sites if s.get("SiteName") == domain), None)
        if site:
            return site.get("SiteId")
        
        self.logger.warning("No matching site found for domain: %s", domain)
        return None

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line, extra):
        """
        查询DNS记录
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-listrecords
        """
        # 构建完整的记录名称
        record_name = self._join_domain(sub_domain, main_domain)
        
        data = self._request(
            "ListRecords",
            SiteId=zone_id,
            RecordName=record_name,
            Type=record_type,
            PageSize=500,
        )
        
        records = data.get("Records", [])
        if not records:
            self.logger.warning(
                "No records found for [%s] with %s <%s>", zone_id, record_name, record_type
            )
            return None
        
        # 返回第一个匹配的记录
        if isinstance(records, list):
            return records[0] if records else None
        else:
            self.logger.error("Invalid records format: %s", records)
            return None

    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl, line, extra):
        """
        创建DNS记录
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-createrecord
        """
        # 构建完整的记录名称
        record_name = self._join_domain(sub_domain, main_domain)
        
        data = self._request(
            "CreateRecord",
            SiteId=zone_id,
            RecordName=record_name,
            Value=value,
            Type=record_type,
            TTL=ttl,
            Comment=extra.get("Remark") or extra.get("Comment"),
            **{k: v for k, v in extra.items() if k not in ["Remark", "Comment"]}
        )
        
        if data and data.get("RecordId"):
            self.logger.info("Record created: %s", data)
            return True
        self.logger.error("Failed to create record: %s", data)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        """
        更新DNS记录
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-updaterecord
        """
        data = self._request(
            "UpdateRecord",
            RecordId=old_record.get("RecordId"),
            Value=value,
            RecordName=old_record.get("RecordName"),
            Type=record_type,
            TTL=ttl,
            Comment=extra.get("Remark") or extra.get("Comment") or old_record.get("Comment"),
            **{k: v for k, v in extra.items() if k not in ["Remark", "Comment"]}
        )
        
        if data and data.get("RecordId"):
            self.logger.info("Record updated: %s", data)
            return True
        self.logger.error("Failed to update record: %s", data)
        return False