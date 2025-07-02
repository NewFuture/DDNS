# coding=utf-8
"""
AliESA API
阿里云边缘安全加速(ESA) DNS 解析操作库
@author: NewFuture
"""

from .alidns import AliBaseProvider


class AliesaProvider(AliBaseProvider):
    """阿里云边缘安全加速(ESA) DNS Provider"""
    API = "https://esa.cn-hangzhou.aliyuncs.com"
    api_version = "2024-09-10"  # ESA API版本

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
                self.logger.debug("Found site ID %s for domain %s", site_id, domain)
                return str(site_id)

        self.logger.error("Site not found for domain: %s", domain)
        return None

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
