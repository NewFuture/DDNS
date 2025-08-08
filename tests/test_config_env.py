# -*- coding:utf-8 -*-
"""
Configuration loader tests for environment variables.
"""

import os
import unittest
from ddns.config.env import load_config


class TestConfigEnv(unittest.TestCase):
    """Test configuration loading from environment variables"""

    def setUp(self):
        """Set up test environment"""
        self._clear_env_prefix("DDNS_TEST_")
        self._clear_env_prefix("DDNS_")
        self._clear_standard_env()

    def tearDown(self):
        """Clean up after tests"""
        self._clear_env_prefix("DDNS_TEST_")
        self._clear_env_prefix("DDNS_")
        self._clear_standard_env()

    def _clear_env_prefix(self, prefix):
        # type: (str) -> None
        """Clear environment variables with a specific prefix"""
        test_prefixes = [prefix.lower(), prefix.upper()]
        for key in list(os.environ.keys()):
            if any(key.startswith(prefix) for prefix in test_prefixes):
                del os.environ[key]

    def _clear_standard_env(self):
        # type: () -> None
        """Clear standard environment variables used in tests"""
        keys = ["PYTHONHTTPSVERIFY"]
        for key in keys:
            if key in os.environ:
                del os.environ[key]

    def test_basic_string_values(self):
        """Test that basic string values are preserved"""
        os.environ["DDNS_DNS"] = "cloudflare"
        os.environ["DDNS_ID"] = "test@example.com"
        os.environ["DDNS_TOKEN"] = "secret123"

        config = load_config()
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("id"), "test@example.com")
        self.assertEqual(config.get("token"), "secret123")

    def test_json_array_conversion(self):
        """Test JSON array format conversion"""
        os.environ["DDNS_IPV4"] = '["domain1.com", "domain2.com"]'
        os.environ["DDNS_INDEX4"] = '["public", 0]'

        config = load_config()
        self.assertEqual(config.get("ipv4"), ["domain1.com", "domain2.com"])
        self.assertEqual(config.get("index4"), ["public", 0])

    def test_key_normalization(self):
        """Test key normalization (uppercase to lowercase)"""
        os.environ["DDNS_DNS"] = "cloudflare"
        os.environ["ddns_id"] = "test@example.com"

        config = load_config()
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("id"), "test@example.com")

    def test_dot_to_underscore_conversion(self):
        """Test conversion of dots to underscores in keys"""
        os.environ["DDNS_LOG.LEVEL"] = "DEBUG"
        os.environ["DDNS_LOG.FILE"] = "/var/log/ddns.log"

        config = load_config()
        self.assertEqual(config.get("log_level"), "DEBUG")
        self.assertEqual(config.get("log_file"), "/var/log/ddns.log")

    def test_pythonhttpsverify_values(self):
        """Test PYTHONHTTPSVERIFY with different values"""
        test_cases = [("0", "0"), ("1", "1"), ("false", "false"), ("true", "true"), ("anything", "anything")]

        for env_value, expected in test_cases:
            os.environ["PYTHONHTTPSVERIFY"] = env_value
            config = load_config()
            self.assertEqual(config.get("ssl"), expected)
            del os.environ["PYTHONHTTPSVERIFY"]

    def test_ddns_proxy_basic(self):
        """Test basic DDNS_PROXY functionality"""
        os.environ["DDNS_PROXY"] = "http://ddns.proxy.com:9090"
        config = load_config()
        self.assertEqual(config.get("proxy"), "http://ddns.proxy.com:9090")
        del os.environ["DDNS_PROXY"]

    def test_ddns_variables_override_standard_vars(self):
        """Test that DDNS variables take precedence over standard environment variables"""
        self._clear_standard_env()

        # Set standard environment variables
        os.environ["PYTHONHTTPSVERIFY"] = "0"

        # Set conflicting DDNS variables
        os.environ["DDNS_SSL"] = "auto"
        config = load_config()

        # DDNS should take precedence
        self.assertEqual(config.get("ssl"), "auto")

        # Clean up
        del os.environ["DDNS_SSL"]
        self._clear_standard_env()

    def test_custom_prefix(self):
        """Test custom prefix functionality"""
        os.environ["CUSTOM_DNS"] = "cloudflare"
        os.environ["CUSTOM_ID"] = "test@example.com"

        config = load_config(prefix="CUSTOM_")
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("id"), "test@example.com")

        # Clean up
        del os.environ["CUSTOM_DNS"]
        del os.environ["CUSTOM_ID"]

    def test_empty_prefix(self):
        """Test empty prefix (loads all environment variables)"""
        os.environ["TEST_DNS"] = "cloudflare"
        config = load_config(prefix="")
        self.assertEqual(config.get("test_dns"), "cloudflare")
        del os.environ["TEST_DNS"]

    def test_no_matching_environment_variables(self):
        """Test behavior when no matching environment variables exist"""
        config = load_config()
        self.assertEqual(config, {})

    def test_whitespace_stripping(self):
        """Test that leading and trailing whitespace is stripped from values"""
        test_cases = [
            ("  value  ", "value"),
            ("\tvalue\t", "value"),
            ("\nvalue\n", "value"),
            ("  value with spaces  ", "value with spaces"),
        ]

        for env_value, expected in test_cases:
            os.environ["DDNS_TEST_STRIP"] = env_value
            config = load_config(prefix="DDNS_TEST_")
            self.assertEqual(config.get("strip"), expected, "Failed for value with whitespace: %r" % env_value)

    def test_case_insensitive_prefix_matching(self):
        """Test case-insensitive prefix matching"""
        os.environ["ddns_dns"] = "cloudflare"
        os.environ["DDNS_ID"] = "test@example.com"

        config = load_config()
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("id"), "test@example.com")

    def test_invalid_json_array(self):
        """Test handling of invalid JSON array format"""
        os.environ["DDNS_TEST_INVALID"] = "[invalid"
        config = load_config(prefix="DDNS_TEST_")
        self.assertEqual(config.get("invalid"), "[invalid")  # Should remain as string

    def test_malformed_json_arrays(self):
        """Test handling of malformed JSON arrays"""
        test_cases = [
            ("[,]", "[,]"),  # Empty elements
            ("[unclosed", "[unclosed"),  # Unclosed bracket
            ("[1,2,3", "[1,2,3"),  # Missing closing bracket
        ]

        for malformed, expected in test_cases:
            os.environ["DDNS_TEST_MALFORMED"] = malformed
            config = load_config(prefix="DDNS_TEST_")
            self.assertEqual(config.get("malformed"), expected)

    def test_json_array_edge_cases(self):
        """Test JSON array edge cases"""
        test_cases = [
            ("[]", []),  # Empty array
            ("[1]", [1]),  # Single element
            ('["string"]', ["string"]),  # Single string
            ('[1, "two", 3]', [1, "two", 3]),  # Mixed types
        ]

        for json_array, expected in test_cases:
            os.environ["DDNS_TEST_ARRAY"] = json_array
            config = load_config(prefix="DDNS_TEST_")
            self.assertEqual(config.get("array"), expected)

    def test_empty_values_remain_as_strings(self):
        """Test that empty values remain as strings"""
        os.environ["DDNS_TEST_EMPTY"] = ""
        config = load_config(prefix="DDNS_TEST_")
        self.assertEqual(config.get("empty"), "")

    def test_numeric_and_boolean_strings(self):
        """Test that numeric and boolean strings are preserved"""
        test_cases = [("123", "123"), ("true", "true"), ("false", "false"), ("3.14", "3.14")]

        for value, expected in test_cases:
            os.environ["DDNS_TEST_VALUE"] = value
            config = load_config(prefix="DDNS_TEST_")
            self.assertEqual(config.get("value"), expected)

    def test_special_characters_in_values(self):
        """Test handling of special characters in values"""
        test_cases = [
            ("value with spaces", "value with spaces"),
            ("value@with#special$chars%", "value@with#special$chars%"),
            ("http://example.com:8080", "http://example.com:8080"),
        ]

        for value, expected in test_cases:
            os.environ["DDNS_TEST_SPECIAL"] = value
            config = load_config(prefix="DDNS_TEST_")
            self.assertEqual(config.get("special"), expected)

    def test_regular_comma_values_kept_as_string(self):
        """Test that regular comma-separated values are kept as strings"""
        os.environ["DDNS_TEST_COMMA"] = "value1,value2,value3"
        config = load_config(prefix="DDNS_TEST_")
        self.assertEqual(config.get("comma"), "value1,value2,value3")

    def test_edge_cases(self):
        """Test edge cases"""
        # Test with only prefix (should be ignored)
        os.environ["DDNS_"] = "ignored"
        config = load_config()
        self.assertNotIn("", config)

        # Clean up
        del os.environ["DDNS_"]

    def test_mixed_params_config(self):
        """Test mixed configuration with different parameter types"""
        os.environ["DDNS_DNS"] = "cloudflare"
        os.environ["DDNS_IPV4"] = '["domain1.com", "domain2.com"]'
        os.environ["DDNS_TTL"] = "300"
        os.environ["DDNS_SSL"] = "auto"

        config = load_config()
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("ipv4"), ["domain1.com", "domain2.com"])
        self.assertEqual(config.get("ttl"), "300")
        self.assertEqual(config.get("ssl"), "auto")

    def test_configuration_consistency(self):
        """Test that configuration parsing is consistent across different input formats"""
        # Test array consistency
        os.environ["DDNS_TEST1"] = '["item1", "item2"]'
        os.environ["DDNS_TEST2"] = "single_item"

        config = load_config(prefix="DDNS_")
        self.assertEqual(config.get("test1"), ["item1", "item2"])
        self.assertEqual(config.get("test2"), "single_item")


if __name__ == "__main__":
    unittest.main()
