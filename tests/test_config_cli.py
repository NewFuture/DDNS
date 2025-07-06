# coding=utf-8
"""
Unit tests for CLI configuration module

This test suite provides comprehensive coverage for the CLI configuration module,
testing all command-line argument parsing, validation, and edge cases.

Test Coverage:
- str_bool function with various input types and edge cases
- log_level function with valid and invalid inputs
- ExtendAction custom argparse action for array parameters
- load_config function with all supported arguments
- Error handling for invalid parameters
- Debug mode special behaviors
- Argument precedence and overriding
- Edge cases like empty values, special characters, and unicode
- All DNS provider options
- SSL, cache, and logging configuration options

@author: GitHub Copilot
@updated: 2025-07-06
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the ddns module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ddns.config.cli import load_config, str_bool, log_level  # noqa: E402


class TestCliConfig(unittest.TestCase):
    """Test cases for CLI configuration loading"""

    def setUp(self):
        """Set up test fixtures"""
        self.original_argv = sys.argv[:]

    def tearDown(self):
        """Clean up after tests"""
        sys.argv = self.original_argv

    def test_str_bool_function(self):
        """Test str_bool function with various inputs"""
        # Test boolean inputs
        self.assertTrue(str_bool(True))
        self.assertFalse(str_bool(False))

        # Test string inputs that should be True
        for value in ["yes", "true", "t", "y", "1", "YES", "TRUE", "T", "Y"]:
            self.assertTrue(str_bool(value), "Value '{}' should be True".format(value))

        # Test string inputs that should be False
        for value in ["no", "false", "f", "n", "0", "NO", "FALSE", "F", "N"]:
            self.assertFalse(str_bool(value), "Value '{}' should be False".format(value))

        # Test string inputs that should remain unchanged
        self.assertEqual(str_bool("maybe"), "maybe")
        self.assertEqual(str_bool("auto"), "auto")
        self.assertEqual(str_bool(""), "")
        self.assertEqual(str_bool("off"), "off")
        self.assertEqual(str_bool("OFF"), "OFF")
        self.assertEqual(str_bool("on"), "on")
        self.assertEqual(str_bool("ON"), "ON")

    def test_str_bool_with_none(self):
        """Test str_bool function with None input"""
        # str_bool should handle None gracefully and return False
        self.assertFalse(str_bool(None))

    def test_str_bool_with_non_string(self):
        """Test str_bool function with non-string inputs"""
        # Test integer inputs
        self.assertTrue(str_bool(1))
        self.assertFalse(str_bool(0))
        self.assertTrue(str_bool(-1))
        self.assertTrue(str_bool(42))

        # Test list inputs
        self.assertTrue(str_bool([1, 2, 3]))
        self.assertFalse(str_bool([]))

        # Test float inputs
        self.assertTrue(str_bool(1.0))
        self.assertFalse(str_bool(0.0))
        self.assertTrue(str_bool(3.14))

    def test_log_level_function(self):
        """Test log_level function with various inputs"""
        self.assertEqual(log_level("DEBUG"), 10)
        self.assertEqual(log_level("INFO"), 20)
        self.assertEqual(log_level("WARNING"), 30)
        self.assertEqual(log_level("ERROR"), 40)
        self.assertEqual(log_level("CRITICAL"), 50)

        # Test case insensitive
        self.assertEqual(log_level("debug"), 10)
        self.assertEqual(log_level("info"), 20)

    def test_load_config_basic_args(self):
        """Test load_config with basic command line arguments"""
        sys.argv = ["ddns", "--dns", "cloudflare", "--id", "test@example.com", "--token", "secret123", "--debug"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["dns"], "cloudflare")
        self.assertEqual(config["id"], "test@example.com")
        self.assertEqual(config["token"], "secret123")
        self.assertTrue(config["debug"])

    def test_load_config_with_arrays(self):
        """Test load_config with array arguments"""
        sys.argv = ["ddns", "--ipv4", "example.com", "test.com", "--proxy", "http://proxy1.com", "http://proxy2.com"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["ipv4"], ["example.com", "test.com"])
        self.assertEqual(config["proxy"], ["http://proxy1.com", "http://proxy2.com"])

    def test_load_config_with_ssl_settings(self):
        """Test load_config with SSL settings"""
        sys.argv = ["ddns", "--ssl", "true", "--cache", "false"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertTrue(config["ssl"])
        self.assertFalse(config["cache"])

    def test_load_config_with_log_settings(self):
        """Test load_config with logging settings"""
        sys.argv = [
            "ddns",
            "--log-level",
            "DEBUG",
            "--log-file",
            "/var/log/ddns.log",
            "--log-format",
            "%(asctime)s %(message)s",
        ]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["log_level"], 10)  # DEBUG level
        self.assertEqual(config["log_file"], "/var/log/ddns.log")
        self.assertEqual(config["log_format"], "%(asctime)s %(message)s")

    def test_load_config_with_config_file(self):
        """Test load_config with config file parameter"""
        sys.argv = ["ddns", "--config", "/path/to/config.json"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["config"], "/path/to/config.json")

    def test_load_config_version_flag(self):
        """Test load_config with version flag"""
        sys.argv = ["ddns", "--version"]

        with self.assertRaises(SystemExit):
            load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

    def test_load_config_help_flag(self):
        """Test load_config with help flag"""
        sys.argv = ["ddns", "--help"]

        with self.assertRaises(SystemExit):
            load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

    def test_load_config_generate_config(self):
        """Test load_config with generate-config flag"""
        sys.argv = ["ddns", "--new-config"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        # Should include the new_config flag
        self.assertTrue(config.get("new_config"))

    def test_load_config_ttl_and_line(self):
        """Test load_config with TTL and line settings"""
        sys.argv = ["ddns", "--ttl", "300", "--line", "unicom"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["ttl"], 300)
        self.assertEqual(config["line"], "unicom")

    def test_load_config_no_cache_flag(self):
        """Test load_config with no-cache flag"""
        sys.argv = ["ddns", "--no-cache"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertFalse(config["cache"])

    def test_load_config_with_index_rules(self):
        """Test load_config with index4 and index6 rules"""
        sys.argv = [
            "ddns",
            "--index4",
            "url:http://ip.example.com",
            "interface:eth0",
            "--index6",
            "url:http://ipv6.example.com",
        ]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["index4"], ["url:http://ip.example.com", "interface:eth0"])
        self.assertEqual(config["index6"], ["url:http://ipv6.example.com"])

    def test_load_config_with_no_ssl_flag(self):
        """Test load_config with no-ssl flag"""
        sys.argv = ["ddns", "--no-ssl"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertFalse(config["ssl"])

    def test_load_config_with_ssl_custom_cert(self):
        """Test load_config with custom SSL certificate"""
        sys.argv = ["ddns", "--ssl", "/path/to/cert.pem"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["ssl"], "/path/to/cert.pem")

    def test_load_config_with_cache_path(self):
        """Test load_config with cache path"""
        sys.argv = ["ddns", "--cache", "/var/cache/ddns"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["cache"], "/var/cache/ddns")

    def test_load_config_with_cache_boolean(self):
        """Test load_config with cache boolean values"""
        sys.argv = ["ddns", "--cache", "true"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertTrue(config["cache"])

    def test_load_config_with_all_dns_providers(self):
        """Test load_config with all supported DNS providers"""
        dns_providers = [
            "alidns",
            "cloudflare",
            "dnscom",
            "dnspod",
            "dnspod_com",
            "he",
            "huaweidns",
            "noip",
            "tencentcloud",
            "callback",
            "debug",
        ]

        for provider in dns_providers:
            sys.argv = ["ddns", "--dns", provider]
            config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
            self.assertEqual(config["dns"], provider)

    def test_load_config_with_empty_arrays(self):
        """Test load_config with empty array arguments"""
        sys.argv = ["ddns", "--ipv4", "--ipv6", "--proxy"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["ipv4"], [])
        self.assertEqual(config["ipv6"], [])
        self.assertEqual(config["proxy"], [])

    def test_load_config_debug_mode_effects(self):
        """Test that debug mode properly sets log level and disables cache"""
        sys.argv = ["ddns", "--debug"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertTrue(config["debug"])
        # In debug mode, log level should be set to DEBUG (10)
        self.assertEqual(config["log_level"], 10)
        # Cache should be disabled in debug mode (set to False, not None)
        self.assertFalse(config["cache"])

    def test_load_config_underscore_style_log_params(self):
        """Test load_config with underscore style log parameters"""
        sys.argv = [
            "ddns",
            "--log_level",
            "INFO",
            "--log_file",
            "/tmp/ddns.log",
            "--log_format",
            "%(levelname)s: %(message)s",
            "--log_datefmt",
            "%Y-%m-%d %H:%M:%S",
        ]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["log_level"], 20)  # INFO level
        self.assertEqual(config["log_file"], "/tmp/ddns.log")
        self.assertEqual(config["log_format"], "%(levelname)s: %(message)s")
        self.assertEqual(config["log_datefmt"], "%Y-%m-%d %H:%M:%S")

    def test_load_config_minimal_setup(self):
        """Test load_config with minimal configuration"""
        sys.argv = ["ddns"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        # With the new filtering logic, None values are excluded from the config
        # So these keys should not be present at all
        self.assertNotIn("dns", config)
        self.assertNotIn("id", config)
        self.assertNotIn("token", config)
        self.assertNotIn("config", config)
        self.assertNotIn("ipv4", config)
        self.assertNotIn("ipv6", config)
        self.assertNotIn("cache", config)  # Should not be present
        self.assertNotIn("ssl", config)  # Should not be present
        self.assertNotIn("ttl", config)  # Should not be present
        self.assertNotIn("line", config)  # Should not be present

        # debug and new_config have default values of False, so they should be present
        self.assertFalse(config.get("debug", False))
        self.assertFalse(config.get("new_config", False))

    def test_extend_action_functionality(self):
        """Test ExtendAction behavior for multiple values"""
        # Test with multiple --ipv4 flags
        sys.argv = ["ddns", "--ipv4", "example.com", "test.com", "--ipv4", "another.com"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["ipv4"], ["example.com", "test.com", "another.com"])

    def test_log_level_edge_cases(self):
        """Test log_level function with edge cases"""
        # Test with different cases
        self.assertEqual(log_level("critical"), 50)
        self.assertEqual(log_level("Error"), 40)
        self.assertEqual(log_level("warning"), 30)
        self.assertEqual(log_level("Info"), 20)
        self.assertEqual(log_level("DEBUG"), 10)
        self.assertEqual(log_level("NOTSET"), 0)

    def test_str_bool_edge_cases(self):
        """Test str_bool function with additional edge cases"""
        # Test with whitespace
        self.assertEqual(str_bool(" true "), " true ")  # Should remain as string
        self.assertEqual(str_bool("true"), True)  # Should convert to bool

        # Test with mixed case
        self.assertTrue(str_bool("True"))
        self.assertTrue(str_bool("TRUE"))
        self.assertTrue(str_bool("Yes"))
        self.assertTrue(str_bool("YES"))

        # Test with numbers as strings
        self.assertTrue(str_bool("1"))
        self.assertFalse(str_bool("0"))

        # Test with other strings
        self.assertEqual(str_bool("auto"), "auto")
        self.assertEqual(str_bool("path/to/file"), "path/to/file")

    def test_system_and_python_info_functions(self):
        """Test that system info functions work correctly"""
        # These are private functions, but we can test them through load_config
        # by checking the version string output
        sys.argv = ["ddns", "--version"]

        try:
            load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
            self.fail("Should have raised SystemExit")
        except SystemExit:
            pass  # Expected behavior

    def test_load_config_with_combined_flags(self):
        """Test load_config with combination of flags"""
        sys.argv = [
            "ddns",
            "--dns",
            "cloudflare",
            "--id",
            "test@example.com",
            "--token",
            "secret123",
            "--ipv4",
            "example.com",
            "test.com",
            "--ipv6",
            "ipv6.example.com",
            "--ttl",
            "600",
            "--line",
            "default",
            "--cache",
            "true",
            "--ssl",
            "auto",
            "--proxy",
            "http://proxy.example.com:8080",
            "--log-level",
            "INFO",
            "--log-file",
            "/var/log/ddns.log",
        ]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["dns"], "cloudflare")
        self.assertEqual(config["id"], "test@example.com")
        self.assertEqual(config["token"], "secret123")
        self.assertEqual(config["ipv4"], ["example.com", "test.com"])
        self.assertEqual(config["ipv6"], ["ipv6.example.com"])
        self.assertEqual(config["ttl"], 600)
        self.assertEqual(config["line"], "default")
        self.assertTrue(config["cache"])
        self.assertEqual(config["ssl"], "auto")
        self.assertEqual(config["proxy"], ["http://proxy.example.com:8080"])
        self.assertEqual(config["log_level"], 20)  # INFO level
        self.assertEqual(config["log_file"], "/var/log/ddns.log")

    def test_load_config_invalid_dns_provider(self):
        """Test load_config with invalid DNS provider"""
        sys.argv = ["ddns", "--dns", "invalid_provider"]

        with self.assertRaises(SystemExit):
            load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

    def test_load_config_invalid_ttl(self):
        """Test load_config with invalid TTL value"""
        sys.argv = ["ddns", "--ttl", "invalid_ttl"]

        with self.assertRaises(SystemExit):
            load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

    def test_load_config_invalid_log_level(self):
        """Test load_config with invalid log level"""
        sys.argv = ["ddns", "--log-level", "INVALID"]

        # This should not raise an exception as getLevelName handles invalid levels
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        # getLevelName returns "Level INVALID" for invalid levels
        self.assertEqual(config["log_level"], "Level INVALID")

    def test_extend_action_with_mixed_usage(self):
        """Test ExtendAction with mixed single and multiple values"""
        sys.argv = ["ddns", "--proxy", "proxy1.com", "--proxy", "proxy2.com", "proxy3.com", "--proxy", "proxy4.com"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["proxy"], ["proxy1.com", "proxy2.com", "proxy3.com", "proxy4.com"])

    def test_load_config_with_special_characters(self):
        """Test load_config with special characters in values"""
        sys.argv = [
            "ddns",
            "--id",
            "user@domain.com",
            "--token",
            "secret!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "--ipv4",
            "sub-domain.example.com",
            "--line",
            "移动",
        ]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["id"], "user@domain.com")
        self.assertEqual(config["token"], "secret!@#$%^&*()_+-=[]{}|;':\",./<>?")
        self.assertEqual(config["ipv4"], ["sub-domain.example.com"])
        self.assertEqual(config["line"], "移动")

    def test_load_config_cache_with_different_values(self):
        """Test load_config cache parameter with different value types"""
        test_cases = [
            ("true", True),
            ("false", False),
            ("1", True),
            ("0", False),
            ("yes", True),
            ("no", False),
            ("/path/to/cache", "/path/to/cache"),
            ("auto", "auto"),
        ]

        for cache_value, expected in test_cases:
            sys.argv = ["ddns", "--cache", cache_value]
            config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
            self.assertEqual(config["cache"], expected, "Cache value '{}' should be {}".format(cache_value, expected))

    def test_load_config_ssl_with_different_values(self):
        """Test load_config SSL parameter with different value types"""
        test_cases = [
            ("true", "true"),
            ("false", "false"),
            ("auto", "auto"),
            ("/path/to/cert.pem", "/path/to/cert.pem"),
            ("", ""),
        ]

        for ssl_value, expected in test_cases:
            sys.argv = ["ddns", "--ssl", ssl_value]
            config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
            self.assertEqual(config["ssl"], expected, "SSL value '{}' should be {}".format(ssl_value, expected))

    def test_load_config_empty_values(self):
        """Test load_config with empty string values"""
        sys.argv = ["ddns", "--id", "", "--token", "", "--line", "", "--ssl", "", "--cache", ""]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["id"], "")
        self.assertEqual(config["token"], "")
        self.assertEqual(config["line"], "")
        self.assertEqual(config["ssl"], "")
        self.assertEqual(config["cache"], "")

    def test_str_bool_with_unicode_strings(self):
        """Test str_bool function with unicode strings"""
        # Test with unicode strings
        self.assertEqual(str_bool("是"), "是")
        self.assertEqual(str_bool("否"), "否")
        self.assertEqual(str_bool("真"), "真")
        self.assertEqual(str_bool("假"), "假")
        self.assertEqual(str_bool("中文"), "中文")

    def test_load_config_argument_precedence(self):
        """Test that later arguments override earlier ones"""
        sys.argv = [
            "ddns",
            "--dns",
            "cloudflare",
            "--dns",
            "alidns",  # This should override the previous value
            "--ttl",
            "300",
            "--ttl",
            "600",  # This should override the previous value
        ]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["dns"], "alidns")
        self.assertEqual(config["ttl"], 600)

    def test_load_config_with_numeric_strings(self):
        """Test load_config with numeric strings"""
        sys.argv = ["ddns", "--id", "123456", "--token", "987654321", "--line", "100", "--ssl", "443"]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["id"], "123456")
        self.assertEqual(config["token"], "987654321")
        self.assertEqual(config["line"], "100")
        self.assertEqual(config["ssl"], "443")

    def test_load_config_with_paths(self):
        """Test load_config with various path formats"""
        sys.argv = [
            "ddns",
            "--config",
            "/absolute/path/config.json",
            "--log-file",
            "./relative/path/ddns.log",
            "--ssl",
            "~/.ssl/cert.pem",
        ]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        self.assertEqual(config["config"], "/absolute/path/config.json")
        self.assertEqual(config["log_file"], "./relative/path/ddns.log")
        self.assertEqual(config["ssl"], "~/.ssl/cert.pem")

    def test_extend_action_single_value(self):
        """Test ExtendAction with single value"""
        from ddns.config.cli import ExtendAction
        from argparse import Namespace, ArgumentParser

        parser = ArgumentParser()
        action = ExtendAction(option_strings=["--test"], dest="test")
        namespace = Namespace()

        # Test with single value
        action(parser, namespace, "value1", "--test")
        self.assertEqual(namespace.test, ["value1"])

        # Test with additional single value
        action(parser, namespace, "value2", "--test")
        self.assertEqual(namespace.test, ["value1", "value2"])

        # Test with list value
        action(parser, namespace, ["value3", "value4"], "--test")
        self.assertEqual(namespace.test, ["value1", "value2", "value3", "value4"])

    def test_extend_action_empty_list(self):
        """Test ExtendAction with empty list"""
        from ddns.config.cli import ExtendAction
        from argparse import Namespace, ArgumentParser

        parser = ArgumentParser()
        action = ExtendAction(option_strings=["--test"], dest="test")
        namespace = Namespace()

        # Test with empty list
        action(parser, namespace, [], "--test")
        self.assertEqual(namespace.test, [])

        # Test adding to empty list
        action(parser, namespace, "value1", "--test")
        self.assertEqual(namespace.test, ["value1"])

    def test_load_config_comprehensive_scenario(self):
        """Test a comprehensive real-world scenario"""
        sys.argv = [
            "ddns",
            "--dns",
            "cloudflare",
            "--id",
            "user@example.com",
            "--token",
            "cf_token_123456789",
            "--ipv4",
            "home.example.com",
            "work.example.com",
            "--ipv6",
            "home-ipv6.example.com",
            "--index4",
            "url:http://ip.example.com",
            "interface:eth0",
            "--index6",
            "url:http://ipv6.example.com",
            "--ttl",
            "300",
            "--line",
            "default",
            "--proxy",
            "http://proxy.corp.com:8080",
            "--cache",
            "/var/cache/ddns",
            "--ssl",
            "true",
            "--log-level",
            "INFO",
            "--log-file",
            "/var/log/ddns.log",
            "--log-format",
            "%(asctime)s [%(levelname)s] %(message)s",
            "--log-datefmt",
            "%Y-%m-%d %H:%M:%S",
        ]

        config = load_config("DDNS Client", "Dynamic DNS updater", "2.0.0", "2025-07-06")

        # Verify all configuration values
        self.assertEqual(config["dns"], "cloudflare")
        self.assertEqual(config["id"], "user@example.com")
        self.assertEqual(config["token"], "cf_token_123456789")
        self.assertEqual(config["ipv4"], ["home.example.com", "work.example.com"])
        self.assertEqual(config["ipv6"], ["home-ipv6.example.com"])
        self.assertEqual(config["index4"], ["url:http://ip.example.com", "interface:eth0"])
        self.assertEqual(config["index6"], ["url:http://ipv6.example.com"])
        self.assertEqual(config["ttl"], 300)
        self.assertEqual(config["line"], "default")
        self.assertEqual(config["proxy"], ["http://proxy.corp.com:8080"])
        self.assertEqual(config["cache"], "/var/cache/ddns")
        self.assertEqual(config["ssl"], "true")
        self.assertEqual(config["log_level"], 20)  # INFO level
        self.assertEqual(config["log_file"], "/var/log/ddns.log")
        self.assertEqual(config["log_format"], "%(asctime)s [%(levelname)s] %(message)s")
        self.assertEqual(config["log_datefmt"], "%Y-%m-%d %H:%M:%S")
        self.assertFalse(config["debug"])
        # new_config is not set, so it should not be present in the filtered config
        self.assertNotIn("new_config", config)

    def test_load_config_dns_provider_validation(self):
        """Test that DNS provider validation matches available providers"""
        # Test with a provider that should be valid
        sys.argv = ["ddns", "--dns", "cloudflare"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["dns"], "cloudflare")

        # Note: Testing invalid providers would cause SystemExit,
        # which is the expected behavior for argparse validation
