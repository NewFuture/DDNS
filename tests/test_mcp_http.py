# -*- coding: utf-8 -*-
"""Tests for the modern MCP Streamable HTTP transport."""

from __future__ import unicode_literals

import json
import logging
import socket
import threading
import base64

try:
    from http.client import HTTPConnection
except ImportError:  # Python 2
    from httplib import HTTPConnection

from __init__ import MagicMock, unittest

from ddns.http_config import HttpConfigError, normalize_http_settings, resolve_http_settings
from ddns.mcp import CLIENT_CAPABILITIES_KEY, PROTOCOL_VERSION, PROTOCOL_VERSION_KEY
from ddns.mcp_http import McpHttpRequestHandler, create_server


class TestMcpHttpServer(unittest.TestCase):
    """Exercise MCP HTTP framing, security, and dispatch."""

    def setUp(self):
        """Start one tokenless loopback server with a shared fake service."""
        self.service = MagicMock()
        self.service.config_path = "config.json"
        self.service.dashboard.return_value = {
            "state": "ready",
            "message": "ready",
            "last_sync": None,
            "addresses": [],
            "providers": [],
            "records": [],
            "token": "provider-secret",
        }
        self.service.sync.return_value = self.service.dashboard.return_value
        self._start_server()

    def _start_server(self, token=None, origins=None):
        """Replace the active server with the requested security settings."""
        if hasattr(self, "server"):
            self._stop_server()
        self.server = create_server(
            settings={"host": "127.0.0.1", "port": 0, "token": token, "origins": origins or []},
            service=self.service,
            logger=logging.getLogger("test.mcp.http"),
        )
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        self.addCleanup(self._stop_server)
        self.port = self.server.server_address[1]

    def _stop_server(self):
        """Stop the active test server once."""
        server = getattr(self, "server", None)
        if server is None:
            return
        self.server = None
        server.shutdown()
        server.server_close()
        self.thread.join(2)

    @staticmethod
    def _message(method, params=None, request_id=1, version=PROTOCOL_VERSION):
        """Build one modern MCP request."""
        params = dict(params or {})
        params["_meta"] = {
            PROTOCOL_VERSION_KEY: version,
            CLIENT_CAPABILITIES_KEY: {},
            "io.modelcontextprotocol/clientInfo": {"name": "http-test", "version": "1.0"},
        }
        message = {"jsonrpc": "2.0", "method": method, "params": params}
        if request_id is not None:
            message["id"] = request_id
        return message

    @staticmethod
    def _headers(message, token=None, origin=None, overrides=None):
        """Build the required Streamable HTTP headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": message["params"]["_meta"][PROTOCOL_VERSION_KEY],
            "Mcp-Method": message["method"],
        }
        if message["method"] == "tools/call":
            headers["Mcp-Name"] = message["params"]["name"]
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        if origin is not None:
            headers["Origin"] = origin
        headers.update(overrides or {})
        return headers

    def _request(self, message, headers=None, method="POST", path="/mcp", raw_body=None):
        """Send one request and return status, headers, and decoded body."""
        body = (
            raw_body
            if raw_body is not None
            else json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
        connection = HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            content = response.read().decode("utf-8")
            headers = {name.lower(): value for name, value in response.getheaders()}
            return response.status, headers, content
        finally:
            connection.close()

    def test_discover_lists_only_modern_http_version(self):
        """Advertise the modern protocol without the stdio legacy lifecycle."""
        message = self._message("server/discover")

        status, _, body = self._request(message, self._headers(message))

        self.assertEqual(status, 200)
        response = json.loads(body)
        self.assertEqual(response["result"]["supportedVersions"], [PROTOCOL_VERSION])

    def test_tools_share_service_and_redact_unrelated_fields(self):
        """Use one injected service and preserve the MCP status whitelist."""
        update = self._message("tools/call", {"name": "update_dns_records", "arguments": {}})
        status_request = self._message("tools/call", {"name": "get_ddns_status", "arguments": {}}, request_id=2)

        update_status, _, update_body = self._request(update, self._headers(update))
        read_status, _, read_body = self._request(status_request, self._headers(status_request))

        self.assertEqual(update_status, 200)
        self.assertEqual(read_status, 200)
        self.assertFalse(json.loads(update_body)["result"]["isError"])
        self.assertNotIn("provider-secret", read_body)
        self.service.sync.assert_called_once()
        self.service.dashboard.assert_called_once()

    def test_notification_returns_accepted_without_body(self):
        """A valid notification receives HTTP 202 and no JSON-RPC response."""
        message = self._message("notifications/cancelled", {"requestId": 1}, request_id=None)

        status, _, body = self._request(message, self._headers(message))

        self.assertEqual(status, 202)
        self.assertEqual(body, "")

    def test_header_mismatches_are_transport_errors(self):
        """Reject version, method, and tool-name envelope mismatches."""
        message = self._message("tools/call", {"name": "get_ddns_status", "arguments": {}})
        mismatch_headers = (
            {"MCP-Protocol-Version": "2025-11-25"},
            {"Mcp-Method": "tools/list"},
            {"Mcp-Name": "update_dns_records"},
        )

        for override in mismatch_headers:
            headers = self._headers(message, overrides=override)
            status, _, body = self._request(message, headers)
            self.assertEqual(status, 400)
            self.assertEqual(json.loads(body)["error"]["code"], -32020)

    def test_transport_errors_never_echo_invalid_request_ids(self):
        """Use null response IDs until the JSON-RPC request ID is validated."""
        message = self._message("tools/list")
        message["id"] = []
        mismatch_headers = self._headers(message, overrides={"Mcp-Method": "tools/call"})

        mismatch_status, _, mismatch_body = self._request(message, mismatch_headers)
        del message["params"]["_meta"][CLIENT_CAPABILITIES_KEY]
        capability_status, _, capability_body = self._request(message, self._headers(message))

        self.assertEqual(mismatch_status, 400)
        self.assertIsNone(json.loads(mismatch_body)["id"])
        self.assertEqual(capability_status, 400)
        self.assertIsNone(json.loads(capability_body)["id"])

    def test_requires_json_and_both_accepted_media_types(self):
        """Enforce current Streamable HTTP media negotiation."""
        message = self._message("tools/list")
        wrong_content = self._headers(message, overrides={"Content-Type": "text/plain"})
        incomplete_accept = self._headers(message, overrides={"Accept": "application/json"})

        content_status, _, _ = self._request(message, wrong_content)
        accept_status, _, _ = self._request(message, incomplete_accept)

        self.assertEqual(content_status, 415)
        self.assertEqual(accept_status, 406)

    def test_rejects_json_rpc_batches(self):
        """Do not accept JSON-RPC batch arrays."""
        message = self._message("tools/list")
        raw_body = json.dumps([message]).encode("utf-8")

        status, _, body = self._request(message, self._headers(message), raw_body=raw_body)

        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"]["code"], -32600)

    def test_rejects_legacy_protocol_on_http(self):
        """Keep the legacy initialize era limited to stdio."""
        message = self._message("tools/list", version="2025-11-25")

        status, _, body = self._request(message, self._headers(message))

        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"]["code"], -32022)

    def test_unknown_method_uses_http_not_found_with_json_rpc_error(self):
        """Distinguish a modern unsupported method from a missing endpoint."""
        message = self._message("resources/list")

        status, _, body = self._request(message, self._headers(message))

        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body)["error"]["code"], -32601)

    def test_decodes_base64_mcp_name_before_validation(self):
        """Accept the protocol sentinel encoding for mirrored non-plain values."""
        message = self._message("tools/call", {"name": "get_ddns_status", "arguments": {}})
        encoded = base64.b64encode(b"get_ddns_status").decode("ascii")
        headers = self._headers(message, overrides={"Mcp-Name": "=?base64?{}?=".format(encoded)})

        status, _, body = self._request(message, headers)

        self.assertEqual(status, 200, body)

    def test_accepts_http_optional_whitespace_around_mcp_name(self):
        """Ignore header OWS before comparing the mirrored tool name."""
        message = self._message("tools/call", {"name": "get_ddns_status", "arguments": {}})
        headers = self._headers(message, overrides={"Mcp-Name": "get_ddns_status  "})

        status, _, body = self._request(message, headers)

        self.assertEqual(status, 200, body)

    def test_missing_client_capabilities_is_http_bad_request(self):
        """Treat missing required per-request metadata as a transport failure."""
        message = self._message("tools/list")
        del message["params"]["_meta"][CLIENT_CAPABILITIES_KEY]
        headers = self._headers(message)

        status, _, body = self._request(message, headers)

        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"]["code"], -32602)

    def test_configured_token_is_required_as_bearer(self):
        """Use one configured token without accepting the dashboard header."""
        self._start_server(token="shared-secret")
        message = self._message("tools/list")

        missing_status, _, _ = self._request(message, self._headers(message))
        dashboard_status, _, _ = self._request(
            message, self._headers(message, overrides={"X-DDNS-Token": "shared-secret"})
        )
        valid_status, _, _ = self._request(message, self._headers(message, token="shared-secret"))

        self.assertEqual(missing_status, 401)
        self.assertEqual(dashboard_status, 401)
        self.assertEqual(valid_status, 200)

    def test_auth_rejection_does_not_wait_for_an_unsent_body(self):
        """Bound early body draining so unauthenticated clients cannot pin a worker."""
        self._start_server(token="shared-secret")
        connection = socket.create_connection(("127.0.0.1", self.port), timeout=2)
        request = (
            "POST /mcp HTTP/1.1\r\n"
            "Host: 127.0.0.1:{port}\r\n"
            "Content-Type: application/json\r\n"
            "Accept: application/json, text/event-stream\r\n"
            "Content-Length: 1\r\n"
            "\r\n"
        ).format(port=self.port)
        connection.sendall(request.encode("ascii"))

        response = connection.recv(4096)
        connection.close()

        self.assertIn(b"401 Unauthorized", response)

    def test_incomplete_headers_are_closed_after_read_timeout(self):
        """Bound worker lifetime before request parsing and authentication."""
        self.server.connection_timeout = 0.1
        connection = socket.create_connection(("127.0.0.1", self.port), timeout=2)
        connection.sendall(b"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1")

        response = connection.recv(4096)
        connection.close()

        self.assertEqual(response, b"")

    def test_origin_policy_and_preflight(self):
        """Allow direct/configured origins and reject untrusted browser origins."""
        allowed = "https://client.example"
        self._start_server(origins=[allowed])
        message = self._message("tools/list")
        direct = "http://127.0.0.1:{}".format(self.port)

        direct_status, _, _ = self._request(message, self._headers(message, origin=direct))
        allowed_status, allowed_headers, _ = self._request(message, self._headers(message, origin=allowed))
        denied_status, _, _ = self._request(message, self._headers(message, origin="https://evil.example"))
        options_status, options_headers, _ = self._request(
            message, {"Origin": allowed, "Access-Control-Request-Method": "POST"}, method="OPTIONS", raw_body=b""
        )

        self.assertEqual(direct_status, 200)
        self.assertEqual(allowed_status, 200)
        self.assertEqual(allowed_headers["access-control-allow-origin"], allowed)
        self.assertEqual(denied_status, 403)
        self.assertEqual(options_status, 204)
        self.assertIn("MCP-Protocol-Version", options_headers["access-control-allow-headers"])

    def test_allowed_origin_can_read_transport_errors(self):
        """Attach CORS headers after Origin validation even when the request fails."""
        allowed = "https://client.example"
        self._start_server(token="shared-secret", origins=[allowed])
        message = self._message("tools/list")
        headers = self._headers(
            message, token="shared-secret", origin=allowed, overrides={"Content-Type": "text/plain"}
        )

        status, response_headers, _ = self._request(message, headers)

        self.assertEqual(status, 415)
        self.assertEqual(response_headers["access-control-allow-origin"], allowed)

    def test_tokenless_listener_rejects_malformed_loopback_host(self):
        """Do not let userinfo syntax bypass the unauthenticated Host check."""
        message = self._message("tools/list")
        headers = self._headers(message, overrides={"Host": "attacker@127.0.0.1"})

        status, _, body = self._request(message, headers)

        self.assertEqual(status, 421)
        self.assertEqual(json.loads(body)["error"]["code"], "invalid_host")

    def test_wrong_methods_and_paths_are_bounded(self):
        """Return explicit HTTP errors outside the POST endpoint contract."""
        message = self._message("tools/list")

        method_status, _, method_body = self._request(message, self._headers(message), method="GET", raw_body=b"")
        path_status, _, _ = self._request(message, self._headers(message), path="/missing")

        self.assertEqual(method_status, 405)
        self.assertIn("method_not_allowed", method_body)
        self.assertEqual(path_status, 404)

    def test_access_log_drops_query_values(self):
        """Keep accidental query-string credentials out of HTTP logs."""
        handler = MagicMock()
        handler.path = "/mcp?token=do-not-log"
        handler.address_string.return_value = "127.0.0.1"

        log_message = getattr(McpHttpRequestHandler.log_message, "im_func", McpHttpRequestHandler.log_message)
        log_message(handler, '"%s" %s', handler.path, 200)

        logged = handler.server.logger.info.call_args[0][-1]
        self.assertNotIn("do-not-log", logged)

    def test_access_log_handles_request_parse_failures(self):
        """Allow the base handler to log errors before assigning a request path."""

        class BareHandler(object):
            server = MagicMock()

            @staticmethod
            def address_string():
                """Return a stable test peer."""
                return "127.0.0.1"

        handler = BareHandler()
        log_message = getattr(McpHttpRequestHandler.log_message, "im_func", McpHttpRequestHandler.log_message)
        log_message(handler, "%s", "bad request")

        handler.server.logger.info.assert_called_once()

    def test_malformed_request_line_returns_http_error(self):
        """Keep pre-routing parser failures inside BaseHTTPRequestHandler."""
        connection = socket.create_connection(("127.0.0.1", self.port), timeout=2)
        connection.sendall(b"BROKEN REQUEST\r\n\r\n")

        response = connection.recv(4096)
        connection.close()

        self.assertIn(b"400", response)


class TestHttpSettings(unittest.TestCase):
    """Test listener authentication boundaries independently of sockets."""

    def test_loopback_may_omit_token(self):
        """Honor the approved unauthenticated-loopback behavior."""
        settings = normalize_http_settings({"host": "127.0.0.2", "port": 9876})

        self.assertIsNone(settings["token"])

    def test_non_loopback_requires_non_empty_token(self):
        """Reject LAN and wildcard listeners without a configured token."""
        for host in ("192.0.2.10", "0.0.0.0", "::"):
            with self.assertRaises(HttpConfigError):
                normalize_http_settings({"host": host, "port": 9876})

    def test_wildcard_accepts_any_non_empty_token(self):
        """Do not impose a token-strength policy beyond non-empty."""
        settings = normalize_http_settings({"host": "0.0.0.0", "token": "x"})

        self.assertEqual(settings["token"], "x")

    def test_listener_values_reject_ambiguous_input(self):
        """Reject fractional ports, malformed hosts, and non-origin URLs."""
        invalid_settings = (
            {"port": 1.5},
            {"host": "127.0.0.1/path"},
            {"origins": None},
            {"origins": ["https://client.example/path"]},
            {"token": "two words"},
            {"token": "not ascii 密钥"},
        )
        for settings in invalid_settings:
            with self.assertRaises(HttpConfigError):
                normalize_http_settings(settings)

        self.assertEqual(normalize_http_settings({"host": "[::1]"})["host"], "::1")

    def test_explicit_null_http_document_is_invalid(self):
        """Do not silently replace an explicit null object with environment settings."""
        with self.assertRaises(HttpConfigError):
            resolve_http_settings(document={"http": None}, env_config={"http_port": "9000"})

    def test_partial_json_settings_inherit_environment_token(self):
        """Apply final bind authentication after JSON/environment precedence."""
        settings = resolve_http_settings(
            document={"http": {"host": "0.0.0.0"}}, env_config={"http_token": "environment-secret"}
        )

        self.assertEqual(settings["token"], "environment-secret")


if __name__ == "__main__":
    unittest.main()
