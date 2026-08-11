# -*- coding: utf-8 -*-
"""Dashboard data and configuration services."""

from __future__ import unicode_literals

import copy
import json
import logging
import math
import os
import pkgutil
import re
import sys
import tempfile
import threading
import time
from ast import literal_eval

from ..config.config import Config, split_array_string
from ..config.env import load_config as load_env_config
from ..config.file import DEFAULT_CONFIG_PATHS, _flatten_single_config, _process_multi_providers
from ..provider import get_provider_class
from ..util.comment import remove_comment
from ..util.fileio import read_file
from .scheduler import WebScheduler

try:
    from ..scheduler import get_scheduler
except ImportError:
    get_scheduler = None

try:
    string_types = (basestring,)  # type: ignore[name-defined]
    integer_types = (int, long)  # type: ignore[name-defined]
    text_type = unicode  # type: ignore[name-defined]
except NameError:
    string_types = (str,)
    integer_types = (int,)
    text_type = str

try:
    from urllib.parse import urlparse
except ImportError:  # Python 2
    from urlparse import urlparse


def _load_config_model():
    # type: () -> dict
    content = pkgutil.get_data("ddns.config", "field-model.json")
    if content is None:
        raise RuntimeError("Embedded configuration field model is missing.")
    if not isinstance(content, text_type):
        content = content.decode("utf-8")
    try:
        model = json.loads(content)
    except (TypeError, ValueError) as error:
        raise RuntimeError("Embedded configuration field model is invalid: {}.".format(error))
    if not isinstance(model, dict) or not isinstance(model.get("providers"), list):
        raise RuntimeError("Embedded configuration field model has an invalid structure.")
    return model


CONFIG_MODEL = _load_config_model()
CONFIG_RULES = CONFIG_MODEL["rules"]
CONFIG_DEFAULTS = CONFIG_MODEL["defaults"]
SCHEMA_URL = CONFIG_MODEL["schema"]["url"]
PROVIDER_LABELS = {provider["id"]: provider["name"] for provider in CONFIG_MODEL["providers"]}
DOMAIN_PATTERN = re.compile(CONFIG_RULES["domainPattern"])
PROXY_PATTERN = re.compile(CONFIG_RULES["proxyPattern"])
LOG_LEVELS = tuple(CONFIG_RULES["logLevels"])
ADDRESS_SOURCE_NAMES = set(CONFIG_RULES["addressSourceNames"])
ADDRESS_SOURCE_PREFIXES = tuple(CONFIG_RULES["addressSourcePrefixes"])
FALSE_ALIASES = tuple(CONFIG_RULES["falseAliases"])
BOOLEAN_TRUE_ALIASES = tuple(CONFIG_RULES["booleanTrueAliases"])
BOOLEAN_FALSE_ALIASES = tuple(CONFIG_RULES["booleanFalseAliases"])
PROVIDER_FIELDS = (
    "id",
    "token",
    "endpoint",
    "ipv4",
    "ipv6",
    "index4",
    "index6",
    "ttl",
    "line",
    "proxy",
    "cache",
    "cache_max_age",
    "ssl",
    "extra",
)
FLAT_METADATA_FIELDS = {
    "$schema",
    "command",
    "config",
    "debug",
    "dns",
    "log",
    "log_datefmt",
    "log_file",
    "log_format",
    "log_level",
    "interval",
    "provider",
}


class DashboardError(Exception):
    """Base dashboard service error."""

    status = 500
    code = "dashboard_error"


class ConfigValidationError(DashboardError):
    """Raised when a dashboard configuration is invalid."""

    status = 400
    code = "invalid_config"


class DashboardOperationError(DashboardError):
    """Raised when an explicit dashboard operation fails."""

    status = 500
    code = "operation_failed"


def _default_document():
    # type: () -> dict
    return {
        "$schema": SCHEMA_URL,
        "ssl": CONFIG_DEFAULTS["ssl"],
        "proxy": copy.deepcopy(CONFIG_DEFAULTS["proxy"]),
        "cache": CONFIG_DEFAULTS["cache"],
        "cache_max_age": CONFIG_DEFAULTS["cacheMaxAge"],
        "interval": CONFIG_DEFAULTS["interval"],
        "log": {"level": CONFIG_DEFAULTS["logLevel"]},
        "providers": [],
    }


def resolve_config_path(config_path=None):
    # type: (str | None) -> str
    """Resolve a local configuration path without accepting remote URLs."""
    if config_path:
        if not isinstance(config_path, text_type):
            config_path = config_path.decode(sys.getfilesystemencoding() or "utf-8")
        if "://" in config_path:
            raise ConfigValidationError("Web console only supports local configuration files.")
        expanded = os.path.expanduser(config_path)
        if not os.path.isabs(expanded):
            getcwd = getattr(os, "getcwdu", os.getcwd)
            expanded = os.path.join(getcwd(), expanded)
        return os.path.normpath(expanded)

    for candidate in DEFAULT_CONFIG_PATHS:
        expanded = os.path.expanduser(candidate)
        if not os.path.isabs(expanded):
            getcwd = getattr(os, "getcwdu", os.getcwd)
            expanded = os.path.join(getcwd(), expanded)
        expanded = os.path.normpath(expanded)
        if os.path.exists(expanded):
            return expanded
    getcwd = getattr(os, "getcwdu", os.getcwd)
    return os.path.normpath(os.path.join(getcwd(), "config.json"))


