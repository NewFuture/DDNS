# coding=utf-8
"""
Tencent Cloud EdgeOne API
腾讯云 EdgeOne (边缘安全速平台) API
API Documentation: https://cloud.tencent.com/document/api/1552/80731
@author: NewFuture
"""

from ddns.provider._base import join_domain
from .tencentcloud import TencentCloudProvider


class EdgeOneProvider(TencentCloudProvider):
    """
    腾讯云 EdgeOne API 提供商
    Tencent Cloud EdgeOne API Provider
    """

    endpoint = "https://teo.tencentcloudapi.com"
    # 腾讯云 EdgeOne API 配置
    service = "teo"
    version_date = "2022-09-01"

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """查询域名的加速域名信息获取 ZoneId https://cloud.tencent.com/document/api/1552/80713"""
        # 首先尝试直接查找域名
        filters = [{"Name": "zone-name", "Values": [domain], "Fuzzy": False}]  # type: Any
        response = self._request("DescribeZones", Filters=filters)

        if response and "Zones" in response:
            for zone in response.get("Zones", []):
                if zone.get("ZoneName") == domain:
                    zone_id = zone.get("ZoneId")
                    if zone_id:
                        self.logger.debug("Found acceleration domain %s with Zone ID: %s", domain, zone_id)
                        return zone_id

        self.logger.debug("Acceleration domain not found for: %s", domain)
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """查询加速域名信息 https://cloud.tencent.com/document/api/1552/86336"""
        domain = join_domain(subdomain, main_domain)
        filters = [{"Name": "domain-name", "Values": [domain], "Fuzzy": False}]  # type: Any
        response = self._request("DescribeAccelerationDomains", ZoneId=zone_id, Filters=filters)

        if response and "AccelerationDomains" in response:
            for domain_info in response.get("AccelerationDomains", []):
                if domain_info.get("DomainName") == domain:
                    self.logger.debug("Found acceleration domain: %s", domain_info)
                    return domain_info

        self.logger.warning("No acceleration domain found for: %s, response: %s", domain, response)
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int, str | None, dict) -> bool
        """创建新的加速域名记录 https://cloud.tencent.com/document/api/1552/86338"""
        domain = join_domain(subdomain, main_domain)
        origin = {"OriginType": "IP_DOMAIN", "Origin": value}  # type: Any
        res = self._request("CreateAccelerationDomain", ZoneId=zone_id, DomainName=domain, OriginInfo=origin, **extra)
        if res:
            self.logger.info("Acceleration domain created (%s)", res.get("RequestId"))
            return True

        self.logger.error("Failed to create acceleration domain, response: %s", res)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        """更新加速域名的源站 IP 地址 https://cloud.tencent.com/document/api/1552/86335"""
        domain = old_record.get("DomainName")
        # 构建源站信息
        backup = old_record.get("OriginDetail", {}).get("BackupOrigin", "")
        origin = {"OriginType": "IP_DOMAIN", "Origin": value, "BackupOrigin": backup}  # type: Any
        response = self._request("ModifyAccelerationDomain", ZoneId=zone_id, DomainName=domain, OriginInfo=origin)

        if response:
            self.logger.info("Acceleration domain updated (%s)", response.get("RequestId"))
            return True
        self.logger.error("Failed to update acceleration domain origin, response: %s", response)
        return False
