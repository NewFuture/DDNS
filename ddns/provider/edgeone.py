# coding=utf-8
"""
Tencent Cloud EdgeOne API
腾讯云 EdgeOne (边缘安全速平台) API

EdgeOne is Tencent Cloud's edge security acceleration platform that provides 
DNS resolution capabilities among other services.

API Documentation: https://cloud.tencent.com/document/product/1552
@author: NewFuture
"""
from ._base import BaseProvider, TYPE_JSON
from ._signature import hmac_sha256_authorization, sha256_hash, hmac_sha256
from time import time, strftime, gmtime


class EdgeOneProvider(BaseProvider):
    """
    腾讯云 EdgeOne API 提供商
    Tencent Cloud EdgeOne API Provider

    API Version: 2022-09-01
    Documentation: https://cloud.tencent.com/document/product/1552
    """

    endpoint = "https://teo.tencentcloudapi.com"
    content_type = TYPE_JSON

    # 腾讯云 EdgeOne API 配置
    service = "teo"
    version_date = "2022-09-01"

    def _request(self, action, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict | None
        """
        发送腾讯云 EdgeOne API 请求

        API 文档: https://cloud.tencent.com/document/product/1552/80725

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
        headers = {
            "content-type": self.content_type,
            "host": self.endpoint.split("://", 1)[1].strip("/"),
        }

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
                    "EdgeOne API error: %s - %s",
                    error.get("Code", "Unknown"),
                    error.get("Message", "Unknown error"),
                )
                return None
            return response["Response"]

        self.logger.warning("Unexpected response format: %s", response)
        return None

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """查询域名的 zone_id (ZoneId) https://cloud.tencent.com/document/api/1552/86336"""
        # 使用 DescribeZones API 查询指定域名的信息
        response = self._request("DescribeZones", Filters=[{"Name": "zone-name", "Values": [domain]}])

        if not response or "Zones" not in response:
            self.logger.debug("Zone info not found or query failed for: %s", domain)
            return None

        zones = response.get("Zones", [])
        if not zones:
            self.logger.debug("No zones found for domain: %s", domain)
            return None

        # 查找精确匹配的域名
        for zone in zones:
            if zone.get("ZoneName") == domain:
                zone_id = zone.get("ZoneId")
                if zone_id:
                    self.logger.debug("Found domain %s with Zone ID: %s", domain, zone_id)
                    return str(zone_id)

        self.logger.debug("Zone ID not found for domain: %s", domain)
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """查询 DNS 记录列表 https://cloud.tencent.com/document/api/1552/86336"""

        response = self._request(
            "DescribeDnsRecords",
            ZoneId=zone_id,
            Filters=[
                {"Name": "name", "Values": [subdomain]},
                {"Name": "type", "Values": [record_type.upper()]},
            ]
        )
        if not response or "DnsRecords" not in response:
            self.logger.debug("No records found or query failed")
            return None

        records = response["DnsRecords"]
        if not records:
            self.logger.debug("No records found for subdomain: %s", subdomain)
            return None

        # 查找匹配的记录
        target_name = subdomain if subdomain and subdomain != "@" else main_domain
        for record in records:
            record_name = record.get("Name", "")
            # EdgeOne可能返回完整域名或者只是子域名，需要灵活匹配
            if (record_name == target_name or 
                record_name == subdomain or 
                record_name == "{}.{}".format(subdomain, main_domain)) and \
               record.get("Type") == record_type.upper():
                self.logger.debug("Found existing record: %s", record)
                return record

        self.logger.debug("No matching record found")
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        """创建 DNS 记录 https://cloud.tencent.com/document/api/1552/86338"""
        record_name = subdomain if subdomain and subdomain != "@" else main_domain
        
        # 构建记录参数
        record_params = {
            "ZoneId": zone_id,
            "Name": record_name,
            "Type": record_type.upper(),
            "Content": value,
        }
        
        # TTL 参数
        if ttl:
            record_params["TTL"] = int(ttl)
            
        # 添加额外参数
        if extra:
            record_params.update(extra)

        response = self._request("CreateDnsRecord", **record_params)
        
        if response and "RecordId" in response:
            self.logger.info("Record created successfully with ID: %s", response["RecordId"])
            return True
        self.logger.error("Failed to create record:\n%s", response)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        """更新 DNS 记录: https://cloud.tencent.com/document/api/1552/86335"""
        
        # 构建更新参数
        update_params = {
            "ZoneId": zone_id,
            "RecordId": old_record.get("RecordId"),
            "Type": record_type.upper(),
            "Name": old_record.get("Name"),
            "Content": value,
        }
        
        # TTL 参数 - 使用新的TTL或保持原有TTL
        if ttl:
            update_params["TTL"] = int(ttl)
        elif old_record.get("TTL"):
            update_params["TTL"] = old_record.get("TTL")
            
        # 添加额外参数
        if extra:
            update_params.update(extra)

        response = self._request("ModifyDnsRecord", **update_params)
        
        if response and "RecordId" in response:
            self.logger.info("Record updated successfully")
            return True

        self.logger.error("Failed to update record")
        return False