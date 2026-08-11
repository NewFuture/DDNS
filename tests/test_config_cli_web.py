# coding=utf-8
"""Unit tests for the embedded dashboard CLI command."""

from __future__ import unicode_literals

import io
import json
import os
import shutil
import sys
import tempfile

from __init__ import mock, patch, unittest

from ddns.config.cli import _handle_web_command, load_config


class TestWebSubcommand(unittest.TestCase):
    """Test the local dashboard subcommand."""

    def setUp(self):
        """Preserve command-line arguments between tests."""
        self.original_argv = sys.argv[:]
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Restore command-line arguments after each test."""
        sys.argv = self.original_argv
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _config_file(self, interval=None):
        """Create one local configuration file for CLI routing tests."""
        config_path = os.path.join(self.temp_dir, "config.json")
        document = {"dns": "debug", "ipv4": ["test.example.com"]}
        if interval is not None:
            document["interval"] = interval
        with io.open(config_path, "w", encoding="utf-8") as config_file:
            config_file.write(json.dumps(document, ensure_ascii=False))
        return config_path

    def test_web_subcommand_defaults(self):
        """Parse the local-only dashboard defaults."""
        sys.argv = ["ddns", "web"]
        captured = [None]

        with patch("ddns.config.cli._handle_web_command") as handler:
            handler.side_effect = lambda args: captured.__setitem__(0, args)
            with self.assertRaises(SystemExit) as context:
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(context.exception.code, 0)
        self.assertEqual(captured[0]["host"], "127.0.0.1")
        self.assertEqual(captured[0]["port"], 9876)
        self.assertIsNone(captured[0]["interval"])
        self.assertFalse(captured[0]["open"])

    def test_interval_shorthand_starts_web_dashboard(self):
        """Infer Web mode when a top-level interval is provided."""
        sys.argv = ["ddns", "--interval", "12"]
        captured = [None]

        with patch("ddns.config.cli._handle_web_command") as handler:
            handler.side_effect = lambda args: captured.__setitem__(0, args)
            with self.assertRaises(SystemExit) as context:
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(context.exception.code, 0)
        self.assertEqual(captured[0]["command"], "web")
        self.assertEqual(captured[0]["interval"], 12)
        self.assertEqual(captured[0]["host"], "127.0.0.1")
        self.assertEqual(captured[0]["port"], 9876)

    def test_interval_shorthand_accepts_local_config(self):
        """Keep the common config-first command order for implicit Web mode."""
        sys.argv = ["ddns", "-c", "dashboard.json", "--interval=9"]
        captured = [None]

        with patch("ddns.config.cli._handle_web_command") as handler:
            handler.side_effect = lambda args: captured.__setitem__(0, args)
            with self.assertRaises(SystemExit):
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(captured[0]["config"], "dashboard.json")
        self.assertEqual(captured[0]["interval"], 9)

    def test_config_interval_starts_web_dashboard(self):
        """Infer Web mode from a root interval in one local config."""
        config_path = self._config_file(interval=7)
        sys.argv = ["ddns", "-c", config_path]
        captured = [None]

        with patch("ddns.config.cli._handle_web_command") as handler:
            handler.side_effect = lambda args: captured.__setitem__(0, args)
            with self.assertRaises(SystemExit) as context:
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(context.exception.code, 0)
        self.assertEqual(captured[0]["command"], "web")
        self.assertEqual(captured[0]["config"], config_path)
        self.assertEqual(captured[0]["interval"], 7)

    def test_default_config_interval_starts_web_dashboard(self):
        """Detect a root interval in the default local configuration."""
        config_path = self._config_file(interval=8)
        sys.argv = ["ddns"]
        captured = [None]

        with patch("ddns.config.cli.DEFAULT_CONFIG_PATHS", (config_path,)):
            with patch("ddns.config.cli._handle_web_command") as handler:
                handler.side_effect = lambda args: captured.__setitem__(0, args)
                with self.assertRaises(SystemExit):
                    load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(captured[0]["config"], config_path)
        self.assertEqual(captured[0]["interval"], 8)

    def test_cli_interval_overrides_config_interval(self):
        """Prefer an explicit CLI interval over the configured value."""
        config_path = self._config_file(interval=7)
        sys.argv = ["ddns", "-c", config_path, "--interval", "11"]
        captured = [None]

        with patch("ddns.config.cli._handle_web_command") as handler:
            handler.side_effect = lambda args: captured.__setitem__(0, args)
            with self.assertRaises(SystemExit):
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(captured[0]["interval"], 11)

    def test_interval_shorthand_rejects_multiple_configs(self):
        """Do not silently choose one editable file for Web mode."""
        first = self._config_file(interval=7)
        second = os.path.join(self.temp_dir, "second.json")
        with io.open(second, "w", encoding="utf-8") as config_file:
            config_file.write(json.dumps({"dns": "debug"}, ensure_ascii=False))
        sys.argv = ["ddns", "-c", first, "-c", second, "--interval", "11"]

        with patch("ddns.config.cli._handle_web_command") as handler:
            with self.assertRaises(SystemExit) as context:
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(context.exception.code, 2)
        handler.assert_not_called()

    def test_config_interval_rejects_multiple_configs(self):
        """Reject an implicit Web interval when multiple files were selected."""
        first = self._config_file(interval=7)
        second = os.path.join(self.temp_dir, "second.json")
        with io.open(second, "w", encoding="utf-8") as config_file:
            config_file.write(json.dumps({"dns": "debug"}, ensure_ascii=False))
        sys.argv = ["ddns", "-c", first, second]

        with patch("ddns.config.cli._handle_web_command") as handler:
            with self.assertRaises(SystemExit) as context:
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(context.exception.code, 2)
        handler.assert_not_called()

    def test_implicit_web_rejects_provider_cli_overrides(self):
        """Do not silently discard one-shot provider overrides in Web mode."""
        config_path = self._config_file(interval=7)
        sys.argv = ["ddns", "-c", config_path, "--token", "override"]

        with patch("ddns.config.cli._handle_web_command") as handler:
            with self.assertRaises(SystemExit) as context:
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(context.exception.code, 2)
        handler.assert_not_called()

    def test_interval_shorthand_rejects_inline_provider_config(self):
        """Require an editable local file instead of ignored provider flags."""
        sys.argv = ["ddns", "--interval", "7", "--dns", "debug", "--ipv4", "test.example.com"]

        with patch("ddns.config.cli._handle_web_command") as handler:
            with self.assertRaises(SystemExit) as context:
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(context.exception.code, 2)
        handler.assert_not_called()

    def test_explicit_web_rejects_repeated_configs(self):
        """Enforce one editable config for the explicit Web command."""
        sys.argv = ["ddns", "web", "-c", "first.json", "-c", "second.json"]

        with patch("ddns.config.cli._handle_web_command") as handler:
            with self.assertRaises(SystemExit) as context:
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(context.exception.code, 2)
        handler.assert_not_called()

    def test_config_without_interval_keeps_one_shot_mode(self):
        """Do not infer Web mode from an ordinary existing config."""
        config_path = self._config_file()
        sys.argv = ["ddns", "-c", config_path]

        with patch("ddns.config.cli._handle_web_command") as handler:
            config = load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        handler.assert_not_called()
        self.assertEqual(config["config"], [config_path])

    def test_new_config_action_does_not_infer_web_mode(self):
        """Keep configuration generation separate from configured Web mode."""
        existing_path = self._config_file(interval=8)
        new_path = os.path.join(self.temp_dir, "new.json")
        sys.argv = ["ddns", "--new-config", new_path]

        with patch("ddns.config.cli.DEFAULT_CONFIG_PATHS", (existing_path,)):
            with patch("ddns.config.cli._handle_web_command") as handler:
                with self.assertRaises(SystemExit):
                    load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        handler.assert_not_called()
        self.assertTrue(os.path.exists(new_path))

    def test_without_interval_keeps_one_shot_mode(self):
        """Preserve the existing one-shot CLI when no Web signal is present."""
        sys.argv = ["ddns", "--dns", "debug"]

        with patch("ddns.config.cli._handle_web_command") as handler:
            config = load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        handler.assert_not_called()
        self.assertEqual(config["dns"], "debug")
        self.assertNotIn("interval", config)

    def test_web_subcommand_options(self):
        """Parse explicit dashboard host, port, config, and browser options."""
        sys.argv = [
            "ddns",
            "web",
            "--config",
            "dashboard.json",
            "--host",
            "::1",
            "--port",
            "8765",
            "--interval",
            "12",
            "--open",
            "--debug",
        ]
        captured = [None]

        with patch("ddns.config.cli._handle_web_command") as handler:
            handler.side_effect = lambda args: captured.__setitem__(0, args)
            with self.assertRaises(SystemExit):
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(captured[0]["config"], "dashboard.json")
        self.assertEqual(captured[0]["host"], "::1")
        self.assertEqual(captured[0]["port"], 8765)
        self.assertEqual(captured[0]["interval"], 12)
        self.assertTrue(captured[0]["open"])
        self.assertTrue(captured[0]["debug"])

    def test_web_subcommand_rejects_public_host(self):
        """Reject dashboard bindings outside loopback addresses."""
        sys.argv = ["ddns", "web", "--host", "0.0.0.0"]

        with self.assertRaises(SystemExit) as context:
            load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(context.exception.code, 2)

    def test_web_subcommand_rejects_invalid_interval(self):
        """Require a positive, bounded internal scheduling interval."""
        sys.argv = ["ddns", "web", "--interval", "0"]

        with self.assertRaises(SystemExit) as context:
            load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(context.exception.code, 2)

    def test_interval_shorthand_rejects_invalid_interval(self):
        """Apply Web interval validation to the shorthand form."""
        sys.argv = ["ddns", "--interval", "0"]

        with self.assertRaises(SystemExit) as context:
            load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

        self.assertEqual(context.exception.code, 2)

    def test_config_interval_rejects_invalid_interval(self):
        """Reject an out-of-range interval discovered in JSON."""
        for invalid in (0, "5", 1.5, True):
            config_path = self._config_file(interval=invalid)
            sys.argv = ["ddns", "-c", config_path]

            with self.assertRaises(SystemExit) as context:
                load_config("Test DDNS", "Test doc", "1.0.0", "2026-01-01")

            self.assertEqual(context.exception.code, 2)

    @patch("ddns.web.serve")
    @patch("ddns.config.cli.load_env_config", return_value={})
    @patch("ddns.config.cli.basicConfig")
    def test_web_handler_starts_server(self, mock_basic_config, mock_load_env, mock_serve):
        """Pass parsed dashboard settings to the embedded server."""
        _handle_web_command(
            {
                "config": ["dashboard.json"],
                "host": "127.0.0.1",
                "port": 7654,
                "interval": 9,
                "open": True,
                "debug": False,
                "log_level": "INFO",
            }
        )

        mock_basic_config.assert_called_once()
        mock_load_env.assert_not_called()
        mock_serve.assert_called_once_with(
            config_path="dashboard.json", host="127.0.0.1", port=7654, open_browser=True, logger=mock.ANY, interval=9
        )

    @patch("ddns.web.serve")
    @patch("ddns.config.cli.basicConfig")
    def test_web_handler_reads_config_interval(self, mock_basic_config, mock_serve):
        """Use the root config interval when the CLI does not override it."""
        config_path = self._config_file(interval=13)

        _handle_web_command({"config": config_path, "host": "127.0.0.1", "port": 7654})

        mock_basic_config.assert_called_once()
        mock_serve.assert_called_once_with(
            config_path=config_path, host="127.0.0.1", port=7654, open_browser=False, logger=mock.ANY, interval=13
        )

    @patch("ddns.web.serve")
    @patch("ddns.config.cli.load_env_config", return_value={})
    @patch("ddns.config.cli.basicConfig")
    def test_web_handler_reads_default_config_interval(self, mock_basic_config, mock_load_env, mock_serve):
        """Honor a configured interval with an explicit bare Web command."""
        config_path = self._config_file(interval=17)

        with patch("ddns.config.cli.DEFAULT_CONFIG_PATHS", (config_path,)):
            _handle_web_command({"host": "127.0.0.1", "port": 7654})

        mock_basic_config.assert_called_once()
        mock_load_env.assert_called_once_with()
        mock_serve.assert_called_once_with(
            config_path=config_path, host="127.0.0.1", port=7654, open_browser=False, logger=mock.ANY, interval=17
        )

    @patch("ddns.web.serve")
    @patch("ddns.config.cli.load_env_config", return_value={"config": "environment.json"})
    @patch("ddns.config.cli.basicConfig")
    def test_web_handler_uses_environment_config_path(self, mock_basic_config, mock_load_env, mock_serve):
        """Use DDNS_CONFIG when the web command has no explicit path."""
        _handle_web_command({"host": "127.0.0.1", "port": 7654})

        mock_basic_config.assert_called_once()
        mock_load_env.assert_called_once_with()
        mock_serve.assert_called_once_with(
            config_path="environment.json", host="127.0.0.1", port=7654, open_browser=False, logger=mock.ANY, interval=5
        )

    @patch("ddns.web.serve")
    @patch("ddns.config.cli.load_env_config", return_value={"config": ["one.json", "two.json"]})
    def test_web_handler_rejects_multiple_environment_configs(self, mock_load_env, mock_serve):
        """Reject DDNS_CONFIG values that cannot be edited as one local file."""
        with self.assertRaises(SystemExit) as context:
            _handle_web_command({"host": "127.0.0.1", "port": 7654})

        self.assertEqual(context.exception.code, 2)
        mock_load_env.assert_called_once_with()
        mock_serve.assert_not_called()

    @patch("ddns.web.serve")
    @patch("ddns.config.cli.load_env_config", return_value={"config": "https://example.com/config.json"})
    def test_web_handler_rejects_remote_environment_config(self, mock_load_env, mock_serve):
        """Reject remote DDNS_CONFIG values because the dashboard can write files."""
        with self.assertRaises(SystemExit) as context:
            _handle_web_command({"host": "127.0.0.1", "port": 7654})

        self.assertEqual(context.exception.code, 2)
        mock_load_env.assert_called_once_with()
        mock_serve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
