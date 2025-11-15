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
        """
        查询域名信息
        支持通过 extra 参数或 options 配置 teoDomainType 控制查询类型:
        - teoDomainType="dns": 查询 DNS 记录 (非加速域名)
        - teoDomainType="acceleration" 或未设置: 查询加速域名 (默认)
        - extra 参数优先级高于 options

        https://cloud.tencent.com/document/api/1552/86336
        """
        domain = join_domain(subdomain, main_domain)

        # 获取域名类型：extra 优先，然后是 options，默认为 "acceleration"
        domain_type = str(extra.get("teoDomainType", self.options.get("teoDomainType", "acceleration"))).lower()

        # 根据域名类型选择API
        if domain_type == "dns":
            # 查询 DNS 记录
            filters = [{"Name": "name", "Values": [domain], "Fuzzy": False}]  # type: Any
            response = self._request("DescribeDnsRecords", ZoneId=zone_id, Filters=filters)

            if response and "DnsRecords" in response:
                for record_info in response.get("DnsRecords", []):
                    if record_info.get("Name") == domain and record_info.get("Type") == record_type:
                        self.logger.debug("Found DNS record: %s", record_info)
                        return record_info

            self.logger.warning("No DNS record found for: %s, response: %s", domain, response)
            return None
        else:
            # 查询加速域名 (默认行为)
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
        """
        创建域名记录
        支持通过 extra 参数或 options 配置 teoDomainType 控制创建类型:
        - teoDomainType="dns": 创建 DNS 记录 (非加速域名)
        - teoDomainType="acceleration" 或未设置: 创建加速域名 (默认)
        - extra 参数优先级高于 options

        https://cloud.tencent.com/document/api/1552/86338
        """
        domain = join_domain(subdomain, main_domain)

        # 获取域名类型：extra 优先，然后是 options，默认为 "acceleration"
        domain_type = str(extra.get("teoDomainType", self.options.get("teoDomainType", "acceleration"))).lower()

        # Filter out teoDomainType from extra parameters before passing to API
        api_extra = {k: v for k, v in extra.items() if k != "teoDomainType"}

        # 根据域名类型选择API
        if domain_type == "dns":
            # 创建 DNS 记录
            res = self._request(
                "CreateDnsRecord", ZoneId=zone_id, Name=domain, Type=record_type, Content=value, **api_extra
            )
            if res:
                self.logger.info("DNS record created (%s)", res.get("RequestId"))
                return True

            self.logger.error("Failed to create DNS record, response: %s", res)
            return False
        else:
            # 创建加速域名 (默认行为)
            origin = {"OriginType": "IP_DOMAIN", "Origin": value}  # type: Any
            res = self._request(
                "CreateAccelerationDomain", ZoneId=zone_id, DomainName=domain, OriginInfo=origin, **api_extra
            )
            if res:
                self.logger.info("Acceleration domain created (%s)", res.get("RequestId"))
                return True

            self.logger.error("Failed to create acceleration domain, response: %s", res)
            return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """
        更新域名记录
        支持通过 extra 参数或 options 配置 teoDomainType 控制更新类型:
        - teoDomainType="dns": 更新 DNS 记录 (非加速域名)
        - teoDomainType="acceleration" 或未设置: 更新加速域名 (默认)
        - extra 参数优先级高于 options

        https://cloud.tencent.com/document/api/1552/86335
        """
        # 获取域名类型：extra 优先，然后是 options，默认为 "acceleration"
        domain_type = str(extra.get("teoDomainType", self.options.get("teoDomainType", "acceleration"))).lower()

        # Filter out teoDomainType from extra parameters before passing to API
        api_extra = {k: v for k, v in extra.items() if k != "teoDomainType"}

        # 根据域名类型选择API
        if domain_type == "dns":
            # 更新 DNS 记录
            new_record = {
                "RecordId": old_record.get("RecordId"),
                "Name": old_record.get("Name"),
                "Type": record_type,
                "Content": value,
            }
            response = self._request("ModifyDnsRecords", ZoneId=zone_id, DnsRecords=[new_record], **api_extra)

            if response:
                self.logger.info("DNS record updated (%s)", response.get("RequestId"))
                return True
            self.logger.error("Failed to update DNS record, response: %s", response)
            return False
        else:
            # 更新加速域名 (默认行为)
            domain = old_record.get("DomainName")
            backup = old_record.get("OriginDetail", {}).get("BackupOrigin", "")
            origin = {"OriginType": "IP_DOMAIN", "Origin": value, "BackupOrigin": backup}  # type: Any
            response = self._request(
                "ModifyAccelerationDomain", ZoneId=zone_id, DomainName=domain, OriginInfo=origin, **api_extra
            )

            if response:
                self.logger.info("Acceleration domain updated (%s)", response.get("RequestId"))
                return True
            self.logger.error("Failed to update acceleration domain origin, response: %s", response)
            return False
