# -*- coding: utf-8 -*-
"""Minimal MCP server for local DDNS status and synchronization."""

from __future__ import unicode_literals

import json
import logging
import sys
import threading

try:
    from queue import Queue
except ImportError:  # Python 2
    from Queue import Queue

from . import __version__
from .web.service import DashboardError, DashboardService

try:
    string_types = (basestring,)  # type: ignore[name-defined]
    integer_types = (int, long)  # type: ignore[name-defined]
    text_type = unicode  # type: ignore[name-defined]
except NameError:
    string_types = (str,)
    integer_types = (int,)
    text_type = str


PROTOCOL_VERSION = "2026-07-28"
LEGACY_PROTOCOL_VERSION = "2025-11-25"
SUPPORTED_PROTOCOL_VERSIONS = (PROTOCOL_VERSION, LEGACY_PROTOCOL_VERSION)
SERVER_NAME = "ddns"
SERVER_INFO_KEY = "io.modelcontextprotocol/serverInfo"
PROTOCOL_VERSION_KEY = "io.modelcontextprotocol/protocolVersion"
CLIENT_CAPABILITIES_KEY = "io.modelcontextprotocol/clientCapabilities"
CLIENT_INFO_KEY = "io.modelcontextprotocol/clientInfo"
STATUS_FIELDS = ("state", "message", "last_sync", "addresses", "providers", "records")

