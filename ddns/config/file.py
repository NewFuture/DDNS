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
    try:
        with open(config_path, "r", encoding="utf-8") as configfile:
            content = configfile.read()

            # 优先尝试JSON解析
            try:
                config = loadjson(content)
                logging.debug("Successfully loaded config file with JSON parser: %s", config_path)
            except (ValueError, SyntaxError) as json_error:
                # JSON解析失败，尝试AST解析
                logging.debug("JSON parsing failed, trying AST parser for: %s", config_path)
                try:
                    config = literal_eval(content)
                    if not isinstance(config, dict):
                        raise ValueError("Config content is not a dictionary")
                    logging.debug("Successfully loaded config file with AST parser: %s", config_path)
                except (ValueError, SyntaxError) as ast_error:
                    logging.error(
                        "Both JSON and AST parsing failed for %s. JSON: %s, AST: %s",
                        config_path,
                        json_error,
                        ast_error,
                    )
                    raise Exception("Failed to parse config file: JSON: {}, AST: {}".format(json_error, ast_error))

            # flatten the config if it contains nested structures
            def flatten_dict(d, parent_key="", sep="_"):
                # type: (dict, str, str) -> dict
                """Recursively flatten nested dictionaries"""
                items = []
                for k, v in d.items():
                    new_key = "{}{}{}".format(parent_key, sep, k) if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key, sep=sep).items())
                    else:
                        items.append((new_key, v))
                return dict(items)

            config = flatten_dict(config)
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
