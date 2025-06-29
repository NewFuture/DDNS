# coding=utf-8
from ._base import SimpleProvider  # noqa: F401
from .alidns import AlidnsProvider
from .callback import CallbackProvider
from .cloudflare import CloudflareProvider
from .dnscom import DnscomProvider
from .dnspod import DnspodProvider
from .dnspod_com import DnspodComProvider
from .he import HeProvider
from .huaweidns import HuaweiDNSProvider
from .tencentcloud import TencentCloudProvider
from .debug import DebugProvider


def get_provider_class(provider_name):
    # type: (str) -> type[SimpleProvider]
    """
    获取指定的DNS提供商类

    :param provider_name: 提供商名称
    :return: 对应的DNS提供商类
    """
    provider_name = str(provider_name).lower()
    mapping = {
        # dnspod.cn
        "dnspod": DnspodProvider,
        "dnspod_cn": DnspodProvider,  # 兼容旧的dnspod_cn
        # dnspod.com
        "dnspod_com": DnspodComProvider,
        "dnspod_global": DnspodComProvider,  # 兼容旧的dnspod_global
        # tencent cloud dnspod
        "tencentcloud": TencentCloudProvider,
        "tencent": TencentCloudProvider,  # 兼容tencent
        "qcloud": TencentCloudProvider,  # 兼容qcloud
        # cloudflare
        "cloudflare": CloudflareProvider,
        # aliyun alidns
        "alidns": AlidnsProvider,
        "aliyun": AlidnsProvider,  # 兼容aliyun
        # dns.com
        "dnscom": DnscomProvider,
        "51dns": DnscomProvider,  # 兼容旧的51dns
        "dns_com": DnscomProvider,  # 兼容旧的dns_com
        # he.net
        "he": HeProvider,
        "he_net": HeProvider,  # 兼容he.net
        # huawei
        "huaweidns": HuaweiDNSProvider,
        "huawei": HuaweiDNSProvider,  # 兼容huawei
        "huaweicloud": HuaweiDNSProvider,
        # callback
        "callback": CallbackProvider,
        "webhook": CallbackProvider,  # 兼容
        "http": CallbackProvider,  # 兼容
        # debug
        "print": DebugProvider,
        "debug": DebugProvider,  # 兼容print
    }
    return mapping.get(provider_name)  # type: ignore[return-value]
