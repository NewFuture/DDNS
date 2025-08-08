# coding=utf-8
"""
Unit tests for ddns.config.cli module
@author: GitHub Copilot
"""

from __init__ import unittest
import sys
import io
from ddns.config.cli import load_config, str_bool, log_level  # noqa: E402


class TestCliConfig(unittest.TestCase):
    def setUp(self):
        encode = sys.stdout.encoding
        if encode is not None and encode.lower() != "utf-8" and hasattr(sys.stdout, "buffer"):
            # 兼容windows 和部分ASCII编码的老旧系统
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

        self.original_argv = sys.argv[:]

    def tearDown(self):
        sys.argv = self.original_argv

    def test_str_bool_function(self):
        """Test str_bool function with various inputs"""
        # Test boolean inputs
        self.assertTrue(str_bool(True))
        self.assertFalse(str_bool(False))
        self.assertFalse(str_bool(None))

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
        self.assertEqual(str_bool("on"), "on")

        # Test non-string inputs
        self.assertTrue(str_bool(1))
        self.assertFalse(str_bool(0))
        self.assertTrue(str_bool([1, 2, 3]))
        self.assertFalse(str_bool([]))
        self.assertTrue(str_bool(1.0))
        self.assertFalse(str_bool(0.0))

        # Test edge cases
        self.assertEqual(str_bool(" true "), " true ")
        self.assertTrue(str_bool("True"))
        self.assertEqual(str_bool("path/to/file"), "path/to/file")
        self.assertEqual(str_bool("中文"), "中文")

    def test_log_level_function(self):
        """Test log_level function with various inputs"""
        self.assertEqual(log_level("DEBUG"), 10)
        self.assertEqual(log_level("INFO"), 20)
        self.assertEqual(log_level("WARNING"), 30)
        self.assertEqual(log_level("ERROR"), 40)
        self.assertEqual(log_level("CRITICAL"), 50)
        self.assertEqual(log_level("debug"), 10)
        self.assertEqual(log_level("critical"), 50)
        self.assertEqual(log_level("NOTSET"), 0)

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

    def test_load_config_ssl_comprehensive(self):
        """Test comprehensive SSL configuration options"""
        # Test --ssl without value (should default to True)
        sys.argv = ["ddns", "--ssl"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertTrue(config["ssl"])

        # Test --ssl with boolean-like values
        ssl_bool_cases = [
            ("true", True),
            ("false", False),
            ("yes", True),
            ("no", False),
            ("1", True),
            ("0", False),
            ("TRUE", True),
            ("FALSE", False),
            ("Y", True),
            ("N", False),
        ]
        for ssl_value, expected in ssl_bool_cases:
            sys.argv = ["ddns", "--ssl", ssl_value]
            config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
            self.assertEqual(config["ssl"], expected, "SSL value '{}' should be {}".format(ssl_value, expected))

        # Test --ssl with special values (auto, file paths)
        ssl_special_cases = [
            ("auto", "auto"),
            ("/path/to/cert.pem", "/path/to/cert.pem"),
            ("./cert.crt", "./cert.crt"),
            ("C:\\certs\\cert.pem", "C:\\certs\\cert.pem"),
            ("", ""),
            ("custom_value", "custom_value"),
        ]
        for ssl_value, expected in ssl_special_cases:
            sys.argv = ["ddns", "--ssl", ssl_value]
            config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
            self.assertEqual(config["ssl"], expected, "SSL value '{}' should be {}".format(ssl_value, expected))

        # Test --no-ssl flag
        sys.argv = ["ddns", "--no-ssl"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertFalse(config["ssl"])

        # Test --no-ssl overrides --ssl
        sys.argv = ["ddns", "--ssl", "true", "--no-ssl"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertFalse(config["ssl"])

    def test_load_config_log_settings(self):
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
        self.assertEqual(config["log_level"], 10)
        self.assertEqual(config["log_file"], "/var/log/ddns.log")
        self.assertEqual(config["log_format"], "%(asctime)s %(message)s")

        sys.argv = ["ddns", "--log_level", "INFO", "--log_file", "/tmp/ddns.log", "--log_datefmt", "%Y-%m-%d %H:%M:%S"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["log_level"], 20)
        self.assertEqual(config["log_file"], "/tmp/ddns.log")
        self.assertEqual(config["log_datefmt"], "%Y-%m-%d %H:%M:%S")

    def test_load_config_system_exit_flags(self):
        sys.argv = ["ddns", "--version"]
        with self.assertRaises(SystemExit):
            load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        sys.argv = ["ddns", "--help"]
        with self.assertRaises(SystemExit):
            load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

    def test_new_config_action_simple(self):
        """Test NewConfigAction behavior in a simple way"""
        from ddns.config.cli import NewConfigAction

        # Create an action and test its basic properties
        action = NewConfigAction(["--new-config"], "new_config", nargs="?")

        # Test that the action has the right configuration
        self.assertEqual(action.option_strings, ["--new-config"])
        self.assertEqual(action.dest, "new_config")
        self.assertEqual(action.nargs, "?")

    def test_load_config_other_flags(self):
        sys.argv = ["ddns", "--ttl", "300", "--line", "unicom"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["ttl"], 300)
        self.assertEqual(config["line"], "unicom")

        sys.argv = ["ddns", "--config", "/path/to/config.json"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["config"], ["/path/to/config.json"])

    def test_load_config_index_rules(self):
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

    def test_load_config_dns_providers(self):
        # 测试CLI中实际支持的DNS providers
        cli_supported_providers = [
            "51dns",
            "alidns",
            "aliesa",
            "callback",
            "cloudflare",
            "debug",
            "dnscom",
            "dnspod_com",
            "dnspod",
            "he",
            "huaweidns",
            "noip",
            "tencentcloud",
        ]
        for provider in cli_supported_providers:
            sys.argv = ["ddns", "--dns", provider]
            config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
            self.assertEqual(config["dns"], provider)

    def test_load_config_debug_mode(self):
        sys.argv = ["ddns", "--debug"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertTrue(config["debug"])
        self.assertEqual(config["log_level"], 10)
        self.assertFalse(config["cache"])

    def test_load_config_minimal_setup(self):
        sys.argv = ["ddns"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertNotIn("dns", config)
        self.assertNotIn("id", config)
        self.assertNotIn("token", config)
        self.assertFalse(config.get("debug", False))

    def test_extend_action_functionality(self):
        sys.argv = ["ddns", "--ipv4", "example.com", "test.com", "--ipv4", "another.com"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["ipv4"], ["example.com", "test.com", "another.com"])

        sys.argv = ["ddns", "--proxy", "proxy1.com", "--proxy", "proxy2.com", "proxy3.com", "--proxy", "proxy4.com"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["proxy"], ["proxy1.com", "proxy2.com", "proxy3.com", "proxy4.com"])

        sys.argv = ["ddns", "--ipv4", "--ipv6", "--proxy"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["ipv4"], [])
        self.assertEqual(config["ipv6"], [])
        self.assertEqual(config["proxy"], [])

    def test_load_config_combined_flags(self):
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
        self.assertEqual(config["log_level"], 20)
        self.assertEqual(config["log_file"], "/var/log/ddns.log")

    def test_load_config_invalid_inputs(self):
        sys.argv = ["ddns", "--dns", "invalid_provider"]
        with self.assertRaises(SystemExit):
            load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        sys.argv = ["ddns", "--ttl", "invalid_ttl"]
        with self.assertRaises(SystemExit):
            load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        sys.argv = ["ddns", "--log-level", "INVALID"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["log_level"], "Level INVALID")

    def test_load_config_value_types(self):
        # Test cache with different value types
        test_cases = [
            ("true", True),
            ("false", False),
            ("1", True),
            ("0", False),
            ("yes", True),
            ("no", False),
            ("/path/to/cache", "/path/to/cache"),
        ]
        for cache_value, expected in test_cases:
            sys.argv = ["ddns", "--cache", cache_value]
            config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
            self.assertEqual(config["cache"], expected)

    def test_load_config_special_characters(self):
        sys.argv = [
            "ddns",
            "--id",
            "user@domain.com",
            "--token",
            "secret!@#$%^&*()",
            "--ipv4",
            "sub-domain.example.com",
            "--line",
            "移动",
        ]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["id"], "user@domain.com")
        self.assertEqual(config["token"], "secret!@#$%^&*()")
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

    def test_load_config_empty_values(self):
        """Test load_config with empty string values"""
        sys.argv = ["ddns", "--id", "", "--token", "", "--line", "", "--ssl", "", "--cache", ""]

        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["id"], "")
        self.assertEqual(config["token"], "")
        self.assertEqual(config["ssl"], "")
        self.assertEqual(config["cache"], "")

        # Test argument precedence
        sys.argv = ["ddns", "--dns", "cloudflare", "--dns", "alidns", "--ttl", "300", "--ttl", "600"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["dns"], "alidns")
        self.assertEqual(config["ttl"], 600)

    def test_load_config_paths_and_numeric(self):
        # Test various path formats
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
        self.assertEqual(config["config"], ["/absolute/path/config.json"])
        self.assertEqual(config["log_file"], "./relative/path/ddns.log")
        self.assertEqual(config["ssl"], "~/.ssl/cert.pem")

        # Test multiple configs
        sys.argv = ["ddns", "--config", "/path/to/config1.json", "--config", "/path/to/config2.json"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["config"], ["/path/to/config1.json", "/path/to/config2.json"])

        # Test numeric strings
        sys.argv = ["ddns", "--id", "123456", "--token", "987654321", "--line", "100"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["id"], "123456")
        self.assertEqual(config["token"], "987654321")
        self.assertEqual(config["line"], "100")

    def test_extend_action_class(self):
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

        # Test with empty list
        namespace2 = Namespace()
        action(parser, namespace2, [], "--test")
        self.assertEqual(namespace2.test, [])
        action(parser, namespace2, "value1", "--test")
        self.assertEqual(namespace2.test, ["value1"])

    def test_comprehensive_scenario(self):
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
        self.assertEqual(config["ssl"], True)
        self.assertEqual(config["log_level"], 20)
        self.assertEqual(config["log_file"], "/var/log/ddns.log")
        self.assertEqual(config["log_format"], "%(asctime)s [%(levelname)s] %(message)s")
        self.assertEqual(config["log_datefmt"], "%Y-%m-%d %H:%M:%S")
        self.assertFalse(config["debug"])
        self.assertNotIn("new_config", config)

    def test_load_config_endpoint_parameter(self):
        # 测试endpoint参数，这在当前测试中缺失
        sys.argv = ["ddns", "--endpoint", "https://api.example.com/v1"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["endpoint"], "https://api.example.com/v1")

    def test_load_config_hidden_parameters(self):
        # 测试隐藏的日志参数变体（带点号和横线的）
        sys.argv = ["ddns", "--log.file", "/test/log.txt", "--log.level", "ERROR"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["log_file"], "/test/log.txt")
        self.assertEqual(config["log_level"], 40)  # ERROR level

        sys.argv = ["ddns", "--log-file", "/test2/log.txt", "--log-level", "WARNING"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["log_file"], "/test2/log.txt")
        self.assertEqual(config["log_level"], 30)  # WARNING level

        sys.argv = ["ddns", "--log.format", "custom format", "--log.datefmt", "%Y-%m-%d"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["log_format"], "custom format")
        self.assertEqual(config["log_datefmt"], "%Y-%m-%d")

        sys.argv = ["ddns", "--log-format", "custom format2", "--log-datefmt", "%H:%M:%S"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config["log_format"], "custom format2")
        self.assertEqual(config["log_datefmt"], "%H:%M:%S")

    def test_log_level_with_integers(self):
        # 测试log_level函数处理整数输入
        self.assertEqual(log_level(10), "DEBUG")
        self.assertEqual(log_level(20), "INFO")
        self.assertEqual(log_level(50), "CRITICAL")

    def test_load_config_cache_none_in_debug(self):
        # 测试debug模式下cache为None时的行为
        sys.argv = ["ddns", "--debug", "--cache", "true"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertTrue(config["debug"])
        self.assertEqual(config["log_level"], 10)  # DEBUG
        self.assertTrue(config["cache"])  # 明确设置的cache应该保持

        # 测试debug模式下没有设置cache时
        sys.argv = ["ddns", "--debug"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertTrue(config["debug"])
        self.assertEqual(config["log_level"], 10)  # DEBUG
        self.assertFalse(config["cache"])  # debug模式下默认禁用cache


if __name__ == "__main__":
    unittest.main()