def _global_from_flat(source):
    # type: (dict) -> dict
    flat_source = _flatten_single_config(source, preserve_keys=["extra"])
    result = {}
    for key in ("ssl", "proxy", "cache", "cache_max_age", "interval"):
        if key in flat_source:
            result[key] = copy.deepcopy(flat_source[key])

    log = {}
    for source_key, log_key in (
        ("log_level", "level"),
        ("log_file", "file"),
        ("log_format", "format"),
        ("log_datefmt", "datefmt"),
    ):
        if source_key in flat_source:
            log[log_key] = copy.deepcopy(flat_source[source_key])
    if log:
        result["log"] = log
    return result


def _provider_from_flat(source, exclude_keys=None):
    # type: (dict, object) -> dict
    flat_source = _flatten_single_config(source, preserve_keys=["extra"])
    excluded = set(exclude_keys or ())
    provider = {"provider": flat_source.get("provider", flat_source.get("dns", ""))}
    for key in PROVIDER_FIELDS:
        if key in flat_source and key != "extra" and key not in excluded:
            provider[key] = copy.deepcopy(flat_source[key])

    extra = copy.deepcopy(flat_source.get("extra", {})) if isinstance(flat_source.get("extra"), dict) else {}
    known_fields = set(PROVIDER_FIELDS) | FLAT_METADATA_FIELDS
    for key, value in flat_source.items():
        if key.startswith("extra_"):
            extra[key[6:]] = copy.deepcopy(value)
        elif key not in known_fields:
            extra[key] = copy.deepcopy(value)
    if extra:
        provider["extra"] = extra

    log = {}
    for source_key, log_key in (
        ("log_level", "level"),
        ("log_file", "file"),
        ("log_format", "format"),
        ("log_datefmt", "datefmt"),
    ):
        if source_key in flat_source:
            log[log_key] = copy.deepcopy(flat_source[source_key])
    if log and "log" not in excluded:
        provider["log"] = log
    return provider


def normalize_document(document, fallback_provider=None):
    # type: (dict | list, str | None) -> dict
    """Convert supported legacy configuration shapes to schema v4.1."""
    if isinstance(document, list):
        result = {"$schema": SCHEMA_URL, "providers": []}
        if not document and fallback_provider:
            result["providers"] = [{"provider": fallback_provider}]
            return result
        for index, item in enumerate(document):
            if not isinstance(item, dict):
                raise ConfigValidationError("Provider {} must be an object.".format(index + 1))
            provider_source = copy.deepcopy(item)
            if fallback_provider and not (item.get("dns") or item.get("provider")):
                provider_source["provider"] = fallback_provider
            result["providers"].append(_provider_from_flat(provider_source))
        return result

    if not isinstance(document, dict):
        raise ConfigValidationError("Configuration root must be a JSON object.")

    if "providers" in document and not isinstance(document.get("providers"), list):
        raise ConfigValidationError("providers must be an array.")

    if isinstance(document.get("providers"), list):
        result = copy.deepcopy(document)
        result.setdefault("$schema", SCHEMA_URL)
        return result

    result = {"$schema": SCHEMA_URL, "providers": []}
    global_settings = _global_from_flat(document)
    result.update(global_settings)
    provider_name = document.get("dns") or document.get("provider") or fallback_provider
    if provider_name:
        provider_source = copy.deepcopy(document)
        provider_source["provider"] = provider_name
        result["providers"] = [_provider_from_flat(provider_source, exclude_keys=global_settings)]
    elif set(document) - {"$schema"}:
        raise ConfigValidationError("Single-provider configuration requires dns or the DDNS_DNS environment variable.")
    return result


def _validate_string(value, label, allow_empty=True):
    # type: (object, str, bool) -> str
    if value is None and allow_empty:
        return ""
    if not isinstance(value, string_types):
        raise ConfigValidationError("{} must be text.".format(label))
    value = value.strip()
    if not value and not allow_empty:
        raise ConfigValidationError("{} is required.".format(label))
    return value


def _validate_domains(value, label):
    # type: (object, str) -> list[str]
    if value is None:
        return []
    if isinstance(value, string_types):
        value = split_array_string(value, preserve_special=False)
    if not isinstance(value, list):
        raise ConfigValidationError("{} must be text or an array.".format(label))
    result = []
    for domain in value:
        domain = _validate_string(domain, label, allow_empty=False).lower()
        if len(domain) > 253 or DOMAIN_PATTERN.match(domain) is None:
            raise ConfigValidationError("{} contains an invalid domain.".format(label))
        result.append(domain)
    if len(set(result)) != len(result):
        raise ConfigValidationError("{} contains duplicate domains.".format(label))
    return result


def _is_false_source(value):
    # type: (object) -> bool
    if value is False:
        return True
    return isinstance(value, string_types) and value.strip().lower() in FALSE_ALIASES


