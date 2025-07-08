# coding=utf-8
"""
Unit tests for ddns.config.__init__ module

This test suite provides comprehensive coverage for the configuration loading
functionality in the ddns.config package, including the main load_config function
and its integration with CLI, JSON, and environment configuration sources.

Test Coverage:
- load_config function with different configuration sources
- Configuration merging priority (CLI > JSON > ENV)
- JSON configuration file discovery in default locations
- --new-config flag handling and configuration generation
- Error handling for missing or invalid configuration files
- Module exports (__all__ validation)

@author: GitHub Copilot
"""

import unittest
import sys
import os
import tempfile
import shutil
import json

# Add the parent directory to the path so we can import the ddns module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_test import patch, MagicMock  # noqa: E402

import ddns.config  # noqa: E402
from ddns.config import load_config, Config  # noqa: E402


class TestConfigInit(unittest.TestCase):
    """Test cases for ddns.config.__init__ module"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_description = "Test DDNS Application"
        self.test_version = "1.0.0"
        self.test_date = "2025-07-07"

        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up test fixtures"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_module_exports(self):
        """Test that module exports are correct"""
        expected_exports = ["load_config", "Config"]
        self.assertEqual(ddns.config.__all__, expected_exports)

        # Test that exported items are actually available
        self.assertTrue(hasattr(ddns.config, "load_config"))
        self.assertTrue(hasattr(ddns.config, "Config"))
        self.assertEqual(ddns.config.load_config, load_config)
        self.assertEqual(ddns.config.Config, Config)

    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_file_config")
    @patch("ddns.config.load_cli_config")
    def test_load_config_basic(self, mock_cli, mock_json, mock_env):
        """Test basic load_config functionality"""
        # Setup mocks
        mock_cli.return_value = {"dns": "debug", "id": "test_id"}
        mock_json.return_value = {"token": "test_token", "ttl": 300}
        mock_env.return_value = {"proxy": ["http://proxy.com"]}

        # Call load_config
        result = load_config(self.test_description, self.test_version, self.test_date)

        # Verify result
        self.assertIsInstance(result, Config)
        self.assertEqual(result.dns, "debug")
        self.assertEqual(result.id, "test_id")
        self.assertEqual(result.token, "test_token")
        self.assertEqual(result.ttl, 300)
        self.assertEqual(result.proxy, ["http://proxy.com"])

        # Verify CLI was called with correct arguments
        mock_cli.assert_called_once()
        args = mock_cli.call_args[0]
        self.assertEqual(args[0], self.test_description)
        self.assertIn("v1.0.0@2025-07-07", args[1])  # doc string
        self.assertEqual(args[2], self.test_version)
        self.assertEqual(args[3], self.test_date)

    def test_load_config_priority_order_integration(self):
        """Test configuration priority order using real Config objects"""
        # Create test configuration files
        json_config_path = os.path.join(self.test_dir, "test_config.json")
        with open(json_config_path, "w") as f:
            json.dump({"dns": "json_dns", "id": "json_id", "token": "json_token"}, f)

        # Set environment variables
        os.environ["DDNS_DNS"] = "env_dns"
        os.environ["DDNS_ID"] = "env_id"
        os.environ["DDNS_TOKEN"] = "env_token"
        os.environ["DDNS_LINE"] = "env_line"

        try:
            # Test CLI config takes priority over JSON and ENV
            from ddns.config.config import Config
            from ddns.config.file import load_config as load_file_config
            from ddns.config.env import load_config as load_env_config

            cli_config = {"dns": "cli_dns", "id": "cli_id", "config": json_config_path}
            json_config = load_file_config(json_config_path)
            env_config = load_env_config()

            result = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)

            # Verify priority order
            self.assertEqual(result.dns, "cli_dns")  # CLI overrides JSON and ENV
            self.assertEqual(result.id, "cli_id")  # CLI overrides JSON and ENV
            self.assertEqual(result.token, "json_token")  # JSON overrides ENV when CLI doesn't have it
            self.assertEqual(result.line, "env_line")  # ENV used when neither CLI nor JSON have it

        finally:
            # Clean up environment variables
            for key in ["DDNS_DNS", "DDNS_ID", "DDNS_TOKEN", "DDNS_LINE"]:
                os.environ.pop(key, None)

    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_file_config")
    @patch("ddns.config.load_cli_config")
    @patch("os.path.exists")
    def test_load_config_with_config_file_path(self, mock_exists, mock_cli, mock_json, mock_env):
        """Test load_config with explicit config file path"""
        # Setup mocks
        mock_cli.return_value = {"config": "/custom/config.json", "dns": "cloudflare"}
        mock_env.return_value = {}
        mock_exists.return_value = True
        mock_json.return_value = {"id": "custom_id", "token": "custom_token"}

        # Call load_config
        result = load_config(self.test_description, self.test_version, self.test_date)

        # Verify JSON was loaded from specified path
        mock_json.assert_called_once_with("/custom/config.json")
        self.assertEqual(result.dns, "cloudflare")
        self.assertEqual(result.id, "custom_id")
        self.assertEqual(result.token, "custom_token")

    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_file_config")
    @patch("ddns.config.load_cli_config")
    @patch("os.path.exists")
    def test_load_config_with_env_config_file_path(self, mock_exists, mock_cli, mock_json, mock_env):
        """Test load_config with config file path from environment"""
        # Setup mocks
        mock_cli.return_value = {"dns": "alidns"}
        mock_env.return_value = {"config": "/env/config.json"}
        mock_exists.return_value = True
        mock_json.return_value = {"id": "env_id", "token": "env_token"}

        # Call load_config
        result = load_config(self.test_description, self.test_version, self.test_date)

        # Verify JSON was loaded from environment path
        mock_json.assert_called_once_with("/env/config.json")
        self.assertEqual(result.dns, "alidns")
        self.assertEqual(result.id, "env_id")
        self.assertEqual(result.token, "env_token")

    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_file_config")
    @patch("ddns.config.load_cli_config")
    @patch("os.path.exists")
    @patch("os.path.expanduser")
    def test_load_config_default_locations(self, mock_expanduser, mock_exists, mock_cli, mock_json, mock_env):
        """Test load_config searches default config file locations"""
        # Setup mocks
        mock_cli.return_value = {"dns": "debug"}
        mock_env.return_value = {}
        mock_expanduser.return_value = "/home/user/.ddns/config.json"

        # Test case 1: config.json exists in current directory
        mock_exists.side_effect = lambda path: path == "config.json"
        mock_json.return_value = {"id": "local_id"}

        result = load_config(self.test_description, self.test_version, self.test_date)
        mock_json.assert_called_with("config.json")
        self.assertEqual(result.id, "local_id")

        # Reset mocks
        mock_json.reset_mock()

        # Test case 2: config.json exists in home directory
        mock_exists.side_effect = lambda path: path == "/home/user/.ddns/config.json"
        mock_json.return_value = {"id": "home_id"}

        result = load_config(self.test_description, self.test_version, self.test_date)
        mock_json.assert_called_with("/home/user/.ddns/config.json")
        self.assertEqual(result.id, "home_id")

        # Reset mocks
        mock_json.reset_mock()

        # Test case 3: config.json exists in system directory
        mock_exists.side_effect = lambda path: path == "/etc/ddns/config.json"
        mock_json.return_value = {"id": "system_id"}

        result = load_config(self.test_description, self.test_version, self.test_date)
        mock_json.assert_called_with("/etc/ddns/config.json")
        self.assertEqual(result.id, "system_id")

    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_file_config")
    @patch("ddns.config.load_cli_config")
    @patch("os.path.exists")
    def test_load_config_no_config_file(self, mock_exists, mock_cli, mock_json, mock_env):
        """Test load_config when no config file exists"""
        # Setup mocks
        mock_cli.return_value = {"dns": "debug"}
        mock_env.return_value = {}
        mock_exists.return_value = False  # No config file exists

        # Call load_config
        result = load_config(self.test_description, self.test_version, self.test_date)

        # Verify JSON was not loaded
        mock_json.assert_not_called()
        self.assertEqual(result.dns, "debug")
        self.assertIsNone(result.id)  # Should use default values

    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_file_config")
    @patch("ddns.config.load_cli_config")
    @patch("os.path.exists")
    def test_load_config_nonexistent_config_file(self, mock_exists, mock_cli, mock_json, mock_env):
        """Test load_config with specified config file that doesn't exist"""
        # Setup mocks
        mock_cli.return_value = {"config": "/nonexistent/config.json", "dns": "debug"}
        mock_env.return_value = {}
        mock_exists.return_value = False

        # Call load_config
        result = load_config(self.test_description, self.test_version, self.test_date)

        # Verify JSON was not loaded
        mock_json.assert_not_called()
        self.assertEqual(result.dns, "debug")

    @patch("ddns.config.save_json")
    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_cli_config")
    @patch("sys.exit")
    def test_load_config_new_config_flag(self, mock_exit, mock_cli, mock_env, mock_save_json):
        """Test load_config with --new-config flag"""
        # Setup mocks
        mock_cli.return_value = {
            "new_config": True,
            "dns": "cloudflare",
            "id": "test@example.com",
            "token": "test_token",
        }
        mock_env.return_value = {}
        mock_save_json.return_value = True

        # Call load_config
        with patch("sys.stdout.write") as mock_stdout:
            load_config(self.test_description, self.test_version, self.test_date)

        # Verify config was saved
        mock_save_json.assert_called_once()
        args = mock_save_json.call_args[0]
        config_path = args[0]
        config_data = args[1]

        self.assertEqual(config_path, "config.json")
        self.assertEqual(config_data["dns"], "cloudflare")
        self.assertEqual(config_data["id"], "test@example.com")
        self.assertEqual(config_data["token"], "test_token")

        # Verify default values were added
        self.assertEqual(config_data["ipv4"], ["ddns.newfuture.cc"])
        self.assertEqual(config_data["index4"], ["default"])

        # Verify output and exit
        mock_stdout.assert_called_once_with("config.json is generated.\n")
        mock_exit.assert_called_once_with(0)

    @patch("ddns.config.save_json")
    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_cli_config")
    @patch("sys.exit")
    def test_load_config_new_config_flag_with_custom_path(self, mock_exit, mock_cli, mock_env, mock_save_json):
        """Test load_config with --new-config flag and custom config path"""
        # Setup mocks
        mock_cli.return_value = {"new_config": "custom-config.json", "dns": "debug"}
        mock_env.return_value = {}
        mock_save_json.return_value = True

        # Call load_config
        with patch("sys.stdout.write") as mock_stdout:
            load_config(self.test_description, self.test_version, self.test_date)

        # Verify config was saved to custom path
        mock_save_json.assert_called_once()
        args = mock_save_json.call_args[0]
        config_path = args[0]
        config_data = args[1]

        self.assertEqual(config_path, "custom-config.json")
        self.assertEqual(config_data["dns"], "debug")

        # Verify default values were added
        self.assertEqual(config_data["id"], "YOUR ID or EMAIL for DNS Provider")
        self.assertEqual(config_data["token"], "YOUR TOKEN or KEY for DNS Provider")
        self.assertEqual(config_data["ipv4"], ["ddns.newfuture.cc"])
        self.assertEqual(config_data["index4"], ["default"])

        # Verify output and exit
        mock_stdout.assert_called_once_with("custom-config.json is generated.\n")
        mock_exit.assert_called_once_with(0)

    @patch("ddns.config.save_json")
    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_cli_config")
    @patch("sys.exit")
    def test_load_config_new_config_flag_with_existing_values(self, mock_exit, mock_cli, mock_env, mock_save_json):
        """Test load_config with --new-config flag and existing ipv4/index4 values"""
        # Setup mocks
        mock_cli.return_value = {
            "new_config": True,
            "dns": "cloudflare",
            "ipv4": ["my.domain.com", "my2.domain.com"],
            "index4": ["custom", "rule"],
        }
        mock_env.return_value = {}
        mock_save_json.return_value = True

        # Call load_config
        with patch("sys.stdout.write"):
            load_config(self.test_description, self.test_version, self.test_date)

        # Verify existing values were preserved
        mock_save_json.assert_called_once()
        config_data = mock_save_json.call_args[0][1]

        self.assertEqual(config_data["ipv4"], ["my.domain.com", "my2.domain.com"])
        self.assertEqual(config_data["index4"], ["custom", "rule"])

        mock_exit.assert_called_once_with(0)

    @patch("ddns.config.save_json")
    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_cli_config")
    @patch("sys.exit")
    def test_load_config_new_config_flag_save_failure(self, mock_exit, mock_cli, mock_env, mock_save_json):
        """Test load_config with --new-config flag when save fails"""
        # Setup mocks
        mock_cli.return_value = {"new_config": True, "dns": "debug"}
        mock_env.return_value = {}
        mock_save_json.return_value = False  # Save fails

        # Call load_config
        with patch("sys.stdout.write") as mock_stdout:
            load_config(self.test_description, self.test_version, self.test_date)

        # Verify no success message was printed
        mock_stdout.assert_not_called()
        mock_exit.assert_called_once_with(0)

    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_file_config")
    @patch("ddns.config.load_cli_config")
    def test_load_config_doc_string_format(self, mock_cli, mock_json, mock_env):
        """Test that doc string is properly formatted with version and date"""
        # Setup mocks
        mock_cli.return_value = {"dns": "debug"}
        mock_env.return_value = {}
        mock_json.return_value = {}

        # Call load_config
        load_config(self.test_description, self.test_version, self.test_date)

        # Verify CLI was called with properly formatted doc string
        mock_cli.assert_called_once()
        doc_string = mock_cli.call_args[0][1]

        self.assertIn("v1.0.0@2025-07-07", doc_string)
        self.assertIn("https://ddns.newfuture.cc/", doc_string)
        self.assertIn("https://github.com/NewFuture/DDNS/issues", doc_string)
        self.assertIn("MIT License", doc_string)

    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_file_config")
    @patch("ddns.config.load_cli_config")
    def test_load_config_config_object_creation(self, mock_cli, mock_json, mock_env):
        """Test that Config object is created with correct parameters"""
        # Setup mocks
        cli_config = {"dns": "cloudflare", "id": "test@example.com"}
        json_config = {"token": "test_token", "ttl": 300}
        env_config = {"proxy": ["http://proxy.com"]}

        mock_cli.return_value = cli_config
        mock_json.return_value = json_config
        mock_env.return_value = env_config

        # Call load_config
        with patch("ddns.config.Config") as mock_config_class:
            mock_config_instance = MagicMock()
            mock_config_class.return_value = mock_config_instance

            result = load_config(self.test_description, self.test_version, self.test_date)

            # Verify Config was created with correct parameters
            mock_config_class.assert_called_once_with(
                cli_config=cli_config, json_config=json_config, env_config=env_config
            )
            self.assertEqual(result, mock_config_instance)

    @patch("ddns.config.load_env_config")
    @patch("ddns.config.load_file_config")
    @patch("ddns.config.load_cli_config")
    def test_load_config_integration(self, mock_cli, mock_json, mock_env):
        """Test complete integration of load_config function"""
        # Setup realistic configuration scenario
        mock_cli.return_value = {
            "dns": "cloudflare",
            "id": "test@example.com",
            "log_level": "DEBUG",
            "cache": "false",
        }
        mock_json.return_value = {
            "token": "cf_token_123",
            "ipv4": ["home.example.com", "office.example.com"],
            "ttl": 300,
            "cache": "true",  # Should be overridden by CLI
        }
        mock_env.return_value = {"proxy": ["http://proxy.corp.com:8080"], "line": "default"}

        # Call load_config
        result = load_config(self.test_description, self.test_version, self.test_date)

        # Verify complete configuration integration
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

    def test_load_config_parameter_validation(self):
        """Test load_config parameter validation"""
        # Test with proper mocking to avoid actual CLI parsing
        with patch("ddns.config.load_cli_config") as mock_cli:
            with patch("ddns.config.load_env_config") as mock_env:
                with patch("ddns.config.load_file_config") as mock_json:
                    mock_cli.return_value = {"dns": "debug"}
                    mock_env.return_value = {}
                    mock_json.return_value = {}

                    # Test with valid parameters - should work properly
                    result = load_config(self.test_description, self.test_version, self.test_date)
                    self.assertIsInstance(result, Config)

                    # Test with empty string parameters
                    result = load_config("", "", "")
                    self.assertIsInstance(result, Config)

    def test_load_config_edge_cases(self):
        """Test load_config edge cases"""
        with patch("ddns.config.load_cli_config") as mock_cli:
            with patch("ddns.config.load_env_config") as mock_env:
                with patch("ddns.config.load_file_config") as mock_json:
                    # Test with empty configurations
                    mock_cli.return_value = {}
                    mock_env.return_value = {}
                    mock_json.return_value = {}

                    result = load_config(self.test_description, self.test_version, self.test_date)

                    # Should create Config with defaults
                    self.assertIsInstance(result, Config)
                    self.assertEqual(result.dns, "debug")  # Default value
                    self.assertIsNone(result.id)  # Default value
                    self.assertIsNone(result.token)  # Default value

    def test_config_file_discovery_integration(self):
        """Test config file discovery without mocking file system"""
        # Create a config file in the test directory
        config_content = {"dns": "cloudflare", "id": "test@example.com", "token": "secret123"}
        config_path = os.path.join(self.test_dir, "config.json")

        with open(config_path, "w") as f:
            json.dump(config_content, f)

        # Change to test directory so config.json is found
        os.chdir(self.test_dir)

        # Test direct Config creation with file loading
        from ddns.config.file import load_config as load_file_config

        loaded_config = load_file_config(config_path)
        self.assertEqual(loaded_config["dns"], "cloudflare")
        self.assertEqual(loaded_config["id"], "test@example.com")
        self.assertEqual(loaded_config["token"], "secret123")

    def test_environment_config_integration(self):
        """Test environment configuration loading without mocking"""
        # Set real environment variables
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
            # Clean up environment variables
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

        # Verify CLI-specific values
        self.assertTrue(hasattr(config, "dns"))

    def test_array_parameter_processing_integration(self):
        """Test array parameter processing without mocking"""
        from ddns.config.config import Config

        # Test various array configurations
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
        # Create a file with Python dict syntax (not valid JSON)
        python_dict_content = "{'dns': 'dnspod', 'id': 'python_user', 'token': 'python_token'}"
        config_path = os.path.join(self.test_dir, "python_config.py")

        with open(config_path, "w") as f:
            f.write(python_dict_content)

        from ddns.config.file import load_config as load_file_config

        # Should fall back to AST parsing
        loaded_config = load_file_config(config_path)
        self.assertEqual(loaded_config["dns"], "dnspod")
        self.assertEqual(loaded_config["id"], "python_user")
        self.assertEqual(loaded_config["token"], "python_token")

    def test_special_value_handling_integration(self):
        """Test special value handling without mocking"""
        from ddns.config.config import Config

        config_data = {"proxy": "DIRECT,http://proxy.com,NONE", "ssl": "auto", "cache": "true", "ttl": "600"}

        config = Config(cli_config=config_data)

        # Verify proxy special value handling
        self.assertEqual(config.proxy, [None, "http://proxy.com", None])

        # Verify boolean conversion
        self.assertTrue(config.cache)

        # Verify TTL conversion to int
        self.assertEqual(config.ttl, 600)
        self.assertIsInstance(config.ttl, int)


if __name__ == "__main__":
    unittest.main()
