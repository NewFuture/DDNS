# coding=utf-8
"""
AliESA API
阿里云边缘安全加速(ESA) DNS 解析操作库
@author: NewFuture
"""

from ._base import TYPE_FORM, BaseProvider, hmac_sha256_authorization, sha256_hash
from time import strftime, gmtime, time


class AliesaProvider(BaseProvider):
    API = "https://esa.cn-hangzhou.aliyuncs.com"
    content_type = TYPE_FORM  # 阿里云ESA API使用表单格式

    api_version = "2024-09-10"  # ESA API版本

    def _request(self, action, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict
        """Aliyun ESA v3 API request with signature"""
        params = {k: v for k, v in params.items() if v is not None}
        body_content = self._encode(params) if len(params) > 0 else ""
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
            method="POST",
            path="/",
            query="",
            headers=headers,
            body_hash=content_hash,
            signing_string_format="ACS3-HMAC-SHA256\n{HashedCanonicalRequest}",
            authorization_format=(
                "ACS3-HMAC-SHA256 Credential=" + self.auth_id + ",SignedHeaders={SignedHeaders},Signature={Signature}"
            ),
        )
        headers["Authorization"] = authorization
        return self._http("POST", "/", body=body_content, headers=headers)

    def _split_zone_and_sub(self, domain):
        # type: (str) -> tuple[str | None, str | None, str]
        """
        AliESA 类似于 AliDNS，需要查询站点 ID
        返回 (zone_id, subdomain, main_domain)
        """
        # 提取主域名
        main_domain = self._extract_main_domain(domain)
        
        # 获取站点ID (zone_id)
        zone_id = self._query_zone_id(main_domain)
        
        if zone_id:
            # 计算子域名部分
            if domain == main_domain:
                subdomain = "@"  # 根域名使用 @
            else:
                # 移除主域名部分得到子域名
                if domain.endswith("." + main_domain):
                    subdomain = domain[:-len("." + main_domain)]
                else:
                    subdomain = domain
            
            return zone_id, subdomain, main_domain
        
        return None, None, main_domain

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """
        查询站点ID
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-listsites
        """
        res = self._request("ListSites", SiteName=domain, PageSize=50)
        sites = res.get("Sites", [])
        
        for site in sites:
            if site.get("SiteName") == domain:
                site_id = site.get("SiteId")
                self.logger.debug("Found site ID %s for domain %s", site_id, domain)
                return str(site_id)
        
        self.logger.error("Site not found for domain: %s", domain)
        return None

    def _extract_main_domain(self, domain):
        # type: (str) -> str
        """提取主域名，去除子域名部分"""
        parts = domain.split('.')
        if len(parts) >= 2:
            # 返回最后两级域名作为主域名
            return '.'.join(parts[-2:])
        return domain

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """
        查询DNS记录
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-listrecords
        """
        full_domain = self._join_domain(subdomain, main_domain)
        
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
                "No records found for [%s] with %s <%s> (line: %s)", zone_id, subdomain, record_type, line
            )
            return None
        
        # 返回第一个匹配的记录
        record = records[0]
        self.logger.debug("Found record: %s", record)
        return record

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | None, str | None, dict) -> bool
        """
        创建DNS记录
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-createrecord
        """
        full_domain = self._join_domain(subdomain, main_domain)
        
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

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
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
            self.logger.warning("No changes detected, skipping update for record: %s", old_record.get("RecordName"))
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