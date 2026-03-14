# coding=utf-8
"""
AliESA API
阿里云边缘安全加速(ESA) DNS 解析操作库
@author: NewFuture, GitHub Copilot
"""

from time import strftime
import ipaddress

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
            # AliESA 只有 A/AAAA 记录类型表示 有不确定数量的IPv4 和 不确定数量的IPv6
            Type='A/AAAA',
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
    
    def extract_unique_ip_addresses(self,input_string):
        """
        从逗号分隔的字符串中提取第一个有效的 IPv4 地址和第一个有效的 IPv6 地址。

        :param input_string: 包含潜在 IP 地址的字符串
        :return: 一个元组 (first_ipv4, first_ipv6)，如果未找到则对应位置为空字符串
        """
        # 默认为空字符串方便拼接
        first_ipv4 = ""
        first_ipv6 = ""
        
        # 1. 按逗号分割字符串，并去除每个部分前后的空白字符
        candidates = [part.strip() for part in input_string.split(',')]
        
        # 2. 遍历候选列表
        for candidate in candidates:
            # 跳过空字符串
            if not candidate:
                continue
                
            # 3. 尝试将候选者解析为 IP 地址
            try:
                ip_obj = ipaddress.ip_address(candidate)
                
                # 4. 判断 IP 地址类型，并记录第一个出现的地址
                if isinstance(ip_obj, ipaddress.IPv4Address) and first_ipv4 == "":
                    first_ipv4 = str(ip_obj)
                elif isinstance(ip_obj, ipaddress.IPv6Address) and first_ipv6 == "":
                    first_ipv6 = str(ip_obj)
                    
                # 5. 如果两个地址都找到了，可以提前退出循环以提高效率
                if first_ipv4  and first_ipv6 :
                    break
                    
            except ValueError:
                # 如果解析失败，说明不是有效的 IP 地址，继续检查下一个
                continue
        
        # 6. 返回结果元组
        return first_ipv4, first_ipv6
    
    def record_final(self, old_record , new_record):
        # type: (str, str) -> str
        """
        获取最终结果 只保留一个ipv4和一个ipv6
        """
        ipv4old, ipv6old = self.extract_unique_ip_addresses(old_record)
        ipv4new, ipv6new = self.extract_unique_ip_addresses(new_record)
        ipv4final,ipv6final = self.extract_unique_ip_addresses(ipv4new+","+ipv6new+","+ipv4old+","+ipv6old)
        
        final =  ipv4final+","+ipv6final
        # // 去除可能的开头的逗号
        return final.lstrip(',')

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """
        更新DNS记录
        https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-updaterecord
        """
        # EAS只有A/AAAA记录并且可能包含多个ip,如果当前域名只配置ipV4或ipV6类型, 则只更新对应部分,然后另一种记录不变
        # ESA可以配置多个Ip作为回源ip, 所以要提取第一个ipv4地址和ipv6地址(DDNS场景下不可能有多个ip)
        # 获取最终结果 只保留一个ipv4和一个ipv6
        final_value = self.record_final(old_record.get("Data", {}).get("Value"), value)
        
        # 检查是否需要更新
        if (
            old_record.get("Data", {}).get("Value") == final_value
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
            Data={"Value": final_value},
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
