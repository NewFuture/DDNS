# coding=utf-8
from .cli import str_bool, log_level as get_log_level

__all__ = ["Config", "split_array_string"]

# 简单数组，支持',', ';' 分隔的参数列表
SIMPLE_ARRAY_PARAMS = ["ipv4", "ipv6", "proxy"]


def split_array_string(value):
    # type: (str|list) -> list
    """
    解析数组字符串
    """
    if isinstance(value, list):
        return value
    elif not value:  # 空值
        return []
    elif not hasattr(value, "strip"):  # 非字符串
        return [value]

    # 尝试使用逗号或分号分隔符解析
    sep, trimmed = None, value.strip()
    if "," in trimmed:
        sep = ","
    elif ";" in trimmed:
        sep = ";"
    if sep:
        return [item.strip() for item in trimmed.split(sep) if item.strip()]
    return [value]  # 返回原始字符串作为单元素列表


class Config(object):
    """
    Configuration class for DDNS.
    This class is used to load and manage configuration settings.
    """

    def __init__(self, cli_config=None, json_config=None, env_config=None):
        # type: (dict | None, dict | None, dict | None) -> None
        """
        Initialize the Config object.
        """
        self._cli_config = cli_config or {}
        self._json_config = json_config or {}
        self._env_config = env_config or {}

        # dns related configurations
        self.dns = self._get("dns", "debug")  # type: str
        self.id = self._get("id")  # type: str | None
        self.token = self._get("token")  # type: str | None
        self.endpoint = self._get("endpoint")  # type: str | None
        self.index4 = self._get("index4", [])  # type: list[str]
        self.index6 = self._get("index6", [])  # type: list[str]
        self.ipv4 = self._get("ipv4", [])  # type: list[str]
        self.ipv6 = self._get("ipv6", [])  # type: list[str]
        ttl = self._get("ttl", None)  # type: int | str | None
        self.ttl = int(ttl) if isinstance(ttl, (str, bytes)) else ttl  # type: int | None
        self.line = self._get("line", None)  # type: str | None
        proxy = self._get("proxy", [])  # type: list[str]
        self.proxy = [None if p and p.upper() in ["DIRECT", "NONE"] else p for p in proxy]  # type: ignore[assignment]

        # cache and SSL settings
        self.cache = str_bool(self._get("cache", True))
        self.ssl = str_bool(self._get("ssl", "auto"))

        log_level = self._get("log_level", "INFO")
        if isinstance(log_level, (str, bytes)):
            log_level = get_log_level(log_level)
        self.log_level = log_level  # type: int  # type: ignore[assignment]
        self.log_format = self._get("log_format", None)  # type: str | None
        self.log_file = self._get("log_file", None)  # type: str | None
        self.log_datefmt = self._get("log_datefmt", "%Y-%m-%dT%H:%M:%S")  # type: str | None

    def _get(self, key, default=None):
        # type: (str, Any) -> Any
        """
        Get a configuration value by key.
        """
        value = self._cli_config.get(key, self._json_config.get(key, self._env_config.get(key, default)))
        # 处理数组参数
        if key in SIMPLE_ARRAY_PARAMS:
            return split_array_string(value)
        return value

    def dict(self):
        # type: () -> dict[str, Any]
        """
        Convert the Config object to a dictionary.

        Returns:
            dict: Dictionary representation of all configuration values.
        """
        log = {
            "level": get_log_level(self.log_level) if isinstance(self.log_level, int) else self.log_level,
            "format": self.log_format,
            "file": self.log_file,
            "datefmt": self.log_datefmt,
        }
        dict_var = {
            # DNS provider settings
            "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
            "dns": self.dns,
            "id": self.id,
            "token": self.token,
            "endpoint": self.endpoint,
            "index4": self.index4,
            "index6": self.index6,
            "ipv4": self.ipv4,
            "ipv6": self.ipv6,
            "ttl": self.ttl,
            "line": self.line,
            # System settings
            "proxy": self.proxy,
            "cache": self.cache,
            "ssl": self.ssl,
            # Logging settings
            "log": {k: v for k, v in log.items() if v is not None},
        }
        return {k: v for k, v in dict_var.items() if v is not None}

    def __hash__(self):
        # type: () -> int
        """
        Generate hash based on all merged configurations.

        Returns:
            int: Hash value based on configuration attributes.
        """
        # Convert list attributes to tuples for hashing, use tuple() for None safety
        return hash(str(self.dict()))
