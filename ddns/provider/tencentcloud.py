# coding=utf-8
"""
Tencent Cloud DNSPod API
腾讯云 DNSPod API

@author: NewFuture
"""

from ._base import BaseProvider, TYPE_JSON
from hashlib import sha256
from hmac import new as hmac
from time import time, strftime


class TencentCloudProvider(BaseProvider):
    """
    腾讯云 DNSPod API 提供商
    Tencent Cloud DNSPod API Provider

    API Version: 2021-03-23
    Documentation: https://cloud.tencent.com/document/api/1427
    """

    API = "https://dnspod.tencentcloudapi.com"
    ContentType = TYPE_JSON

    # 腾讯云 DNSPod API 配置
    service = "dnspod"
    version = "2021-03-23"

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
            if key.lower() in ["content-type", "host"]:
                signed_headers_list.append(key.lower())
                canonical_headers += "{}:{}\n".format(key.lower(), headers[key])

        signed_headers = ";".join(signed_headers_list)
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()

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
        date = strftime("%Y%m%d")  # 日期
        credential_scope = "{}/{}/tc3_request".format(date, self.service)
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()

        string_to_sign = "\n".join([algorithm, str(timestamp), credential_scope, hashed_canonical_request])

        # Step 3: 计算签名
        def _sign(key, msg):
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = _sign(("TC3" + self.auth_token).encode("utf-8"), date)
        secret_service = _sign(secret_date, self.service)
        secret_signing = _sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        # Step 4: 构建 Authorization 头部
        authorization = "{} Credential={}/{}, SignedHeaders={}, Signature={}".format(
            algorithm, self.auth_id, credential_scope, signed_headers, signature
        )

        return authorization

    def _request(self, action, params=None):
        """
        发送腾讯云 API 请求

        API 文档: https://cloud.tencent.com/document/api/1427/56187

        Args:
            action (str): API 操作名称
            params (dict): 请求参数

        Returns:
            dict: API 响应结果
        """

        timestamp = int(time())
        # 构建请求头
        headers = {
            "content-type": self.ContentType,
            "host": self.API.split("://", 1)[1].strip("/"),
            "X-TC-Action": action,
            "X-TC-Version": self.version,
            "X-TC-Timestamp": int(timestamp),
        }

        # 构建请求体
        payload = self._encode(params or {}) if params else "{}"

        # 生成签名
        authorization = self._sign_tc3("POST", "/", "", headers, payload, timestamp)
        headers["Authorization"] = authorization

        # 发送请求
        try:
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

        except Exception as e:
            self.logger.error("Request failed: %s", e)
            return None

    def _query_zone_id(self, domain):
        """查询域名的 zone_id (domain id)"""
        # 腾讯云 DNSPod 中，domain 就是域名本身，不需要额外的 zone_id
        # 但为了兼容基类接口，我们返回域名作为 zone_id
        return domain

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line=None, extra=None):
        """
        查询 DNS 记录

        API 文档: https://cloud.tencent.com/document/api/1427/56166
        """
        params = {"Domain": main_domain, "RecordType": record_type.upper()}

        # 添加子域名筛选
        if sub_domain and sub_domain != "@":
            params["Subdomain"] = sub_domain

        # 添加线路筛选
        if line:
            params["RecordLine"] = line

        response = self._request("DescribeRecordList", params)
        if not response or "RecordList" not in response:
            self.logger.debug("No records found or query failed")
            return None

        records = response["RecordList"]
        if not records:
            self.logger.debug("No records found for subdomain: %s", sub_domain)
            return None

        # 查找匹配的记录
        target_name = sub_domain if sub_domain and sub_domain != "@" else "@"
        for record in records:
            if record.get("Name") == target_name and record.get("Type") == record_type.upper():
                self.logger.debug("Found existing record: %s", record)
                return record

        self.logger.debug("No matching record found")
        return None

    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra=None):
        """
        创建 DNS 记录

        API 文档: https://cloud.tencent.com/document/api/1427/56180
        """
        params = {
            "Domain": main_domain,
            "RecordType": record_type.upper(),
            "RecordLine": line or "默认",
            "Value": value,
        }

        # 添加子域名
        if sub_domain and sub_domain != "@":
            params["SubDomain"] = sub_domain

        # 添加 TTL
        if ttl:
            params["TTL"] = int(ttl)

        # 添加备注
        params["Remark"] = self.Remark

        # 处理额外参数
        if extra:
            if "mx" in extra:
                params["MX"] = int(extra["mx"])
            if "weight" in extra:
                params["Weight"] = int(extra["weight"])

        response = self._request("CreateRecord", params)
        if response and "RecordId" in response:
            self.logger.info("Record created successfully with ID: %s", response["RecordId"])
            return True

        self.logger.error("Failed to create record")
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra=None):
        """
        更新 DNS 记录

        API 文档: https://cloud.tencent.com/document/api/1427/56157
        """
        record_id = old_record.get("RecordId")
        if not record_id:
            self.logger.error("No RecordId found in old record")
            return False

        params = {
            "Domain": zone_id,  # zone_id 就是域名
            "RecordId": record_id,
            "RecordType": record_type.upper(),
            "RecordLine": line or old_record.get("Line", "默认"),
            "Value": value,
        }

        # 保持原有的子域名
        if old_record.get("Name") and old_record.get("Name") != "@":
            params["SubDomain"] = old_record["Name"]

        # 添加 TTL
        if ttl:
            params["TTL"] = int(ttl)
        elif old_record.get("TTL"):
            params["TTL"] = old_record["TTL"]

        # 保持原有的 MX 和权重设置
        if old_record.get("MX"):
            params["MX"] = old_record["MX"]
        if old_record.get("Weight"):
            params["Weight"] = old_record["Weight"]

        # 处理额外参数
        if extra:
            if "mx" in extra:
                params["MX"] = int(extra["mx"])
            if "weight" in extra:
                params["Weight"] = int(extra["weight"])

        # 保持原有备注或使用新备注
        params["Remark"] = old_record.get("Remark", self.Remark)

        response = self._request("ModifyRecord", params)
        if response and "RecordId" in response:
            self.logger.info("Record updated successfully")
            return True

        self.logger.error("Failed to update record")
        return False
