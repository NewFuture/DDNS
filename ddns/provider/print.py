# coding=utf-8
"""
PrintProvider
仅打印出 IP 地址，不进行任何实际 DNS 操作。
"""

from ._base import BaseProvider


class PrintProvider(BaseProvider):

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        ip_type = "IPv4" if record_type == "A" else "IPv6" if record_type == "AAAA" else ""
        print("{} -- type: {}({}) domain: {}".format(value, record_type, ip_type, domain))
        return True