def _validate_source_rule(source, label):
    # type: (object, str) -> int | str
    if isinstance(source, bool) or not isinstance(source, integer_types + string_types):
        raise ConfigValidationError("{} contains an invalid source rule.".format(label))
    if isinstance(source, integer_types):
        if source < 0:
            raise ConfigValidationError("{} contains a negative interface index.".format(label))
        return source

    source = source.strip()
    if source.isdigit():
        return int(source)
    if source in ADDRESS_SOURCE_NAMES:
        return source
    prefix = next((item for item in ADDRESS_SOURCE_PREFIXES if source.startswith(item)), None)
    if prefix is None:
        raise ConfigValidationError("{} contains an unsupported source rule.".format(label))
    payload = source[len(prefix) :].strip()
    if not payload:
        raise ConfigValidationError("{} contains an empty {} rule.".format(label, prefix))
    if prefix == "url:":
        try:
            parsed = urlparse(payload)
            valid_url = parsed.scheme in ("http", "https") and bool(parsed.hostname)
        except ValueError:
            valid_url = False
        if not valid_url:
            raise ConfigValidationError("{} contains an invalid URL source.".format(label))
    return prefix + payload


def _validate_sources(value, label):
    # type: (object, str) -> list | bool
    if _is_false_source(value):
        return False
    if value is None:
        return []
    if isinstance(value, bool):
        raise ConfigValidationError("{} must be an address source or false.".format(label))
    if isinstance(value, integer_types):
        value = [value]
    elif isinstance(value, string_types):
        value = split_array_string(value)
    if not isinstance(value, list):
        raise ConfigValidationError("{} must be an address source, array, or false.".format(label))
    if not value:
        raise ConfigValidationError("{} cannot be empty; use false to disable this address family.".format(label))
    result = [_validate_source_rule(source, label) for source in value]
    if len(set(result)) != len(result):
        raise ConfigValidationError("{} contains duplicate source rules.".format(label))
    return result


def _validate_proxy(value, label):
    # type: (object, str) -> list[str]
    if value is None:
        return []
    if isinstance(value, string_types):
        value = split_array_string(value, preserve_special=False)
    if not isinstance(value, list) or not all(isinstance(item, string_types) for item in value):
        raise ConfigValidationError("{} must be text or an array of text values.".format(label))
    result = []
    for proxy in value:
        proxy = proxy.strip()
        if PROXY_PATTERN.match(proxy) is None:
            raise ConfigValidationError("{} contains an invalid proxy.".format(label))
        result.append(proxy)
    if len(set(result)) != len(result):
        raise ConfigValidationError("{} contains duplicate proxies.".format(label))
    return result


def _validate_cache_max_age(value, label):
    # type: (object, str) -> int
    if isinstance(value, bool):
        raise ConfigValidationError("{} must be a non-negative integer.".format(label))
    if isinstance(value, integer_types):
        parsed = int(value)
    elif isinstance(value, float) and value.is_integer():
        parsed = int(value)
    elif isinstance(value, string_types):
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            raise ConfigValidationError("{} must be a non-negative integer.".format(label))
    else:
        raise ConfigValidationError("{} must be a non-negative integer.".format(label))
    if parsed < 0:
        raise ConfigValidationError("{} must be a non-negative integer.".format(label))
    return parsed


def _validate_interval(value):
    # type: (object) -> int
    if isinstance(value, bool) or not isinstance(value, integer_types):
        raise ConfigValidationError("interval must be an integer between 1 and 1440 minutes.")
    parsed = int(value)
    if parsed < 1 or parsed > 1440:
        raise ConfigValidationError("interval must be an integer between 1 and 1440 minutes.")
    return parsed


def _validate_cache(value, label):
    # type: (object, str) -> bool | str
    if isinstance(value, bool):
        return value
    if isinstance(value, string_types):
        normalized = value.strip().lower()
        if normalized in BOOLEAN_TRUE_ALIASES:
            return True
        if normalized in BOOLEAN_FALSE_ALIASES:
            return False
        if value.strip():
            return value.strip()
    raise ConfigValidationError("{} must be true, false, or a cache file path.".format(label))


def _validate_ssl(value):
    # type: (object) -> bool | str
    if isinstance(value, bool):
        return value
    if isinstance(value, string_types) and value.strip():
        normalized = value.strip().lower()
        if normalized in BOOLEAN_TRUE_ALIASES:
            return True
        if normalized in BOOLEAN_FALSE_ALIASES:
            return False
        if normalized == "auto":
            return normalized
        return value.strip()
    raise ConfigValidationError("ssl must be a boolean, auto, or a certificate path.")


def _validate_log(value, label):
    # type: (object, str) -> dict
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigValidationError("{} must be an object.".format(label))
    result = copy.deepcopy(value)
    level = result.get("level")
    if level is not None:
        level = _validate_string(level, "{} level".format(label), allow_empty=False).upper()
        if level not in LOG_LEVELS:
            raise ConfigValidationError("{} level is not supported.".format(label))
        result["level"] = level
    for key in ("file", "format", "datefmt"):
        if key in result:
            result[key] = _validate_string(result[key], "{} {}".format(label, key))
    return result


