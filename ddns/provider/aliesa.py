# coding=utf-8
"""
AliESA API
阿里云边缘安全加速(ESA) DNS 解析操作库
@author: NewFuture, GitHub Copilot
"""

from time import strftime

from ._base import TYPE_JSON, join_domain
from .alidns import AliBaseProvider


class AliesaProvider(AliBaseProvider):
    """阿里云边缘安全加速(ESA) DNS Provider"""

    endpoint = "https://esa.cn-hangzhou.aliyuncs.com"
    api_version = "2024-09-10"  # ESA API版本
    content_type = TYPE_JSON
    remark = "Managed by DDNS %s" % strftime("%Y-%m-%d %H:%M:%S")

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """
        查询站点ID
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-listsites
        """
        res = self._request(method="GET", action="ListSites", SiteName=domain, PageSize=500)
        sites = res.get("Sites", [])

        for site in sites:
            if site.get("SiteName") == domain:
                site_id = site.get("SiteId")
                self.logger.debug("Found site ID %s for domain %s", site_id, domain)
                return site_id

        self.logger.error("Site not found for domain: %s", domain)
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """
        查询DNS记录
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-listrecords
        """
        full_domain = join_domain(subdomain, main_domain)
        res = self._request(
            method="GET",
            action="ListRecords",
            SiteId=int(zone_id),
            RecordName=full_domain,
            Type=self._get_type(record_type),
            RecordMatchType="exact",  # 精确匹配
            PageSize=100,
        )

        records = res.get("Records", [])
        if len(records) == 0:
            self.logger.warning("No records found for [%s] with %s <%s>", zone_id, full_domain, record_type)
            return None

        # 返回第一个匹配的记录
        record = records[0]
        self.logger.debug("Found record: %s", record)
        return record

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | str | None, str | None, dict) -> bool
        """
        创建DNS记录
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-createrecord
        """
        full_domain = join_domain(subdomain, main_domain)
        extra["Comment"] = extra.get("Comment", self.remark)
        extra["BizName"] = extra.get("BizName", "web")
        extra["Proxied"] = extra.get("Proxied", True)
        data = self._request(
            method="POST",
            action="CreateRecord",
            SiteId=int(zone_id),
            RecordName=full_domain,
            Type=self._get_type(record_type),
            Data={"Value": value},
            Ttl=ttl or 1,
            **extra
        )  # fmt: skip

        if data and data.get("RecordId"):
            self.logger.info("Record created: %s", data)
            return True

        self.logger.error("Failed to create record: %s", data)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """
        更新DNS记录
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-updaterecord
        """
        # 检查是否需要更新
        if (
            old_record.get("Data", {}).get("Value") == value
            and old_record.get("RecordType") == self._get_type(record_type)
            and (not ttl or old_record.get("Ttl") == ttl)
        ):
            self.logger.warning("No changes detected, skipping update for record: %s", old_record.get("RecordName"))
            return True

        extra["Comment"] = extra.get("Comment", self.remark)
        extra["Proxied"] = extra.get("Proxied", old_record.get("Proxied"))
        data = self._request(
            method="POST",
            action="UpdateRecord",
            RecordId=old_record.get("RecordId"),
            Data={"Value": value},
            Ttl=ttl,
            **extra
        )  # fmt: skip

        if data and data.get("RecordId"):
            self.logger.info("Record updated: %s", data)
            return True

        self.logger.error("Failed to update record: %s", data)
        return False

    def _get_type(self, record_type):
        # type: (str) -> str
        return "A/AAAA" if record_type in ("A", "AAAA") else record_type
