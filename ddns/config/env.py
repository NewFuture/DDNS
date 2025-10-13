# -*- coding:utf-8 -*-
"""
Configuration loader for DDNS environment variables.
@author: NewFuture
"""

from ast import literal_eval
from os import environ
from sys import stderr

__all__ = ["load_config"]


def _try_parse_array(value, key=None):
    # type: (str, str|None) -> Any
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
            stderr.write("Failed to parse JSON array from value: {}={}\n".format(key, value))
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
    4. 自动检测标准 Python 环境变量：
       - SSL 验证：PYTHONHTTPSVERIFY
    5. 支持 extra 字段：DDNS_EXTRA_XXX 会被转换为 extra_xxx
    6. 其他所有值保持原始字符串格式，去除前后空格

    Args:
        prefix (str): 环境变量前缀，默认为 "DDNS_"

    Returns:
        dict: 从环境变量解析的配置字典
    """
    env_vars = {}  # type: dict[str, str | list]

    # 标准环境变量映射
    alias_mappings = {"pythonhttpsverify": "ssl"}

    for key, value in environ.items():
        lower_key = key.lower()
        config_key = None

        if lower_key in alias_mappings:
            config_key = alias_mappings[lower_key]
            if config_key in env_vars:
                continue  # DDNS变量优先级更高
        elif lower_key.startswith(prefix.lower()):
            config_key = lower_key[len(prefix) :].replace(".", "_")  # noqa: E203

        if config_key:
            env_vars[config_key] = _try_parse_array(value, key=key)

    return env_vars
