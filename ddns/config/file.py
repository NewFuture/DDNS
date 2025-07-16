# -*- coding:utf-8 -*-
"""
Configuration file loader for DDNS. supports both JSON and AST parsing.
@author: NewFuture
"""
from ast import literal_eval
from io import open
from json import loads as json_decode, dumps as json_encode
from sys import stderr, stdout
from ..util.comment import remove_comment


def _process_multi_providers(config):
    # type: (dict) -> list[dict]
    """Process v4.1 providers format and return list of configs."""
    result = []

    # 提取全局配置（除providers之外的所有配置）
    global_config = _flatten_single_config(config, exclude_keys=["providers"])

    # 检查providers和dns字段不能同时使用
    if global_config.get("dns"):
        stderr.write("Error: 'providers' and 'dns' fields cannot be used simultaneously in config file!\n")
        raise ValueError("providers and dns fields conflict")

    # 为每个provider创建独立配置
    for provider_config in config["providers"]:
        # 验证provider必须有name字段
        if not provider_config.get("name"):
            stderr.write("Error: Each provider must have a 'name' field!\n")
            raise ValueError("provider missing name field")

        flat_config = global_config.copy()  # 从全局配置开始
        provider_flat = _flatten_single_config(provider_config, exclude_keys=["name"])
        flat_config['dns'] = provider_config.get("name")
        flat_config.update(provider_flat)
        result.append(provider_flat)
    return result


def _flatten_single_config(config, exclude_keys=None):
    # type: (dict, list[str]|None) -> dict
    """Flatten a single config object with optional key exclusion."""
    if exclude_keys is None:
        exclude_keys = []
    flat_config = {}
    for k, v in config.items():
        if k in exclude_keys:
            continue
        if isinstance(v, dict):
            for subk, subv in v.items():
                flat_config["{}_{}".format(k, subk)] = subv
        else:
            flat_config[k] = v
    return flat_config


def load_config(config_path):
    # type: (str) -> dict|list[dict]
    """
    加载配置文件并返回配置字典或配置字典数组。
    对于单个对象返回dict，对于数组返回list[dict]。
    优先尝试JSON解析，失败后尝试AST解析。

    Args:
        config_path (str): 配置文件路径

    Returns:
        dict|list[dict]: 配置字典或配置字典数组

    Raises:
        Exception: 当配置文件加载失败时抛出异常
    """
    try:
        with open(config_path, "r") as f:
            content = f.read()

        # 移除注释后尝试JSON解析
        content_without_comments = remove_comment(content)
        try:
            config = json_decode(content_without_comments)
        except (ValueError, SyntaxError) as json_error:
            # JSON解析失败，尝试AST解析
            try:
                config = literal_eval(content)
                stdout.write("Successfully loaded config file with AST parser: %s\n" % config_path)
            except (ValueError, SyntaxError) as ast_error:
                if config_path.endswith(".json"):
                    stderr.write("JSON parsing failed for %s\n" % (config_path))
                    raise json_error

                stderr.write(
                    "Both JSON and AST parsing failed for %s\nJSON Error: %s\nAST Error: %s\n"
                    % (config_path, json_error, ast_error)
                )
                raise ast_error
    except Exception as e:
        stderr.write("Failed to load config file `%s`: %s\n" % (config_path, e))
        raise

    # 处理配置格式：v4.1 providers格式或单个对象
    if "providers" in config and isinstance(config["providers"], list):
        return _process_multi_providers(config)
    else:
        return _flatten_single_config(config)


def save_config(config_path, config):
    # type: (str, dict) -> bool
    """
    保存配置到文件。

    Args:
        config_path (str): 配置文件路径
        config (dict): 配置字典

    Returns:
        bool: 保存成功返回True

    Raises:
        Exception: 保存失败时抛出异常
    """
    # 补全默认配置
    config = {
        "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
        "dns": config.get("dns", "debug"),
        "id": config.get("id", "YOUR ID or EMAIL for DNS Provider"),
        "token": config.get("token", "YOUR TOKEN or KEY for DNS Provider"),
        "ipv4": config.get("ipv4", ["ddns.newfuture.cc"]),
        "index4": config.get("index4", ["default"]),
        "ipv6": config.get("ipv6", []),
        "index6": config.get("index6", []),
        "ttl": config.get("ttl", 600),
        "line": config.get("line", None),
        "proxy": config.get("proxy", []),
        "cache": config.get("cache", True),
        "ssl": config.get("ssl", "auto"),
        "log": {
            "file": config.get("log_file"),
            "level": config.get("log_level", "INFO"),
            "format": config.get("log_format"),
            "datefmt": config.get("log_datefmt"),
        },
    }
    try:
        with open(config_path, "w") as f:
            content = json_encode(config, indent=2, ensure_ascii=False)
            # Python 2 兼容性：检查是否需要解码
            if hasattr(content, "decode"):
                content = content.decode("utf-8")  # type: ignore
            f.write(content)
            return True
    except Exception:
        stderr.write("Cannot open config file to write: `%s`!\n" % config_path)
        raise

