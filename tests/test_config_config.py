# coding=utf-8
"""
Unit tests for ddns.config.config module
@author: GitHub Copilot
"""

from __init__ import unittest
from ddns.config.config import Config, split_array_string, SIMPLE_ARRAY_PARAMS  # noqa: E402


class TestSplitArrayString(unittest.TestCase):
    def test_split_array_string_comprehensive(self):
        """Test split_array_string with various input types"""
        # List input
        self.assertEqual(split_array_string(["item1", "item2"]), ["item1", "item2"])

        # Empty values
        self.assertEqual(split_array_string(""), [])
        self.assertEqual(split_array_string(None), [])  # type: ignore[assignment]
        self.assertEqual(split_array_string(False), [])  # type: ignore[assignment]
        self.assertEqual(split_array_string(0), [])  # type: ignore[assignment]

        # Non-string, non-list input
        self.assertEqual(split_array_string(123), [123])  # type: ignore[assignment]
        self.assertEqual(split_array_string(True), [True])  # type: ignore[assignment]

        # Comma and semicolon separated
        self.assertEqual(split_array_string("item1,item2,item3"), ["item1", "item2", "item3"])
        self.assertEqual(split_array_string("item1, item2 , item3"), ["item1", "item2", "item3"])
        self.assertEqual(split_array_string("item1;item2;item3"), ["item1", "item2", "item3"])
        self.assertEqual(split_array_string("item1,,item3,"), ["item1", "item3"])

        # Single value and mixed separators
        self.assertEqual(split_array_string("single_item"), ["single_item"])
        self.assertEqual(split_array_string("item1,item2;item3"), ["item1", "item2;item3"])

        # Special prefixes (no split)
        self.assertEqual(split_array_string("regex:192\\.168\\..*,public"), ["regex:192\\.168\\..*,public"])
        self.assertEqual(split_array_string("cmd:curl -s ip.sb,public"), ["cmd:curl -s ip.sb,public"])
        self.assertEqual(
            split_array_string("shell:ip -6 addr | grep global,public"), ["shell:ip -6 addr | grep global,public"]
        )
        self.assertEqual(split_array_string("public,regex:192\\.168\\..*"), ["public", "regex:192\\.168\\..*"])


