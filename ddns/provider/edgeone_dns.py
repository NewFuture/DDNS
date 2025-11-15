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

    def __init__(self, id, token, logger=None, ssl="auto", proxy=None, endpoint=None, **options):
        # type: (str, str, object, bool|str, list[str]|None, str|None, **object) -> None
        """
        初始化 EdgeOne DNS 提供商，自动设置 teoDomainType 为 "dns"

        Initialize EdgeOne DNS provider with teoDomainType set to "dns"
        """
        # 设置域名类型为 DNS 记录
        options["teoDomainType"] = "dns"
        super(EdgeOneDnsProvider, self).__init__(id, token, logger, ssl, proxy, endpoint, **options)
