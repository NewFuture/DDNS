# coding=utf-8
"""
Tencent Cloud EdgeOne API
腾讯云 EdgeOne (边缘安全速平台) API

EdgeOne is Tencent Cloud's edge security acceleration platform that provides 
DNS resolution capabilities among other services.

API Documentation: https://cloud.tencent.com/document/product/1552
@author: NewFuture
"""
from .tencentcloud import TencentCloudProvider


class EdgeOneProvider(TencentCloudProvider):
    """
    腾讯云 EdgeOne API 提供商
    Tencent Cloud EdgeOne API Provider

    API Version: 2022-09-01
    Documentation: https://cloud.tencent.com/document/product/1552
    """

    endpoint = "https://teo.tencentcloudapi.com"
    # 腾讯云 EdgeOne API 配置
    service = "teo"
    version_date = "2022-09-01"

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """查询域名的 zone_id (ZoneId) https://cloud.tencent.com/document/api/1552/86336"""
        response = self._request("DescribeZones", Filters=[{"Name": "zone-name", "Values": [domain]}])

        if not response or "Zones" not in response:
            self.logger.debug("Zone info not found or query failed for: %s", domain)
            return None

        zones = response.get("Zones", [])
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
        target_name = subdomain if subdomain and subdomain != "@" else main_domain
        for record in records:
            record_name = record.get("Name", "")
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
        
        response = self._request(
            "CreateDnsRecord",
            ZoneId=zone_id,
            Name=record_name,
            Type=record_type.upper(),
            Content=value,
            TTL=int(ttl) if ttl else None,
            **extra
        )
        
        if response and "RecordId" in response:
            self.logger.info("Record created successfully with ID: %s", response["RecordId"])
            return True
        self.logger.error("Failed to create record:\n%s", response)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        """更新 DNS 记录: https://cloud.tencent.com/document/api/1552/86335"""
        
        response = self._request(
            "ModifyDnsRecord",
            ZoneId=zone_id,
            RecordId=old_record.get("RecordId"),
            Type=record_type.upper(),
            Name=old_record.get("Name"),
            Content=value,
            TTL=int(ttl) if ttl else old_record.get("TTL"),
            **extra
        )
        
        if response and "RecordId" in response:
            self.logger.info("Record updated successfully")
            return True

        self.logger.error("Failed to update record")
        return False