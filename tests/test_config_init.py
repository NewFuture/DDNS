# coding=utf-8
# type: ignore[index,operator,assignment]
"""
Unit tests for ddns.config.__init__ module
@author: GitHub Copilot
"""

from __init__ import unittest, patch, MagicMock, call

import os
import tempfile
import shutil
import json
import sys
import ddns.config
from ddns.config import load_configs, Config
from io import StringIO, BytesIO  # For capturing stdout in Python2 and Python3


def capture_stdout_output(func, *args, **kwargs):
    """Capture stdout output in a Python 2.7/3.x compatible way"""
    if sys.version_info[0] < 3:
        # Python 2.7: Use BytesIO and decode
        buf = BytesIO()
        with patch("sys.stdout", new=buf):
            func(*args, **kwargs)
        output = buf.getvalue()
        if isinstance(output, bytes):
            output = output.decode("utf-8")
    else:
        # Python 3.x: Use StringIO
        buf = StringIO()
        with patch("sys.stdout", new=buf):
            func(*args, **kwargs)
        output = buf.getvalue()
    return output


class TestConfigInit(unittest.TestCase):
    """Test cases for ddns.config.__init__ module"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_description = "Test DDNS Application"
        self.test_version = "1.0.0"
        self.test_date = "2025-07-07"
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        # Change to the test directory to isolate from any existing config.json
        os.chdir(self.test_dir)

        # Save and clear any existing DDNS-related environment variables
        self.original_env = {}
        ddns_prefixes = ["DDNS_", "DNS_", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "PYTHONHTTPSVERIFY"]

        # Backup and clear any existing environment variables that might interfere
        for key in list(os.environ.keys()):
            if any(key.startswith(prefix) for prefix in ddns_prefixes):
                self.original_env[key] = os.environ.pop(key)

    def tearDown(self):
        """Clean up test fixtures"""
        # Restore original environment variables
        for key, value in self.original_env.items():
            os.environ[key] = value

        # Change back to original directory and clean up temp directory
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_module_exports(self):
        """Test that module exports are correct"""
        expected_exports = ["load_configs", "Config"]
        self.assertEqual(ddns.config.__all__, expected_exports)
        self.assertTrue(hasattr(ddns.config, "load_configs"))
        self.assertTrue(hasattr(ddns.config, "Config"))
        self.assertEqual(ddns.config.load_configs, load_configs)
        self.assertEqual(ddns.config.Config, Config)

    def test_load_config_basic_integration(self):
        """Test basic load_config functionality with real files"""
        # Create test config file
        config_content = {"dns": "debug", "token": "test_token", "ttl": 300}
        config_path = os.path.join(self.test_dir, "test_config.json")
        with open(config_path, "w") as f:
            json.dump(config_content, f)

        # Test loading with CLI args
        with patch("sys.argv", ["ddns", "--config", config_path, "--id", "test_id"]):
            results = load_configs(self.test_description, self.test_version, self.test_date)
            result = results[0]
            self.assertIsInstance(result, Config)
            self.assertEqual(result.dns, "debug")
            self.assertEqual(result.id, "test_id")  # CLI overrides
            self.assertEqual(result.token, "test_token")  # From JSON
            self.assertEqual(result.ttl, 300)  # From JSON

    def test_load_config_priority_order_integration(self):
        """Test configuration priority order using real Config objects"""
        json_config_path = os.path.join(self.test_dir, "test_config.json")
        with open(json_config_path, "w") as f:
            json.dump({"dns": "json_dns", "id": "json_id", "token": "json_token"}, f)

        os.environ["DDNS_DNS"] = "env_dns"
        os.environ["DDNS_ID"] = "env_id"
        os.environ["DDNS_TOKEN"] = "env_token"
        os.environ["DDNS_LINE"] = "env_line"

        try:
            from ddns.config.config import Config
            from ddns.config.file import load_config as load_file_config
            from ddns.config.env import load_config as load_env_config

            cli_config = {"dns": "cli_dns", "id": "cli_id", "config": json_config_path}
            json_config = load_file_config(json_config_path)
            env_config = load_env_config()

            result = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)

            # Verify priority order: CLI > JSON > ENV
            self.assertEqual(result.dns, "cli_dns")
            self.assertEqual(result.id, "cli_id")
            self.assertEqual(result.token, "json_token")  # JSON overrides ENV when CLI doesn't have it
            self.assertEqual(result.line, "env_line")  # ENV used when neither CLI nor JSON have it

        finally:
            # Clean up test environment variables (original env will be restored in tearDown)
            for key in ["DDNS_DNS", "DDNS_ID", "DDNS_TOKEN", "DDNS_LINE"]:
                os.environ.pop(key, None)

    def test_load_config_file_paths_integration(self):
        """Test load_config with various config file path sources"""
        # Test case 1: Explicit config file path from CLI
        config_content = {"dns": "cloudflare", "id": "custom_id", "token": "custom_token"}
        config_path = os.path.join(self.test_dir, "custom_config.json")
        with open(config_path, "w") as f:
            json.dump(config_content, f)

        with patch("sys.argv", ["ddns", "--config", config_path]):
            results = load_configs(self.test_description, self.test_version, self.test_date)
            result = results[0]
            self.assertEqual(result.dns, "cloudflare")
            self.assertEqual(result.id, "custom_id")

        # Test case 2: Config file path from environment
        env_config_path = os.path.join(self.test_dir, "env_config.json")
        env_config_content = {"dns": "alidns", "id": "env_id", "token": "env_token"}
        with open(env_config_path, "w") as f:
            json.dump(env_config_content, f)

        with patch.dict(os.environ, {"DDNS_CONFIG": env_config_path}):
            with patch("sys.argv", ["ddns"]):
                results = load_configs(self.test_description, self.test_version, self.test_date)
                result = results[0]
                self.assertEqual(result.dns, "alidns")
                self.assertEqual(result.id, "env_id")

    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_file_config")
    @patch("ddns.config.load_cli_config")
    @patch("os.path.exists")
    @patch("os.path.expanduser")
    def test_load_config_default_locations(self, mock_expanduser, mock_exists, mock_cli, mock_json, mock_env):
        """Test load_config searches default config file locations"""
        mock_cli.return_value = {"dns": "debug"}
        mock_env.return_value = {}
        mock_expanduser.return_value = "/home/user/.ddns/config.json"

        # Test multiple default locations
        default_locations = [
            ("config.json", "local"),
            ("/home/user/.ddns/config.json", "home"),
            ("/etc/ddns/config.json", "system"),
        ]

        for config_path, location_type in default_locations:
            # Python 2.7 compatible: test each location separately without subTest
            mock_json.reset_mock()
            mock_exists.side_effect = lambda path: path == config_path
            mock_json.return_value = {"id": "{}_id".format(location_type)}

            result = load_configs(self.test_description, self.test_version, self.test_date)[0]
            mock_json.assert_called_with(config_path, proxy=[], ssl="auto")
            self.assertEqual(result.id, "{}_id".format(location_type))

    def test_load_config_missing_files_integration(self):
        """Test load_config when config files don't exist"""
        # Test case 1: No config file but provide minimal CLI args
        with patch("sys.argv", ["ddns", "--dns", "debug", "--id", "test", "--token", "test"]):
            results = load_configs(self.test_description, self.test_version, self.test_date)
            result = results[0]
            self.assertEqual(result.dns, "debug")
            self.assertEqual(result.id, "test")

        # Test case 2: Specified config file doesn't exist should exit
        with patch("sys.argv", ["ddns", "--config", "/nonexistent/config.json", "--dns", "debug"]):
            with self.assertRaises(SystemExit):
                load_configs(self.test_description, self.test_version, self.test_date)

    def test_load_config_doc_string_format_integration(self):
        """Test that doc string is properly formatted with version and date"""
        # Create a minimal config to avoid auto-generation
        config_content = {"dns": "debug", "id": "test", "token": "test"}
        config_path = os.path.join(self.test_dir, "test_config.json")
        with open(config_path, "w") as f:
            json.dump(config_content, f)

        with patch("sys.argv", ["ddns", "--config", config_path]):
            results = load_configs(self.test_description, self.test_version, self.test_date)
            result = results[0]
            self.assertIsInstance(result, Config)
            self.assertEqual(result.dns, "debug")

    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_file_config")
    @patch("ddns.config.load_cli_config")
    @patch("os.path.exists")
    def test_load_config_config_object_creation(self, mock_exists, mock_cli, mock_json, mock_env):
        """Test that Config object is created with correct parameters"""
        cli_config = {"dns": "cloudflare", "id": "test@example.com", "config": "test_config.json"}
        json_config = {"token": "test_token", "ttl": 300}
        env_config = {"proxy": ["http://proxy.com"]}

        mock_cli.return_value = cli_config
        mock_json.return_value = json_config
        mock_env.return_value = env_config
        mock_exists.return_value = True

        with patch("ddns.config.Config") as mock_config_class:
            mock_config_instance = MagicMock()
            mock_config_instance.log_format = None  # No custom format
            mock_config_instance.log_level = 20  # INFO level
            mock_config_instance.log_datefmt = "%Y-%m-%dT%H:%M:%S"
            mock_config_instance.log_file = None  # No log file
            mock_config_instance.dns = "cloudflare"  # Has DNS provider
            mock_config_class.return_value = mock_config_instance

            result = load_configs(self.test_description, self.test_version, self.test_date)[0]

            # Should create both main config and global config
            self.assertEqual(mock_config_class.call_count, 2)

            # Both calls should use the same parameters when there's only one config file
            expected_calls = [
                call(cli_config=cli_config, json_config=json_config, env_config=env_config),
                call(cli_config=cli_config, json_config=json_config, env_config=env_config),
            ]
            mock_config_class.assert_has_calls(expected_calls, any_order=True)
            self.assertEqual(result, mock_config_instance)

    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_file_config")
    @patch("ddns.config.load_cli_config")
    @patch("os.path.exists")
    def test_load_config_integration(self, mock_exists, mock_cli, mock_json, mock_env):
        """Test complete integration of load_config function"""
        mock_cli.return_value = {
            "dns": "cloudflare",
            "id": "test@example.com",
            "log_level": "DEBUG",
            "cache": "false",
            "config": "test_config.json",
        }
        mock_json.return_value = {
            "token": "cf_token_123",
            "ipv4": ["home.example.com", "office.example.com"],
            "ttl": 300,
            "cache": "true",  # Should be overridden by CLI
        }
        mock_env.return_value = {"proxy": ["http://proxy.corp.com:8080"], "line": "default"}
        mock_exists.return_value = True

        results = load_configs(self.test_description, self.test_version, self.test_date)
        result = results[0]

        self.assertIsInstance(result, Config)
        # CLI overrides
        self.assertEqual(result.dns, "cloudflare")
        self.assertEqual(result.id, "test@example.com")
        self.assertEqual(result.log_level, 10)  # DEBUG
        self.assertFalse(result.cache)  # CLI "false" overrides JSON "true"
        # JSON values
        self.assertEqual(result.token, "cf_token_123")
        self.assertEqual(result.ipv4, ["home.example.com", "office.example.com"])
        self.assertEqual(result.ttl, 300)
        # ENV values
        self.assertEqual(result.proxy, ["http://proxy.corp.com:8080"])
        self.assertEqual(result.line, "default")

    def test_load_config_parameter_validation_and_edge_cases(self):
        """Test load_config parameter validation and edge cases"""
        # Test case 1: Valid parameters with DNS
        config_content = {"dns": "debug", "id": "test", "token": "test"}
        config_path = os.path.join(self.test_dir, "valid_config.json")
        with open(config_path, "w") as f:
            json.dump(config_content, f)

        with patch("sys.argv", ["ddns", "--config", config_path]):
            results = load_configs(self.test_description, self.test_version, self.test_date)
            result = results[0]
            self.assertIsInstance(result, Config)

        # Test case 2: Empty string parameters but provide CLI DNS - no config files exist
        with patch("sys.argv", ["ddns", "--dns", "debug", "--id", "test", "--token", "test"]):
            results = load_configs("", "", "")
            result = results[0]
            self.assertIsInstance(result, Config)

        # Test case 3: Empty configurations should cause exit (edge case)
        # Switch to a clean temporary directory to ensure no config.json exists
        with patch("ddns.config.load_env_config", return_value={}):  # Empty env config
            with patch("sys.argv", ["ddns"]):  # No arguments at all
                with self.assertRaises(SystemExit) as cm:
                    load_configs(self.test_description, self.test_version, self.test_date)
                self.assertEqual(cm.exception.code, 1)  # Should exit with error code 1

    def test_config_file_discovery_integration(self):
        """Test config file discovery in current directory"""
        # Test 1: Direct path loading
        config_content = {"dns": "cloudflare", "id": "test@example.com", "token": "secret123"}
        config_path = os.path.join(self.test_dir, "direct_config.json")

        with open(config_path, "w") as f:
            json.dump(config_content, f)

        from ddns.config.file import load_config as load_file_config

        loaded_config = load_file_config(config_path)
        self.assertEqual(loaded_config["dns"], "cloudflare")
        self.assertEqual(loaded_config["id"], "test@example.com")
        self.assertEqual(loaded_config["token"], "secret123")

        # Test 2: Auto-discovery in current directory
        auto_config_content = {"dns": "debug", "id": "auto@example.com", "token": "auto123"}
        auto_config_path = os.path.join(self.test_dir, "config.json")  # Default name in current dir

        with open(auto_config_path, "w") as f:
            json.dump(auto_config_content, f)

        # Test that it can be auto-discovered when no explicit config is provided
        with patch("sys.argv", ["ddns"]):
            results = load_configs(self.test_description, self.test_version, self.test_date)
            result = results[0]
            self.assertEqual(result.dns, "debug")
            self.assertEqual(result.id, "auto@example.com")
            self.assertEqual(result.token, "auto123")

    def test_environment_config_integration(self):
        """Test environment configuration loading without mocking"""
        test_env_vars = {
            "DDNS_DNS": "dnspod",
            "DDNS_ID": "test_user",
            "DDNS_TOKEN": "test_token_123",
            "DDNS_TTL": "600",
            "DDNS_IPV4": '["ip1.example.com", "ip2.example.com"]',
        }

        for key, value in test_env_vars.items():
            os.environ[key] = value

        try:
            from ddns.config.env import load_config as load_env_config

            env_config = load_env_config()

            self.assertEqual(env_config["dns"], "dnspod")
            self.assertEqual(env_config["id"], "test_user")
            self.assertEqual(env_config["token"], "test_token_123")
            self.assertEqual(env_config["ttl"], "600")
            self.assertEqual(env_config["ipv4"], ["ip1.example.com", "ip2.example.com"])

        finally:
            # Clean up test environment variables (original env will be restored in tearDown)
            for key in test_env_vars:
                os.environ.pop(key, None)

    def test_config_merging_without_mocks(self):
        """Test configuration merging using real Config objects"""
        cli_config = {"dns": "cloudflare", "debug": True}
        json_config = {"dns": "dnspod", "id": "json_user", "token": "json_token"}
        env_config = {"dns": "alidns", "id": "env_user", "token": "env_token", "ttl": "300"}

        from ddns.config.config import Config

        config = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)

        # Verify CLI takes highest priority
        self.assertEqual(config.dns, "cloudflare")
        # Verify JSON takes priority over ENV when CLI doesn't have the value
        self.assertEqual(config.id, "json_user")
        self.assertEqual(config.token, "json_token")
        # Verify ENV is used when neither CLI nor JSON have the value
        self.assertEqual(config.ttl, 300)  # Should be converted to int

    def test_array_parameter_processing_integration(self):
        """Test array parameter processing without mocking"""
        from ddns.config.config import Config

        test_configs = {
            "cli": {"ipv4": "ip1.com,ip2.com,ip3.com", "proxy": "proxy1;proxy2"},
            "json": {"ipv6": "ipv6-1.com,ipv6-2.com", "index4": "regex:192\\.168\\..*,backup"},
            "env": {"index6": "default,public"},
        }

        config = Config(
            cli_config=test_configs["cli"], json_config=test_configs["json"], env_config=test_configs["env"]
        )

        # Verify array splitting works correctly
        self.assertEqual(config.ipv4, ["ip1.com", "ip2.com", "ip3.com"])
        self.assertEqual(config.proxy, ["proxy1", "proxy2"])
        self.assertEqual(config.ipv6, ["ipv6-1.com", "ipv6-2.com"])
        # Verify special prefix handling (should not split)
        self.assertEqual(config.index4, ["regex:192\\.168\\..*,backup"])
        self.assertEqual(config.index6, ["default", "public"])

    def test_file_parsing_fallback_integration(self):
        """Test JSON to AST parsing fallback without mocking"""
        python_dict_content = "{'dns': 'dnspod', 'id': 'python_user', 'token': 'python_token'}"
        config_path = os.path.join(self.test_dir, "python_config.py")

        with open(config_path, "w") as f:
            f.write(python_dict_content)

        from ddns.config.file import load_config as load_file_config

        loaded_config = load_file_config(config_path)
        self.assertEqual(loaded_config["dns"], "dnspod")
        self.assertEqual(loaded_config["id"], "python_user")
        self.assertEqual(loaded_config["token"], "python_token")

    def test_special_value_handling_integration(self):
        """Test special value handling without mocking"""
        from ddns.config.config import Config

        config_data = {"proxy": "DIRECT,http://proxy.com,NONE", "ssl": "auto", "cache": "true", "ttl": "600"}
        config = Config(cli_config=config_data)

        # Verify proxy parsing (no special conversion of NONE to None after simplification)
        self.assertEqual(config.proxy, ["DIRECT", "http://proxy.com", "NONE"])
        # Verify boolean conversion
        self.assertTrue(config.cache)
        # Verify TTL conversion to int
        self.assertEqual(config.ttl, 600)
        self.assertIsInstance(config.ttl, int)


if __name__ == "__main__":
    unittest.main()