def _validate_reserved_extras(settings, label):
    # type: (dict, str) -> None
    reserved = set(CONFIG_RULES["reservedExtraKeys"])
    direct_conflicts = [key for key in ("domain", "value", "record_type") if key in settings]
    alias_conflicts = [key for key in settings if key.startswith("extra_") and key[len("extra_") :] in reserved]
    extra = settings.get("extra")
    if extra is not None and not isinstance(extra, dict):
        raise ConfigValidationError("{} extra settings must be an object.".format(label))
    nested_conflicts = [key for key in reserved if isinstance(extra, dict) and key in extra]
    conflicts = direct_conflicts + alias_conflicts + nested_conflicts
    if conflicts:
        raise ConfigValidationError(
            "{} extra settings contain reserved fields: {}.".format(label, ", ".join(sorted(conflicts)))
        )


def _validate_inherited_fields(settings, label):  # noqa: C901
    # type: (dict, str) -> None
    _validate_reserved_extras(settings, label)
    for key, field_label in (("id", "ID"), ("token", "token"), ("endpoint", "API endpoint")):
        if key in settings:
            value = settings.get(key)
            settings[key] = (
                None
                if value is None and key != "token"
                else _validate_string(value, "{} {}".format(label, field_label))
            )

    for key, field_label in (("ipv4", "IPv4 domains"), ("ipv6", "IPv6 domains")):
        if key in settings:
            settings[key] = _validate_domains(settings.get(key, []), "{} {}".format(label, field_label))

    for key, field_label in (("index4", "IPv4 sources"), ("index6", "IPv6 sources")):
        if key in settings:
            settings[key] = _validate_sources(settings.get(key, ["default"]), "{} {}".format(label, field_label))

    if "ttl" in settings:
        ttl = settings.get("ttl")
        if ttl not in (None, ""):
            if isinstance(ttl, bool):
                raise ConfigValidationError("{} TTL must be a non-negative number.".format(label))
            if isinstance(ttl, integer_types):
                ttl = int(ttl)
            elif isinstance(ttl, float):
                if math.isnan(ttl) or math.isinf(ttl):
                    raise ConfigValidationError("{} TTL must be a non-negative number.".format(label))
            elif isinstance(ttl, string_types):
                try:
                    ttl = int(ttl)
                except (TypeError, ValueError):
                    raise ConfigValidationError("{} TTL must be a non-negative number.".format(label))
            else:
                raise ConfigValidationError("{} TTL must be a non-negative number.".format(label))
            if ttl < 0:
                raise ConfigValidationError("{} TTL must be a non-negative number.".format(label))
            settings["ttl"] = ttl
        else:
            settings["ttl"] = None

    if "line" in settings:
        line = settings.get("line")
        settings["line"] = None if line in (None, "") else _validate_string(line, "{} DNS line".format(label))
    if "proxy" in settings:
        settings["proxy"] = _validate_proxy(settings.get("proxy"), "{} proxy".format(label))
    if "cache_max_age" in settings:
        settings["cache_max_age"] = _validate_cache_max_age(
            settings.get("cache_max_age"), "{} cache_max_age".format(label)
        )
    if "cache" in settings:
        settings["cache"] = _validate_cache(settings.get("cache"), "{} cache".format(label))
    if "ssl" in settings:
        settings["ssl"] = _validate_ssl(settings.get("ssl"))
    if "log" in settings:
        settings["log"] = _validate_log(settings.get("log"), "{} log".format(label))


def validate_document(document, fallback_provider=None):  # noqa: C901
    # type: (dict | list, str | None) -> dict
    """Validate and canonicalize a configuration document."""
    result = normalize_document(document, fallback_provider=fallback_provider)
    providers = result.get("providers")
    if not isinstance(providers, list):
        raise ConfigValidationError("providers must be an array.")
    if len(providers) > CONFIG_MODEL["limits"]["providers"]:
        raise ConfigValidationError(
            "providers cannot contain more than {} entries.".format(CONFIG_MODEL["limits"]["providers"])
        )
    conflicting_keys = [key for key in CONFIG_RULES["legacyProviderKeys"] if key in result]
    if conflicting_keys:
        raise ConfigValidationError("providers cannot be combined with {}.".format(", ".join(conflicting_keys)))
    _validate_inherited_fields(result, "Global")
    if "interval" in result:
        result["interval"] = _validate_interval(result["interval"])

    validated_providers = []
    for index, raw_provider in enumerate(providers):
        if not isinstance(raw_provider, dict):
            raise ConfigValidationError("Provider {} must be an object.".format(index + 1))
        provider = copy.deepcopy(raw_provider)
        if "dns" in provider:
            raise ConfigValidationError(
                "Provider {} cannot contain dns; use the provider field instead.".format(index + 1)
            )
        if "interval" in provider:
            raise ConfigValidationError("Provider {} interval must be configured globally.".format(index + 1))
        provider_name = _validate_string(
            provider.get("provider"), "Provider {}".format(index + 1), allow_empty=False
        ).lower()
        try:
            provider_class = get_provider_class(provider_name)
        except UnicodeEncodeError:
            provider_class = None
        if provider_class is None:
            raise ConfigValidationError("Unsupported DNS provider: {}.".format(provider_name))
        provider["provider"] = provider_name
        _validate_inherited_fields(provider, "Provider {}".format(index + 1))
        validated_providers.append(provider)

    result["providers"] = validated_providers
    result["$schema"] = SCHEMA_URL
    return result


