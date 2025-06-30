# coding=utf-8
"""
Tencent Cloud DNSPod API
腾讯云 DNSPod API

@author: NewFuture
"""
from ._base import BaseProvider, TYPE_JSON
from hashlib import sha256
from hmac import new as hmac
from time import time, strftime, gmtime
from json import dumps as jsonencode


class TencentCloudProvider(BaseProvider):
    """
    腾讯云 DNSPod API 提供商
    Tencent Cloud DNSPod API Provider

    API Version: 2021-03-23
    Documentation: https://cloud.tencent.com/document/api/1427
    """

    API = "https://dnspod.tencentcloudapi.com"
    content_type = TYPE_JSON

    # 腾讯云 DNSPod API 配置
    service = "dnspod"
    version_date = "2021-03-23"

    def _sign_tc3(self, method, uri, query, headers, payload, timestamp):
        """
        腾讯云 API 3.0 签名算法 (TC3-HMAC-SHA256)

        API 文档: https://cloud.tencent.com/document/api/1427/56189

        Args:
            method (str): HTTP 方法
            uri (str): URI 路径
            query (str): 查询字符串
            headers (dict): 请求头
            payload (str): 请求体
            timestamp (int): 时间戳

        Returns:
            str: Authorization 头部值
        """
        algorithm = "TC3-HMAC-SHA256"

        # Step 1: 构建规范请求串
        http_request_method = method.upper()
        canonical_uri = uri
        canonical_querystring = query or ""

        # 构建规范头部
        signed_headers_list = []
        canonical_headers = ""
        for key in sorted(headers.keys()):
            if key in ["content-type", "host"]:
                signed_headers_list.append(key)
                canonical_headers += "{}:{}\n".format(key, headers[key])

        signed_headers = ";".join(signed_headers_list)
        hashed_request_payload = sha256(payload.encode("utf-8")).hexdigest()

        canonical_request = "\n".join(
            [
                http_request_method,
                canonical_uri,
                canonical_querystring,
                canonical_headers,
                signed_headers,
                hashed_request_payload,
            ]
        )

        # Step 2: 构建待签名字符串
        date = strftime("%Y-%m-%d", gmtime())  # 日期
        credential_scope = "{}/{}/tc3_request".format(date, self.service)
        hashed_canonical_request = sha256(canonical_request.encode("utf-8")).hexdigest()

        string_to_sign = "\n".join([algorithm, str(timestamp), credential_scope, hashed_canonical_request])

        # Step 3: 计算签名
        def _sign(key, msg):
            return hmac(key, msg.encode("utf-8"), sha256).digest()

        secret_date = _sign(("TC3" + self.auth_token).encode("utf-8"), date)
        secret_service = _sign(secret_date, self.service)
        secret_signing = _sign(secret_service, "tc3_request")
        signature = hmac(secret_signing, string_to_sign.encode("utf-8"), sha256).hexdigest()

        # Step 4: 构建 Authorization 头部
        authorization = "{} Credential={}/{}, SignedHeaders={}, Signature={}".format(
            algorithm, self.auth_id, credential_scope, signed_headers, signature
        )

        return authorization

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
        params = {k: v for k, v in params.items() if v is not None}
        timestamp = int(time())
        # 构建请求头,小写
        headers = {
            "content-type": self.content_type,
            "host": self.API.split("://", 1)[1].strip("/"),
            "X-TC-Action": action,
            "X-TC-Version": self.version_date,
            "X-TC-Timestamp": str(timestamp),
        }

        # 构建请求体
        payload = jsonencode(params)

        # 生成签名
        authorization = self._sign_tc3("POST", "/", "", headers, payload, timestamp)
        headers["authorization"] = authorization

        # 发送请求
        response = self._http("POST", "/", body=payload, headers=headers)

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
        )
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
        )
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
        )
        if response and "RecordId" in response:
            self.logger.info("Record updated successfully")
            return True

        self.logger.error("Failed to update record")
        return False
