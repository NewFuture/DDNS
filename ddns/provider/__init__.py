# coding=utf-8

from ._base import BaseProvider
from .dnspod import DnspodProvider

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
