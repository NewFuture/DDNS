# coding=utf-8
"""
AliDNS API
阿里DNS解析操作库
@author: NewFuture
"""

from ._base import TYPE_FORM, BaseProvider
from hashlib import sha256
from hmac import new as hmac
from time import strftime, gmtime, time


class AlidnsProvider(BaseProvider):
    API = "https://alidns.aliyuncs.com"
    content_type = TYPE_FORM  # 阿里云DNS API使用表单格式

    api_version = "2015-01-09"  # API版本，v3签名需要

    def _signature_v3(self, method, path, headers, query="", body_hash=""):
        # type: (str, str, dict, str, str) -> str
        """阿里云API v3签名算法 https://help.aliyun.com/zh/sdk/product-overview/v3-request-structure-and-signature"""
        # 构造规范化头部
        headers_to_sign = {k.lower(): str(v).strip() for k, v in headers.items()}

        # 按字母顺序排序并构造
        signed_headers_list = sorted(headers_to_sign.keys())
        canonical_headers = "".join("{}:{}\n".format(key, headers_to_sign[key]) for key in signed_headers_list)
        signed_headers = ";".join(signed_headers_list)

        # 构造规范化请求
        canonical_request = "\n".join([method, path, query, canonical_headers, signed_headers, body_hash])

        # 5. 构造待签名字符串
        algorithm = "ACS3-HMAC-SHA256"
        hashed_canonical_request = sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = "\n".join([algorithm, hashed_canonical_request])
        self.logger.debug("String to sign: %s", string_to_sign)

        # 6. 计算签名
        signature = hmac(self.auth_token.encode("utf-8"), string_to_sign.encode("utf-8"), sha256).hexdigest()

        # 7. 构造Authorization头
        authorization = "{} Credential={},SignedHeaders={},Signature={}".format(
            algorithm, self.auth_id, signed_headers, signature
        )
        return authorization

    def _request(self, action, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict
        params = {k: v for k, v in params.items() if v is not None}
        # 从API URL中提取host
        host = self.API.replace("https://", "").replace("http://", "").strip("/")
        body_content = self._encode(params) if len(params) > 0 else ""
        content_hash = sha256(body_content.encode("utf-8")).hexdigest()
        # 构造请求头部
        headers = {
            "host": host,
            "content-type": self.content_type,
            "x-acs-action": action,
            "x-acs-content-sha256": content_hash,
            "x-acs-date": strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()),
            "x-acs-signature-nonce": str(hash(time()))[2:],
            "x-acs-version": self.api_version,
        }

        # 生成Authorization头
        authorization = self._signature_v3("POST", "/", headers, body_hash=content_hash)
        headers["Authorization"] = authorization
        # 对于v3签名的RPC API，参数在request body中
        return self._http("POST", "/", body=body_content, headers=headers)

    def _split_zone_and_sub(self, domain):
        # type: (str) -> tuple[str | None, str | None, str]
        """
        AliDNS 支持直接查询主域名和RR，无需循环查询。
        返回没有DomainId,用DomainName代替
        https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-getmaindomainname
        """
        res = self._request("GetMainDomainName", InputString=domain)
        sub, main = res.get("RR"), res.get("DomainName")
        return (main, sub, main or domain)

    def _query_zone_id(self, domain):
        """调用_split_zone_and_sub可直接获取，无需调用_query_zone_id"""
        raise NotImplementedError("_split_zone_and_sub is used to get zone_id")

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        """https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-describesubdomainrecords"""
        sub = self._join_domain(subdomain, main_domain)
        data = self._request(
            "DescribeSubDomainRecords",
            SubDomain=sub,  # aliyun API要求SubDomain为完整域名
            DomainName=main_domain,
            Type=record_type,
            Line=line,
            PageSize=500,
            Lang=extra.get("Lang"),  # 默认中文
            Status=extra.get("Status"),  # 默认全部状态
        )
        records = data.get("DomainRecords", {}).get("Record", [])
        if not records:
            self.logger.warning(
                "No records found for [%s] with %s <%s> (line: %s)", zone_id, subdomain, record_type, line
            )
        elif not isinstance(records, list):
            self.logger.error("Invalid records format: %s", records)
        else:
            return next((r for r in records), None)
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        """https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-adddomainrecord"""
        data = self._request(
            "AddDomainRecord",
            DomainName=main_domain,
            RR=subdomain,
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

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        """https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-updatedomainrecord"""
        # 阿里云DNS update新旧值不能一样，先判断是否发生变化
        if (
            old_record.get("Value") == value
            and old_record.get("Type") == record_type
            and (not ttl or old_record.get("TTL") == ttl)
        ):
            domain = self._join_domain(old_record.get("RR"), old_record.get("DomainName"))
            self.logger.warning("No changes detected, skipping update for record: %s", domain)
            return True
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
