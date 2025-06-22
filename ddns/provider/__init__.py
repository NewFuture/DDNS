# coding=utf-8
# flake8: noqa: F401
from ._base import BaseProvider
from .dnspod import DnspodProvider
from .dnspod_com import DnspodComProvider
from .cloudflare import CloudflareProvider
from .alidns import AlidnsProvider
from .dnscom import DnscomProvider
from .huaweidns import HuaweiDNSProvider


def get_provider_class(provider_name):
    # type: (str) -> type[BaseProvider]
    """
    获取指定的DNS提供商类

    :param provider_name: 提供商名称
    :return: 对应的DNS提供商类
    """
    provider_name = str(provider_name).lower()
    mapping = {
        "dnspod": DnspodProvider,
        "dnspod_cn": DnspodComProvider,  # 兼容旧的dnspod_cn
        "dnspod_com": DnspodComProvider,
        "dnspod_global": DnspodComProvider,  # 兼容旧的dnspod_global
        "cloudflare": CloudflareProvider,
        "alidns": AlidnsProvider,
        "aliyun": AlidnsProvider,  # 兼容aliyun
        "ali": AlidnsProvider,  # 兼容ali
        "dnscom": DnscomProvider,
        "51dns": DnscomProvider,  # 兼容旧的51dns
        "dns_com": DnscomProvider,  # 兼容旧的dns_com
        "huaweidns": HuaweiDNSProvider,  # 兼容huawei
        "huawei": HuaweiDNSProvider,  # 兼容旧的huawei
        "huaweicloud": HuaweiDNSProvider,
    }
    return mapping.get(provider_name)  # type: ignore[return-value]
