# coding=utf-8
"""
DNSPOD Global (国际版) API
http://www.dnspod.com/docs/domains.html
@author: NewFuture
"""

from .dnspod import DnspodProvider  # noqa: F401


class DnspodComProvider(DnspodProvider):
    """
    DNSPOD.com Provider (国际版)
    This class extends the DnspodProvider to use the global DNSPOD API.
    """

    endpoint = "https://api.dnspod.com"
    DefaultLine = "default"
