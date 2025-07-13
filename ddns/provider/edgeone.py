# coding=utf-8
"""
Tencent Cloud EdgeOne API
腾讯云 EdgeOne API

@author: NewFuture, GitHub Copilot
"""
from .tencentcloud import TencentCloudProvider


class EdgeOneProvider(TencentCloudProvider):
    """
    腾讯云 EdgeOne API 提供商
    Tencent Cloud EdgeOne API Provider

    API Version: 2022-09-01
    Documentation: https://edgeone.ai/zh/document
    """

    endpoint = "https://teo.tencentcloudapi.com"

    # 腾讯云 EdgeOne API 配置
    service = "teo"
    version_date = "2022-09-01"

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """查询域名的 zone_id https://edgeone.ai/zh/document/54132"""
        # 使用 DescribeZones API 查询站点信息
        response = self._request("DescribeZones", Filters=[{"Name": "zone-name", "Values": [domain]}])

        if not response or "Zones" not in response:
            self.logger.debug("Zone info not found or query failed for: %s", domain)
            return None

        zones = response.get("Zones", [])
        if not zones:
            self.logger.debug("No zones found for domain: %s", domain)
            return None

        zone = zones[0]  # 取第一个匹配的站点
        zone_id = zone.get("ZoneId")

        if zone_id is not None:
            self.logger.debug("Found zone %s with ID: %s", domain, zone_id)
            return str(zone_id)

        self.logger.debug("Zone ID not found in response for: %s", domain)
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """查询 DNS 记录列表 https://edgeone.ai/zh/document/50484"""

        filters = [
            {"Name": "name", "Values": [subdomain if subdomain != "@" else main_domain]},
            {"Name": "type", "Values": [record_type.upper()]},
        ]

        response = self._request("DescribeRecords", ZoneId=zone_id, Filters=filters)

        if not response or "Records" not in response:
            self.logger.debug("No records found or query failed")
            return None

        records = response["Records"]
        if not records:
            self.logger.debug("No records found for subdomain: %s", subdomain)
            return None

        # 查找匹配的记录
        target_name = subdomain if subdomain and subdomain != "@" else main_domain
        for record in records:
            record_name = record.get("Name", "")
            if record_name == target_name and record.get("Type") == record_type.upper():
                self.logger.debug("Found existing record: %s", record)
                return record

        self.logger.debug("No matching record found")
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | str | None, str | None, dict) -> bool
        """创建 DNS 记录 https://edgeone.ai/zh/document/50488"""

        record_name = subdomain if subdomain and subdomain != "@" else main_domain

        record_data = {
            "ZoneId": zone_id,
            "Name": record_name,
            "Type": record_type.upper(),
            "Content": value,
            "TTL": ttl and int(ttl),
            "Comment": extra.get("Comment", self.remark),
        }

        response = self._request("CreateRecord", **record_data)

        if response and "RecordId" in response:
            self.logger.info("Record created successfully with ID: %s", response["RecordId"])
            return True

        self.logger.error("Failed to create record:\n%s", response)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """更新 DNS 记录: https://edgeone.ai/zh/document/67541"""

        record_data = {
            "ZoneId": zone_id,
            "RecordId": old_record.get("RecordId"),
            "Name": old_record.get("Name"),
            "Type": record_type.upper(),
            "Content": value,
            "TTL": int(ttl) if ttl else old_record.get("TTL", 300),
            "Comment": extra.get("Comment", self.remark),
        }

        response = self._request("ModifyRecord", **record_data)

        if response and "RecordId" in response:
            self.logger.info("Record updated successfully")
            return True

        self.logger.error("Failed to update record")
        return False
