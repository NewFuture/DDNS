# -*- coding: utf-8 -*-
"""Shared HTTP listener configuration for the Web and MCP servers."""

from __future__ import unicode_literals

import hmac
import socket
import struct

try:
    from urllib.parse import urlparse
except ImportError:  # Python 2
    from urlparse import urlparse

try:
    string_types = (basestring,)  # type: ignore[name-defined]
except NameError:
    string_types = (str,)


DEFAULT_HTTP_HOST = "127.0.0.1"
DEFAULT_HTTP_PORT = 9876


class HttpConfigError(ValueError):
    """Raised when shared HTTP listener settings are invalid."""


def is_loopback_host(host):
    # type: (str) -> bool
    """Return whether a bind host is unambiguously loopback-only."""
    if not isinstance(host, string_types):
        return False
    normalized = host.strip().lower()
    if normalized == "localhost":
        return True
    if normalized.startswith("[") and normalized.endswith("]"):
        normalized = normalized[1:-1]
    try:
        packed = socket.inet_aton(normalized)
        return struct.unpack("!I", packed)[0] >> 24 == 127
    except (AttributeError, socket.error, struct.error):
        pass
    if normalized == "::1":
        return True
    if hasattr(socket, "inet_pton"):
        try:
            packed = socket.inet_pton(socket.AF_INET6, normalized)
            return packed == (b"\x00" * 15 + b"\x01")
        except (AttributeError, socket.error):
            pass
    return False


def _constant_time_equal(left, right):
    # type: (str, str) -> bool
    left_bytes = left.encode("utf-8")
    right_bytes = right.encode("utf-8")
    try:
        return hmac.compare_digest(left_bytes, right_bytes)
    except AttributeError:  # Python 2.7 before compare_digest
        result = len(left_bytes) ^ len(right_bytes)
        for index in range(max(len(left_bytes), len(right_bytes))):
            left_value = ord(left_bytes[index]) if index < len(left_bytes) else 0
            right_value = ord(right_bytes[index]) if index < len(right_bytes) else 0
            result |= left_value ^ right_value
        return result == 0


def _bearer_token(value):
    # type: (str | None) -> str | None
    if not isinstance(value, string_types):
        return None
    parts = value.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def request_token_matches(headers, token, allow_dashboard_header=False):
    # type: (object, str | None, bool) -> bool
    """Validate the shared HTTP token without reflecting it."""
    if token is None:
        return True
    supplied = _bearer_token(headers.get("Authorization"))
    if supplied is None and allow_dashboard_header:
        supplied = headers.get("X-DDNS-Token")
    if not isinstance(supplied, string_types):
        return False
    try:
        return _constant_time_equal(supplied, token)
    except (TypeError, UnicodeError):
        return False


def _normalize_host(value):
    # type: (object) -> str
    if not isinstance(value, string_types):
        raise HttpConfigError("HTTP host must be a string.")
    host = value.strip()
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    if (
        not host
        or any(character in host for character in ("\r", "\n", "\x00", "/", "\\"))
        or any(character.isspace() for character in host)
    ):
        raise HttpConfigError("HTTP host must be a non-empty bind address.")
    return host


def _normalize_port(value):
    # type: (object) -> int
    if isinstance(value, (bool, float)):
        raise HttpConfigError("HTTP port must be an integer from 0 to 65535.")
    try:
        port = int(value)
    except (TypeError, ValueError):
        raise HttpConfigError("HTTP port must be an integer from 0 to 65535.")
    if port < 0 or port > 65535:
        raise HttpConfigError("HTTP port must be an integer from 0 to 65535.")
    return port


def _normalize_token(value):
    # type: (object) -> str | None
    if value is None:
        return None
    if not isinstance(value, string_types):
        raise HttpConfigError("HTTP token must be a string or null.")
    token = value.strip()
    if not token:
        return None
    if "\r" in token or "\n" in token or "\x00" in token:
        raise HttpConfigError("HTTP token cannot contain control characters.")
    try:
        encoded = token.encode("ascii")
    except (UnicodeDecodeError, UnicodeEncodeError):
        raise HttpConfigError("HTTP token must contain visible ASCII characters only.")
    if any(byte < 0x21 or byte > 0x7E for byte in bytearray(encoded)):
        raise HttpConfigError("HTTP token must contain visible ASCII characters only.")
    return token


