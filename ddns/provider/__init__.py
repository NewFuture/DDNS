# coding=utf-8
# flake8: noqa: F401
from ._base import BaseProvider
from .dnspod import DnspodProvider
from .dnspod_com import DnspodComProvider
from .cloudflare import CloudflareProvider
from .alidns import AlidnsProvider
from .dnscom import DnscomProvider


def get_provider_class(provider_name):
    # type: (str) -> type[BaseProvider]
    """
    获取指定的DNS提供商类

    :param provider_name: 提供商名称
    :return: 对应的DNS提供商类
    """
    provider_name = str(provider_name).lower()
    provider_class_name = "{}Provider".format(provider_name.capitalize())
    return globals()[provider_class_name]  # type: type[BaseProvider]
