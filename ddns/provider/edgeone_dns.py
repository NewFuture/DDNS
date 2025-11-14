# coding=utf-8
"""
Tencent Cloud EdgeOne DNS API
腾讯云 EdgeOne (边缘安全速平台) DNS API - 非加速域名管理
API Documentation: https://cloud.tencent.com/document/api/1552/80731
@author: NewFuture
"""

from ddns.provider._base import join_domain
from .edgeone import EdgeOneProvider


class EdgeOneDnsProvider(EdgeOneProvider):
    """
    腾讯云 EdgeOne DNS API 提供商 - 用于管理非加速域名
    Tencent Cloud EdgeOne DNS API Provider - For managing non-accelerated DNS records
    """

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """查询 DNS 记录 https://cloud.tencent.com/document/api/1552/86336"""
        domain = join_domain(subdomain, main_domain)
        filters = [{"Name": "name", "Values": [domain], "Fuzzy": False}]  # type: Any
        response = self._request("DescribeDnsRecords", ZoneId=zone_id, Filters=filters)

        if response and "DnsRecords" in response:
            for record_info in response.get("DnsRecords", []):
                if record_info.get("Name") == domain and record_info.get("Type") == record_type:
                    self.logger.debug("Found DNS record: %s", record_info)
                    return record_info

        self.logger.warning("No DNS record found for: %s, response: %s", domain, response)
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int, str | None, dict) -> bool
        """创建新的 DNS 记录 https://cloud.tencent.com/document/api/1552/86338"""
        domain = join_domain(subdomain, main_domain)
        res = self._request("CreateDnsRecord", ZoneId=zone_id, Name=domain, Type=record_type, Content=value)
        if res:
            self.logger.info("DNS record created (%s)", res.get("RequestId"))
            return True

        self.logger.error("Failed to create DNS record, response: %s", res)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """更新 DNS 记录 https://cloud.tencent.com/document/api/1552/86335"""
        # 构建 DNS 记录更新信息
        new_record = {
            "RecordId": old_record.get("RecordId"),
            "Name": old_record.get("Name"),
            "Type": record_type,
            "Content": value,
        }
        response = self._request("ModifyDnsRecords", ZoneId=zone_id, DnsRecords=[new_record])

        if response:
            self.logger.info("DNS record updated (%s)", response.get("RequestId"))
            return True
        self.logger.error("Failed to update DNS record, response: %s", response)
        return False
