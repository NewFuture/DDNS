# coding=utf-8
"""
Unit tests for ddns.config.env module
@author: GitHub Copilot
"""

from __init__ import unittest
import os
from ddns.config.env import load_config


class TestConfigEnv(unittest.TestCase):
    """Test environment variable configuration loading"""

    def setUp(self):
        """Set up test environment"""
        self._clear_test_env()
        self._clear_standard_env()

    def tearDown(self):
        """Clean up test environment"""
        self._clear_test_env()
        self._clear_standard_env()

    def _clear_test_env(self):
        # type: () -> None
        """Clear test environment variables"""
        test_prefixes = ["DDNS_", "CUSTOM_", "MYAPP_"]
        for key in list(os.environ.keys()):
            if any(key.startswith(prefix) for prefix in test_prefixes):
                del os.environ[key]

    def _clear_standard_env(self):
        # type: () -> None
        """Clear standard environment variables used in tests"""
        keys = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "PYTHONHTTPSVERIFY"]
        for key in keys:
            if key in os.environ:
                del os.environ[key]

    def _assert_proxy_value(self, expected_proxy, config=None):
        # type: (str | None, dict | None) -> None
        """Assert proxy value in config"""
        if config is None:
            config = load_config()
        if expected_proxy is None:
            self.assertIsNone(config.get("proxy"))
        else:
            self.assertEqual(config.get("proxy"), expected_proxy)

    def test_basic_string_values(self):
        """Test that basic string values are preserved"""
        os.environ["DDNS_TEST_STRING"] = "test_value"
        os.environ["DDNS_TEST_NUMBER"] = "42"
        os.environ["DDNS_TEST_BOOL"] = "true"

        config = load_config(prefix="DDNS_TEST_")

        self.assertEqual(config.get("string"), "test_value")
        self.assertEqual(config.get("number"), "42")  # Kept as string
        self.assertEqual(config.get("bool"), "true")  # Kept as string

    def test_json_array_conversion(self):
        """Test JSON array format conversion"""
        test_cases = [
            ('["item1", "item2", "item3"]', ["item1", "item2", "item3"]),
            ("['a', 'b']", ["a", "b"]),
            ("[]", []),
            ("[1, 2, 3]", [1, 2, 3]),
        ]

        for env_value, expected in test_cases:
            os.environ["DDNS_TEST_JSON"] = env_value
            config = load_config(prefix="DDNS_TEST_")
            self.assertEqual(config.get("json"), expected, "Failed for JSON value: %s" % env_value)

    def test_regular_comma_values_kept_as_string(self):
        """Test that regular comma-separated values are kept as strings"""
        test_cases = [
            ("item1,item2,item3", "item1,item2,item3"),
            ("a,b,c,d", "a,b,c,d"),
            ("host1:port1,host2:port2", "host1:port1,host2:port2"),
        ]

        for env_value, expected in test_cases:
            os.environ["DDNS_TEST_REGULAR"] = env_value
            config = load_config(prefix="DDNS_TEST_")
            self.assertEqual(config.get("regular"), expected, "Failed for regular value: %s" % env_value)

    def test_key_normalization(self):
        """Test key normalization (uppercase to lowercase)"""
        os.environ["DDNS_TEST_UPPER_CASE"] = "value1"
        os.environ["DDNS_TEST_lower_case"] = "value2"
        os.environ["DDNS_TEST_Mixed.Case"] = "value3"

        config = load_config(prefix="DDNS_TEST_")

        self.assertEqual(config.get("upper_case"), "value1")
        self.assertEqual(config.get("lower_case"), "value2")
        self.assertEqual(config.get("mixed_case"), "value3")  # Dot replaced with underscore

    def test_custom_prefix(self):
        """Test custom prefix functionality"""
        os.environ["CUSTOM_TEST"] = "custom_value"
        os.environ["DDNS_TEST_NORMAL"] = "normal_value"

        config = load_config(prefix="CUSTOM_")

        self.assertEqual(config.get("test"), "custom_value")
        self.assertIsNone(config.get("normal"))

    def test_empty_prefix(self):
        """Test empty prefix (loads all environment variables)"""
        os.environ["TEST_EMPTY_PREFIX"] = "test_value"

        config = load_config(prefix="")

        # Should contain the test variable
        self.assertEqual(config.get("test_empty_prefix"), "test_value")

    def test_edge_cases(self):
        """Test edge cases"""
        test_cases = [
            ("DDNS_TEST_EMPTY", "", ""),
            ("DDNS_TEST_SPACES", "   ", ""),  # Spaces are stripped
            ("DDNS_TEST_SPECIAL", "hello@world.com", "hello@world.com"),
            ("DDNS_TEST_URL", "https://api.example.com?key=value", "https://api.example.com?key=value"),
        ]

        for env_key, env_value, expected in test_cases:
            os.environ[env_key] = env_value

        config = load_config(prefix="DDNS_TEST_")

        self.assertEqual(config.get("empty"), "")
        self.assertEqual(config.get("spaces"), "")  # Spaces are stripped
        self.assertEqual(config.get("special"), "hello@world.com")
        self.assertEqual(config.get("url"), "https://api.example.com?key=value")

    def test_invalid_json_array(self):
        """Test handling of invalid JSON array format"""
        # Invalid JSON should be treated as regular string for non-array params
        os.environ["DDNS_TEST_INVALID"] = "[invalid json"
        config = load_config(prefix="DDNS_TEST_")
        self.assertEqual(config.get("invalid"), "[invalid json")

        # Invalid JSON for array param should also return as string
        os.environ["DDNS_TEST_IPV4"] = "[invalid json"
        config = load_config(prefix="DDNS_TEST_")
        self.assertEqual(config.get("ipv4"), "[invalid json")

    def test_empty_values_remain_as_strings(self):
        """Test that empty values remain as strings"""
        test_params = ["index4", "index6", "ipv4", "ipv6", "proxy", "regular_param"]

        for param in test_params:
            # Test empty string
            os.environ["DDNS_TEST_" + param.upper()] = ""
            config = load_config(prefix="DDNS_TEST_")
            self.assertEqual(config.get(param), "", "Failed for empty param: %s" % param)

    def test_json_array_edge_cases(self):
        """Test JSON array edge cases"""
        test_cases = [
            ('[""]', [""]),  # Array with empty string
            ("[True, False]", [True, False]),  # Array with booleans (Python style)
            ('["mixed", 123, True]', ["mixed", 123, True]),  # Mixed types
            ("[1.5, 2.7]", [1.5, 2.7]),  # Array with floats
            ('["single"]', ["single"]),  # Single item array
        ]

        for env_value, expected in test_cases:
            os.environ["DDNS_TEST_JSON"] = env_value
            config = load_config(prefix="DDNS_TEST_")
            self.assertEqual(config.get("json"), expected, "Failed for JSON edge case: %s" % env_value)

    def test_malformed_json_arrays(self):
        """Test handling of malformed JSON arrays"""
        malformed_cases = [
            "[unclosed",  # Unclosed bracket
            "closed]",  # Missing opening bracket
            "[,]",  # Invalid comma
            "[invalid syntax}",  # Wrong closing bracket
            "not_json_at_all",  # Not JSON
        ]

        for malformed in malformed_cases:
            os.environ["DDNS_TEST_MALFORMED"] = malformed
            config = load_config(prefix="DDNS_TEST_")
            # Should return as string for all params
            self.assertEqual(config.get("malformed"), malformed, "Failed for malformed JSON: %s" % malformed)

            # Also test with common params
            os.environ["DDNS_TEST_IPV4"] = malformed
            config = load_config(prefix="DDNS_TEST_")
            self.assertEqual(config.get("ipv4"), malformed, "Failed for malformed JSON in param: %s" % malformed)

    def test_case_insensitive_prefix_matching(self):
        """Test case-insensitive prefix matching"""
        os.environ["ddns_test_lowercase"] = "value1"
        os.environ["DDNS_TEST_UPPERCASE"] = "value2"
        os.environ["Ddns_Test_MixedCase"] = "value3"

        config = load_config(prefix="DDNS_TEST_")

        self.assertEqual(config.get("lowercase"), "value1")
        self.assertEqual(config.get("uppercase"), "value2")
        self.assertEqual(config.get("mixedcase"), "value3")

    def test_special_characters_in_values(self):
        """Test handling of special characters in values"""
        special_values = [
            ("DDNS_TEST_UNICODE", "café", "café"),
            ("DDNS_TEST_SYMBOLS", "!@#$%^&*()", "!@#$%^&*()"),
            ("DDNS_TEST_NEWLINES", "line1\nline2", "line1\nline2"),
            ("DDNS_TEST_TABS", "col1\tcol2", "col1\tcol2"),
            ("DDNS_TEST_QUOTES", 'He said "Hello"', 'He said "Hello"'),
            ("DDNS_TEST_BACKSLASH", "path\\to\\file", "path\\to\\file"),
        ]

        for env_key, env_value, expected in special_values:
            os.environ[env_key] = env_value

        config = load_config(prefix="DDNS_TEST_")

        self.assertEqual(config.get("unicode"), "café")
        self.assertEqual(config.get("symbols"), "!@#$%^&*()")
        self.assertEqual(config.get("newlines"), "line1\nline2")
        self.assertEqual(config.get("tabs"), "col1\tcol2")
        self.assertEqual(config.get("quotes"), 'He said "Hello"')
        self.assertEqual(config.get("backslash"), "path\\to\\file")

    def test_numeric_and_boolean_strings(self):
        """Test that numeric and boolean strings are preserved"""
        test_cases = [
            ("123", "123"),
            ("0", "0"),
            ("-456", "-456"),
            ("3.14", "3.14"),
            ("true", "true"),
            ("false", "false"),
            ("True", "True"),
            ("False", "False"),
            ("yes", "yes"),
            ("no", "no"),
            ("on", "on"),
            ("off", "off"),
        ]

        for env_value, expected in test_cases:
            os.environ["DDNS_TEST_VALUE"] = env_value
            config = load_config(prefix="DDNS_TEST_")
            self.assertEqual(config.get("value"), expected, "Failed to preserve string value: %s" % env_value)

    def test_dot_to_underscore_conversion(self):
        """Test conversion of dots to underscores in keys"""
        test_keys = [
            ("DDNS_TEST_SIMPLE.KEY", "simple_key"),
            ("DDNS_TEST_MULTIPLE.DOT.KEY", "multiple_dot_key"),
            ("DDNS_TEST_MIXED_key.name", "mixed_key_name"),
            ("DDNS_TEST_END.DOT.", "end_dot_"),
            ("DDNS_TEST_.START.DOT", "_start_dot"),
        ]

        for env_key, expected_key in test_keys:
            os.environ[env_key] = "test_value"

        config = load_config(prefix="DDNS_TEST_")

        for _, expected_key in test_keys:
            self.assertEqual(config.get(expected_key), "test_value", "Failed for key conversion: %s" % expected_key)

    def test_no_matching_environment_variables(self):
        """Test behavior when no matching environment variables exist"""
        # Clear all test variables
        self._clear_test_env()

        config = load_config(prefix="NONEXISTENT_PREFIX_")

        self.assertEqual(len(config), 0)
        self.assertIsInstance(config, dict)

    def test_mixed_params_config(self):
        """Test mixed configuration with different parameter types"""
        os.environ["DDNS_TEST_STRING"] = "simple_string"
        os.environ["DDNS_TEST_IPV4"] = '["192.168.1.1", "10.0.0.1"]'  # JSON format
        os.environ["DDNS_TEST_IPV6"] = "::1,2001:db8::1"  # String format
        os.environ["DDNS_TEST_OTHER_JSON"] = '["item1", "item2"]'  # JSON format
        os.environ["DDNS_TEST_COMMA_VALUE"] = "a,b,c"  # String format

        config = load_config(prefix="DDNS_TEST_")

        self.assertEqual(config.get("string"), "simple_string")
        self.assertEqual(config.get("ipv4"), ["192.168.1.1", "10.0.0.1"])  # Parsed as array
        self.assertEqual(config.get("ipv6"), "::1,2001:db8::1")  # Kept as string
        self.assertEqual(config.get("other_json"), ["item1", "item2"])  # Parsed as array
        self.assertEqual(config.get("comma_value"), "a,b,c")  # Kept as string

    def test_configuration_consistency(self):
        """Test that configuration parsing is consistent across different input formats"""
        # Test mixed array and object configurations
        os.environ["DDNS_TEST_ARRAY_CONFIG"] = '["domain1.com", "domain2.com"]'
        os.environ["DDNS_TEST_OBJECT_CONFIG"] = '{"ttl": 300, "line": "default"}'  # Kept as string
        os.environ["DDNS_TEST_STRING_CONFIG"] = "simple_value"
        os.environ["DDNS_TEST_NUMBER_CONFIG"] = "42"

        config = load_config(prefix="DDNS_TEST_")

        # Verify different types are handled correctly
        self.assertIsInstance(config.get("array_config"), list)
        self.assertIsInstance(config.get("object_config"), str)  # Objects are now kept as strings
        self.assertIsInstance(config.get("string_config"), str)
        self.assertIsInstance(config.get("number_config"), str)  # Numbers remain as strings

        # Verify actual values
        self.assertEqual(config.get("array_config"), ["domain1.com", "domain2.com"])
        self.assertEqual(config.get("object_config"), '{"ttl": 300, "line": "default"}')  # Kept as string
        self.assertEqual(config.get("string_config"), "simple_value")
        self.assertEqual(config.get("number_config"), "42")

    def test_whitespace_stripping(self):
        """Test that leading and trailing whitespace is stripped from values"""
        test_cases = [
            ("  value  ", "value"),
            ("\tvalue\t", "value"),
            ("\n value \n", "value"),
            ("  ", ""),  # Only whitespace becomes empty
            (" \t\n ", ""),  # Mixed whitespace becomes empty
            ("  [1, 2, 3]  ", [1, 2, 3]),  # JSON arrays are parsed after stripping
            ('  {"key": "value"}  ', '{"key": "value"}'),  # JSON objects are kept as strings after stripping
        ]

        for env_value, expected in test_cases:
            os.environ["DDNS_TEST_STRIP"] = env_value
            config = load_config(prefix="DDNS_TEST_")
            self.assertEqual(config.get("strip"), expected, "Failed for value with whitespace: %r" % env_value)

    def test_standard_environment_variables_integration(self):
        """Test integration with standard Python environment variables"""
        self._clear_standard_env()

        # Test HTTP proxy variables
        os.environ["HTTP_PROXY"] = "http://proxy.example.com:8080"
        os.environ["PYTHONHTTPSVERIFY"] = "0"

        config = load_config()
        self._assert_proxy_value("DIRECT;http://proxy.example.com:8080", config)
        self.assertEqual(config.get("ssl"), "0")

        # Clean up
        self._clear_standard_env()

    def test_ddns_variables_override_standard_vars(self):
        """Test that DDNS variables take precedence over standard environment variables"""
        # Set standard variables
        os.environ["HTTP_PROXY"] = "http://standard.proxy.com:8080"
        os.environ["PYTHONHTTPSVERIFY"] = "0"

        # Set DDNS variables
        os.environ["DDNS_PROXY"] = "http://ddns.proxy.com:9090"
        os.environ["DDNS_SSL"] = "true"

        config = load_config()

        # DDNS variables should override standard ones
        self.assertEqual(config.get("proxy"), "http://ddns.proxy.com:9090")
        self.assertEqual(config.get("ssl"), "true")

        # Clean up
        self._clear_standard_env()

    def test_partial_standard_variable_override(self):
        """Test mixing standard and DDNS variables"""
        # Set standard proxy but DDNS ssl
        os.environ["HTTP_PROXY"] = "http://standard.proxy.com:8080"
        os.environ["DDNS_SSL"] = "false"
        os.environ["DDNS_DNS"] = "cloudflare"

        config = load_config()

        # Should get proxy from standard env, ssl from DDNS
        self._assert_proxy_value("DIRECT;http://standard.proxy.com:8080", config)
        self.assertEqual(config.get("ssl"), "false")
        self.assertEqual(config.get("dns"), "cloudflare")

        # Clean up
        self._clear_standard_env()

    def test_standard_env_vars_basic(self):
        """Test basic standard environment variable support"""
        # Test HTTP_PROXY (uppercase)
        os.environ["HTTP_PROXY"] = "http://proxy.example.com:8080"
        self._assert_proxy_value("DIRECT;http://proxy.example.com:8080")
        del os.environ["HTTP_PROXY"]

        # Test http_proxy (lowercase)
        os.environ["http_proxy"] = "http://proxy.example.com:8080"
        self._assert_proxy_value("DIRECT;http://proxy.example.com:8080")
        del os.environ["http_proxy"]

        # Test PYTHONHTTPSVERIFY
        os.environ["PYTHONHTTPSVERIFY"] = "0"
        config = load_config()
        self.assertEqual(config.get("ssl"), "0")
        del os.environ["PYTHONHTTPSVERIFY"]

    def test_standard_env_vars_priority(self):
        """Test standard environment variable collection"""
        # Test HTTP_PROXY and HTTPS_PROXY (different variables)
        os.environ["HTTP_PROXY"] = "http://http.proxy.com:8080"
        os.environ["HTTPS_PROXY"] = "http://https.proxy.com:8080"

        config = load_config()
        # Both proxies should be in the string
        proxy_value = config.get("proxy")
        self.assertIsNotNone(proxy_value)
        self.assertTrue(proxy_value.startswith("DIRECT;"))  # type: ignore
        self.assertIn("http://http.proxy.com:8080", proxy_value)  # type: ignore
        self.assertIn("http://https.proxy.com:8080", proxy_value)  # type: ignore

    def test_standard_env_vars_pythonhttpsverify_values(self):
        """Test PYTHONHTTPSVERIFY with different values"""
        test_cases = [
            ("0", "0"),
            ("1", "1"),
            ("false", "false"),
            ("true", "true"),
            ("anything", "anything"),
        ]

        for env_value, expected in test_cases:
            os.environ["PYTHONHTTPSVERIFY"] = env_value
            config = load_config()
            self.assertEqual(config.get("ssl"), expected)
            del os.environ["PYTHONHTTPSVERIFY"]

    def test_standard_env_vars_no_conflict_when_ddns_exists(self):
        """Test that standard vars don't override existing DDNS vars due to priority logic"""
        # Set DDNS variable first (should be processed later and take precedence)
        os.environ["DDNS_PROXY"] = "http://ddns.proxy.com:9090"
        os.environ["HTTP_PROXY"] = "http://standard.proxy.com:8080"

        config = load_config()
        # DDNS variable should win due to processing order
        self.assertEqual(config.get("proxy"), "http://ddns.proxy.com:9090")

    def test_standard_env_vars_with_json_arrays(self):
        """Test standard environment variables with JSON array values"""
        # Test that HTTP_PROXY JSON arrays are treated as simple strings (not parsed)
        os.environ["HTTP_PROXY"] = '["proxy1.com:8080", "proxy2.com:8080"]'
        self._assert_proxy_value('DIRECT;["proxy1.com:8080", "proxy2.com:8080"]')
        del os.environ["HTTP_PROXY"]

    def test_standard_env_vars_integration_full(self):
        """Test full integration of standard and DDNS environment variables"""
        # Set a mix of standard and DDNS variables
        os.environ["HTTP_PROXY"] = "http://standard.proxy.com:8080"
        os.environ["PYTHONHTTPSVERIFY"] = "0"
        os.environ["DDNS_DNS"] = "cloudflare"
        os.environ["DDNS_TOKEN"] = "secret123"
        os.environ["DDNS_IPV4"] = '["example.com", "test.com"]'

        config = load_config()

        # Standard vars
        self._assert_proxy_value("DIRECT;http://standard.proxy.com:8080", config)
        self.assertEqual(config.get("ssl"), "0")
        # DDNS vars
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("token"), "secret123")
        self.assertEqual(config.get("ipv4"), ["example.com", "test.com"])

        # Clean up
        self._clear_standard_env()

    def test_standard_env_vars_edge_cases(self):
        """Test edge cases for standard environment variables"""
        # Empty values - empty HTTP_PROXY should not create proxy config
        os.environ["HTTP_PROXY"] = ""
        self._assert_proxy_value(None)  # No proxy should be set for empty value
        del os.environ["HTTP_PROXY"]

        # Whitespace values
        os.environ["PYTHONHTTPSVERIFY"] = "  1  "
        config = load_config()
        self.assertEqual(config.get("ssl"), "1")  # Should be stripped
        del os.environ["PYTHONHTTPSVERIFY"]

        # Special characters
        os.environ["HTTP_PROXY"] = "http://user:pass@proxy.com:8080"
        self._assert_proxy_value("DIRECT;http://user:pass@proxy.com:8080")
        del os.environ["HTTP_PROXY"]

    def test_proxy_direct_default_behavior(self):
        """Test that proxy string starts with DIRECT and collects all proxy values"""
        # Test no proxy environment variables - should not create proxy config
        self._assert_proxy_value(None)

        # Test single HTTP_PROXY
        os.environ["HTTP_PROXY"] = "http://proxy1.com:8080"
        self._assert_proxy_value("DIRECT;http://proxy1.com:8080")
        del os.environ["HTTP_PROXY"]

        # Test both HTTP_PROXY and HTTPS_PROXY (order-independent check for Python 2 compatibility)
        os.environ["HTTP_PROXY"] = "http://proxy1.com:8080"
        os.environ["HTTPS_PROXY"] = "http://proxy2.com:8080"
        config = load_config()
        proxy_value = config.get("proxy")
        self.assertIsNotNone(proxy_value)
        # Check that it starts with DIRECT and contains both proxies (order-independent)
        self.assertTrue(proxy_value.startswith("DIRECT;"))  # type: ignore
        self.assertIn("http://proxy1.com:8080", proxy_value)  # type: ignore
        self.assertIn("http://proxy2.com:8080", proxy_value)  # type: ignore
        # Verify the format is correct (should have exactly 3 parts: DIRECT + 2 proxies)
        proxy_parts = proxy_value.split(";")  # type: ignore
        self.assertEqual(len(proxy_parts), 3)
        self.assertEqual(proxy_parts[0], "DIRECT")
        del os.environ["HTTP_PROXY"]
        del os.environ["HTTPS_PROXY"]

    def test_proxy_ddns_priority_over_standard(self):
        """Test that DDNS_PROXY takes precedence and standard proxies are ignored"""
        # Set both standard and DDNS proxy
        os.environ["HTTP_PROXY"] = "http://standard.proxy.com:8080"
        os.environ["HTTPS_PROXY"] = "http://standard2.proxy.com:8080"
        os.environ["DDNS_PROXY"] = "http://ddns.proxy.com:9090"
        config = load_config()
        # Only DDNS proxy should be used, standard proxies should be ignored
        self.assertEqual(config.get("proxy"), "http://ddns.proxy.com:9090")

    def test_proxy_whitespace_handling(self):
        """Test proxy handling with whitespace values"""
        # Test proxy with leading/trailing whitespace
        os.environ["HTTP_PROXY"] = "  http://proxy.com:8080  "
        self._assert_proxy_value("DIRECT;http://proxy.com:8080")
        del os.environ["HTTP_PROXY"]

        # Test empty whitespace proxy (should be ignored)
        os.environ["HTTP_PROXY"] = "   "
        self._assert_proxy_value(None)  # Should not create proxy config
        del os.environ["HTTP_PROXY"]

        # Test mixed: one real proxy, one whitespace
        os.environ["HTTP_PROXY"] = "http://real.proxy.com:8080"
        os.environ["HTTPS_PROXY"] = "   "
        self._assert_proxy_value("DIRECT;http://real.proxy.com:8080")
        del os.environ["HTTP_PROXY"]
        del os.environ["HTTPS_PROXY"]


if __name__ == "__main__":
    unittest.main()
