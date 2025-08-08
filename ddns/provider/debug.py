# coding=utf-8
"""
DebugProvider
仅打印出 IP 地址，不进行任何实际 DNS 更新。
"""

from ._base import SimpleProvider


class DebugProvider(SimpleProvider):
    def _validate(self):
        """无需任何验证"""
        pass

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        self.logger.debug("DebugProvider: %s(%s) => %s", domain, record_type, value)
        ip_type = "IPv4" if record_type == "A" else "IPv6" if record_type == "AAAA" else record_type
        print("[{}] {}".format(ip_type, value))
        return True
