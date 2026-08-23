# -*- coding: utf-8 -*-
"""Modern MCP Streamable HTTP transport."""

from __future__ import unicode_literals

import base64
import binascii
import json
import logging
import re
import socket
import sys

try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn
    from urllib.parse import urlparse
except ImportError:  # Python 2
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
    from urlparse import urlparse

from .http_config import (
    HTTP_CONNECTION_TIMEOUT,
    is_loopback_host,
    normalize_http_settings,
    normalize_origin,
    request_token_matches,
)
from .mcp import CLIENT_CAPABILITIES_KEY, PROTOCOL_VERSION, PROTOCOL_VERSION_KEY, McpServer, _error_response
from .web.service import DashboardService

try:
    string_types = (basestring,)  # type: ignore[name-defined]
    text_type = unicode  # type: ignore[name-defined]
except NameError:
    string_types = (str,)
    text_type = str


MCP_PATH = "/mcp"
MAX_BODY_SIZE = 2 * 1024 * 1024
JSON_MEDIA_TYPE = "application/json"
SSE_MEDIA_TYPE = "text/event-stream"
HEADER_MISMATCH = -32020
_BASE64_SENTINEL = re.compile(r"^=\?base64\?([A-Za-z0-9+/]*={0,2})\?=$")


class McpHttpRequestError(Exception):
    """Map one transport validation failure to an HTTP response."""

    def __init__(self, status, payload, headers=None):
        # type: (int, dict, dict | None) -> None
        Exception.__init__(self, status)
        self.status = status
        self.payload = payload
        self.headers = headers or {}


def _json_bytes(payload):
    # type: (dict) -> bytes
    content = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if not isinstance(content, bytes):
        content = content.encode("utf-8")
    return content


def _host_header_is_loopback(host_header):
    # type: (str) -> bool
    try:
        parsed = urlparse("http://{}".format(host_header))
        parsed.port
    except (AttributeError, TypeError, ValueError):
        return False
    return (
        parsed.username is None
        and parsed.password is None
        and not parsed.path
        and not parsed.query
        and not parsed.fragment
        and is_loopback_host(parsed.hostname)
    )


def _direct_request_origin(host_header):
    # type: (str) -> str | None
    try:
        return normalize_origin("http://{}".format(host_header))
    except (TypeError, ValueError):
        return None


def _decode_mirrored_value(value):
    # type: (str | None) -> str | None
    """Decode one MCP mirrored header value before comparison."""
    if not isinstance(value, string_types):
        return None
    value = value.strip(" \t")
    try:
        sentinel = _BASE64_SENTINEL.match(value)
    except UnicodeError:
        return None
    if sentinel:
        encoded = sentinel.group(1)
        if len(encoded) % 4:
            return None
        try:
            decoded = base64.b64decode(encoded).decode("utf-8")
        except (binascii.Error, TypeError, ValueError, UnicodeDecodeError):
            return None
        return decoded
    try:
        encoded_value = value.encode("ascii")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return None
    if value != value.strip() or any(byte < 0x20 or byte > 0x7E for byte in bytearray(encoded_value)):
        return None
    return value


