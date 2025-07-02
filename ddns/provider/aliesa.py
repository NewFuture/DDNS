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

    def _split_zone_and_sub(self, domain):
        # type: (str) -> tuple[str | None, str | None, str]
        """
        AliESA 支持手动指定站点ID格式: www.example.com#siteId
        对于其他格式使用BaseProvider的标准逻辑
        """
        # 检查是否有手动指定的站点ID格式（使用#分隔符）
        if '#' in domain:
            parts = domain.split('#')
            domain_part = parts[0]
            site_id = parts[1] if len(parts) > 1 and parts[1] else None
            
            # 如果提供了站点ID，直接使用
            if site_id:
                # 处理 + 分隔符格式
                if '+' in domain_part:
                    subdomain, main_domain = domain_part.split('+', 1)
                else:
                    # 自动提取主域名
                    parts = domain_part.split('.')
                    if len(parts) >= 2:
                        # 返回最后两级域名作为主域名
                        main_domain = '.'.join(parts[-2:])
                    else:
                        main_domain = domain_part
                    
                    if domain_part == main_domain:
                        subdomain = "@"
                    else:
                        if domain_part.endswith("." + main_domain):
                            subdomain = domain_part[:-len("." + main_domain)]
                        else:
                            subdomain = domain_part
                
                self.logger.debug("Manual site ID provided: %s for domain %s", site_id, domain_part)
                return site_id, subdomain, main_domain
            else:
                # 站点ID为空，回退到标准查询，但仍使用解析出的domain_part
                domain = domain_part
        
        # 使用BaseProvider的标准逻辑进行自动查询
        return super(AliBaseProvider, self)._split_zone_and_sub(domain)

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