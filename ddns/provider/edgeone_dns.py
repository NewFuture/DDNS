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

    # 默认域名类型为 DNS 记录
    _default_domain_type = "dns"

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """查询 DNS 记录 https://cloud.tencent.com/document/api/1552/86336"""
        extra = extra.copy() if extra else {}
        extra.setdefault("teoDomainType", self._default_domain_type)
        return super(EdgeOneDnsProvider, self)._query_record(zone_id, subdomain, main_domain, record_type, line, extra)

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int, str | None, dict) -> bool
        """创建新的 DNS 记录 https://cloud.tencent.com/document/api/1552/86338"""
        extra = extra.copy() if extra else {}
        extra.setdefault("teoDomainType", self._default_domain_type)
        return super(EdgeOneDnsProvider, self)._create_record(
            zone_id, subdomain, main_domain, value, record_type, ttl, line, extra
        )

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """更新 DNS 记录 https://cloud.tencent.com/document/api/1552/86335"""
        extra = extra.copy() if extra else {}
        extra.setdefault("teoDomainType", self._default_domain_type)
        return super(EdgeOneDnsProvider, self)._update_record(zone_id, old_record, value, record_type, ttl, line, extra)