EMPTY_INPUT_SCHEMA = {"type": "object", "additionalProperties": False}
TOOLS = (
    {
        "name": "get_ddns_status",
        "title": "Get DDNS status",
        "description": "Read configured providers, cached DNS records, addresses, and the latest local sync status.",
        "inputSchema": EMPTY_INPUT_SCHEMA,
        "annotations": {
            "title": "Get DDNS status",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
    {
        "name": "update_dns_records",
        "title": "Update DNS records",
        "description": "Run one complete DDNS synchronization for every record in the configured local file.",
        "inputSchema": EMPTY_INPUT_SCHEMA,
        "annotations": {
            "title": "Update DNS records",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
)
_END_OF_INPUT = object()
_STDOUT_REDIRECT_LOCK = threading.RLock()


def _error_response(request_id, code, message, data=None):
    # type: (object, int, str, object | None) -> dict
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


class McpServer(object):
    """Handle modern MCP requests and the Copilot-compatible legacy lifecycle."""

    def __init__(
        self, config_path=None, logger=None, service_factory=DashboardService, service=None, supported_versions=None
    ):
        # type: (str | None, logging.Logger | None, object, DashboardService | None, object | None) -> None
        self.config_path = config_path
        self.logger = (logger or logging.getLogger()).getChild("mcp")
        self._service_factory = service_factory
        self._service = service
        self.supported_versions = tuple(
            SUPPORTED_PROTOCOL_VERSIONS if supported_versions is None else supported_versions
        )
        self._cancelled = set()
        self._pending = set()
        self._cancel_lock = threading.Lock()
        self._legacy_initialized = False
        self._legacy_ready = False

    @staticmethod
    def _server_meta():
        # type: () -> dict
        return {SERVER_INFO_KEY: {"name": SERVER_NAME, "version": __version__}}

    def _complete_result(self, result, modern=True):
        # type: (dict, bool) -> dict
        if modern:
            result["resultType"] = "complete"
            result["_meta"] = self._server_meta()
        return result

    def _discover(self):
        # type: () -> dict
        return self._complete_result(
            {
                "supportedVersions": list(self.supported_versions),
                "capabilities": {"tools": {}},
                "instructions": (
                    "Use get_ddns_status to inspect local cached state. "
                    "Use update_dns_records only with user approval to update configured DNS records."
                ),
                "ttlMs": 3600000,
                "cacheScope": "public",
            }
        )

    def _list_tools(self, params, modern):
        # type: (dict, bool) -> dict
        if params.get("cursor") is not None:
            raise ValueError("Pagination cursor is not supported.")
        result = {"tools": list(TOOLS)}
        if modern:
            result.update({"ttlMs": 3600000, "cacheScope": "public"})
        return self._complete_result(result, modern=modern)

    @staticmethod
    def _status_view(status):
        # type: (dict) -> dict
        return {field: status.get(field) for field in STATUS_FIELDS}

    def _new_service(self):
        # type: () -> DashboardService
        if self._service is not None:
            return self._service
        return self._service_factory(config_path=self.config_path, logger=self.logger)

    def _tool_success(self, status, modern):
        # type: (dict, bool) -> dict
        status = self._status_view(status)
        text = json.dumps(status, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return self._complete_result(
            {"content": [{"type": "text", "text": text}], "structuredContent": status, "isError": False}, modern=modern
        )

    def _tool_error(self, error, modern):
        # type: (Exception, bool) -> dict
        return self._complete_result(
            {"content": [{"type": "text", "text": text_type(error)}], "isError": True}, modern=modern
        )

    def _call_tool(self, params, modern, request_id):
        # type: (dict, bool, object) -> dict
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, string_types):
            raise ValueError("Tool name must be a string.")
        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be an object.")
        if arguments:
            raise ValueError("This tool does not accept arguments.")
        if name not in ("get_ddns_status", "update_dns_records"):
            raise ValueError("Unknown tool: {}".format(name))

        try:
            service = self._new_service()
            if name == "get_ddns_status":
                return self._tool_success(service.dashboard(), modern=modern)
            with _STDOUT_REDIRECT_LOCK:
                protocol_stdout = sys.stdout
                try:
                    sys.stdout = sys.stderr
                    status = service.sync(source="MCP", cancelled=lambda: self._is_cancelled(request_id))
                finally:
                    sys.stdout = protocol_stdout
            return self._tool_success(status, modern=modern)
        except DashboardError as error:
            return self._tool_error(error, modern=modern)

    def _dispatch(self, method, params, modern, request_id):
        # type: (str, dict, bool, object) -> dict | None
        if method == "server/discover":
            return self._discover() if modern else None
        if method == "tools/list":
            return self._list_tools(params, modern=modern)
        if method == "tools/call":
            return self._call_tool(params, modern=modern, request_id=request_id)
        if method == "ping" and not modern:
            return {}
        return None

    def _initialize_legacy(self, params):
        # type: (dict) -> dict
        if not isinstance(params.get("protocolVersion"), string_types):
            raise ValueError("protocolVersion is required.")
        if not isinstance(params.get("capabilities"), dict):
            raise ValueError("capabilities must be an object.")
        client_info = params.get("clientInfo")
        if (
            not isinstance(client_info, dict)
            or not isinstance(client_info.get("name"), string_types)
            or not isinstance(client_info.get("version"), string_types)
        ):
            raise ValueError("clientInfo must contain string name and version fields.")
        self._legacy_initialized = True
        self._legacy_ready = False
        return {
            "protocolVersion": LEGACY_PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": self._server_meta()[SERVER_INFO_KEY],
            "instructions": (
                "Use get_ddns_status to inspect local cached state. "
                "Use update_dns_records only with user approval to update configured DNS records."
            ),
        }

    def _dispatch_response(self, request_id, method, params, modern):
        # type: (object, str, dict, bool) -> dict
        try:
            result = self._dispatch(method, params, modern=modern, request_id=request_id)
            if result is None:
                return _error_response(request_id, -32601, "Method not found")
        except ValueError as error:
            return _error_response(request_id, -32602, text_type(error))
        except Exception:
            self.logger.exception("Unhandled MCP request failure")
            return _error_response(request_id, -32603, "Internal error")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _handle_legacy_request(self, request_id, method, params):
        # type: (object, str, dict) -> dict
        if method == "initialize":
            try:
                result = self._initialize_legacy(params)
            except ValueError as error:
                return _error_response(request_id, -32602, text_type(error))
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        if not self._legacy_ready and method != "ping":
            return _error_response(request_id, -32600, "Server is not initialized")
        return self._dispatch_response(request_id, method, params, modern=False)

    def _handle_modern_request(self, request_id, method, params):
        # type: (object, str, dict) -> dict
        if method == "server/discover" and not isinstance(params.get("_meta"), dict):
            return _error_response(request_id, -32601, "Method not found")
        try:
            meta = self._validate_meta(params)
        except ValueError as error:
            return _error_response(request_id, -32602, text_type(error))
        requested_version = meta[PROTOCOL_VERSION_KEY]
        if requested_version != PROTOCOL_VERSION:
            return _error_response(
                request_id,
                -32022,
                "Unsupported protocol version",
                {"supported": list(self.supported_versions), "requested": requested_version},
            )
        return self._dispatch_response(request_id, method, params, modern=True)

    @staticmethod
    def _request_id(message):
        # type: (dict) -> object
        request_id = message.get("id")
        if isinstance(request_id, bool) or not isinstance(request_id, string_types + integer_types):
            return None
        return request_id

    @staticmethod
    def _validate_meta(params):
        # type: (dict) -> dict
        meta = params.get("_meta")
        if not isinstance(meta, dict):
            raise ValueError("params._meta must be an object.")
        if not isinstance(meta.get(PROTOCOL_VERSION_KEY), string_types):
            raise ValueError("{} is required.".format(PROTOCOL_VERSION_KEY))
        if not isinstance(meta.get(CLIENT_CAPABILITIES_KEY), dict):
            raise ValueError("{} is required.".format(CLIENT_CAPABILITIES_KEY))
        client_info = meta.get(CLIENT_INFO_KEY)
        if client_info is not None and (
            not isinstance(client_info, dict)
            or not isinstance(client_info.get("name"), string_types)
            or not isinstance(client_info.get("version"), string_types)
        ):
            raise ValueError("{} must contain string name and version fields.".format(CLIENT_INFO_KEY))
        return meta

    def handle_message(self, message):
        # type: (object) -> dict | None
        if not isinstance(message, dict):
            return _error_response(None, -32600, "Invalid Request")

        request_id = self._request_id(message)
        method = message.get("method")
        if message.get("jsonrpc") != "2.0" or not isinstance(method, string_types):
            return _error_response(request_id, -32600, "Invalid Request")
        if "id" not in message:
            if method == "notifications/initialized" and self._legacy_initialized:
                self._legacy_ready = True
            return None
        if request_id is None:
            return _error_response(None, -32600, "Invalid Request")

        params = message.get("params", {})
        if not isinstance(params, dict):
            return _error_response(request_id, -32602, "Invalid params")
        if method == "initialize" or self._legacy_initialized:
            return self._handle_legacy_request(request_id, method, params)
        return self._handle_modern_request(request_id, method, params)

    def handle_modern_message(self, message):
        # type: (object) -> dict | None
        """Handle one modern request without entering the legacy lifecycle."""
        if not isinstance(message, dict):
            return _error_response(None, -32600, "Invalid Request")

        request_id = self._request_id(message)
        method = message.get("method")
        if message.get("jsonrpc") != "2.0" or not isinstance(method, string_types):
            return _error_response(request_id, -32600, "Invalid Request")
        if "id" not in message:
            return None
        if request_id is None:
            return _error_response(None, -32600, "Invalid Request")

        params = message.get("params", {})
        if not isinstance(params, dict):
            return _error_response(request_id, -32602, "Invalid params")
        return self._handle_modern_request(request_id, method, params)

    def handle_line(self, line):
        # type: (str | bytes) -> dict | None
        if not isinstance(line, text_type):
            try:
                line = line.decode("utf-8")
            except UnicodeDecodeError:
                return _error_response(None, -32700, "Parse error")
        try:
            message = json.loads(line)
        except (TypeError, ValueError):
            return _error_response(None, -32700, "Parse error")
        return self.handle_message(message)

    def _record_cancellation(self, message):
        # type: (object) -> bool
        if not isinstance(message, dict) or message.get("method") != "notifications/cancelled":
            return False
        if message.get("jsonrpc") != "2.0" or "id" in message:
            return True
        params = message.get("params")
        request_id = params.get("requestId") if isinstance(params, dict) else None
        if isinstance(request_id, bool) or not isinstance(request_id, string_types + integer_types):
            return True
        with self._cancel_lock:
            if request_id in self._pending:
                self._cancelled.add(request_id)
        return True

    def _cancel_before_start(self, request_id):
        # type: (object) -> bool
        if request_id is None:
            return False
        with self._cancel_lock:
            if request_id not in self._cancelled:
                return False
            self._cancelled.discard(request_id)
            self._pending.discard(request_id)
            return True

    def _is_cancelled(self, request_id):
        # type: (object) -> bool
        with self._cancel_lock:
            return request_id in self._cancelled

    def _write_response(self, response, output_stream):
        # type: (dict, object) -> None
        request_id = response.get("id")
        with self._cancel_lock:
            if request_id in self._cancelled:
                self._cancelled.discard(request_id)
                self._pending.discard(request_id)
                return
            output_stream.write(json.dumps(response, ensure_ascii=True, separators=(",", ":")) + "\n")
            output_stream.flush()
            self._cancelled.discard(request_id)
            self._pending.discard(request_id)

    def _read_messages(self, input_stream, messages):
        # type: (object, Queue) -> None
        try:
            for line in input_stream:
                if not isinstance(line, text_type):
                    try:
                        line = line.decode("utf-8")
                    except UnicodeDecodeError:
                        messages.put((True, _error_response(None, -32700, "Parse error")))
                        continue
                try:
                    message = json.loads(line)
                except (TypeError, ValueError):
                    messages.put((True, _error_response(None, -32700, "Parse error")))
                    continue
                if not self._record_cancellation(message):
                    request_id = self._request_id(message) if isinstance(message, dict) and "id" in message else None
                    if request_id is not None:
                        with self._cancel_lock:
                            self._pending.add(request_id)
                    messages.put((False, message))
        except (IOError, OSError, UnicodeError) as error:
            self.logger.error("MCP input stream failed: %s", error)
        finally:
            messages.put(_END_OF_INPUT)

    def serve(self, input_stream=None, output_stream=None):
        # type: (object | None, object | None) -> None
        input_stream = input_stream or getattr(sys.stdin, "buffer", sys.stdin)
        output_stream = output_stream or sys.stdout
        messages = Queue()
        reader = threading.Thread(target=self._read_messages, args=(input_stream, messages), name="ddns-mcp-reader")
        reader.daemon = True
        reader.start()

        while True:
            item = messages.get()
            if item is _END_OF_INPUT:
                return
            is_response, message = item
            request_id = self._request_id(message) if isinstance(message, dict) and "id" in message else None
            if not is_response and self._cancel_before_start(request_id):
                continue
            response = message if is_response else self.handle_message(message)
            if response is None:
                continue
            self._write_response(response, output_stream)


def serve(config_path=None, input_stream=None, output_stream=None, logger=None):
    # type: (str | None, object | None, object | None, logging.Logger | None) -> None
    """Run the DDNS MCP server until stdin reaches EOF."""
    McpServer(config_path=config_path, logger=logger).serve(input_stream=input_stream, output_stream=output_stream)


__all__ = ["LEGACY_PROTOCOL_VERSION", "McpServer", "PROTOCOL_VERSION", "TOOLS", "serve"]
