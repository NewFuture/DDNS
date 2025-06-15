# coding=utf-8

"""
BaseDNSProvider 抽象基类
Abstract base class for all DNS provider APIs.

本模块定义了所有DNS服务商API类应继承的抽象基类，统一接口规范，便于后续扩展和多服务商适配。
This module defines the abstract base class that all DNS provider API classes should inherit from,
ensuring a unified interface for easy extension and adaptation to multiple providers.

"""
from abc import ABC, abstractmethod

__author__ = 'New Future'
__all__ = ["BaseDNSProvider"]


class BaseDNSProvider(ABC):
    """
    所有DNS服务商API的抽象基类
    Abstract base class for all DNS provider APIs.

    子类需实现以下方法以适配不同DNS服务商的API。
    Subclasses must implement the following methods to adapt to different DNS provider APIs.
    """

    def __init__(self, config):
        """
        初始化，传入配置参数（如API密钥、域名等）
        Initialize with configuration parameters (e.g., API keys, domain info).
        :param config: dict类型，包含API认证信息、域名等
                       dict, contains API credentials, domain, etc.
        """
        self.config = config

    @abstractmethod
    def get_domain_info(self, domain):
        """
        获取域名信息（如主域名、zone_id等）
        Get domain information (e.g., main domain, zone_id, etc.)
        :param domain: 需要操作的完整域名
                       The full domain name to operate on.
        :return: 域名相关信息（如主域名、zone_id等），具体结构由子类定义
                 Domain info (such as main domain, zone_id, etc.), defined by subclass.
        """

    @abstractmethod
    def get_records(self, domain, record_type=None):
        """
        查询DNS记录
        Query DNS records.
        :param domain: 域名
                       Domain name.
        :param record_type: 记录类型（如A、AAAA等），可选
                           Record type (e.g., A, AAAA), optional.
        :return: 记录列表，结构由子类定义
                 List of records, structure defined by subclass.
        """

    @abstractmethod
    def update_record(self, domain, value, record_type="A"):
        """
        更新DNS记录（如IP变更）
        Update DNS record (e.g., IP change).
        :param domain: 域名
                       Domain name.
        :param value: 新的记录值（如新的IP地址）
                      New record value (e.g., IP address).
        :param record_type: 记录类型，默认"A"
                           Record type, default is "A".
        :return: 操作结果，结构由子类定义
                 Operation result, structure defined by subclass.
        """
