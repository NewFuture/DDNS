# -*- coding:utf-8 -*-
"""
Configuration loader for DDNS.

This module handles loading configuration from command-line arguments,
JSON configuration files, and environment variables.
"""

import os
import sys

from .cli import load_config as load_cli_config
from .file import load_config as load_file_config, save_config as save_json
from .env import load_config as load_env_config
from .config import Config


def load_config(description, version, date):
    # type: (str, str, str) -> Config
    """
    Load and merge configuration from CLI, JSON, and environment variables.

    This function loads configuration from all three sources and returns a
    Config object that provides easy access to merged configuration values.

    Priority order:
    1. Command-line arguments (highest priority)
    2. JSON configuration file (medium priority)
    3. Environment variables (lowest priority)

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
    # Handle --new-config flag before loading other configs
    new_config = cli_config.get("new_config")
    if new_config:
        config = Config(cli_config=cli_config).dict()
        config["id"] = cli_config.get("id", "YOUR ID or EMAIL for DNS Provider")
        config["token"] = cli_config.get("token", "YOUR TOKEN or KEY for DNS Provider")
        if not config["ipv4"] or len(config["ipv4"]) == 0:
            config["ipv4"] = ["ddns.newfuture.cc"]
        if not config["index4"] or len(config["index4"]) == 0:
            config["index4"] = ["default"]
        config_path = isinstance(new_config, str) and new_config or "config.json"
        if save_json(config_path, config):
            sys.stdout.write("%s is generated.\n" % config_path)
        sys.exit(0)
    env_config = load_env_config()

    # Determine and load JSON configuration
    config_path = cli_config.get("config", env_config.get("config"))
    if not config_path:
        # Find config file in default locations
        for p in ["config.json", os.path.expanduser("~/.ddns/config.json"), "/etc/ddns/config.json"]:
            if os.path.exists(p):
                config_path = p
                break
    if config_path and os.path.exists(config_path):
        json_config = load_file_config(config_path)
    else:
        json_config = {}

    # Create and return Config object with all configurations
    conf = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)

    return conf


__all__ = [
    "load_config",
    "Config",
]
