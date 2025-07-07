# coding=utf-8
"""
Unit tests for Config class and utility functions

This test suite provides comprehensive coverage for the main Config class,
testing configuration merging, type conversions, and various edge cases.

Test Coverage:
- Config class initialization with different input sources
- Configuration merging priority (CLI > JSON > ENV > default)
- Type conversions (str to int, str to bool, log levels)
- Array parameter parsing (split_array_string function)
- Special value handling (proxy DIRECT/NONE)
- Configuration dictionary export
- Hash generation for configuration comparison

@author: GitHub Copilot
@updated: 2025-07-07
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the ddns module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ddns.config.config import Config, split_array_string, SIMPLE_ARRAY_PARAMS  # noqa: E402


class TestSplitArrayString(unittest.TestCase):
    """Test cases for split_array_string utility function"""

    def test_split_array_string_list_input(self):
        """Test split_array_string with list input"""
        input_list = ["item1", "item2", "item3"]
        result = split_array_string(input_list)
        self.assertEqual(result, input_list)

    def test_split_array_string_empty_values(self):
        """Test split_array_string with empty values"""
        self.assertEqual(split_array_string(""), [])
        self.assertEqual(split_array_string(None), [])  # type: ignore[assignment]
        self.assertEqual(split_array_string(False), [])  # type: ignore[assignment]
        self.assertEqual(split_array_string(0), [])  # type: ignore[assignment]

    def test_split_array_string_non_string(self):
        """Test split_array_string with non-string, non-list input"""
        self.assertEqual(split_array_string(123), [123])  # type: ignore[assignment]
        self.assertEqual(split_array_string(True), [True])  # type: ignore[assignment]
        self.assertEqual(split_array_string({"key": "value"}), [{"key": "value"}])  # type: ignore[assignment]

    def test_split_array_string_comma_separated(self):
        """Test split_array_string with comma-separated values"""
        result = split_array_string("item1,item2,item3")
        self.assertEqual(result, ["item1", "item2", "item3"])

        # Test with spaces
        result = split_array_string("item1, item2 , item3")
        self.assertEqual(result, ["item1", "item2", "item3"])

        # Test with empty items
        result = split_array_string("item1,,item3,")
        self.assertEqual(result, ["item1", "item3"])

    def test_split_array_string_semicolon_separated(self):
        """Test split_array_string with semicolon-separated values"""
        result = split_array_string("item1;item2;item3")
        self.assertEqual(result, ["item1", "item2", "item3"])

        # Test with spaces
        result = split_array_string("item1; item2 ; item3")
        self.assertEqual(result, ["item1", "item2", "item3"])

        # Test with empty items
        result = split_array_string("item1;;item3;")
        self.assertEqual(result, ["item1", "item3"])

    def test_split_array_string_single_value(self):
        """Test split_array_string with single value (no separators)"""
        result = split_array_string("single_item")
        self.assertEqual(result, ["single_item"])

        # Test that whitespace is trimmed for single values
        result = split_array_string("  single_item  ")
        self.assertEqual(result, ["single_item"])

    def test_split_array_string_mixed_separators(self):
        """Test split_array_string with both comma and semicolon (comma takes precedence)"""
        result = split_array_string("item1,item2;item3")
        self.assertEqual(result, ["item1", "item2;item3"])

    def test_split_array_string_whitespace_handling(self):
        """Test split_array_string whitespace handling"""
        result = split_array_string("  item1  ,  item2  ,  item3  ")
        self.assertEqual(result, ["item1", "item2", "item3"])

        result = split_array_string("  item1  ;  item2  ;  item3  ")
        self.assertEqual(result, ["item1", "item2", "item3"])

    def test_split_array_string_special_prefixes(self):
        """Test split_array_string automatically disables split for special prefixes"""
        # Test with regex: prefix at start
        result = split_array_string("regex:192\\.168\\..*,public")
        self.assertEqual(result, ["regex:192\\.168\\..*,public"])

        # Test with cmd: prefix at start
        result = split_array_string("cmd:curl -s ip.sb,public")
        self.assertEqual(result, ["cmd:curl -s ip.sb,public"])

        # Test with shell: prefix at start
        result = split_array_string("shell:ip -6 addr | grep global,public")
        self.assertEqual(result, ["shell:ip -6 addr | grep global,public"])

        # Test that prefixes in the middle don't prevent splitting
        result = split_array_string("public,regex:192\\.168\\..*")
        self.assertEqual(result, ["public", "regex:192\\.168\\..*"])

        # Test normal case without special prefixes
        result = split_array_string("public,default")
        self.assertEqual(result, ["public", "default"])


class TestConfig(unittest.TestCase):
    """Test cases for Config class"""

    def test_config_initialization_empty(self):
        """Test Config initialization with no arguments"""
        config = Config()

        # Test default values
        self.assertEqual(config.dns, "debug")
        self.assertIsNone(config.id)
        self.assertIsNone(config.token)
        self.assertEqual(config.index4, ["default"])
        self.assertEqual(config.index6, ["default"])
        self.assertEqual(config.ipv4, [])
        self.assertEqual(config.ipv6, [])
        self.assertIsNone(config.ttl)
        self.assertIsNone(config.line)
        self.assertEqual(config.proxy, [])
        self.assertTrue(config.cache)  # Default is True
        self.assertEqual(config.ssl, "auto")  # str_bool("auto") returns "auto"
        self.assertEqual(config.log_level, 20)  # INFO level
        self.assertIsNone(config.log_format)
        self.assertIsNone(config.log_file)
        self.assertEqual(config.log_datefmt, "%Y-%m-%dT%H:%M:%S")

    def test_config_initialization_with_cli_config(self):
        """Test Config initialization with CLI configuration"""
        cli_config = {
            "dns": "cloudflare",
            "id": "test@example.com",
            "token": "secret123",
            "ttl": "300",
            "cache": "false",
            "ssl": "true",
            "log_level": "DEBUG",
        }
        config = Config(cli_config=cli_config)

        self.assertEqual(config.dns, "cloudflare")
        self.assertEqual(config.id, "test@example.com")
        self.assertEqual(config.token, "secret123")
        self.assertEqual(config.ttl, 300)  # Converted to int
        self.assertFalse(config.cache)  # str_bool("false") returns False
        self.assertTrue(config.ssl)  # str_bool("true") returns True
        self.assertEqual(config.log_level, 10)  # DEBUG level

    def test_config_initialization_with_json_config(self):
        """Test Config initialization with JSON configuration"""
        json_config = {
            "dns": "alidns",
            "ipv4": ["example.com", "test.com"],
            "ipv6": ["ipv6.example.com"],
            "proxy": ["http://proxy1.com", "http://proxy2.com"],
            "ttl": 600,
            "log_level": "WARNING",
        }
        config = Config(json_config=json_config)

        self.assertEqual(config.dns, "alidns")
        self.assertEqual(config.ipv4, ["example.com", "test.com"])
        self.assertEqual(config.ipv6, ["ipv6.example.com"])
        self.assertEqual(config.proxy, ["http://proxy1.com", "http://proxy2.com"])
        self.assertEqual(config.ttl, 600)
        self.assertEqual(config.log_level, 30)  # WARNING level

    def test_config_initialization_with_env_config(self):
        """Test Config initialization with environment configuration"""
        env_config = {
            "dns": "dnspod",
            "id": "env_id",
            "token": "env_token",
            "line": "default",
            "cache": "1",  # Should be converted to True
            "ssl": "0",  # Should be converted to False
            "log_level": "ERROR",
        }
        config = Config(env_config=env_config)

        self.assertEqual(config.dns, "dnspod")
        self.assertEqual(config.id, "env_id")
        self.assertEqual(config.token, "env_token")
        self.assertEqual(config.line, "default")
        self.assertTrue(config.cache)  # str_bool("1") returns True
        self.assertFalse(config.ssl)  # str_bool("0") returns False
        self.assertEqual(config.log_level, 40)  # ERROR level

    def test_config_priority_cli_over_json_over_env(self):
        """Test configuration priority: CLI > JSON > ENV > default"""
        cli_config = {"dns": "cli_dns", "id": "cli_id"}
        json_config = {"dns": "json_dns", "id": "json_id", "token": "json_token"}
        env_config = {"dns": "env_dns", "id": "env_id", "token": "env_token", "line": "env_line"}

        config = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)

        # CLI should override JSON and ENV
        self.assertEqual(config.dns, "cli_dns")
        self.assertEqual(config.id, "cli_id")

        # JSON should override ENV when CLI doesn't have the key
        self.assertEqual(config.token, "json_token")

        # ENV should be used when neither CLI nor JSON have the key
        self.assertEqual(config.line, "env_line")

    def test_config_array_parameters(self):
        """Test array parameter processing"""
        cli_config = {
            "ipv4": "domain1.com,domain2.com,domain3.com",
            "ipv6": "ipv6domain1.com;ipv6domain2.com",
            "proxy": ["http://proxy1.com", "http://proxy2.com"],
            "index4": "public,regex:192\\.168\\..*",
            "index6": "public;regex:fe80::.*",
        }
        config = Config(cli_config=cli_config)

        self.assertEqual(config.ipv4, ["domain1.com", "domain2.com", "domain3.com"])
        self.assertEqual(config.ipv6, ["ipv6domain1.com", "ipv6domain2.com"])
        self.assertEqual(config.proxy, ["http://proxy1.com", "http://proxy2.com"])
        self.assertEqual(config.index4, ["public", "regex:192\\.168\\..*"])
        self.assertEqual(config.index6, ["public", "regex:fe80::.*"])

    def test_config_ttl_conversion(self):
        """Test TTL string to integer conversion"""
        # String TTL
        config = Config(cli_config={"ttl": "300"})
        self.assertEqual(config.ttl, 300)
        self.assertIsInstance(config.ttl, int)

        # Integer TTL
        config = Config(cli_config={"ttl": 600})
        self.assertEqual(config.ttl, 600)
        self.assertIsInstance(config.ttl, int)

        # Bytes TTL (edge case)
        config = Config(cli_config={"ttl": b"150"})
        self.assertEqual(config.ttl, 150)
        self.assertIsInstance(config.ttl, int)

        # None TTL
        config = Config()
        self.assertIsNone(config.ttl)

    def test_config_proxy_special_values(self):
        """Test proxy special value handling (DIRECT, NONE)"""
        # DIRECT should be converted to None
        config = Config(cli_config={"proxy": ["http://proxy1.com", "DIRECT", "http://proxy2.com"]})
        self.assertEqual(config.proxy, ["http://proxy1.com", None, "http://proxy2.com"])

        # NONE should be converted to None
        config = Config(cli_config={"proxy": ["NONE", "http://proxy.com"]})
        self.assertEqual(config.proxy, [None, "http://proxy.com"])

        # Case insensitive
        config = Config(cli_config={"proxy": ["direct", "none", "NoNe", "DiReCt"]})
        self.assertEqual(config.proxy, [None, None, None, None])

    def test_config_log_level_conversion(self):
        """Test log level conversion from string to integer"""
        test_cases = [("DEBUG", 10), ("INFO", 20), ("WARNING", 30), ("ERROR", 40), ("CRITICAL", 50), ("NOTSET", 0)]

        for level_str, expected_int in test_cases:
            config = Config(cli_config={"log_level": level_str})
            self.assertEqual(config.log_level, expected_int)

        # Test case insensitive
        config = Config(cli_config={"log_level": "debug"})
        self.assertEqual(config.log_level, 10)

        # Test with integer input
        config = Config(cli_config={"log_level": 25})
        self.assertEqual(config.log_level, 25)

    def test_config_boolean_conversions(self):
        """Test boolean value conversions for cache and ssl"""
        # String boolean values
        test_cases = [
            ("true", True),
            ("false", False),
            ("yes", True),
            ("no", False),
            ("1", True),
            ("0", False),
            ("y", True),
            ("n", False),
            ("auto", "auto"),  # ssl special case
            ("path/to/cert", "path/to/cert"),  # ssl special case
        ]

        for input_val, expected in test_cases:
            config = Config(cli_config={"cache": input_val, "ssl": input_val})
            if expected is True or expected is False:
                self.assertEqual(config.cache, expected)
                if input_val not in ["auto", "path/to/cert"]:
                    self.assertEqual(config.ssl, expected)
            else:
                # For ssl special cases
                self.assertEqual(config.ssl, expected)

    def test_config_dict_method(self):
        """Test Config.dict() method"""
        cli_config = {
            "dns": "cloudflare",
            "id": "test@example.com",
            "token": "secret123",
            "ipv4": ["example.com"],
            "ttl": "300",
            "cache": "true",
            "ssl": "false",
            "log_level": "DEBUG",
            "log_format": "%(message)s",
            "log_file": "/var/log/ddns.log",
        }
        config = Config(cli_config=cli_config)
        result = config.dict()

        # Check required fields
        self.assertIn("$schema", result)
        self.assertEqual(result["dns"], "cloudflare")
        self.assertEqual(result["id"], "test@example.com")
        self.assertEqual(result["token"], "secret123")
        self.assertEqual(result["ipv4"], ["example.com"])
        self.assertEqual(result["ttl"], 300)
        self.assertTrue(result["cache"])
        self.assertFalse(result["ssl"])

        # Check log section
        self.assertIn("log", result)
        log_section = result["log"]
        self.assertEqual(log_section["level"], "DEBUG")
        self.assertEqual(log_section["format"], "%(message)s")
        self.assertEqual(log_section["file"], "/var/log/ddns.log")
        self.assertEqual(log_section["datefmt"], "%Y-%m-%dT%H:%M:%S")

    def test_config_dict_method_filters_none_values(self):
        """Test Config.dict() method filters out None values"""
        config = Config()  # Use defaults (many None values)
        result = config.dict()

        # None values should be filtered out
        self.assertNotIn("id", result)
        self.assertNotIn("token", result)
        self.assertNotIn("ttl", result)
        self.assertNotIn("line", result)

        # Log section should only contain non-None values
        log_section = result["log"]
        self.assertNotIn("format", log_section)
        self.assertNotIn("file", log_section)
        self.assertIn("level", log_section)  # Should have level
        self.assertIn("datefmt", log_section)  # Should have datefmt

    def test_config_simple_array_params_constant(self):
        """Test SIMPLE_ARRAY_PARAMS constant"""
        expected_params = ["ipv4", "ipv6", "proxy", "index4", "index6"]
        self.assertEqual(SIMPLE_ARRAY_PARAMS, expected_params)

    def test_config_empty_arrays_vs_none(self):
        """Test that array parameters default to appropriate values, not None"""
        config = Config()

        # Array parameters should default to appropriate values
        self.assertEqual(config.index4, ["default"])
        self.assertEqual(config.index6, ["default"])
        self.assertEqual(config.ipv4, [])
        self.assertEqual(config.ipv6, [])
        self.assertEqual(config.proxy, [])

        # These should be lists, not None
        self.assertIsInstance(config.index4, list)
        self.assertIsInstance(config.index6, list)
        self.assertIsInstance(config.ipv4, list)
        self.assertIsInstance(config.ipv6, list)
        self.assertIsInstance(config.proxy, list)

    def test_config_complex_scenario(self):
        """Test a complex real-world configuration scenario"""
        cli_config = {"dns": "cloudflare", "cache": "false", "log_level": "DEBUG"}
        json_config = {
            "id": "json_user@example.com",
            "token": "json_secret",
            "ipv4": ["home.example.com", "work.example.com"],
            "ipv6": ["ipv6.example.com"],
            "ttl": 300,
            "cache": "true",  # Should be overridden by CLI
            "ssl": "auto",
            "log_format": "%(asctime)s %(message)s",
        }
        env_config = {
            "id": "env_user@example.com",  # Should be overridden by JSON
            "token": "env_secret",  # Should be overridden by JSON
            "line": "default",
            "proxy": "http://proxy.corp.com:8080,DIRECT",
            "log_file": "/var/log/ddns.log",
        }

        config = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)

        # CLI overrides
        self.assertEqual(config.dns, "cloudflare")
        self.assertFalse(config.cache)  # CLI "false" overrides JSON "true"
        self.assertEqual(config.log_level, 10)  # DEBUG

        # JSON overrides ENV
        self.assertEqual(config.id, "json_user@example.com")
        self.assertEqual(config.token, "json_secret")
        self.assertEqual(config.ipv4, ["home.example.com", "work.example.com"])
        self.assertEqual(config.ipv6, ["ipv6.example.com"])
        self.assertEqual(config.ttl, 300)
        self.assertEqual(config.ssl, "auto")

        # ENV values used where not overridden
        self.assertEqual(config.line, "default")
        self.assertEqual(config.proxy, ["http://proxy.corp.com:8080", None])  # DIRECT -> None

        # Test dict output
        result_dict = config.dict()
        self.assertEqual(result_dict["dns"], "cloudflare")
        self.assertFalse(result_dict["cache"])
        self.assertEqual(result_dict["proxy"], ["http://proxy.corp.com:8080", None])

    def test_config_edge_cases(self):
        """Test various edge cases"""
        # Empty string values
        config = Config(cli_config={"id": "", "token": "", "line": ""})
        self.assertEqual(config.id, "")
        self.assertEqual(config.token, "")
        self.assertEqual(config.line, "")

        # Zero and False values
        config = Config(cli_config={"ttl": 0, "cache": False})
        self.assertEqual(config.ttl, 0)
        self.assertFalse(config.cache)

        # Very large TTL
        config = Config(cli_config={"ttl": "999999"})
        self.assertEqual(config.ttl, 999999)

        # Mixed case boolean
        config = Config(cli_config={"cache": "True", "ssl": "FALSE"})
        self.assertTrue(config.cache)
        self.assertFalse(config.ssl)

    def test_config_invalid_ttl_handling(self):
        """Test handling of invalid TTL values"""
        # Non-numeric string TTL should raise ValueError
        with self.assertRaises(ValueError):
            Config(cli_config={"ttl": "invalid"})

        # Float TTL should raise ValueError (int() doesn't handle float strings)
        with self.assertRaises(ValueError):
            Config(cli_config={"ttl": "300.5"})

    def test_config_log_datefmt_default(self):
        """Test default log date format"""
        config = Config()
        self.assertEqual(config.log_datefmt, "%Y-%m-%dT%H:%M:%S")

        # Custom log date format
        config = Config(cli_config={"log_datefmt": "%Y-%m-%d %H:%M:%S"})
        self.assertEqual(config.log_datefmt, "%Y-%m-%d %H:%M:%S")

    def test_config_with_all_three_sources(self):
        """Test config initialization with all three sources and proper priority"""
        cli_config = {"dns": "cli", "ttl": "100"}
        json_config = {"dns": "json", "ttl": "200", "id": "json_id"}
        env_config = {"dns": "env", "ttl": "300", "id": "env_id", "token": "env_token"}

        config = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)

        # CLI has highest priority
        self.assertEqual(config.dns, "cli")
        self.assertEqual(config.ttl, 100)

        # JSON overrides ENV when CLI doesn't have the value
        self.assertEqual(config.id, "json_id")

        # ENV is used when neither CLI nor JSON have the value
        self.assertEqual(config.token, "env_token")

    def test_config_bytes_to_int_conversion(self):
        """Test that bytes values are properly converted to integers for TTL"""
        config = Config(cli_config={"ttl": b"500"})
        self.assertEqual(config.ttl, 500)
        self.assertIsInstance(config.ttl, int)

    def test_config_log_level_integer_passthrough(self):
        """Test that integer log levels are passed through unchanged"""
        config = Config(cli_config={"log_level": 15})
        self.assertEqual(config.log_level, 15)

    def test_config_ssl_special_values(self):
        """Test SSL special value handling (auto, paths)"""
        # Auto value
        config = Config(cli_config={"ssl": "auto"})
        self.assertEqual(config.ssl, "auto")

        # Path value
        config = Config(cli_config={"ssl": "/path/to/cert.pem"})
        self.assertEqual(config.ssl, "/path/to/cert.pem")

        # Boolean values
        config = Config(cli_config={"ssl": "true"})
        self.assertTrue(config.ssl)

        config = Config(cli_config={"ssl": "false"})
        self.assertFalse(config.ssl)

    def test_config_env_variable_types(self):
        """Test Config with various environment variable types"""
        env_config = {
            "dns": "dnspod",
            "id": "12345",
            "token": "secret_token",
            "ttl": "600",  # String that should be converted to int
            "cache": "1",  # String that should be converted to bool
            "ssl": "0",  # String that should be converted to bool
            "log_level": "DEBUG",
            "ipv4": ["domain1.com", "domain2.com"],  # Already a list
            "proxy": ["proxy1:8080", "proxy2:8080"],  # Already a list
        }
        config = Config(env_config=env_config)

        self.assertEqual(config.dns, "dnspod")
        self.assertEqual(config.id, "12345")
        self.assertEqual(config.token, "secret_token")
        self.assertEqual(config.ttl, 600)  # Should be converted to int
        self.assertTrue(config.cache)  # "1" should be True
        self.assertFalse(config.ssl)  # "0" should be False
        self.assertEqual(config.log_level, 10)  # DEBUG level
        self.assertEqual(config.ipv4, ["domain1.com", "domain2.com"])
        self.assertEqual(config.proxy, ["proxy1:8080", "proxy2:8080"])

    def test_config_env_variable_string_conversion(self):
        """Test Config with environment variables as strings (mimicking real env vars)"""
        env_config = {
            "cache": "true",
            "ssl": "false",
            "ttl": "300",
            "log_level": "ERROR",
        }
        config = Config(env_config=env_config)

        self.assertTrue(config.cache)
        self.assertFalse(config.ssl)
        self.assertEqual(config.ttl, 300)
        self.assertEqual(config.log_level, 40)  # ERROR level

    def test_config_env_special_ssl_values(self):
        """Test Config SSL handling with special environment values"""
        test_cases = [
            ("auto", "auto"),
            ("/path/to/cert.pem", "/path/to/cert.pem"),
            ("true", True),
            ("false", False),
            ("1", True),
            ("0", False),
        ]

        for env_value, expected in test_cases:
            config = Config(env_config={"ssl": env_value})
            self.assertEqual(config.ssl, expected, "Failed for SSL value: {}".format(env_value))

    def test_config_env_proxy_special_values(self):
        """Test Config proxy handling with DIRECT and NONE values from environment"""
        test_cases = [
            (["DIRECT"], [None]),
            (["NONE"], [None]),
            (["direct"], [None]),  # Case insensitive
            (["none"], [None]),  # Case insensitive
            (["proxy1:8080", "DIRECT", "proxy2:8080"], ["proxy1:8080", None, "proxy2:8080"]),
            ([""], [None]),  # Empty string
        ]

        for env_value, expected in test_cases:
            config = Config(env_config={"proxy": env_value})
            self.assertEqual(config.proxy, expected, "Failed for proxy value: {}".format(env_value))

    def test_config_md5_method(self):
        """Test Config.md5() method"""
        config1 = Config(cli_config={"dns": "cloudflare", "id": "test"})
        config2 = Config(cli_config={"dns": "cloudflare", "id": "test"})
        config3 = Config(cli_config={"dns": "alidns", "id": "test"})

        # Same configuration should have same MD5
        self.assertEqual(config1.md5(), config2.md5())

        # Different configuration should have different MD5
        self.assertNotEqual(config1.md5(), config3.md5())

        # MD5 should be a valid hex string
        md5_hash = config1.md5()
        self.assertEqual(len(md5_hash), 32)  # MD5 is 32 characters
        self.assertTrue(all(c in "0123456789abcdef" for c in md5_hash))

    def test_config_md5_consistency(self):
        """Test that MD5 hash is consistent across multiple calls"""
        config = Config(cli_config={"dns": "cloudflare", "id": "test", "token": "secret"})

        hash1 = config.md5()
        hash2 = config.md5()
        hash3 = config.md5()

        self.assertEqual(hash1, hash2)
        self.assertEqual(hash2, hash3)

    def test_config_env_variable_priority_over_defaults(self):
        """Test that environment variables override defaults"""
        env_config = {
            "dns": "custom_provider",  # Should override default "debug"
            "cache": "false",  # Should override default True
            "ssl": "true",  # Should override default "auto"
            "log_level": "CRITICAL",  # Should override default "INFO"
            "index4": "public",  # Should override default ["default"]
            "index6": "public",  # Should override default ["default"]
        }
        config = Config(env_config=env_config)

        self.assertEqual(config.dns, "custom_provider")
        self.assertFalse(config.cache)
        self.assertTrue(config.ssl)
        self.assertEqual(config.log_level, 50)  # CRITICAL level
        self.assertEqual(config.index4, ["public"])
        self.assertEqual(config.index6, ["public"])

    def test_config_env_json_array_like_values(self):
        """Test Config with environment variables that look like JSON arrays"""
        # Note: In real environment usage, these would come from the env loader
        # which might parse JSON arrays, but here we test with already parsed values
        env_config = {
            "ipv4": ["test1.example.com", "test2.example.com"],
            "index4": ["public", "regex:192\\.168\\..*"],
            "proxy": ["http://proxy1:8080", "http://proxy2:8080", "DIRECT"],
        }
        config = Config(env_config=env_config)

        self.assertEqual(config.ipv4, ["test1.example.com", "test2.example.com"])
        self.assertEqual(config.index4, ["public", "regex:192\\.168\\..*"])
        self.assertEqual(config.proxy, ["http://proxy1:8080", "http://proxy2:8080", None])

    def test_config_env_empty_and_none_values(self):
        """Test Config with empty and None environment values"""
        env_config = {
            "id": "",  # Empty string
            "token": None,  # None value
            "endpoint": "",  # Empty string
            "line": None,  # None value
        }
        config = Config(env_config=env_config)

        self.assertEqual(config.id, "")  # Empty string preserved
        self.assertIsNone(config.token)  # None preserved
        self.assertEqual(config.endpoint, "")  # Empty string preserved
        self.assertIsNone(config.line)  # None preserved

    def test_config_env_ttl_type_conversion_edge_cases(self):
        """Test TTL conversion with various environment variable formats"""
        test_cases = [
            ("300", 300),  # String number
            (300, 300),  # Already int
            ("0", 0),  # Zero as string
            (0, 0),  # Zero as int
            (None, None),  # None value
        ]

        for env_value, expected in test_cases:
            config = Config(env_config={"ttl": env_value})
            self.assertEqual(config.ttl, expected, "Failed for TTL value: {}".format(env_value))

    def test_config_index_false_values(self):
        """Test that index4 and index6 can be set to False to disable them"""
        cli_config = {
            "index4": "false",
            "index6": False,
        }
        config = Config(cli_config=cli_config)

        self.assertFalse(config.index4)
        self.assertFalse(config.index6)

        # Test with "none" string as well
        cli_config2 = {
            "index4": "none",
            "index6": "NONE",
        }
        config2 = Config(cli_config=cli_config2)

        self.assertFalse(config2.index4)
        self.assertFalse(config2.index6)

    def test_config_index_special_prefixes_no_split(self):
        """Test that index4 and index6 with special prefixes don't get split"""
        # Test regex: prefix at start - should not split
        cli_config1 = {"index4": "regex:192\\.168\\..*,10\\..*", "index6": "regex:fe80::.*,::1"}
        config1 = Config(cli_config=cli_config1)

        self.assertEqual(config1.index4, ["regex:192\\.168\\..*,10\\..*"])
        self.assertEqual(config1.index6, ["regex:fe80::.*,::1"])

        # Test cmd: prefix at start - should not split
        cli_config2 = {"index4": "cmd:curl -s ip.sb,backup", "index6": "cmd:curl -s ipv6.icanhazip.com,backup"}
        config2 = Config(cli_config=cli_config2)

        self.assertEqual(config2.index4, ["cmd:curl -s ip.sb,backup"])
        self.assertEqual(config2.index6, ["cmd:curl -s ipv6.icanhazip.com,backup"])

        # Test shell: prefix at start - should not split
        cli_config3 = {
            "index4": "shell:ip route get 8.8.8.8 | awk '{print $7}';backup",
            "index6": "shell:ip -6 addr | grep global;backup",
        }
        config3 = Config(cli_config=cli_config3)

        self.assertEqual(config3.index4, ["shell:ip route get 8.8.8.8 | awk '{print $7}';backup"])
        self.assertEqual(config3.index6, ["shell:ip -6 addr | grep global;backup"])

        # Test that prefixes in the middle still allow splitting
        cli_config4 = {"index4": "public,regex:192\\.168\\..*", "index6": "public,cmd:curl -s ipv6.icanhazip.com"}
        config4 = Config(cli_config=cli_config4)

        self.assertEqual(config4.index4, ["public", "regex:192\\.168\\..*"])
        self.assertEqual(config4.index6, ["public", "cmd:curl -s ipv6.icanhazip.com"])

        # Test that normal values still get split
        cli_config5 = {"index4": "public,default", "index6": "public;default"}
        config5 = Config(cli_config=cli_config5)

        self.assertEqual(config5.index4, ["public", "default"])
        self.assertEqual(config5.index6, ["public", "default"])


class TestIsFalse(unittest.TestCase):
    """Test cases for is_false utility function"""

    def test_is_false_with_strings(self):
        """Test is_false with string values"""
        from ddns.config.config import is_false

        # These should return True
        self.assertTrue(is_false("false"))
        self.assertTrue(is_false("FALSE"))
        self.assertTrue(is_false("  false  "))
        self.assertTrue(is_false("none"))
        self.assertTrue(is_false("NONE"))
        self.assertTrue(is_false("  none  "))

        # These should return False
        self.assertFalse(is_false("true"))
        self.assertFalse(is_false("0"))
        self.assertFalse(is_false("1"))
        self.assertFalse(is_false(""))
        self.assertFalse(is_false("anything"))

    def test_is_false_with_non_strings(self):
        """Test is_false with non-string values"""
        from ddns.config.config import is_false

        # Boolean False should return True
        self.assertTrue(is_false(False))

        # These should return False
        self.assertFalse(is_false(True))
        self.assertFalse(is_false(0))  # 0 is not False according to the function
        self.assertFalse(is_false(1))
        self.assertFalse(is_false(None))
        self.assertFalse(is_false([]))
        self.assertFalse(is_false({}))


if __name__ == "__main__":
    unittest.main()
