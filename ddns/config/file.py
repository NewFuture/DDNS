# -*- coding:utf-8 -*-
from json import loads as loadjson, dump as dumpjson
import logging
from ast import literal_eval


def load_config(config_path):
    # type: (str) -> dict
    """
    加载配置文件并返回配置字典。
    优先尝试JSON解析，失败后尝试AST解析。

    Args:
        config_path (str): 配置文件路径

    Returns:
        dict: 配置字典

    Raises:
        Exception: 当配置文件加载失败时抛出异常
    """
    content = ""
    try:
        with open(config_path, "r") as configfile:
            content = configfile.read()
    except Exception as e:
        logging.exception("Failed to load config file `%s`: %s", config_path, e)
        raise
    # 优先尝试JSON解析
    try:
        config = loadjson(content)
        logging.debug("Successfully loaded config file with JSON parser: %s", config_path)
    except (ValueError, SyntaxError) as json_error:
        # JSON解析失败，尝试AST解析
        if config_path.endswith(".json"):
            logging.warning("JSON parsing failed for %s: %s", config_path, json_error)
        else:
            logging.debug("JSON parsing failed, trying AST parser for: %s", config_path)
        try:
            config = literal_eval(content)
            logging.debug("Successfully loaded config file with AST parser: %s", config_path)
        except (ValueError, SyntaxError) as ast_error:
            logging.exception(
                "Both JSON and AST parsing failed for %s. JSON: %s, AST: %s",
                config_path,
                json_error,
                ast_error,
            )
            raise Exception("Failed to parse config file: JSON: {}, AST: {}".format(json_error, ast_error))
    if not isinstance(config, dict):
        logging.error("Config file `%s` does not contain a valid config!", config_path)
        raise Exception("Config file must contain a dictionary, got: {}".format(type(config).__name__))

    # flatten the config if it contains nested structures
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
