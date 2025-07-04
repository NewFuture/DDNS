# coding=utf-8
"""
AliESA API
阿里云边缘安全加速(ESA) DNS 解析操作库
@author: NewFuture
"""

from .alidns import AliBaseProvider
from ._base import join_domain


class AliesaProvider(AliBaseProvider):
    """阿里云边缘安全加速(ESA) DNS Provider"""
    API = "https://esa.cn-hangzhou.aliyuncs.com"
    api_version = "2024-09-10"  # ESA API版本

    def _validate(self):
        """验证并解析认证信息，支持区域配置"""
        # 解析auth_id，支持 "region:access_id" 或 "access_id" 格式
        if ':' in self.auth_id:
            region, access_id = self.auth_id.split(':', 1)
            if not region or not access_id:
                raise ValueError(
                    "Invalid auth_id format. "
                    "Use 'region:access_id' or 'access_id'"
                )
            self.API = "https://esa.{}.aliyuncs.com".format(region)
            self.auth_id = access_id
        # 调用父类验证
        super(AliesaProvider, self)._validate()

    def _request(self, action, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict
        """ESA API request with appropriate HTTP method for each action"""
        # ESA API uses different HTTP methods for different operations
        if action in ["ListSites", "ListRecords"]:
            # Query operations use GET
            return self._request_with_method("GET", action, **params)
        else:
            # Modification operations use POST
            return self._request_with_method("POST", action, **params)

    def _request_with_method(self, method, action, **params):
        # type: (str, str, **(str | int | bytes | bool | None)) -> dict
        """ESA API request with specific HTTP method"""
        from ._base import sha256_hash, hmac_sha256_authorization
        from time import strftime, gmtime, time

        params = {k: v for k, v in params.items() if v is not None}

        if method == "GET":
            # For GET requests, parameters go in query string
            query_string = self._encode(params) if len(params) > 0 else ""
            body_content = ""
            path = "/" if not query_string else "/?{}".format(query_string)
        else:
            # For POST requests, parameters go in body
            body_content = self._encode(params) if len(params) > 0 else ""
            path = "/"
            query_string = ""

        content_hash = sha256_hash(body_content)

        # 构造请求头部
        headers = {
            "host": self.API.split("://", 1)[1].strip("/"),
            "content-type": self.content_type,
            "x-acs-action": action,
            "x-acs-content-sha256": content_hash,
            "x-acs-date": strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()),
            "x-acs-signature-nonce": str(hash(time()))[2:],
            "x-acs-version": self.api_version,
        }

        # 使用通用签名函数
        authorization = hmac_sha256_authorization(
            secret_key=self.auth_token,
            method=method,
            path=path,
            query=query_string,
            headers=headers,
            body_hash=content_hash,
            signing_string_format="ACS3-HMAC-SHA256\n{HashedCanonicalRequest}",
            authorization_format=(
                "ACS3-HMAC-SHA256 Credential=" + self.auth_id +
                ",SignedHeaders={SignedHeaders},Signature={Signature}"
            ),
        )
        headers["Authorization"] = authorization

        # Make the HTTP request
        return self._http(method, path, body=body_content, headers=headers)

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """
        查询站点ID
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-listsites
        """
        res = self._request("ListSites", SiteName=domain, PageSize=500)
        sites = res.get("Sites", [])

        for site in sites:
            if site.get("SiteName") == domain:
                site_id = site.get("SiteId")
                self.logger.debug(
                    "Found site ID %s for domain %s", site_id, domain
                )
                return str(site_id)

        self.logger.error("Site not found for domain: %s", domain)
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type,
                      line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """
        查询DNS记录
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-listrecords
        """
        full_domain = join_domain(subdomain, main_domain)

        res = self._request(
            "ListRecords",
            SiteId=int(zone_id),
            RecordName=full_domain,
            Type=record_type,
            PageSize=100
        )

        records = res.get("Records", [])
        if not records:
            self.logger.warning(
                "No records found for [%s] with %s <%s> (line: %s)",
                zone_id, subdomain, record_type, line
            )
            return None

        # 返回第一个匹配的记录
        record = records[0]
        self.logger.debug("Found record: %s", record)
        return record

    def _create_record(self, zone_id, subdomain, main_domain, value,
                       record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | None, str | None, dict) -> bool
        """
        创建DNS记录
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-createrecord
        """
        full_domain = join_domain(subdomain, main_domain)

        params = {
            "SiteId": int(zone_id),
            "RecordName": full_domain,
            "Type": record_type,
            "Value": value,
        }

        if ttl:
            params["TTL"] = int(ttl)

        # 添加备注信息
        if extra.get("Comment"):
            params["Remark"] = extra["Comment"]

        data = self._request("CreateRecord", **params)

        if data and data.get("RecordId"):
            self.logger.info("Record created: %s", data)
            return True

        self.logger.error("Failed to create record: %s", data)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl,
                       line, extra):
        # type: (str, dict, str, str, int | None, str | None, dict) -> bool
        """
        更新DNS记录
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-updaterecord
        """
        # 检查是否需要更新
        if (
            old_record.get("Value") == value
            and old_record.get("Type") == record_type
            and (not ttl or old_record.get("TTL") == ttl)
        ):
            self.logger.warning(
                "No changes detected, skipping update for record: %s",
                old_record.get("RecordName")
            )
            return True

        params = {
            "SiteId": int(zone_id),
            "RecordId": old_record.get("RecordId"),
            "Type": record_type,
            "Value": value,
        }

        if ttl:
            params["TTL"] = int(ttl)

        # 添加备注信息
        if extra.get("Comment"):
            params["Remark"] = extra["Comment"]

        data = self._request("UpdateRecord", **params)

        if data and data.get("RecordId"):
            self.logger.info("Record updated: %s", data)
            return True

        self.logger.error("Failed to update record: %s", data)
        return False
