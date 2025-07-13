# coding=utf-8
"""
Tencent Cloud EdgeOne API
腾讯云 EdgeOne API

@author: NewFuture, GitHub Copilot
"""
from .tencentcloud import TencentCloudProvider
from ._base import join_domain


class EdgeOneProvider(TencentCloudProvider):
    """
    腾讯云 EdgeOne API 提供商
    Tencent Cloud EdgeOne API Provider
    Documentation: https://edgeone.ai/zh/document
    """

    endpoint = "https://teo.tencentcloudapi.com"

    # 腾讯云 EdgeOne API 配置
    service = "teo"
    version_date = "2022-09-01"

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """查询域名的 zone_id https://edgeone.ai/zh/document/54132"""
        response = self._request(
            "DescribeZones",
            Filters=[{"Name": "zone-name", "Values": [domain]}],  # type: ignore[arg-type]
        )

        zones = response.get("Zones", []) if response else []
        if zones and zones[0].get("ZoneId"):
            zone_id = zones[0]["ZoneId"]
            self.logger.debug("Found zone %s with ID: %s", domain, zone_id)
            return zone_id
        self.logger.info("No zone found for domain %s", domain)
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """查询 DNS 记录列表 https://edgeone.ai/zh/document/50484"""
        name = join_domain(subdomain, main_domain)
        filters = [
            {"Name": "name", "Values": [name]},
            {"Name": "type", "Values": [record_type]},
        ]
        response = self._request("DescribeRecords", ZoneId=zone_id, Filters=filters)  # type: ignore[arg-type]

        records = response.get("Records", []) if response else []
        for record in records:
            if record.get("Name") == name and record.get("Type") == record_type:
                self.logger.debug("Found existing record: %s", record)
                return record
        self.logger.warning("No existing record found for %s", name)
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | str | None, str | None, dict) -> bool
        """创建 DNS 记录 https://edgeone.ai/zh/document/50488"""
        response = self._request(
            "CreateRecord",
            ZoneId=zone_id,
            Name=join_domain(subdomain, main_domain),
            Type=record_type.upper(),
            Content=value,
            TTL=ttl and int(ttl),
            Comment=extra.get("Comment", self.remark),
        )

        if response and response.get("RecordId"):
            self.logger.info("Record created successfully with ID: %s", response["RecordId"])
            return True
        self.logger.error("Failed to create record: %s", response)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """更新 DNS 记录 https://edgeone.ai/zh/document/67541"""
        response = self._request(
            "ModifyRecord",
            ZoneId=zone_id,
            RecordId=old_record.get("RecordId"),
            Name=old_record.get("Name"),
            Type=record_type.upper(),
            Content=value,
            TTL=int(ttl) if ttl else old_record.get("TTL", 300),
            Comment=extra.get("Comment", self.remark),
        )

        if response and response.get("RecordId"):
            self.logger.info("Record updated successfully")
            return True
        self.logger.error("Failed to update record: %s", response)
        return False
