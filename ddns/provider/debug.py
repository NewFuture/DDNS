# coding=utf-8
"""
DebugProvider
仅打印出 IP 地址，不进行任何实际 DNS 更新
"""

from ._base import BaseProvider


class DebugProvider(BaseProvider):

    def _validate(self):
        """
        无需任何验证
        """
        pass

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        self.logger.debug("DebugProvider: %s(%s) => %s", domain, record_type, value)
        ip_type = "IPv4" if record_type == "A" else "IPv6" if record_type == "AAAA" else ""
        print("[{}] {}".format(ip_type, value))
        return True

    def _query_zone_id(self, domain):
        return domain

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line=None, extra=None):
        pass

    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra=None):
        return self.set_record(self._join_domain(sub_domain, main_domain), value, record_type)

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra=None):
        return self.set_record(zone_id, value, record_type)
