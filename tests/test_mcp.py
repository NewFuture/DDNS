# -*- coding: utf-8 -*-
"""Tests for the dependency-free MCP stdio server."""

from __future__ import unicode_literals

import io
import json
import threading

from __init__ import MagicMock, patch, unittest

from ddns.mcp import (
    CLIENT_CAPABILITIES_KEY,
    LEGACY_PROTOCOL_VERSION,
    PROTOCOL_VERSION,
    PROTOCOL_VERSION_KEY,
    SERVER_INFO_KEY,
    McpServer,
)
from ddns.web.service import DashboardOperationError

try:
    text_type = unicode  # type: ignore[name-defined]
except NameError:
    text_type = str


class TextCapture(object):
    """Capture both byte and Unicode writes on Python 2 and 3."""

    def __init__(self):
        self._stream = io.StringIO()

    def write(self, value):
        """Normalize byte writes before forwarding them to the text stream."""
        if not isinstance(value, text_type):
            value = value.decode("utf-8")
        return self._stream.write(value)

    def flush(self):
        """Match the file API used by print and logging."""

    def getvalue(self):
        """Return all captured text."""
        return self._stream.getvalue()


class TestMcpServer(unittest.TestCase):
    """Test modern MCP request validation and DDNS tool dispatch."""

    def _request(self, method, params=None, request_id=1, version=PROTOCOL_VERSION):
        """Build one valid modern MCP request."""
        params = dict(params or {})
        params["_meta"] = {
            PROTOCOL_VERSION_KEY: version,
            CLIENT_CAPABILITIES_KEY: {},
            "io.modelcontextprotocol/clientInfo": {"name": "test-client", "version": "1.0"},
        }
        return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}

    @staticmethod
    def _dashboard():
        """Return representative status with unrelated sensitive fields."""
        return {
            "state": "synced",
            "message": "ready",
            "config_path": "config.json",
            "last_sync": 123.0,
            "addresses": [{"family": "IPv4", "value": "192.0.2.1"}],
            "providers": [{"id": "debug", "records": 1, "status": "synced"}],
            "records": [{"domain": "example.com", "type": "A", "value": "192.0.2.1"}],
            "activities": [{"level": "INFO", "message": "done"}],
            "scheduler": {"token": "scheduler-secret"},
            "token": "provider-secret",
        }

    def test_discover_declares_modern_tool_capability(self):
        """Advertise supported protocol versions and the tool capability."""
        response = McpServer().handle_message(self._request("server/discover"))

        result = response["result"]
        self.assertEqual(result["resultType"], "complete")
        self.assertEqual(result["supportedVersions"], [PROTOCOL_VERSION, LEGACY_PROTOCOL_VERSION])
        self.assertEqual(result["capabilities"], {"tools": {}})
        self.assertEqual(result["cacheScope"], "public")
        self.assertIn(SERVER_INFO_KEY, result["_meta"])

    def test_tools_list_is_deterministic_and_describes_side_effects(self):
        """List status before update and expose accurate safety annotations."""
        response = McpServer().handle_message(self._request("tools/list"))

        result = response["result"]
        tools = result["tools"]
        self.assertEqual([tool["name"] for tool in tools], ["get_ddns_status", "update_dns_records"])
        self.assertTrue(tools[0]["annotations"]["readOnlyHint"])
        self.assertFalse(tools[1]["annotations"]["readOnlyHint"])
        self.assertTrue(tools[1]["annotations"]["destructiveHint"])
        self.assertEqual(tools[0]["inputSchema"], {"type": "object", "additionalProperties": False})
        self.assertEqual(result["ttlMs"], 3600000)

    def test_status_tool_returns_only_whitelisted_state(self):
        """Return local state without exposing configuration credentials."""
        service = MagicMock()
        service.dashboard.return_value = self._dashboard()
        factory = MagicMock(return_value=service)
        server = McpServer(config_path="config.json", service_factory=factory)

        response = server.handle_message(self._request("tools/call", {"name": "get_ddns_status", "arguments": {}}))

        result = response["result"]
        self.assertFalse(result["isError"])
        self.assertEqual(result["structuredContent"]["state"], "synced")
        self.assertNotIn("token", result["structuredContent"])
        self.assertNotIn("scheduler", result["structuredContent"])
        self.assertNotIn("config_path", result["structuredContent"])
        self.assertNotIn("activities", result["structuredContent"])
        self.assertNotIn("provider-secret", result["content"][0]["text"])
        factory.assert_called_once_with(config_path="config.json", logger=server.logger)
        service.dashboard.assert_called_once_with()

    def test_update_tool_runs_complete_config_sync(self):
        """Invoke the existing full synchronization without accepting record arguments."""
        service = MagicMock()
        service.sync.return_value = self._dashboard()
        server = McpServer(service_factory=MagicMock(return_value=service))

        response = server.handle_message(self._request("tools/call", {"name": "update_dns_records", "arguments": {}}))

        self.assertFalse(response["result"]["isError"])
        self.assertEqual(service.sync.call_args[1]["source"], "MCP")
        self.assertTrue(callable(service.sync.call_args[1]["cancelled"]))
        self.assertFalse(service.sync.call_args[1]["cancelled"]())

    def test_update_tool_redirects_provider_stdout_to_stderr(self):
        """Prevent provider print calls from corrupting the MCP protocol stream."""
        service = MagicMock()

        def noisy_sync(source, cancelled=None):
            """Simulate the existing debug provider's print-based output."""
            print("provider output")
            return self._dashboard()

        service.sync.side_effect = noisy_sync
        server = McpServer(service_factory=MagicMock(return_value=service))
        protocol_stdout = TextCapture()
        protocol_stderr = TextCapture()

        with patch("ddns.mcp.sys.stdout", protocol_stdout):
            with patch("ddns.mcp.sys.stderr", protocol_stderr):
                response = server.handle_message(
                    self._request("tools/call", {"name": "update_dns_records", "arguments": {}})
                )

        self.assertFalse(response["result"]["isError"])
        self.assertEqual(protocol_stdout.getvalue(), "")
        self.assertEqual(protocol_stderr.getvalue().strip(), "provider output")

    def test_tool_rejects_arbitrary_arguments(self):
        """Prevent the model from supplying arbitrary domains, addresses, or credentials."""
        factory = MagicMock()
        server = McpServer(service_factory=factory)

        response = server.handle_message(
            self._request("tools/call", {"name": "update_dns_records", "arguments": {"domain": "example.com"}})
        )

        self.assertEqual(response["error"]["code"], -32602)
        factory.assert_not_called()

    def test_dashboard_error_is_a_tool_execution_error(self):
        """Return actionable DDNS failures to the model as tool results."""
        service = MagicMock()
        service.sync.side_effect = DashboardOperationError("Synchronization failed for: debug.")
        server = McpServer(service_factory=MagicMock(return_value=service))

        response = server.handle_message(self._request("tools/call", {"name": "update_dns_records", "arguments": {}}))

        self.assertTrue(response["result"]["isError"])
        self.assertIn("Synchronization failed", response["result"]["content"][0]["text"])

    def test_unexpected_tool_error_is_sanitized(self):
        """Keep unexpected exception details out of the protocol response."""
        service = MagicMock()
        service.dashboard.side_effect = RuntimeError("provider-secret")
        logger = MagicMock()
        server = McpServer(logger=logger, service_factory=MagicMock(return_value=service))

        response = server.handle_message(self._request("tools/call", {"name": "get_ddns_status", "arguments": {}}))

        self.assertEqual(response["error"], {"code": -32603, "message": "Internal error"})
        self.assertNotIn("provider-secret", json.dumps(response))
        logger.getChild.return_value.exception.assert_called_once_with("Unhandled MCP request failure")

    def test_missing_metadata_is_invalid_params(self):
        """Require modern per-request metadata instead of an initialize handshake."""
        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

        response = McpServer().handle_message(request)

        self.assertEqual(response["error"]["code"], -32602)

    def test_invalid_optional_client_info_is_rejected(self):
        """Validate client identity metadata when a client supplies it."""
        request = self._request("tools/list")
        request["params"]["_meta"]["io.modelcontextprotocol/clientInfo"] = {"name": 1, "version": "1.0"}

        response = McpServer().handle_message(request)

        self.assertEqual(response["error"]["code"], -32602)

    def test_unsupported_version_lists_supported_version(self):
        """Return the protocol-defined version mismatch error."""
        response = McpServer().handle_message(self._request("server/discover", version="2025-11-25"))

        self.assertEqual(response["error"]["code"], -32022)
        self.assertEqual(response["error"]["data"]["supported"], [PROTOCOL_VERSION, LEGACY_PROTOCOL_VERSION])
        self.assertEqual(response["error"]["data"]["requested"], "2025-11-25")

    def test_legacy_copilot_lifecycle_lists_and_calls_tools(self):
        """Support the MCP 2025-11-25 lifecycle used by GitHub Copilot CLI."""
        service = MagicMock()
        service.dashboard.return_value = self._dashboard()
        server = McpServer(service_factory=MagicMock(return_value=service))
        initialize = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": LEGACY_PROTOCOL_VERSION,
                "capabilities": {"sampling": {}},
                "clientInfo": {"name": "github-copilot-developer", "version": "1.0.79"},
            },
        }

        initialize_response = server.handle_message(initialize)
        initialized_response = server.handle_message({"jsonrpc": "2.0", "method": "notifications/initialized"})
        list_response = server.handle_message(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"_meta": {"progressToken": 0}}}
        )
        call_response = server.handle_message(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "get_ddns_status", "arguments": {}}}
        )

        self.assertEqual(initialize_response["result"]["protocolVersion"], LEGACY_PROTOCOL_VERSION)
        self.assertNotIn("resultType", initialize_response["result"])
        self.assertIsNone(initialized_response)
        self.assertEqual(
            [tool["name"] for tool in list_response["result"]["tools"]], ["get_ddns_status", "update_dns_records"]
        )
        self.assertNotIn("resultType", list_response["result"])
        self.assertNotIn("ttlMs", list_response["result"])
        self.assertFalse(call_response["result"]["isError"])
        self.assertNotIn("resultType", call_response["result"])
        service.dashboard.assert_called_once_with()

    def test_legacy_ping_works_before_initialized_notification(self):
        """Allow the legacy lifecycle health check during initialization."""
        server = McpServer()
        server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": LEGACY_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "client", "version": "1.0"},
                },
            }
        )

        response = server.handle_message({"jsonrpc": "2.0", "id": 1, "method": "ping"})

        self.assertEqual(response["result"], {})

    def test_missing_meta_discover_allows_legacy_fallback(self):
        """Return Method not found for Copilot's legacy-era discovery probe."""
        response = McpServer().handle_message({"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {}})

        self.assertEqual(response["error"]["code"], -32601)

    def test_unknown_method_and_tool_are_protocol_errors(self):
        """Use JSON-RPC errors for unsupported protocol operations."""
        method_response = McpServer().handle_message(self._request("resources/list"))
        tool_response = McpServer().handle_message(self._request("tools/call", {"name": "missing", "arguments": {}}))

        self.assertEqual(method_response["error"]["code"], -32601)
        self.assertEqual(tool_response["error"]["code"], -32602)

    def test_invalid_json_and_request_id_are_rejected(self):
        """Return parse and invalid-request errors with a null response ID."""
        parse_response = McpServer().handle_line("{")
        id_response = McpServer().handle_message(self._request("tools/list", request_id=True))

        self.assertEqual(parse_response["error"]["code"], -32700)
        self.assertIsNone(parse_response["id"])
        self.assertEqual(id_response["error"]["code"], -32600)
        self.assertIsNone(id_response["id"])

    def test_utf8_bytes_are_decoded_explicitly(self):
        """Accept UTF-8 request bytes independently of the process locale."""
        request = self._request("server/discover")
        request["params"]["_meta"]["io.modelcontextprotocol/clientInfo"]["name"] = "测试客户端"
        line = json.dumps(request, ensure_ascii=False).encode("utf-8")

        response = McpServer().handle_line(line)

        self.assertEqual(response["result"]["supportedVersions"], [PROTOCOL_VERSION, LEGACY_PROTOCOL_VERSION])

    def test_notifications_do_not_receive_responses(self):
        """Honor JSON-RPC notification semantics."""
        notification = {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 1}}

        self.assertIsNone(McpServer().handle_message(notification))

    def test_stdio_writes_one_json_response_per_line(self):
        """Keep stdout limited to newline-delimited JSON-RPC responses."""
        notification = {"jsonrpc": "2.0", "method": "notifications/cancelled"}
        malformed_cancellation = {"jsonrpc": "1.0", "id": 4, "method": "notifications/cancelled"}
        input_stream = io.StringIO(
            json.dumps(notification)
            + "\n"
            + json.dumps(malformed_cancellation)
            + "\n"
            + json.dumps(self._request("server/discover"))
            + "\n"
        )
        output_stream = io.StringIO()

        McpServer().serve(input_stream=input_stream, output_stream=output_stream)

        lines = output_stream.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(
            json.loads(lines[0])["result"]["supportedVersions"], [PROTOCOL_VERSION, LEGACY_PROTOCOL_VERSION]
        )

    def test_in_flight_cancellation_suppresses_tool_response(self):
        """Observe cancellation while a blocking synchronization is running."""
        started = threading.Event()
        cancellation_seen = threading.Event()
        service = MagicMock()
        server = McpServer(service_factory=MagicMock(return_value=service))
        original_record_cancellation = server._record_cancellation

        def record_cancellation(message):
            """Signal after the reader records a cancellation notification."""
            recorded = original_record_cancellation(message)
            if isinstance(message, dict) and message.get("method") == "notifications/cancelled":
                cancellation_seen.set()
            return recorded

        def blocking_sync(source, cancelled=None):
            """Wait until the reader consumes and exposes the cancellation."""
            started.set()
            self.assertTrue(cancellation_seen.wait(1))
            self.assertTrue(cancelled())
            raise DashboardOperationError("Synchronization cancelled.")

        def input_lines():
            """Send cancellation only after synchronization has started."""
            yield json.dumps(self._request("tools/call", {"name": "update_dns_records", "arguments": {}}, request_id=9))
            self.assertTrue(started.wait(1))
            yield json.dumps({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 9}})

        server._record_cancellation = record_cancellation
        service.sync.side_effect = blocking_sync
        output_stream = io.StringIO()

        server.serve(input_stream=input_lines(), output_stream=output_stream)

        self.assertEqual(service.sync.call_args[1]["source"], "MCP")
        self.assertTrue(callable(service.sync.call_args[1]["cancelled"]))
        self.assertEqual(output_stream.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