def normalize_origin(value):
    # type: (object) -> str
    """Validate and canonicalize one exact HTTP origin."""
    if not isinstance(value, string_types):
        raise HttpConfigError("HTTP origins must contain strings.")
    origin = value.strip()
    if any(character.isspace() or ord(character) < 0x20 for character in origin):
        raise HttpConfigError("HTTP origin is invalid: {}.".format(value))
    try:
        parsed = urlparse(origin)
        port = parsed.port
    except (AttributeError, TypeError, ValueError):
        raise HttpConfigError("HTTP origin is invalid: {}.".format(value))
    if (
        parsed.scheme.lower() not in ("http", "https")
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise HttpConfigError("HTTP origin must be an exact http(s) origin: {}.".format(value))

    scheme = parsed.scheme.lower()
    hostname = parsed.hostname.lower()
    if ":" in hostname:
        hostname = "[{}]".format(hostname)
    default_port = 80 if scheme == "http" else 443
    suffix = "" if port in (None, default_port) else ":{}".format(port)
    return "{}://{}{}".format(scheme, hostname, suffix)


def _normalize_origins(value):
    # type: (object) -> list[str]
    if isinstance(value, string_types):
        values = [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]
    elif isinstance(value, (list, tuple)):
        values = list(value)
    else:
        raise HttpConfigError("HTTP origins must be an array.")

    origins = []
    for item in values:
        origin = normalize_origin(item)
        if origin not in origins:
            origins.append(origin)
    return origins


def normalize_http_settings(value=None, enforce_bind_auth=True):
    # type: (dict | None, bool) -> dict
    """Normalize a complete or partial HTTP settings object."""
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise HttpConfigError("http must be an object.")
    unknown = set(value) - {"host", "port", "token", "origins"}
    if unknown:
        raise HttpConfigError("Unsupported HTTP setting: {}.".format(sorted(unknown)[0]))

    settings = {
        "host": _normalize_host(value.get("host", DEFAULT_HTTP_HOST)),
        "port": _normalize_port(value.get("port", DEFAULT_HTTP_PORT)),
        "token": _normalize_token(value.get("token")),
        "origins": _normalize_origins(value["origins"] if "origins" in value else []),
    }
    if enforce_bind_auth and not is_loopback_host(settings["host"]) and settings["token"] is None:
        raise HttpConfigError("A non-empty HTTP token is required for non-loopback listeners.")
    return settings


def resolve_http_settings(cli_config=None, document=None, env_config=None):
    # type: (dict | None, dict | None, dict | None) -> dict
    """Resolve CLI > JSON > environment > defaults HTTP settings."""
    cli_config = cli_config or {}
    document = document or {}
    env_config = env_config or {}
    if not isinstance(document, dict):
        raise HttpConfigError("Configuration root must be an object.")

    merged = {}
    env_keys = {"host": "http_host", "port": "http_port", "token": "http_token", "origins": "http_origins"}
    for key, env_key in env_keys.items():
        if env_key in env_config:
            merged[key] = env_config[env_key]

    if "http" in document:
        json_settings = document["http"]
        if not isinstance(json_settings, dict):
            raise HttpConfigError("http must be an object.")
        if "origins" in json_settings and not isinstance(json_settings["origins"], (list, tuple)):
            raise HttpConfigError("HTTP origins must be an array.")
        merged.update(json_settings)

    cli_keys = {"host": "host", "port": "port", "token": "http_token", "origins": "http_origins"}
    for key, cli_key in cli_keys.items():
        if cli_config.get(cli_key) is not None:
            merged[key] = cli_config[cli_key]
    return normalize_http_settings(merged)


__all__ = [
    "DEFAULT_HTTP_HOST",
    "DEFAULT_HTTP_PORT",
    "HttpConfigError",
    "is_loopback_host",
    "normalize_http_settings",
    "normalize_origin",
    "request_token_matches",
    "resolve_http_settings",
]
