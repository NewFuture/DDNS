# -*- coding:utf-8 -*-
from os import environ
from ast import literal_eval
import logging

# from json import loads as json_decode

__all__ = ["load_config"]


def try_parse_array_or_dict(value):
    # type: (str) -> Any
    """解析数组值[], 非数组返回元素字符串（去除前后空格）"""
    if not value:
        return value

    value = value.strip()
    # 尝试解析 JSON
    # if (value.startswith("{'") and value.endswith("'}")) or (value.startswith('{"') and value.endswith('"}')):
    #     try:
    #         return json_decode(value)
    #     except Exception:
    #         logging.warning("Failed to parse JSON from value: %s", value)
    if value.startswith("[") and value.endswith("]"):
        # or (value.startswith("{") and value.endswith("}"))
        try:
            return literal_eval(value)
        except Exception:
            logging.warning("Failed to parse JSON array from value: %s", value)
            pass
    # 返回去除前后空格的字符串
    return value


def load_config(prefix="DDNS_"):
    # type: (str) -> dict
    """
    从环境变量加载配置并返回配置字典。

    支持以下转换：
    1. 对于特定的数组参数（index4, index6, ipv4, ipv6, proxy），转换为数组
    2. 对于 JSON 格式的数组 [item1,item2]，转换为数组
    3. 键名转换：点号转下划线，支持大小写变体
    4. 其他所有值保持原始字符串格式，去除前后空格

    Args:
        prefix (str): 环境变量前缀，默认为 "DDNS_"

    Returns:
        dict: 从环境变量解析的配置字典
    """
    # 收集所有符合前缀的环境变量
    env_vars = {}  # type: dict[str, str | list]
    for key, value in environ.items():
        key_lower = key.lower()
        if key_lower.startswith(prefix.lower()):
            # 移除前缀并转换为小写，点号转下划线
            config_key = key_lower[len(prefix) :].replace(".", "_")  # noqa: E203

            # 对 JSON 数组和对象格式进行转换
            env_vars[config_key] = try_parse_array_or_dict(value)

    return env_vars