class McpHttpEndpoint(object):
    """Handle `/mcp` requests independently of the surrounding HTTP server."""

    def __init__(self, server, settings, logger=None):
        # type: (McpServer, dict, logging.Logger | None) -> None
        self.server = server
        self.settings = normalize_http_settings(settings)
        self.logger = (logger or logging.getLogger()).getChild("mcp.http")

    @property
    def token(self):
        # type: () -> str | None
        return self.settings["token"]

    def _send(self, handler, status, payload=None, extra_headers=None):
        # type: (BaseHTTPRequestHandler, int, dict | None, dict | None) -> None
        content = b"" if payload is None else _json_bytes(payload)
        handler.close_connection = True
        handler.send_response(status)
        if payload is not None:
            handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(content)))
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Connection", "close")
        handler.send_header("X-Content-Type-Options", "nosniff")
        for name, value in (extra_headers or {}).items():
            handler.send_header(name, value)
        handler.end_headers()
        if content and handler.command != "HEAD":
            handler.wfile.write(content)
        handler.wfile.flush()

    def _cors_headers(self, handler):
        # type: (BaseHTTPRequestHandler) -> dict
        origin = handler.headers.get("Origin")
        if not origin:
            return {}
        try:
            normalized = normalize_origin(origin)
        except ValueError:
            return {}
        if normalized not in self.settings["origins"]:
            return {}
        return {"Access-Control-Allow-Origin": normalized, "Vary": "Origin"}

    def _origin_allowed(self, handler):
        # type: (BaseHTTPRequestHandler) -> bool
        origin = handler.headers.get("Origin")
        if not origin:
            return True
        try:
            normalized = normalize_origin(origin)
        except ValueError:
            return False
        direct = _direct_request_origin(handler.headers.get("Host", ""))
        return normalized == direct or normalized in self.settings["origins"]

    def _validate_access(self, handler):
        # type: (BaseHTTPRequestHandler) -> None
        if self.token is None and not _host_header_is_loopback(handler.headers.get("Host", "")):
            raise McpHttpRequestError(
                421, {"error": {"code": "invalid_host", "message": "Unauthenticated HTTP only accepts loopback hosts."}}
            )
        if not self._origin_allowed(handler):
            raise McpHttpRequestError(
                403, {"error": {"code": "invalid_origin", "message": "HTTP request origin is not allowed."}}
            )
        if not request_token_matches(handler.headers, self.token):
            raise McpHttpRequestError(
                401,
                {"error": {"code": "invalid_token", "message": "HTTP bearer token is invalid."}},
                {"WWW-Authenticate": 'Bearer realm="ddns-mcp"'},
            )

    @staticmethod
    def _media_types(header_value):
        # type: (str) -> set[str]
        accepted = set()
        for item in header_value.split(","):
            parts = [part.strip() for part in item.split(";")]
            if not parts[0]:
                continue
            quality = 1.0
            valid = True
            for parameter in parts[1:]:
                name, separator, value = parameter.partition("=")
                if separator and name.strip().lower() == "q":
                    try:
                        quality = float(value.strip())
                    except (TypeError, ValueError):
                        valid = False
                    if quality < 0 or quality > 1:
                        valid = False
            if valid and quality > 0:
                accepted.add(parts[0].lower())
        return accepted

    def _read_message(self, handler):
        # type: (BaseHTTPRequestHandler) -> dict
        content_type = handler.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != JSON_MEDIA_TYPE:
            raise McpHttpRequestError(
                415, {"error": {"code": "unsupported_media_type", "message": "Content-Type must be application/json."}}
            )
        accept = self._media_types(handler.headers.get("Accept", ""))
        if JSON_MEDIA_TYPE not in accept or SSE_MEDIA_TYPE not in accept:
            raise McpHttpRequestError(
                406,
                {
                    "error": {
                        "code": "not_acceptable",
                        "message": "Accept must include application/json and text/event-stream.",
                    }
                },
            )
        content_length = handler.headers.get("Content-Length")
        if content_length is None:
            raise McpHttpRequestError(
                411, {"error": {"code": "length_required", "message": "Content-Length is required."}}
            )
        try:
            content_length = int(content_length)
        except (TypeError, ValueError):
            raise McpHttpRequestError(
                400, {"error": {"code": "invalid_length", "message": "Content-Length is invalid."}}
            )
        if content_length < 0 or content_length > MAX_BODY_SIZE:
            raise McpHttpRequestError(
                413, {"error": {"code": "payload_too_large", "message": "Request body is too large."}}
            )
        content = handler.rfile.read(content_length)
        handler.mcp_body_consumed = True
        try:
            message = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, TypeError, ValueError):
            raise McpHttpRequestError(400, _error_response(None, -32700, "Parse error"))
        if not isinstance(message, dict):
            raise McpHttpRequestError(400, _error_response(None, -32600, "Invalid Request"))
        return message

    @staticmethod
    def _discard_request_body(handler):
        # type: (BaseHTTPRequestHandler) -> None
        """Briefly drain an already-buffered body so Windows can deliver an early response."""
        if getattr(handler, "mcp_body_consumed", False):
            return
        try:
            content_length = int(handler.headers.get("Content-Length", ""))
        except (TypeError, ValueError):
            return
        if content_length < 0 or content_length > MAX_BODY_SIZE:
            return
        previous_timeout = handler.connection.gettimeout()
        try:
            handler.connection.settimeout(0.05)
            if content_length:
                handler.rfile.read(content_length)
        except (IOError, OSError, socket.timeout):
            return
        finally:
            try:
                handler.connection.settimeout(previous_timeout)
            except (IOError, OSError):
                pass
        handler.mcp_body_consumed = True

    def _header_mismatch(self, message, detail):
        # type: (dict, str) -> McpHttpRequestError
        request_id = self.server._request_id(message)
        return McpHttpRequestError(400, _error_response(request_id, HEADER_MISMATCH, detail))

    def _validate_message(self, message):
        # type: (dict) -> None
        request_id = self.server._request_id(message) if "id" in message else None
        if (
            message.get("jsonrpc") != "2.0"
            or not isinstance(message.get("method"), string_types)
            or ("id" in message and request_id is None)
        ):
            raise McpHttpRequestError(400, _error_response(request_id, -32600, "Invalid Request"))
        if not isinstance(message.get("params", {}), dict):
            raise McpHttpRequestError(400, _error_response(request_id, -32602, "Invalid params"))

    def _validate_envelope(self, handler, message):
        # type: (BaseHTTPRequestHandler, dict) -> None
        header_version = handler.headers.get("MCP-Protocol-Version")
        header_method = handler.headers.get("Mcp-Method")
        body_method = message.get("method")
        params = message.get("params")
        meta = params.get("_meta") if isinstance(params, dict) else None
        body_version = meta.get(PROTOCOL_VERSION_KEY) if isinstance(meta, dict) else None
        if not header_version or header_version != body_version:
            raise self._header_mismatch(message, "MCP-Protocol-Version does not match request metadata.")
        if not header_method or header_method != body_method:
            raise self._header_mismatch(message, "Mcp-Method does not match the JSON-RPC method.")
        if not isinstance(meta.get(CLIENT_CAPABILITIES_KEY) if isinstance(meta, dict) else None, dict):
            raise McpHttpRequestError(
                400,
                _error_response(
                    self.server._request_id(message), -32602, "{} is required.".format(CLIENT_CAPABILITIES_KEY)
                ),
            )
        if body_method == "tools/call":
            header_name = _decode_mirrored_value(handler.headers.get("Mcp-Name"))
            body_name = params.get("name") if isinstance(params, dict) else None
            if not header_name or header_name != body_name:
                raise self._header_mismatch(message, "Mcp-Name does not match the requested tool.")

    def handle_post(self, handler):
        # type: (BaseHTTPRequestHandler) -> None
        handler.mcp_body_consumed = False
        try:
            self._validate_access(handler)
            message = self._read_message(handler)
            self._validate_message(message)
            self._validate_envelope(handler, message)
        except McpHttpRequestError as error:
            self._discard_request_body(handler)
            headers = dict(error.headers)
            headers.update(self._cors_headers(handler))
            self._send(handler, error.status, error.payload, headers)
            return

        response = self.server.handle_modern_message(message)

        cors_headers = self._cors_headers(handler)
        status = 200
        if response is not None and "error" in response:
            error_code = response["error"].get("code")
            if error_code == -32022:
                status = 400
            elif error_code == -32601:
                status = 404
        try:
            if response is None:
                self._send(handler, 202, extra_headers=cors_headers)
            else:
                self._send(handler, status, response, cors_headers)
        except (IOError, OSError, socket.error):
            self.logger.info("MCP HTTP client disconnected before receiving its response")

    def handle_options(self, handler):
        # type: (BaseHTTPRequestHandler) -> None
        origin = handler.headers.get("Origin")
        try:
            normalized = normalize_origin(origin)
        except (TypeError, ValueError):
            normalized = None
        if normalized is None or normalized not in self.settings["origins"]:
            self._send(
                handler, 403, {"error": {"code": "invalid_origin", "message": "HTTP request origin is not allowed."}}
            )
            return
        headers = {
            "Access-Control-Allow-Origin": normalized,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": ("Authorization, Content-Type, MCP-Protocol-Version, Mcp-Method, Mcp-Name"),
            "Access-Control-Max-Age": "600",
            "Vary": "Origin",
        }
        self._send(handler, 204, extra_headers=headers)

    def method_not_allowed(self, handler):
        # type: (BaseHTTPRequestHandler) -> None
        self._send(
            handler,
            405,
            {"error": {"code": "method_not_allowed", "message": "MCP HTTP only accepts POST."}},
            {"Allow": "POST, OPTIONS"},
        )


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Threaded MCP HTTP server."""

    allow_reuse_address = False
    daemon_threads = True
    connection_timeout = HTTP_CONNECTION_TIMEOUT

    def get_request(self):
        # type: () -> tuple[object, object]
        request, client_address = HTTPServer.get_request(self)
        request.settimeout(self.connection_timeout)
        return request, client_address

    def server_bind(self):
        # type: () -> None
        if sys.platform.startswith("win") and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        HTTPServer.server_bind(self)


class ThreadingHTTPServerV6(ThreadingHTTPServer):
    """IPv6 MCP HTTP server."""

    address_family = socket.AF_INET6


class McpHttpRequestHandler(BaseHTTPRequestHandler):
    """Serve only the modern MCP HTTP endpoint."""

    protocol_version = "HTTP/1.1"
    server_version = "DDNS"
    sys_version = ""

    @property
    def endpoint(self):
        # type: () -> McpHttpEndpoint
        return self.server.mcp_endpoint  # type: ignore[attr-defined]

    def log_message(self, format_string, *args):
        # type: (str, *object) -> None
        message = format_string % args
        request_path = getattr(self, "path", "") or ""
        if request_path:
            message = message.replace(request_path, urlparse(request_path).path)
        self.server.logger.info("%s - %s", self.address_string(), message)  # type: ignore[attr-defined]

    def _path_is_mcp(self):
        # type: () -> bool
        return urlparse(self.path).path == MCP_PATH

    def do_POST(self):
        # type: () -> None
        if not self._path_is_mcp():
            self.endpoint._send(self, 404, {"error": {"code": "not_found", "message": "Resource not found."}})
            return
        self.endpoint.handle_post(self)

    def do_OPTIONS(self):
        # type: () -> None
        if not self._path_is_mcp():
            self.endpoint._send(self, 404, {"error": {"code": "not_found", "message": "Resource not found."}})
            return
        self.endpoint.handle_options(self)

    def _method_not_allowed(self):
        # type: () -> None
        if self._path_is_mcp():
            self.endpoint.method_not_allowed(self)
        else:
            self.endpoint._send(self, 404, {"error": {"code": "not_found", "message": "Resource not found."}})

    do_GET = _method_not_allowed
    do_HEAD = _method_not_allowed
    do_PUT = _method_not_allowed
    do_DELETE = _method_not_allowed


def create_server(config_path=None, settings=None, service=None, logger=None):
    # type: (str | None, dict | None, DashboardService | None, logging.Logger | None) -> ThreadingHTTPServer
    """Create a standalone modern MCP HTTP server."""
    settings = normalize_http_settings(settings)
    logger = logger or logging.getLogger()
    service = service or DashboardService(config_path=config_path, logger=logger)
    mcp_server = McpServer(
        config_path=config_path, logger=logger, service=service, supported_versions=(PROTOCOL_VERSION,)
    )
    server_class = ThreadingHTTPServerV6 if ":" in settings["host"] else ThreadingHTTPServer
    server = server_class((settings["host"], settings["port"]), McpHttpRequestHandler)
    server.logger = logger.getChild("mcp.http.server")
    server.http_settings = settings
    server.mcp_endpoint = McpHttpEndpoint(mcp_server, settings=settings, logger=logger)
    return server


def serve(config_path=None, settings=None, logger=None):
    # type: (str | None, dict | None, logging.Logger | None) -> None
    """Run the standalone MCP HTTP server until interrupted."""
    server = create_server(config_path=config_path, settings=settings, logger=logger)
    host, port = server.server_address[:2]
    display_host = "127.0.0.1" if host == "0.0.0.0" else "::1" if host == "::" else host
    if ":" in display_host:
        display_host = "[{}]".format(display_host)
    sys.stdout.write("DDNS MCP HTTP: http://{}:{}{}\n".format(display_host, port, MCP_PATH))
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stdout.write("\nStopping DDNS MCP HTTP...\n")
        sys.stdout.flush()
    finally:
        server.server_close()


__all__ = ["MCP_PATH", "McpHttpEndpoint", "McpHttpRequestHandler", "create_server", "request_token_matches", "serve"]
