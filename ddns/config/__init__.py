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


def _get_config_path(config_path):
    # type: (str|None) -> str | None
    if not config_path:
        # Find config file in default locations
        for p in [
            "config.json",
            os.path.expanduser("~/.ddns/config.json"),
            os.path.expanduser("~/.ddns.json"),
            "/etc/ddns/config.json",
            "/etc/ddns.json",
        ]:
            if os.path.exists(p):
                return p
    elif not os.path.exists(config_path):
        sys.stderr.write("Config file `%s` does not exist!\n" % config_path)
        sys.stdout.write("Please check the path or use `--new-config` to create new one.\n")
        sys.exit(1)
    return config_path


def load_config(description, version, date):
    # type: (str, str, str) -> Config
    """
    Load and merge configuration from CLI, JSON, and environment variables.

    This function loads configuration from all three sources and returns a
    Config object that provides easy access to merged configuration values.

    Args:
        description (str): The program description for the CLI parser.
        doc (str): The program documentation (epilog) for the CLI parser.
        version (str): The program version for the CLI parser.
        date (str): The program release date for the CLI parser.

    Returns:
        Config: A Config object with merged configuration from all sources.
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

    config_path = _get_config_path(cli_config.get("config", env_config.get("config")))
    json_config = load_file_config(config_path) if config_path else {}

    # Create and return Config object with all configurations
    conf = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)

    log_format = conf.log_format  # type: str  # type: ignore
    if log_format:
        # A custom log format is already set; no further action is required.
        pass
    elif conf.log_level < logging.INFO:
        # Override log format in debug mode to include filename and line number for detailed debugging
        log_format = "%(asctime)s %(levelname)s [%(name)s.%(funcName)s](%(filename)s:%(lineno)d): %(message)s"
    elif conf.log_level > logging.INFO:
        log_format = "%(asctime)s %(levelname)s: %(message)s"
    else:
        log_format = "%(asctime)s %(levelname)s [%(name)s]: %(message)s"
    logging.basicConfig(level=conf.log_level, format=log_format, datefmt=conf.log_datefmt, filename=conf.log_file)
    logger = logging.getLogger().getChild("config")  # type: logging.Logger

    if len(cli_config) <= 1 and len(json_config) == 0 and len(env_config) == 0:
        # No configuration provided, use CLI and environment variables only
        logger.warning("[deprecated] auto gernerate config file will be deprecated in future versions.")
        logger.warning("usage:\n  `ddns --new-config` to generate a new config.\n  `ddns -h` for help.")
        save_config(config_path or "config.json", cli_config)
        logger.info("No config file found, generated default config at `%s`.", config_path or "config.json")
        sys.exit(1)

    # logger 初始化之后再开始记log
    if config_path:
        logger.info("load config: %s", config_path)
    else:
        logger.debug("No config file specified, using CLI and environment variables only.")

    if not conf.dns:
        if cli_config.get("debug"):
            conf.dns = "debug"
        else:
            logger.critical("No DNS provider specified! Please set `dns` in config or use `--dns` CLI option.")
            sys.exit(2)

    return conf


__all__ = [
    "load_config",
    "Config",
]
