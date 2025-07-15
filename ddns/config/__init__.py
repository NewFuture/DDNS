# -*- coding:utf-8 -*-
"""
Configuration loader for DDNS.

This module handles loading configuration from command-line arguments,
JSON configuration files, and environment variables.

@author: NewFuture
"""
import os
import sys
import logging
from .cli import load_config as load_cli_config
from .file import load_config as load_file_config, save_config
from .env import load_config as load_env_config
from .config import Config


def _get_config_paths(config_paths):
    # type: (list[str] | str | None) -> list[str]
    """
    获取配置文件路径列表，支持多个配置文件
    """
    if not config_paths:
        # Find config file in default locations
        for p in [
            "config.json",
            os.path.expanduser("~/.ddns/config.json"),
            os.path.expanduser("~/.ddns.json"),
            "/etc/ddns/config.json",
            "/etc/ddns.json",
        ]:
            if os.path.exists(p):
                return [p]
        return []
    
    # 处理单个路径或路径列表
    if isinstance(config_paths, str):
        paths = [config_paths]
    else:
        paths = config_paths
    
    # 验证所有路径都存在
    result = []
    for config_path in paths:
        if not os.path.exists(config_path):
            sys.stderr.write("Config file `%s` does not exist!\n" % config_path)
            sys.stdout.write("Please check the path or use `--new-config` to create new one.\n")
            sys.exit(1)
        result.append(config_path)
    
    return result


def load_config(description, version, date):
    # type: (str, str, str) -> Config
    """
    Load and merge configuration from CLI, JSON, and environment variables.
    Returns a single Config object for backward compatibility.

    This function loads configuration from all three sources and returns a
    Config object that provides easy access to merged configuration values.

    Args:
        description (str): The program description for the CLI parser.
        version (str): The program version for the CLI parser.
        date (str): The program release date for the CLI parser.

    Returns:
        Config: A Config object with merged configuration from all sources.
    """
    configs = load_configs(description, version, date)
    return configs[0]  # Return first config for backward compatibility


def load_configs(description, version, date):
    # type: (str, str, str) -> list[Config]
    """
    Load and merge configuration from CLI, JSON, and environment variables.
    Supports multiple config files and array config formats.

    This function loads configuration from all three sources and returns a
    list of Config objects that provides easy access to merged configuration values.

    Args:
        description (str): The program description for the CLI parser.
        version (str): The program version for the CLI parser.
        date (str): The program release date for the CLI parser.

    Returns:
        list[Config]: A list of Config objects with merged configuration from all sources.
    """
    doc = """
ddns [v{version}@{date}]
(i) homepage or docs [文档主页]: https://ddns.newfuture.cc/
(?) issues or bugs [问题和反馈]: https://github.com/NewFuture/DDNS/issues
Copyright (c) NewFuture (MIT License)
""".format(
        version=version, date=date
    )
    # Load CLI configuration first
    cli_config = load_cli_config(description, doc, version, date)
    env_config = load_env_config()

    # 获取配置文件路径列表
    cli_config_paths = cli_config.get("config", [])
    env_config_paths = env_config.get("config", [])
    
    # 合并CLI和环境变量中的配置文件路径
    if cli_config_paths:
        config_paths = cli_config_paths
    elif env_config_paths:
        config_paths = env_config_paths
    else:
        config_paths = []
    
    config_paths = _get_config_paths(config_paths)
    
    # 加载所有配置文件
    all_json_configs = []
    if config_paths:
        for config_path in config_paths:
            json_configs = load_file_config(config_path)
            if isinstance(json_configs, list):
                all_json_configs.extend(json_configs)
            else:
                all_json_configs.append(json_configs)
    
    # 如果没有找到任何配置文件或JSON配置，创建一个空配置
    if not all_json_configs:
        all_json_configs = [{}]

    # 为每个JSON配置创建Config对象
    configs = []
    for json_config in all_json_configs:
        conf = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)
        configs.append(conf)

    # 使用第一个配置来设置日志系统
    first_conf = configs[0]
    log_format = first_conf.log_format  # type: str  # type: ignore
    if log_format:
        # A custom log format is already set; no further action is required.
        pass
    elif first_conf.log_level < logging.INFO:
        # Override log format in debug mode to include filename and line number for detailed debugging
        log_format = "%(asctime)s %(levelname)s [%(name)s.%(funcName)s](%(filename)s:%(lineno)d): %(message)s"
    elif first_conf.log_level > logging.INFO:
        log_format = "%(asctime)s %(levelname)s: %(message)s"
    else:
        log_format = "%(asctime)s %(levelname)s [%(name)s]: %(message)s"
    logging.basicConfig(level=first_conf.log_level, format=log_format, datefmt=first_conf.log_datefmt, filename=first_conf.log_file)
    logger = logging.getLogger().getChild("config")  # type: logging.Logger

    if len(cli_config) <= 1 and len(all_json_configs) == 1 and len(all_json_configs[0]) == 0 and len(env_config) == 0:
        # No configuration provided, use CLI and environment variables only
        logger.warning("[deprecated] auto gernerate config file will be deprecated in future versions.")
        logger.warning("usage:\n  `ddns --new-config` to generate a new config.\n  `ddns -h` for help.")
        default_config_path = config_paths[0] if config_paths else "config.json"
        save_config(default_config_path, cli_config)
        logger.info("No config file found, generated default config at `%s`.", default_config_path)
        sys.exit(1)

    # logger 初始化之后再开始记log
    if config_paths:
        logger.info("load config: %s", config_paths)
    else:
        logger.debug("No config file specified, using CLI and environment variables only.")

    # 验证每个配置都有DNS provider
    for i, conf in enumerate(configs):
        if not conf.dns:
            if cli_config.get("debug"):
                conf.dns = "debug"
            else:
                logger.critical("No DNS provider specified in config %d! Please set `dns` in config or use `--dns` CLI option.", i + 1)
                sys.exit(2)

    return configs


__all__ = [
    "load_config",
    "load_configs",
    "Config",
]
