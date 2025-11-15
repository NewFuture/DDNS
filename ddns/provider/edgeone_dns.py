# coding=utf-8
"""
Tencent Cloud EdgeOne DNS API
腾讯云 EdgeOne (边缘安全速平台) DNS API - 非加速域名管理
API Documentation: https://cloud.tencent.com/document/api/1552/80731
@author: NewFuture
"""

from .edgeone import EdgeOneProvider


class EdgeOneDnsProvider(EdgeOneProvider):
    """
    腾讯云 EdgeOne DNS API 提供商 - 用于管理非加速域名
    Tencent Cloud EdgeOne DNS API Provider - For managing non-accelerated DNS records
    """

    def _prepare_extra(self, extra):
        # type: (dict) -> dict
        """
        准备 extra 参数，设置 teoDomainType 为 "dns"
        Prepare extra parameter with teoDomainType set to "dns"
        """
        extra = extra.copy() if extra else {}
        extra["teoDomainType"] = "dns"
        return extra

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """查询 DNS 记录 https://cloud.tencent.com/document/api/1552/86336"""
        return super(EdgeOneDnsProvider, self)._query_record(
            zone_id, subdomain, main_domain, record_type, line, self._prepare_extra(extra)
        )

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int, str | None, dict) -> bool
        """创建新的 DNS 记录 https://cloud.tencent.com/document/api/1552/86338"""
        return super(EdgeOneDnsProvider, self)._create_record(
            zone_id, subdomain, main_domain, value, record_type, ttl, line, self._prepare_extra(extra)
        )

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """更新 DNS 记录 https://cloud.tencent.com/document/api/1552/86335"""
        return super(EdgeOneDnsProvider, self)._update_record(
            zone_id, old_record, value, record_type, ttl, line, self._prepare_extra(extra)
        )
