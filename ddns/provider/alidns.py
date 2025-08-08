# coding=utf-8
"""
AliDNS API
阿里DNS解析操作库
@author: NewFuture
"""

from time import gmtime, strftime, time

from ._base import TYPE_FORM, BaseProvider, encode_params, join_domain
from ._signature import hmac_sha256_authorization, sha256_hash


class AliBaseProvider(BaseProvider):
    """阿里云基础Provider，提供通用的_request方法"""

    endpoint = "https://alidns.aliyuncs.com"
    content_type = TYPE_FORM  # 阿里云DNS API使用表单格式
    api_version = "2015-01-09"  # API版本，v3签名需要

    def _request(self, action, method="POST", **params):
        # type: (str, str, **(Any)) -> dict
        """Aliyun v3 https://help.aliyun.com/zh/sdk/product-overview/v3-request-structure-and-signature"""
        params = {k: v for k, v in params.items() if v is not None}

        if method in ("GET", "DELETE"):
            # For GET and DELETE requests, parameters go in query string
            query_string = encode_params(params) if len(params) > 0 else ""
            body_content = ""
        else:
            # For POST requests, parameters go in body
            body_content = self._encode_body(params)
            query_string = ""

        path = "/"
        content_hash = sha256_hash(body_content)
        # 构造请求头部
        headers = {
            "host": self.endpoint.split("://", 1)[1].strip("/"),
            "content-type": self.content_type,
            "x-acs-action": action,
            "x-acs-content-sha256": content_hash,
            "x-acs-date": strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()),
            "x-acs-signature-nonce": str(hash(time()))[2:],
            "x-acs-version": self.api_version,
        }

        # 使用通用签名函数
        authorization = hmac_sha256_authorization(
            secret_key=self.token,
            method=method,
            path=path,
            query=query_string,
            headers=headers,
            body_hash=content_hash,
            signing_string_format="ACS3-HMAC-SHA256\n{HashedCanonicalRequest}",
            authorization_format=(
                "ACS3-HMAC-SHA256 Credential=" + self.id + ",SignedHeaders={SignedHeaders},Signature={Signature}"
            ),
        )
        headers["Authorization"] = authorization
        # 对于v3签名的RPC API，参数在request body中
        path = path if not query_string else path + "?" + format(query_string)
        return self._http(method, path, body=body_content, headers=headers)


class AlidnsProvider(AliBaseProvider):
    """阿里云DNS Provider"""

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
        sub = join_domain(subdomain, main_domain)
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
        )  # fmt: skip
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
            domain = join_domain(old_record.get("RR"), old_record.get("DomainName"))
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
        )  # fmt: skip
        if data and data.get("RecordId"):
            self.logger.info("Record updated: %s", data)
            return True
        self.logger.error("Failed to update record: %s", data)
        return False
