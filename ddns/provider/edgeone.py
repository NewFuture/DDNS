# coding=utf-8
"""
Tencent Cloud EdgeOne API
腾讯云 EdgeOne (边缘安全速平台) API

EdgeOne is Tencent Cloud's edge security acceleration platform.
For DDNS, EdgeOne manages acceleration domains and updates the origin server IP address.

API Documentation: https://cloud.tencent.com/document/api/1552/80731
@author: NewFuture
"""
from .tencentcloud import TencentCloudProvider


class EdgeOneProvider(TencentCloudProvider):
    """
    腾讯云 EdgeOne API 提供商
    Tencent Cloud EdgeOne API Provider

    EdgeOne manages acceleration domains, not traditional DNS records.
    DDNS updates the origin server IP address for acceleration domains.

    API Version: 2022-09-01
    Documentation: https://cloud.tencent.com/document/api/1552/80731
    """

    endpoint = "https://teo.tencentcloudapi.com"
    # 腾讯云 EdgeOne API 配置
    service = "teo"
    version_date = "2022-09-01"

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """查询域名的加速域名信息获取 ZoneId
        使用 DescribeAccelerationDomains API
        https://cloud.tencent.com/document/api/1552/80731
        """
        # 首先尝试直接查找域名
        response = self._request(
            "DescribeAccelerationDomains",
            Filters=[
                {
                    "Name": "domain-name",
                    "Values": [domain],
                    "Fuzzy": False
                }
            ]
        )

        if response and "AccelerationDomains" in response:
            domains = response["AccelerationDomains"]
            for domain_info in domains:
                if domain_info.get("DomainName") == domain:
                    zone_id = domain_info.get("ZoneId")
                    if zone_id:
                        self.logger.debug("Found acceleration domain %s with Zone ID: %s", domain, zone_id)
                        return str(zone_id)

        self.logger.debug("Acceleration domain not found for: %s", domain)
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """查询加速域名信息
        EdgeOne 通过查询加速域名的源站信息来获取当前配置
        https://cloud.tencent.com/document/api/1552/80731
        """
        target_domain = "{}.{}".format(subdomain, main_domain) if subdomain and subdomain != "@" else main_domain
        
        response = self._request(
            "DescribeAccelerationDomains",
            ZoneId=zone_id,
            Filters=[
                {
                    "Name": "domain-name",
                    "Values": [target_domain],
                    "Fuzzy": False
                }
            ]
        )

        if response and "AccelerationDomains" in response:
            domains = response["AccelerationDomains"]
            for domain_info in domains:
                if domain_info.get("DomainName") == target_domain:
                    # 返回加速域名信息，包含当前的源站配置
                    self.logger.debug("Found acceleration domain: %s", domain_info)
                    return domain_info

        self.logger.debug("No acceleration domain found for: %s", target_domain)
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        """EdgeOne 不支持创建新的加速域名记录
        需要在 EdgeOne 控制台预先配置加速域名
        """
        self.logger.error("EdgeOne does not support creating new acceleration domains via API")
        self.logger.error("Please configure the acceleration domain in EdgeOne console first")
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        """更新加速域名的源站 IP 地址
        使用 ModifyAccelerationDomain API
        https://cloud.tencent.com/document/api/1552/80730
        """
        domain_name = old_record.get("DomainName")
        if not domain_name:
            self.logger.error("Domain name not found in acceleration domain info")
            return False

        # 构建源站信息
        origin_info = {
            "OriginType": "ip_domain",
            "Origin": value
        }

        # 如果原配置中有备用源站，保持不变
        origin_detail = old_record.get("OriginDetail", {})
        if origin_detail.get("BackupOrigin"):
            origin_info["BackupOrigin"] = origin_detail["BackupOrigin"]

        response = self._request(
            "ModifyAccelerationDomain",
            ZoneId=zone_id,
            DomainName=domain_name,
            OriginInfo=origin_info
        )

        if response is not None:
            # EdgeOne ModifyAccelerationDomain 成功时通常返回空响应体
            self.logger.info("Acceleration domain origin updated successfully for %s to %s", domain_name, value)
            return True

        self.logger.error("Failed to update acceleration domain origin")
        return False