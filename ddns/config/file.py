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
    content = ""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        stderr.write("Failed to load config file `%s`: %s\n" % (config_path, e))
        raise
    # 移除注释后尝试JSON解析
    try:
        # 移除单行注释（# 和 // 风格）
        content_without_comments = remove_comment(content)
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
                "Both JSON and AST parsing failed for %s.\nJSON: %s\nAST: %s\n" % (config_path, json_error, ast_error)
            )
            raise ast_error
    except Exception as e:
        stderr.write("Failed to load config file `%s`: %s\n" % (config_path, e))
        raise
    
    # 处理配置格式：数组、对象包含configs数组、或单个对象
    if isinstance(config, list):
        # 处理数组格式，展平每个配置项（保持向后兼容）
        result = []
        for config_item in config:
            flat_config = {}
            for k, v in config_item.items():
                if isinstance(v, dict):
                    for subk, subv in v.items():
                        flat_config["{}_{}".format(k, subk)] = subv
                else:
                    flat_config[k] = v
            result.append(flat_config)
        return result
    elif isinstance(config, dict) and "configs" in config and isinstance(config["configs"], list):
        # 处理对象包含configs数组的格式（推荐格式）
        result = []
        for config_item in config["configs"]:
            flat_config = {}
            for k, v in config_item.items():
                if isinstance(v, dict):
                    for subk, subv in v.items():
                        flat_config["{}_{}".format(k, subk)] = subv
                else:
                    flat_config[k] = v
            result.append(flat_config)
        return result
    else:
        # 处理单个对象格式，展平嵌套结构（保持原有逻辑）
        flat_config = {}
        for k, v in config.items():
            if isinstance(v, dict):
                for subk, subv in v.items():
                    flat_config["{}_{}".format(k, subk)] = subv
            else:
                flat_config[k] = v
        return flat_config


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
        "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
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
        with open(config_path, "w", encoding="utf-8") as f:
            content = json_encode(config, indent=2, ensure_ascii=False)
            # Python 2 兼容性：检查是否需要解码
            if hasattr(content, "decode"):
                content = content.decode("utf-8")  # type: ignore
            f.write(content)
            return True
    except Exception:
        stderr.write("Cannot open config file to write: `%s`!\n" % config_path)
        raise
