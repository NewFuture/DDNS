# coding=utf-8
"""
Tencent Cloud DNSPod API
腾讯云 DNSPod API

@author: NewFuture
"""

from time import gmtime, strftime, time

from ._base import TYPE_JSON, BaseProvider
from ._signature import hmac_sha256, hmac_sha256_authorization, sha256_hash


class TencentCloudProvider(BaseProvider):
    """
    腾讯云 DNSPod API 提供商
    Tencent Cloud DNSPod API Provider

    API Version: 2021-03-23
    Documentation: https://cloud.tencent.com/document/api/1427
    """

    endpoint = "https://dnspod.tencentcloudapi.com"
    content_type = TYPE_JSON

    # 腾讯云 DNSPod API 配置
    service = "dnspod"
    version_date = "2021-03-23"

    def _request(self, action, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict | None
        """
        发送腾讯云 API 请求

        API 文档: https://cloud.tencent.com/document/api/1427/56187

        Args:
            action (str): API 操作名称
            params (dict): 请求参数

        Returns:
            dict: API 响应结果
        """
        # 构建请求体
        params = {k: v for k, v in params.items() if v is not None}
        body = self._encode_body(params)

        # 构建请求头,小写 腾讯云只签名特定头部
        headers = {"content-type": self.content_type, "host": self.endpoint.split("://", 1)[1].strip("/")}

        # 腾讯云特殊的密钥派生过程
        date = strftime("%Y-%m-%d", gmtime())
        credential_scope = "{}/{}/tc3_request".format(date, self.service)

        # 派生签名密钥
        secret_date = hmac_sha256("TC3" + self.token, date).digest()
        secret_service = hmac_sha256(secret_date, self.service).digest()
        signing_key = hmac_sha256(secret_service, "tc3_request").digest()

        # 预处理模板字符串
        auth_format = "TC3-HMAC-SHA256 Credential=%s/%s, SignedHeaders={SignedHeaders}, Signature={Signature}" % (
            self.id,
            credential_scope,
        )
        timestamp = str(int(time()))
        sign_template = "\n".join(["TC3-HMAC-SHA256", timestamp, credential_scope, "{HashedCanonicalRequest}"])
        authorization = hmac_sha256_authorization(
            secret_key=signing_key,
            method="POST",
            path="/",
            query="",
            headers=headers,
            body_hash=sha256_hash(body),
            signing_string_format=sign_template,
            authorization_format=auth_format,
        )
        # X-TC 更新签名之后方可添加
        headers.update(
            {
                "X-TC-Action": action,
                "X-TC-Version": self.version_date,
                "X-TC-Timestamp": timestamp,
                "authorization": authorization,
            }
        )

        response = self._http("POST", "/", body=body, headers=headers)
        if response and "Response" in response:
            if "Error" in response["Response"]:
                error = response["Response"]["Error"]
                self.logger.error(
                    "TencentCloud API error: %s - %s",
                    error.get("Code", "Unknown"),
                    error.get("Message", "Unknown error"),
                )
                return None
            return response["Response"]

        self.logger.warning("Unexpected response format: %s", response)
        return None

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """查询域名的 zone_id (domain id) https://cloud.tencent.com/document/api/1427/56173"""
        # 使用 DescribeDomain API 查询指定域名的信息
        response = self._request("DescribeDomain", Domain=domain)

        if not response or "DomainInfo" not in response:
            self.logger.debug("Domain info not found or query failed for: %s", domain)
            return None

        domain_id = response.get("DomainInfo", {}).get("DomainId")

        if domain_id is not None:
            self.logger.debug("Found domain %s with ID: %s", domain, domain_id)
            return str(domain_id)

        self.logger.debug("Domain ID not found in response for: %s", domain)
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """查询 DNS 记录列表 https://cloud.tencent.com/document/api/1427/56166"""

        response = self._request(
            "DescribeRecordList",
            DomainId=int(zone_id),
            Subdomain=subdomain,
            Domain=main_domain,
            RecordType=record_type,
            RecordLine=line,
            **extra
        )  # fmt: skip
        if not response or "RecordList" not in response:
            self.logger.debug("No records found or query failed")
            return None

        records = response["RecordList"]
        if not records:
            self.logger.debug("No records found for subdomain: %s", subdomain)
            return None

        # 查找匹配的记录
        target_name = subdomain if subdomain and subdomain != "@" else "@"
        for record in records:
            if record.get("Name") == target_name and record.get("Type") == record_type.upper():
                self.logger.debug("Found existing record: %s", record)
                return record

        self.logger.debug("No matching record found")
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        """创建 DNS 记录 https://cloud.tencent.com/document/api/1427/56180"""
        extra["Remark"] = extra.get("Remark", self.remark)
        response = self._request(
            "CreateRecord",
            Domain=main_domain,
            DomainId=int(zone_id),
            SubDomain=subdomain,
            RecordType=record_type,
            Value=value,
            RecordLine=line or "默认",
            TTL=int(ttl) if ttl else None,
            **extra
        )  # fmt: skip
        if response and "RecordId" in response:
            self.logger.info("Record created successfully with ID: %s", response["RecordId"])
            return True
        self.logger.error("Failed to create record:\n%s", response)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        """更新 DNS 记录: https://cloud.tencent.com/document/api/1427/56157"""
        extra["Remark"] = extra.get("Remark", self.remark)
        response = self._request(
            "ModifyRecord",
            Domain=old_record.get("Domain", ""),
            DomainId=old_record.get("DomainId", int(zone_id)),
            SubDomain=old_record.get("Name"),
            RecordId=old_record.get("RecordId"),
            RecordType=record_type,
            RecordLine=old_record.get("Line", line or "默认"),
            Value=value,
            TTL=int(ttl) if ttl else None,
            **extra
        )  # fmt: skip
        if response and "RecordId" in response:
            self.logger.info("Record updated successfully")
            return True

        self.logger.error("Failed to update record")
        return False