def _parse_document(content):
    # type: (str) -> dict | list
    without_comments = remove_comment(content)
    try:
        return json.loads(without_comments)
    except (TypeError, ValueError):
        try:
            return literal_eval(content)
        except (SyntaxError, ValueError) as error:
            raise ConfigValidationError("Configuration cannot be parsed: {}.".format(error))


def _write_secure_temp(directory, content):
    # type: (str, str) -> str
    file_descriptor, temp_path = tempfile.mkstemp(prefix=".ddns-config-", suffix=".tmp", dir=directory or ".")
    completed = False
    try:
        data = content.encode("utf-8") if isinstance(content, text_type) else content
        offset = 0
        while offset < len(data):
            written = os.write(file_descriptor, data[offset:])
            if written <= 0:
                raise IOError("Cannot write dashboard configuration temporary file.")
            offset += written
        os.fsync(file_descriptor)
        completed = True
    finally:
        os.close(file_descriptor)
        if not completed and os.path.exists(temp_path):
            os.remove(temp_path)
    return temp_path


def _copy_secure_temp(source, directory, prefix):
    # type: (str, str, str) -> str
    file_descriptor, temp_path = tempfile.mkstemp(prefix=prefix, suffix=".tmp", dir=directory or ".")
    completed = False
    source_file = None
    try:
        source_file = open(source, "rb")
        while True:
            chunk = source_file.read(64 * 1024)
            if not chunk:
                break
            offset = 0
            while offset < len(chunk):
                written = os.write(file_descriptor, chunk[offset:])
                if written <= 0:
                    raise IOError("Cannot copy dashboard configuration temporary file.")
                offset += written
        os.fsync(file_descriptor)
        completed = True
    finally:
        if source_file is not None:
            source_file.close()
        os.close(file_descriptor)
        if not completed and os.path.exists(temp_path):
            os.remove(temp_path)
    return temp_path


def _replace_file(source, destination):
    # type: (str, str) -> None
    replace = getattr(os, "replace", None)
    if replace is not None:
        replace(source, destination)
        return
    if os.name != "nt":
        os.rename(source, destination)
        return

    import ctypes

    source_path = source if isinstance(source, text_type) else source.decode(sys.getfilesystemencoding() or "utf-8")
    destination_path = (
        destination
        if isinstance(destination, text_type)
        else destination.decode(sys.getfilesystemencoding() or "utf-8")
    )
    move_file = ctypes.windll.kernel32.MoveFileExW
    move_file.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
    move_file.restype = ctypes.c_int
    if not move_file(source_path, destination_path, 0x1 | 0x8):
        raise ctypes.WinError()


def _remove_with_warning(path, label):
    # type: (str | None, str) -> None
    if not path or not os.path.exists(path):
        return
    try:
        os.remove(path)
    except (IOError, OSError) as error:
        logging.getLogger(__name__).warning("Cannot remove %s %s: %s", label, path, error)


def _configuration_storage_path(path):
    # type: (str) -> str
    """Resolve a configuration symlink without changing its public path."""
    return os.path.realpath(path) if os.path.islink(path) else path


def _atomic_write(path, content):
    # type: (str, str) -> None
    path = _configuration_storage_path(path)
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    temp_path = None
    backup_path = path + ".bak"
    current_copy_path = None
    try:
        temp_path = _write_secure_temp(directory, content)
        if os.path.exists(path):
            current_copy_path = _copy_secure_temp(path, directory, ".ddns-backup-")
        _replace_file(temp_path, path)
        temp_path = None
    except (IOError, OSError):
        _remove_with_warning(temp_path, "failed configuration temporary file")
        _remove_with_warning(current_copy_path, "failed configuration backup copy")
        raise

    if current_copy_path is None:
        return
    try:
        _replace_file(current_copy_path, backup_path)
    except (IOError, OSError):
        try:
            _replace_file(current_copy_path, path)
        except (IOError, OSError) as rollback_error:
            raise OSError(
                "Configuration backup failed and the previous file remains at {}: {}.".format(
                    current_copy_path, rollback_error
                )
            )
        raise


def _swap_backup(path):
    # type: (str) -> None
    path = _configuration_storage_path(path)
    backup_path = path + ".bak"
    if not os.path.exists(backup_path):
        raise DashboardOperationError("No saved configuration backup is available.")

    directory = os.path.dirname(path)
    restore_path = None
    current_copy_path = None
    try:
        restore_path = _copy_secure_temp(backup_path, directory, ".ddns-restore-")
        if os.path.exists(path):
            current_copy_path = _copy_secure_temp(path, directory, ".ddns-current-")
        _replace_file(restore_path, path)
        restore_path = None
    except (IOError, OSError):
        _remove_with_warning(restore_path, "failed configuration restore copy")
        _remove_with_warning(current_copy_path, "failed current configuration copy")
        raise

    if current_copy_path is None:
        return
    try:
        _replace_file(current_copy_path, backup_path)
    except (IOError, OSError):
        try:
            _replace_file(current_copy_path, path)
        except (IOError, OSError) as rollback_error:
            raise OSError(
                "Configuration restore failed and the previous file remains at {}: {}.".format(
                    current_copy_path, rollback_error
                )
            )
        raise


