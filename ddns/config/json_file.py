# -*- coding:utf-8 -*-
from json import load as loadjson, dump as dumpjson
import logging


def load_config(config_path):
    # type: (str) -> dict
    """
    加载配置文件并返回配置字典。

    Args:
        config_path (str): 配置文件路径

    Returns:
        dict: 配置字典

    Raises:
        Exception: 当配置文件加载失败时抛出异常
    """
    try:
        with open(config_path, "r") as configfile:
            config = loadjson(configfile)
            # flatten the config if it contains nested structures
            # Create a copy of items to avoid "dictionary changed size during iteration" error
            items_to_process = list(config.items())
            for key, value in items_to_process:
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        config["{}_{}".format(key, subkey)] = subvalue
            return config
    except Exception as e:
        logging.exception("Failed to load config file `%s`: %s", config_path, e)
        raise


def save_config(config_path, config):
    # type: (str, dict) -> bool
    """
    保存配置到文件。

    Args:
        config_path (str): 配置文件路径
        config (dict | None): 配置字典，如果为None则使用默认配置

    Returns:
        bool: 保存成功返回True，失败返回False
    """
    try:
        with open(config_path, "w") as f:
            dumpjson(config, f, indent=2)
            return True
    except IOError:
        logging.critical("Cannot open config file to write: `%s`!", config_path)
        return False
    except Exception as e:
        logging.exception("Failed to write config file `%s`: %s", config_path, e)
        return False
