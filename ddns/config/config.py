# coding=utf-8
"""
Configuration class merged from CLI, JSON, and environment variables.
@author: NewFuture
"""

from hashlib import md5
from .cli import str_bool, log_level as get_log_level

__all__ = ["Config", "split_array_string"]

# 简单数组，支持',', ';' 分隔的参数列表
SIMPLE_ARRAY_PARAMS = ["ipv4", "ipv6", "proxy", "index4", "index6"]


def is_false(value):
    """
    判断值是否为 False
    字符串 'false', 或者 False, 或者 'none';
    0 不是 False
    """
    if hasattr(value, "strip"):  # 字符串
        return value.strip().lower() in ["false", "none"]
    return value is False


def split_array_string(value):
    # type: (str|list) -> list
    """
    解析数组字符串
    逐个分解，遇到特殊前缀时停止分割
    """
    if isinstance(value, list):
        return value
    if not value or not hasattr(value, "strip"):
        return [value] if value else []

    trimmed = value.strip()

    # 选择分隔符（逗号优先）
    sep = "," if "," in trimmed else (";" if ";" in trimmed else None)
    if not sep:
        return [trimmed]

    # 逐个分解，遇到特殊前缀时停止
    parts = []
    split_parts = trimmed.split(sep)
    for i, part in enumerate(split_parts):
        part = part.strip()
        if not part:
            continue

        # 检查是否包含特殊前缀，如果有则合并剩余部分
        if any(prefix in part for prefix in ["regex:", "cmd:", "shell:"]):
            parts.append(sep.join(split_parts[i:]).strip())
            break
        parts.append(part)

    return parts


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

        # Known configuration keys that should not go into extra
        self._known_keys = {
            "dns",
            "id",
            "token",
            "endpoint",
            "index4",
            "index6",
            "ipv4",
            "ipv6",
            "ttl",
            "line",
            "proxy",
            "cache",
            "ssl",
            "log_level",
            "log_format",
            "log_file",
            "log_datefmt",
            "extra",
            "debug",
            "config",
            "command",
            "$schema",  # JSON schema reference, should not be sent to API
        }

        # dns related configurations
        self.dns = self._get("dns", "")  # type: str
        self.id = self._get("id", "")  # type: str
        self.token = self._get("token", "")  # type: str
        self.endpoint = self._get("endpoint")  # type: str | None
        self.index4 = self._get("index4", ["default"])  # type: list[str]|Literal[False]
        self.index6 = self._get("index6", ["default"])  # type: list[str]|Literal[False]
        self.ipv4 = self._get("ipv4", [])  # type: list[str]
        self.ipv6 = self._get("ipv6", [])  # type: list[str]
        ttl = self._get("ttl", None)  # type: int | str | None
        self.ttl = int(ttl) if isinstance(ttl, (str, bytes)) else ttl  # type: int | None
        self.line = self._get("line", None)  # type: str | None
        self.proxy = self._get("proxy", [])  # type: list[str] | None
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

        # Collect extra fields from all config sources
        self.extra = self._collect_extra()  # type: dict

    def _get(self, key, default=None):
        # type: (str, Any) -> Any
        """
        Get a configuration value by key.
        """
        value = self._cli_config.get(key)
        if isinstance(value, list) and len(value) == 1:
            # 如果是单个元素的列表，取出第一个元素, 这样可以避免在 CLI 配置中使用单个值时仍然得到一个列表
            value = value[0]
        if value is None:
            value = self._json_config.get(key, self._env_config.get(key, default))
        if is_false(value):
            return False
        # 处理数组参数
        if key in SIMPLE_ARRAY_PARAMS:
            return split_array_string(value)
        return value

    def _process_extra_from_source(self, source_config, extra, process_nested_extra=True):
        # type: (dict, dict, bool) -> None
        """
        Process extra fields from a single config source.
        Updates the extra dict in place.
        Within the same source, extra_ prefixed keys override values in the "extra" dict.
        """
        # Process "extra" dict first if it exists and processing is enabled
        if process_nested_extra and "extra" in source_config and isinstance(source_config["extra"], dict):
            extra.update(source_config["extra"])

        # Process all keys from the source
        for key, value in source_config.items():
            if key == "extra":
                continue  # Already processed above
            elif key.startswith("extra_"):
                extra_key = key[6:]  # Remove "extra_" prefix
                extra[extra_key] = value  # Overrides value from nested "extra" dict if present
            elif key not in self._known_keys:
                extra[key] = value

    def _collect_extra(self):
        # type: () -> dict
        """
        Collect all extra fields from CLI, JSON, and ENV configs that are not known keys.
        Priority: CLI > JSON > ENV
        """
        extra = {}  # type: dict

        # Collect from env config first (lowest priority)
        self._process_extra_from_source(self._env_config, extra, process_nested_extra=True)

        # Collect from JSON config (medium priority)
        self._process_extra_from_source(self._json_config, extra, process_nested_extra=True)

        # Collect from CLI config (highest priority)
        # CLI does not support nested extra dict by convention
        self._process_extra_from_source(self._cli_config, extra, process_nested_extra=False)

        return extra

    def md5(self):
        # type: () -> str
        """
        Generate hash based on all merged configurations.

        Returns:
            str: Hash value based on configuration attributes.
        """
        dict_var = {
            "dns": self.dns,
            "id": self.id,
            "token": self.token,
            "endpoint": self.endpoint,
            "index4": self.index4,
            "index6": self.index6,
            "ipv4": self.ipv4,
            "ipv6": self.ipv6,
            "line": self.line,
            "ttl": self.ttl,
            # System settings
            "cache": self.cache,
            "proxy": self.proxy,
            "ssl": self.ssl,
            # Logging settings
            "log_level": self.log_level,
            "log_format": self.log_format,
            "log_file": self.log_file,
            "log_datefmt": self.log_datefmt,
            # Extra fields
            "extra": self.extra,
        }
        return md5(str(dict_var).encode("utf-8")).hexdigest()
