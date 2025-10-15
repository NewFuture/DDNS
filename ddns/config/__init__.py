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
from .config import Config, split_array_string


def _get_config_paths(config_paths):
    # type: (list[str] | None) -> list[str]
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

    # 验证所有路径都存在（跳过URL检查）
    for config_path in config_paths:
        # 跳过远程URL的存在性检查
        if "://" not in config_path and not os.path.exists(config_path):
            sys.stderr.write("Config file `%s` does not exist!\n" % config_path)
            sys.stdout.write("Please check the path or use `--new-config` to create new one.\n")
            sys.exit(1)

    return config_paths


def _setup_logging(cli_config, env_config, all_json_configs):
    # type: (dict, dict, list[dict]) -> logging.Logger
    """Setup logging configuration and return logger."""
    # Use first config for global log settings (log config is inherited from global in v4.1 format)
    json_config = all_json_configs[0] if all_json_configs else {}
    global_conf = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)
    log_format = global_conf.log_format  # type: str  # type: ignore
    if log_format:
        # A custom log format is already set; no further action is required.
        pass
    elif global_conf.log_level < logging.INFO:
        # Override log format in debug mode to include filename and line number for detailed debugging
        log_format = "%(asctime)s %(levelname)s [%(name)s.%(funcName)s](%(filename)s:%(lineno)d): %(message)s"
    elif global_conf.log_level > logging.INFO:
        log_format = "%(asctime)s %(levelname)s: %(message)s"
    else:
        log_format = "%(asctime)s %(levelname)s [%(name)s]: %(message)s"
    logging.basicConfig(
        level=global_conf.log_level, format=log_format, datefmt=global_conf.log_datefmt, filename=global_conf.log_file
    )
    return logging.getLogger().getChild("config")  # type: logging.Logger


def _load_json_configs(config_paths, proxy, ssl):
    # type: (list[str], list[str], str) -> list[dict]
    """Load all JSON configurations from config paths."""
    all_json_configs = []
    for config_path in config_paths:
        json_configs = load_file_config(config_path, proxy=proxy, ssl=ssl)
        if isinstance(json_configs, list):
            all_json_configs.extend(json_configs)
        else:
            all_json_configs.append(json_configs)

    # 如果没有找到任何配置文件或JSON配置，创建一个空配置
    return all_json_configs or [{}]


def _validate_configs(configs, logger):
    # type: (list[Config], logging.Logger) -> None
    """Validate that all configs have DNS providers."""
    for i, conf in enumerate(configs):
        if not conf.dns:
            logger.critical(
                "No DNS provider specified in config %d! Please set `dns` in config or use `--dns` CLI option.", i + 1
            )
            sys.exit(2)


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
""".format(version=version, date=date)
    # Load CLI configuration first
    cli_config = load_cli_config(description, doc, version, date)
    env_config = load_env_config()

    # 获取配置文件路径列表
    config_paths = split_array_string(cli_config.get("config", env_config.get("config", [])))
    config_paths = _get_config_paths(config_paths)

    # 提取代理和SSL设置用于HTTP请求
    proxy_settings = split_array_string(cli_config.get("proxy", env_config.get("proxy", [])))  # type: list[str]
    ssl_settings = cli_config.get("ssl", env_config.get("ssl", "auto"))

    # 加载所有配置文件
    all_json_configs = _load_json_configs(config_paths, proxy_settings, ssl_settings)

    # 为每个JSON配置创建Config对象
    configs = [
        Config(cli_config=cli_config, json_config=json_config, env_config=env_config)
        for json_config in all_json_configs
    ]

    # 设置日志
    logger = _setup_logging(cli_config, env_config, all_json_configs)

    # 处理无配置情况 - inline _handle_no_config logic
    if len(cli_config) <= 1 and len(all_json_configs) == 1 and not all_json_configs[0] and not env_config:
        # 没有配置时生成默认配置文件
        logger.warning("[deprecated] auto gernerate config file will be deprecated in future versions.")
        logger.warning("usage:\n  `ddns --new-config` to generate a new config.\n  `ddns -h` for help.")
        default_config_path = config_paths[0] if config_paths else "config.json"
        save_config(default_config_path, cli_config)
        logger.info("No config file found, generated default config at `%s`.", default_config_path)
        sys.exit(1)

    # 记录配置加载情况
    if config_paths:
        logger.info("load config: %s", config_paths)
    else:
        logger.debug("No config file specified, using CLI and environment variables only.")

    # 仅在没有配置文件且开启debug时自动设置debug provider
    if not config_paths and cli_config.get("debug") and len(configs) == 1 and not configs[0].dns:
        configs[0].dns = "debug"

    # 验证每个配置都有DNS provider
    _validate_configs(configs, logger)

    return configs


__all__ = ["load_configs", "Config"]
