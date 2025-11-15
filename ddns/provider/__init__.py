# coding=utf-8
from ._base import SimpleProvider
from .alidns import AlidnsProvider
from .aliesa import AliesaProvider
from .callback import CallbackProvider
from .cloudflare import CloudflareProvider
from .debug import DebugProvider
from .dnscom import DnscomProvider
from .dnspod import DnspodProvider
from .dnspod_com import DnspodComProvider
from .edgeone import EdgeOneProvider
from .edgeone_dns import EdgeOneDnsProvider
from .he import HeProvider
from .huaweidns import HuaweiDNSProvider
from .namesilo import NamesiloProvider
from .noip import NoipProvider
from .tencentcloud import TencentCloudProvider

__all__ = ["SimpleProvider", "get_provider_class"]


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
        # tencent cloud edgeone (accelerated domains)
        "edgeone": EdgeOneProvider,
        "edgeone_acc": EdgeOneProvider,  # 加速域名
        "teo_acc": EdgeOneProvider,  # 加速域名别名
        "teo": EdgeOneProvider,  # 兼容旧版本 (不在文档中提示)
        # tencent cloud edgeone dns (non-accelerated domains)
        "edgeone_dns": EdgeOneDnsProvider,  # DNS记录管理
        "teo_dns": EdgeOneDnsProvider,  # DNS记录管理别名
        "edgeone_noacc": EdgeOneDnsProvider,  # 非加速域名
        # cloudflare
        "cloudflare": CloudflareProvider,
        # aliyun alidns
        "alidns": AlidnsProvider,
        "aliyun": AlidnsProvider,  # 兼容aliyun
        # aliyun esa
        "aliesa": AliesaProvider,
        "esa": AliesaProvider,  # 兼容esa
        # dns.com
        "dnscom": DnscomProvider,
        "51dns": DnscomProvider,  # 兼容51dns
        "dns_com": DnscomProvider,  # 兼容dns_com
        # he.net
        "he": HeProvider,
        "he_net": HeProvider,  # 兼容he.net
        # huawei
        "huaweidns": HuaweiDNSProvider,
        "huawei": HuaweiDNSProvider,  # 兼容huawei
        "huaweicloud": HuaweiDNSProvider,
        # namesilo
        "namesilo": NamesiloProvider,
        "namesilo_com": NamesiloProvider,  # 兼容namesilo.com
        # no-ip
        "noip": NoipProvider,
        "no-ip": NoipProvider,  # 兼容no-ip
        "noip_com": NoipProvider,  # 兼容noip.com
        # callback
        "callback": CallbackProvider,
        "webhook": CallbackProvider,  # 兼容
        "http": CallbackProvider,  # 兼容
        # debug
        "print": DebugProvider,
        "debug": DebugProvider,  # 兼容print
    }
    return mapping.get(provider_name)  # type: ignore[return-value]