class TestConfig(unittest.TestCase):
    def test_config_initialization_comprehensive(self):
        """Test Config initialization with various sources and priority"""
        # Empty initialization
        config = Config()
        self.assertEqual(config.dns, "")  # Default is empty string, not "debug"
        self.assertEqual(config.id, "")
        self.assertEqual(config.index4, ["default"])
        self.assertEqual(config.index6, ["default"])
        self.assertEqual(config.ipv4, [])
        self.assertIsNone(config.ttl)
        self.assertTrue(config.cache)
        self.assertEqual(config.ssl, "auto")
        self.assertEqual(config.log_level, 20)
        self.assertEqual(config.log_datefmt, "%Y-%m-%dT%H:%M:%S")

        # CLI configuration
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
        self.assertEqual(config.ttl, 300)
        self.assertFalse(config.cache)
        self.assertTrue(config.ssl)
        self.assertEqual(config.log_level, 10)

        # JSON configuration
        json_config = {
            "dns": "alidns",
            "ipv4": ["example.com"],
            "proxy": ["http://proxy1.com"],
            "ttl": 600,
            "log_level": "WARNING",
        }
        config = Config(json_config=json_config)
        self.assertEqual(config.dns, "alidns")
        self.assertEqual(config.ipv4, ["example.com"])
        self.assertEqual(config.ttl, 600)
        self.assertEqual(config.log_level, 30)

        # Priority test: CLI > JSON > ENV
        cli_config = {"dns": "cli_dns", "id": "cli_id"}
        json_config = {"dns": "json_dns", "id": "json_id", "token": "json_token"}
        env_config = {"dns": "env_dns", "id": "env_id", "token": "env_token", "line": "env_line"}
        config = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)
        self.assertEqual(config.dns, "cli_dns")
        self.assertEqual(config.id, "cli_id")
        self.assertEqual(config.token, "json_token")
        self.assertEqual(config.line, "env_line")

    def test_config_array_and_conversion_parameters(self):
        """Test array parameter processing and type conversions"""
        # Array parameters
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

        # TTL conversion
        config = Config(cli_config={"ttl": "300"})
        self.assertEqual(config.ttl, 300)
        self.assertIsInstance(config.ttl, int)
        config = Config(cli_config={"ttl": 600})
        self.assertEqual(config.ttl, 600)
        config = Config(cli_config={"ttl": b"150"})
        self.assertEqual(config.ttl, 150)

        # Proxy special values - simplified (no conversion in config)
        config = Config(cli_config={"proxy": ["http://proxy1.com", "DIRECT", "http://proxy2.com"]})
        self.assertEqual(config.proxy, ["http://proxy1.com", "DIRECT", "http://proxy2.com"])
        config = Config(cli_config={"proxy": ["NONE", "direct", "none", "NoNe"]})
        self.assertEqual(config.proxy, ["NONE", "direct", "none", "NoNe"])

        # Log level conversion
        test_cases = [("DEBUG", 10), ("INFO", 20), ("WARNING", 30), ("ERROR", 40), ("CRITICAL", 50), ("NOTSET", 0)]
        for level_str, expected_int in test_cases:
            config = Config(cli_config={"log_level": level_str})
            self.assertEqual(config.log_level, expected_int)
        config = Config(cli_config={"log_level": "debug"})
        self.assertEqual(config.log_level, 10)
        config = Config(cli_config={"log_level": 25})
        self.assertEqual(config.log_level, 25)

    def test_config_boolean_and_special_values(self):
        """Test boolean value conversions and special handling"""
        # Boolean conversions for cache and ssl
        test_cases = [
            ("true", True),
            ("false", False),
            ("yes", True),
            ("no", False),
            ("1", True),
            ("0", False),
            ("y", True),
            ("n", False),
            ("auto", "auto"),
            ("path/to/cert", "path/to/cert"),
        ]
        for str_val, expected in test_cases:
            config = Config(cli_config={"ssl": str_val})
            self.assertEqual(config.ssl, expected)
            if expected in [True, False]:
                config = Config(cli_config={"cache": str_val})
                self.assertEqual(config.cache, expected)

        # SSL special values
        ssl_cases = [("auto", "auto"), ("/path/to/cert.pem", "/path/to/cert.pem"), ("true", True), ("false", False)]
        for env_value, expected in ssl_cases:
            config = Config(env_config={"ssl": env_value})
            self.assertEqual(config.ssl, expected)

        # Index parameters with False values
        config = Config(cli_config={"index4": "false", "index6": "none"})
        self.assertFalse(config.index4)
        self.assertFalse(config.index6)

    def test_config_dict_and_utility_methods(self):
        """Test Config attributes and utility functions"""
        config = Config(cli_config={"dns": "cloudflare", "id": "test_id", "token": "secret", "ttl": 300})

        # Test individual attributes
        self.assertEqual(config.dns, "cloudflare")
        self.assertEqual(config.id, "test_id")
        self.assertEqual(config.token, "secret")
        self.assertEqual(config.ttl, 300)

        # Test SIMPLE_ARRAY_PARAMS constant
        self.assertIn("ipv4", SIMPLE_ARRAY_PARAMS)
        self.assertIn("ipv6", SIMPLE_ARRAY_PARAMS)
        self.assertIn("proxy", SIMPLE_ARRAY_PARAMS)
        self.assertIn("index4", SIMPLE_ARRAY_PARAMS)
        self.assertIn("index6", SIMPLE_ARRAY_PARAMS)

        # Test empty arrays vs none
        config = Config(cli_config={"ipv4": [], "ipv6": []})
        self.assertEqual(config.ipv4, [])
        self.assertEqual(config.ipv6, [])

    def test_config_md5_and_edge_cases(self):
        """Test MD5 functionality and edge cases"""
        # MD5 functionality
        config1 = Config(cli_config={"dns": "cloudflare", "id": "test"})
        config2 = Config(cli_config={"dns": "cloudflare", "id": "test"})
        config3 = Config(cli_config={"dns": "alidns", "id": "test"})
        self.assertEqual(config1.md5(), config2.md5())
        self.assertNotEqual(config1.md5(), config3.md5())
        md5_hash = config1.md5()
        self.assertEqual(len(md5_hash), 32)
        self.assertTrue(all(c in "0123456789abcdef" for c in md5_hash))

        # Edge cases and complex scenario
        cli_config = {
            "dns": "cloudflare",
            "id": "user@example.com",
            "token": "cf_token_123",
            "ipv4": "home.example.com,work.example.com",
            "ttl": 300,
            "cache": "auto",
            "ssl": "/path/to/cert.pem",
            "log_level": "INFO",
        }
        json_config = {
            "dns": "alidns",
            "token": "json_token",
            "proxy": ["proxy1.example.com:8080"],
            "cache": True,
            "ssl": "false",
        }
        env_config = {"line": "default", "endpoint": "https://api.example.com", "log_format": "%(message)s"}
        config = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)
        self.assertEqual(config.dns, "cloudflare")
        self.assertEqual(config.token, "cf_token_123")
        self.assertEqual(config.ipv4, ["home.example.com", "work.example.com"])
        self.assertEqual(config.ttl, 300)
        self.assertEqual(config.cache, "auto")
        self.assertEqual(config.ssl, "/path/to/cert.pem")
        self.assertEqual(config.line, "default")
        self.assertEqual(config.endpoint, "https://api.example.com")

        # Invalid TTL handling and bytes conversion
        config = Config(cli_config={"ttl": None})
        self.assertIsNone(config.ttl)

        # Bytes to int conversion
        config = Config(cli_config={"ttl": b"300"})
        self.assertEqual(config.ttl, 300)

    def test_config_environment_variables_comprehensive(self):
        """Test comprehensive environment variable handling"""
        # Environment variable types and conversions
        env_config = {
            "dns": "dnspod",
            "id": "12345",
            "token": "secret_token",
            "ttl": "600",
            "cache": "1",
            "ssl": "0",
            "log_level": "DEBUG",
            "ipv4": ["domain1.com", "domain2.com"],
            "proxy": ["proxy1:8080", "proxy2:8080"],
        }
        config = Config(env_config=env_config)
        self.assertEqual(config.dns, "dnspod")
        self.assertEqual(config.ttl, 600)
        self.assertTrue(config.cache)
        self.assertFalse(config.ssl)
        self.assertEqual(config.log_level, 10)
        self.assertEqual(config.ipv4, ["domain1.com", "domain2.com"])

        # Environment variable priority over defaults
        env_config = {
            "dns": "custom_provider",
            "cache": "false",
            "ssl": "true",
            "log_level": "CRITICAL",
            "index4": "public",
            "index6": "public",
        }
        config = Config(env_config=env_config)
        self.assertEqual(config.dns, "custom_provider")
        self.assertFalse(config.cache)
        self.assertTrue(config.ssl)
        self.assertEqual(config.log_level, 50)
        self.assertEqual(config.index4, ["public"])
        self.assertEqual(config.index6, ["public"])

        # Empty and None environment values
        env_config = {"id": "", "token": None, "endpoint": "", "line": None}
        config = Config(env_config=env_config)
        self.assertEqual(config.id, "")
        self.assertIsNone(config.token)
        self.assertEqual(config.endpoint, "")
        self.assertIsNone(config.line)

        # TTL type conversion edge cases
        test_cases = [("300", 300), (300, 300), ("0", 0), (0, 0), (None, None)]
        for env_value, expected in test_cases:
            config = Config(env_config={"ttl": env_value})
            self.assertEqual(config.ttl, expected)

    def test_config_array_parameters_comprehensive(self):
        """Test array parameters with various input forms"""
        # Test special prefixes and complex scenarios
        prefix_cases = [
            (
                {"index4": "regex:192\\.168\\..*,10\\..*", "index6": "regex:fe80::.*,::1"},
                {"index4": ["regex:192\\.168\\..*,10\\..*"], "index6": ["regex:fe80::.*,::1"]},
            ),
            (
                {"index4": "cmd:curl -s ip.sb,backup", "index6": "cmd:curl -s ipv6.icanhazip.com,backup"},
                {"index4": ["cmd:curl -s ip.sb,backup"], "index6": ["cmd:curl -s ipv6.icanhazip.com,backup"]},
            ),
            (
                {
                    "index4": "shell:ip route get 8.8.8.8 | awk '{print $7}';backup",
                    "index6": "shell:ip -6 addr | grep global;backup",
                },
                {
                    "index4": ["shell:ip route get 8.8.8.8 | awk '{print $7}';backup"],
                    "index6": ["shell:ip -6 addr | grep global;backup"],
                },
            ),
        ]
        for cli_config, expected in prefix_cases:
            config = Config(cli_config=cli_config)
            for key, value in expected.items():
                self.assertEqual(getattr(config, key), value)

        # Normal splitting when prefix is in the middle
        normal_cases = [
            (
                {"index4": "public,regex:192\\.168\\..*", "index6": "public,cmd:curl -s ipv6.icanhazip.com"},
                {"index4": ["public", "regex:192\\.168\\..*"], "index6": ["public", "cmd:curl -s ipv6.icanhazip.com"]},
            ),
            (
                {"index4": "public,default", "index6": "public;default"},
                {"index4": ["public", "default"], "index6": ["public", "default"]},
            ),
        ]
        for cli_config, expected in normal_cases:
            config = Config(cli_config=cli_config)
            for key, value in expected.items():
                self.assertEqual(getattr(config, key), value)

        # CLI array parameters with various input forms
        test_cases = [
            ({"proxy": "192.168.1.1:8080;direct"}, {"proxy": ["192.168.1.1:8080", "direct"]}),
            ({"index4": "public,default"}, {"index4": ["public", "default"]}),
            (
                {"proxy": "proxy1.com:8080;DIRECT;proxy2.com:3128"},
                {"proxy": ["proxy1.com:8080", "DIRECT", "proxy2.com:3128"]},
            ),
            ({"proxy": ["192.168.1.1:8080;direct"]}, {"proxy": ["192.168.1.1:8080", "direct"]}),
            (
                {"proxy": ["192.168.1.1:8080", "direct", "proxy2.com:3128"]},
                {"proxy": ["192.168.1.1:8080", "direct", "proxy2.com:3128"]},
            ),
            ({"index4": ["public", "default", "custom"]}, {"index4": ["public", "default", "custom"]}),
            ({"proxy": []}, {"proxy": []}),
        ]
        for cli_config, expected in test_cases:
            config = Config(cli_config=cli_config)
            for key, value in expected.items():
                self.assertEqual(
                    getattr(config, key), value, "Failed for config: {} on key: {}".format(cli_config, key)
                )


class TestIsFalse(unittest.TestCase):
    def test_is_false_comprehensive(self):
        """Test is_false utility function"""
        from ddns.config.config import is_false

        # String values that return True
        for value in ["false", "FALSE", "  false  ", "none", "NONE", "  none  "]:
            self.assertTrue(is_false(value))

        # String values that return False
        for value in ["true", "0", "1", "", "anything"]:
            self.assertFalse(is_false(value))

        # Non-string values
        self.assertTrue(is_false(False))
        for value in [True, 0, 1, None, [], {}]:
            self.assertFalse(is_false(value))


if __name__ == "__main__":
    unittest.main()