class DashboardService(object):
    """Own local dashboard configuration and runtime operations."""

    def __init__(self, config_path=None, logger=None, scheduler_interval=5, scheduler=None):
        # type: (str | None, logging.Logger | None, int, WebScheduler | None) -> None
        self.config_path = resolve_config_path(config_path)
        self.logger = (logger or logging.getLogger()).getChild("web")
        self._lock = threading.RLock()
        self._activities = []
        self._web_scheduler = scheduler or WebScheduler(
            self._scheduled_sync,
            interval=scheduler_interval,
            enabled=True,
            guard=self._scheduled_sync_guard,
            logger=self.logger,
        )
        self._reset_sync_state()
        self._record_activity("INFO", "控制台", "本机控制台已启动", os.path.basename(self.config_path))

    def start_scheduler(self):
        # type: () -> None
        """Start periodic synchronization for the lifetime of the web process."""
        self._web_scheduler.start()

    def stop_scheduler(self):
        # type: () -> None
        """Stop periodic synchronization before the web process exits."""
        self._web_scheduler.stop()

    def _external_scheduler_status(self):
        # type: () -> dict
        if get_scheduler is None:
            return {"installed": False, "scheduler": "unavailable"}
        try:
            return get_scheduler("auto").get_status()
        except (IOError, OSError, RuntimeError, ValueError, NotImplementedError) as error:
            return {"installed": False, "scheduler": "unavailable", "error": text_type(error)}

    def _scheduled_sync_guard(self):
        # type: () -> tuple[bool, str | None]
        external = self._external_scheduler_status()
        if external.get("installed") and external.get("enabled"):
            name = external.get("scheduler") or "system"
            return False, "{} scheduled task is still enabled".format(name)
        try:
            document = self.load_document()
            configs = self._runtime_configs(document)
        except DashboardError as error:
            return False, text_type(error)
        if not any(config.ipv4 or config.ipv6 for config in configs):
            return False, "Waiting for at least one configured domain."
        return True, None

    def _scheduled_sync(self):
        # type: () -> dict
        return self.sync(source="自动同步")

    def _reset_sync_state(self):
        # type: () -> None
        self._last_sync_time = None
        self._last_sync_provider_indexes = set()
        self._last_sync_status = None
        self._last_sync_failed_provider_indexes = set()

    def _record_activity(self, level, source, message, detail=""):
        # type: (str, str, str, str) -> None
        self._activities.insert(
            0, {"level": level, "source": source, "message": message, "detail": detail, "timestamp": time.time()}
        )
        del self._activities[50:]

    def _validate_document(self, document):
        # type: (dict | list) -> dict
        env_config = load_env_config()
        fallback_provider = env_config.get("dns") or env_config.get("provider")
        return validate_document(document, fallback_provider=fallback_provider)

    def load_document(self):
        # type: () -> dict
        with self._lock:
            if not os.path.exists(self.config_path):
                return self._validate_document({})
            try:
                content = read_file(self.config_path)
            except (IOError, OSError) as error:
                raise DashboardOperationError("Cannot read configuration: {}.".format(error))
            return self._validate_document(_parse_document(content))

    def config_state(self):
        # type: () -> dict
        with self._lock:
            state = {
                "config": _default_document(),
                "model": copy.deepcopy(CONFIG_MODEL),
                "path": self.config_path,
                "exists": os.path.exists(self.config_path),
                "backup_available": os.path.exists(_configuration_storage_path(self.config_path) + ".bak"),
            }
            if not state["exists"]:
                try:
                    state["config"] = self._validate_document({})
                except ConfigValidationError as error:
                    state["validation_error"] = text_type(error)
                    state["raw"] = "{}"
                return state
            try:
                content = read_file(self.config_path)
            except (IOError, OSError) as error:
                raise DashboardOperationError("Cannot read configuration: {}.".format(error))
            try:
                state["config"] = self._validate_document(_parse_document(content))
            except ConfigValidationError as error:
                state["validation_error"] = text_type(error)
                state["raw"] = content
            return state

    def validate(self, document):
        # type: (dict | list) -> dict
        return self._validate_document(document)

    def save(self, document):
        # type: (dict | list) -> dict
        with self._lock:
            previous_interval = None
            if os.path.exists(self.config_path):
                try:
                    previous_interval = self.load_document().get("interval")
                except (ConfigValidationError, DashboardOperationError):
                    pass
            validated = self._validate_document(document)
            content = json.dumps(validated, ensure_ascii=False, indent=2)
            if not isinstance(content, text_type):
                content = content.decode("utf-8")
            try:
                _atomic_write(self.config_path, content + "\n")
            except (IOError, OSError) as error:
                raise DashboardOperationError("Cannot save configuration: {}.".format(error))
            if validated.get("interval") != previous_interval and "interval" in validated:
                scheduler_status = self._web_scheduler.status()
                self._web_scheduler.configure(
                    enabled=bool(scheduler_status.get("enabled")), interval=validated["interval"]
                )
            self._reset_sync_state()
            self._record_activity("INFO", "配置", "配置已保存", "{} 个 DNS 服务商".format(len(validated["providers"])))
            return self.config_state()

    def restore_backup(self):
        # type: () -> dict
        with self._lock:
            backup_path = _configuration_storage_path(self.config_path) + ".bak"
            if not os.path.exists(backup_path):
                raise DashboardOperationError("No saved configuration backup is available.")
            current_interval = None
            if os.path.exists(self.config_path):
                try:
                    current_interval = self.load_document().get("interval")
                except (ConfigValidationError, DashboardOperationError):
                    pass
            try:
                restored = self._validate_document(_parse_document(read_file(backup_path)))
                _swap_backup(self.config_path)
            except (IOError, OSError) as error:
                raise DashboardOperationError("Cannot restore configuration backup: {}.".format(error))
            if restored.get("interval") != current_interval and "interval" in restored:
                scheduler_status = self._web_scheduler.status()
                self._web_scheduler.configure(
                    enabled=bool(scheduler_status.get("enabled")), interval=restored["interval"]
                )
            self._reset_sync_state()
            self._record_activity("WARN", "配置", "已恢复上一版配置", os.path.basename(self.config_path))
            return self.config_state()

    def _runtime_configs(self, document):
        # type: (dict) -> list[Config]
        env_config = load_env_config()
        try:
            return [Config(json_config=item, env_config=env_config) for item in _process_multi_providers(document)]
        except (TypeError, ValueError) as error:
            raise ConfigValidationError("Runtime configuration is invalid: {}.".format(error))

    def _read_cache(self, config):
        # type: (Config) -> tuple[dict, float | None]
        if config.cache is False:
            return {}, None
        if config.cache is True:
            cache_path = os.path.join(tempfile.gettempdir(), "ddns.{}.cache".format(config.md5()))
        else:
            cache_path = os.path.abspath(os.path.expanduser(config.cache))
        if not os.path.exists(cache_path):
            return {}, None
        try:
            cache_time = os.path.getmtime(cache_path)
            now = time.time()
            if cache_time > now or now - cache_time >= config.cache_max_age:
                return {}, None
            cache = json.loads(read_file(cache_path))
            return (cache if isinstance(cache, dict) else {}), cache_time
        except (IOError, OSError, TypeError, ValueError) as error:
            self.logger.warning("Cannot read cache %s: %s", cache_path, error)
            return {}, None

    def _scheduler_status(self):
        # type: () -> dict
        status = self._web_scheduler.status()
        external = self._external_scheduler_status()
        requested_enabled = bool(status.get("enabled"))
        conflict = bool(external.get("installed") and external.get("enabled"))
        status["requested_enabled"] = requested_enabled
        status["conflict"] = conflict
        if conflict:
            status["enabled"] = False
            status["external_scheduler"] = external.get("scheduler") or "system"
            status["blocked_reason"] = "{} scheduled task is still enabled".format(status["external_scheduler"])
        elif external.get("error"):
            status["external_error"] = external["error"]
        return status

    def dashboard(self):
        # type: () -> dict
        with self._lock:
            document = self.load_document()
            runtime_configs = self._runtime_configs(document)
            providers = []
            records = []
            addresses = []
            seen_addresses = set()
            cache_last_sync = None
            last_sync = self._last_sync_time
            configured_record_count = 0

            for provider_index, (provider, config) in enumerate(zip(document.get("providers", []), runtime_configs)):
                cache, cache_time = self._read_cache(config)
                provider_records = []
                configured_keys = {(domain.lower(), "A") for domain in config.ipv4}
                configured_keys.update((domain.lower(), "AAAA") for domain in config.ipv6)
                for key, value in cache.items():
                    if key.startswith("__") or not isinstance(value, string_types):
                        continue
                    if ":" in key:
                        domain, record_type = key.rsplit(":", 1)
                    else:
                        domain, record_type = key, "A"
                    record_type = record_type.upper()
                    if (domain.lower(), record_type) not in configured_keys:
                        continue
                    record = {
                        "domain": domain,
                        "type": record_type,
                        "value": value,
                        "provider": provider["provider"],
                        "updated": cache_time,
                    }
                    provider_records.append(record)
                    records.append(record)
                    family = "IPv6" if ":" in value else "IPv4"
                    address_key = (family, value)
                    if address_key not in seen_addresses:
                        seen_addresses.add(address_key)
                        addresses.append({"family": family, "value": value})

                if provider_records and cache_time is not None:
                    cache_last_sync = max(cache_last_sync or cache_time, cache_time)
                    last_sync = max(last_sync or cache_time, cache_time)
                configured_records = len(config.ipv4) + len(config.ipv6)
                configured_record_count += configured_records
                providers.append(
                    {
                        "id": provider["provider"],
                        "label": PROVIDER_LABELS.get(provider["provider"], provider["provider"]),
                        "records": configured_records,
                        "status": (
                            "error"
                            if provider_index in self._last_sync_failed_provider_indexes
                            else (
                                "synced"
                                if provider_records or provider_index in self._last_sync_provider_indexes
                                else "configured"
                            )
                        ),
                    }
                )

            if not providers or configured_record_count == 0:
                state = "unconfigured"
                message = "尚未添加需要更新的域名"
            elif self._last_sync_status == "failed":
                state = "error"
                message = "最近一次同步失败"
            elif records or self._last_sync_time is not None:
                state = "synced"
                message = "解析记录同步数据可用" if records else "最近一次同步已完成"
            else:
                state = "ready"
                message = "配置已就绪，等待首次同步"

            activities = list(self._activities)
            if cache_last_sync:
                activities.insert(
                    0,
                    {
                        "level": "INFO",
                        "source": "同步缓存",
                        "message": "最近一次同步已完成",
                        "detail": "{} 条记录".format(len(records)),
                        "timestamp": cache_last_sync,
                    },
                )
            activities.sort(key=lambda item: item.get("timestamp") or 0, reverse=True)
            records.sort(key=lambda item: (item["domain"], item["type"], item["provider"]))
            addresses.sort(key=lambda item: (item["family"], item["value"]))

            return {
                "state": state,
                "message": message,
                "config_path": self.config_path,
                "last_sync": last_sync,
                "addresses": addresses,
                "providers": providers,
                "records": records,
                "activities": activities[:50],
                "scheduler": self._scheduler_status(),
            }

    def sync(self, source="同步"):
        # type: (str) -> dict
        with self._lock:
            document = self.load_document()
            indexed_configs = [
                (index, config)
                for index, config in enumerate(self._runtime_configs(document))
                if config.ipv4 or config.ipv6
            ]
            if not indexed_configs:
                raise ConfigValidationError("Add at least one domain before running synchronization.")

            from ..__main__ import run

            failures = []
            successful_indexes = set()
            for provider_index, config in indexed_configs:
                try:
                    if config.log_level is not None:
                        logging.getLogger().setLevel(config.log_level)
                    if not run(config):
                        failures.append((provider_index, config.dns))
                    else:
                        successful_indexes.add(provider_index)
                except Exception:
                    self.logger.exception("Dashboard synchronization failed for %s", config.dns)
                    failures.append((provider_index, config.dns))

            if failures:
                self._last_sync_status = "failed"
                self._last_sync_provider_indexes = successful_indexes
                self._last_sync_failed_provider_indexes = {index for index, _ in failures}
                failure_names = [name for _, name in failures]
                self._record_activity("WARN", source, "部分服务商同步失败", ", ".join(failure_names))
                raise DashboardOperationError("Synchronization failed for: {}.".format(", ".join(failure_names)))

            self._last_sync_time = time.time()
            self._last_sync_provider_indexes = {index for index, _ in indexed_configs}
            self._last_sync_status = "success"
            self._last_sync_failed_provider_indexes = set()
            self._record_activity("INFO", source, "所有配置同步完成", "{} 个 DNS 服务商".format(len(indexed_configs)))
            return self.dashboard()

    def configure_scheduler(self, action, scheduler_name="web", interval=5):
        # type: (str, str, int) -> dict
        with self._lock:
            action = {"install": "enable", "uninstall": "disable"}.get(action, action)
            if action not in ("configure", "enable", "disable", "takeover"):
                raise ConfigValidationError("Unsupported scheduler action.")
            if scheduler_name not in ("auto", "web"):
                raise ConfigValidationError("Unsupported scheduler.")
            try:
                interval = WebScheduler._validate_interval(interval)
            except (TypeError, ValueError):
                raise ConfigValidationError("Scheduler interval must be between 1 and 1440 minutes.")

            current = self._web_scheduler.status()
            enabled = bool(current.get("enabled"))
            if action == "takeover":
                if get_scheduler is not None:
                    external_scheduler = get_scheduler("auto")
                    external = external_scheduler.get_status()
                    if external.get("installed") and external.get("enabled"):
                        if not external_scheduler.disable():
                            raise DashboardOperationError("Cannot disable the existing system scheduled task.")
                        external = external_scheduler.get_status()
                        if external.get("enabled"):
                            raise DashboardOperationError("The existing system scheduled task is still enabled.")
                enabled = True
            elif action == "enable":
                external = self._external_scheduler_status()
                if external.get("installed") and external.get("enabled"):
                    raise DashboardOperationError(
                        "An external {} scheduled task is enabled; use takeover or ddns task --disable first.".format(
                            external.get("scheduler") or "system"
                        )
                    )
                enabled = True
            elif action == "disable":
                enabled = False

            self._web_scheduler.configure(enabled=enabled, interval=interval)

            self._record_activity(
                "INFO",
                "自动任务",
                {
                    "configure": "自动同步间隔已更新",
                    "enable": "Web 自动同步已启用",
                    "disable": "Web 自动同步已暂停",
                    "takeover": "Web 进程已接管自动同步",
                }[action],
                "每 {} 分钟".format(interval),
            )
            return self._scheduler_status()
