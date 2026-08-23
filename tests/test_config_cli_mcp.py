# -*- coding: utf-8 -*-
"""Tests for the local MCP CLI command."""

from __future__ import unicode_literals

import sys

from __init__ import mock, patch, unittest

from ddns.config.cli import _handle_mcp_command, load_config


class TestMcpSubcommand(unittest.TestCase):
    """Test MCP command parsing and local configuration restrictions."""

    def setUp(self):
        """Preserve command-line arguments between tests."""
        self.original_argv = sys.argv[:]

    def tearDown(self):
        """Restore command-line arguments after each test."""
        sys.argv = self.original_argv

    def test_mcp_subcommand_defaults(self):
        """Start MCP with the conventional local config resolution."""
        sys.argv = ["ddns", "mcp"]
        captured = [None]

        with patch("ddns.config.cli._handle_mcp_command") as handler:
            handler.side_effect = lambda args: captured.__setitem__(0, args)
            with self.assertRaises(SystemExit) as context:
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-08-12")

        self.assertEqual(context.exception.code, 0)
        self.assertEqual(captured[0]["command"], "mcp")
        self.assertIsNone(captured[0]["config"])
        self.assertEqual(captured[0]["transport"], "stdio")
        self.assertIsNone(captured[0]["host"])
        self.assertIsNone(captured[0]["port"])

    def test_mcp_subcommand_accepts_local_config(self):
        """Pass one explicit local configuration to the MCP handler."""
        sys.argv = ["ddns", "mcp", "-c", "config.json"]
        captured = [None]

        with patch("ddns.config.cli._handle_mcp_command") as handler:
            handler.side_effect = lambda args: captured.__setitem__(0, args)
            with self.assertRaises(SystemExit):
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-08-12")

        self.assertEqual(captured[0]["config"], "config.json")

    def test_mcp_subcommand_rejects_multiple_configs(self):
        """Keep the MCP service bound to one deterministic local configuration."""
        sys.argv = ["ddns", "mcp", "-c", "first.json", "-c", "second.json"]

        with self.assertRaises(SystemExit) as context:
            load_config("Test DDNS", "Test doc", "1.0.0", "2026-08-12")

        self.assertEqual(context.exception.code, 2)

    def test_mcp_subcommand_rejects_http_options_with_stdio(self):
        """Fail rather than silently applying HTTP options to stdio."""
        sys.argv = ["ddns", "mcp", "--host", "127.0.0.1"]

        with self.assertRaises(SystemExit) as context:
            load_config("Test DDNS", "Test doc", "1.0.0", "2026-08-12")

        self.assertEqual(context.exception.code, 2)

    @patch("ddns.config.cli.basicConfig")
    @patch("ddns.mcp.serve")
    @patch("ddns.config.cli.load_env_config", return_value={})
    def test_mcp_handler_starts_stdio_server(self, mock_load_env, mock_serve, mock_basic_config):
        """Pass the selected path to the stdio server."""
        _handle_mcp_command({"config": "config.json"})

        mock_basic_config.assert_called_once_with()
        mock_load_env.assert_not_called()
        mock_serve.assert_called_once_with(config_path="config.json")

    @patch("ddns.config.cli.basicConfig")
    @patch("ddns.mcp.serve")
    @patch("ddns.config.cli.load_env_config", return_value={"config": "environment.json"})
    def test_mcp_handler_uses_environment_config(self, mock_load_env, mock_serve, mock_basic_config):
        """Use DDNS_CONFIG when no explicit path is supplied."""
        _handle_mcp_command({})

        mock_basic_config.assert_called_once_with()
        mock_load_env.assert_called_once_with()
        mock_serve.assert_called_once_with(config_path="environment.json")

    @patch("ddns.mcp.serve")
    def test_mcp_handler_rejects_remote_config(self, mock_serve):
        """Do not let the local stdio server fetch remote credential documents."""
        with self.assertRaises(SystemExit) as context:
            _handle_mcp_command({"config": "https://example.com/config.json"})

        self.assertEqual(context.exception.code, 2)
        mock_serve.assert_not_called()

    @patch("ddns.mcp.serve")
    @patch("ddns.config.cli.load_env_config", return_value={"config": ["one.json", "two.json"]})
    def test_mcp_handler_rejects_multiple_environment_configs(self, mock_load_env, mock_serve):
        """Reject ambiguous DDNS_CONFIG lists."""
        with self.assertRaises(SystemExit) as context:
            _handle_mcp_command({})

        self.assertEqual(context.exception.code, 2)
        mock_load_env.assert_called_once_with()
        mock_serve.assert_not_called()

    def test_mcp_subcommand_parses_http_transport_options(self):
        """Expose the shared listener controls on the HTTP transport."""
        sys.argv = [
            "ddns",
            "mcp",
            "--transport",
            "http",
            "--host",
            "0.0.0.0",
            "--port",
            "8765",
            "--http-token",
            "x",
            "--http-origin",
            "https://client.example",
        ]
        captured = [None]

        with patch("ddns.config.cli._handle_mcp_command") as handler:
            handler.side_effect = lambda args: captured.__setitem__(0, args)
            with self.assertRaises(SystemExit) as context:
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-08-12")

        self.assertEqual(context.exception.code, 0)
        self.assertEqual(captured[0]["transport"], "http")
        self.assertEqual(captured[0]["host"], "0.0.0.0")
        self.assertEqual(captured[0]["port"], 8765)
        self.assertEqual(captured[0]["http_token"], "x")
        self.assertEqual(captured[0]["http_origins"], ["https://client.example"])

    @patch("ddns.mcp_http.serve")
    @patch("ddns.config.cli.load_env_config", return_value={"http_host": "0.0.0.0", "http_token": "environment-secret"})
    @patch("ddns.config.cli.basicConfig")
    def test_mcp_handler_starts_http_server(self, mock_basic_config, mock_load_env, mock_serve):
        """Resolve shared settings before starting standalone HTTP MCP."""
        _handle_mcp_command({"transport": "http", "port": 0})

        mock_basic_config.assert_called_once_with()
        mock_load_env.assert_called_once_with()
        mock_serve.assert_called_once_with(
            config_path=mock.ANY,
            settings={"host": "0.0.0.0", "port": 0, "token": "environment-secret", "origins": []},
            logger=mock.ANY,
        )


if __name__ == "__main__":
    unittest.main()
