# coding=utf-8
"""
Unit tests for environment variable extra field support
@author: GitHub Copilot
"""

import os
from __init__ import unittest
from ddns.config.env import load_config  # noqa: E402


class TestEnvExtraFields(unittest.TestCase):
    """Test environment variable extra field parsing"""

    def setUp(self):
        """Clear DDNS environment variables before each test"""
        self._clear_env_prefix("DDNS_")

    def tearDown(self):
        """Clean up after tests"""
        self._clear_env_prefix("DDNS_")

    def _clear_env_prefix(self, prefix):
        # type: (str) -> None
        """Clear environment variables with a specific prefix (case-insensitive)"""
        keys_to_delete = [key for key in os.environ.keys() if key.upper().startswith(prefix.upper())]
        for key in keys_to_delete:
            del os.environ[key]

    def test_env_extra_single_field(self):
        """Test single DDNS_EXTRA_XXX environment variable"""
        os.environ["DDNS_DNS"] = "cloudflare"
        os.environ["DDNS_EXTRA_PROXIED"] = "true"

        config = load_config()
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("extra_proxied"), "true")

    def test_env_extra_multiple_fields(self):
        """Test multiple DDNS_EXTRA_XXX environment variables"""
        os.environ["DDNS_DNS"] = "alidns"
        os.environ["DDNS_EXTRA_PROXIED"] = "true"
        os.environ["DDNS_EXTRA_COMMENT"] = "Test comment"
        os.environ["DDNS_EXTRA_PRIORITY"] = "10"

        config = load_config()
        self.assertEqual(config.get("dns"), "alidns")
        self.assertEqual(config.get("extra_proxied"), "true")
        self.assertEqual(config.get("extra_comment"), "Test comment")
        self.assertEqual(config.get("extra_priority"), "10")

    def test_env_extra_with_standard_vars(self):
        """Test DDNS_EXTRA_XXX mixed with standard environment variables"""
        os.environ["DDNS_DNS"] = "cloudflare"
        os.environ["DDNS_ID"] = "test@example.com"
        os.environ["DDNS_TOKEN"] = "secret123"
        os.environ["DDNS_EXTRA_CUSTOM_FIELD"] = "custom_value"
        os.environ["DDNS_TTL"] = "300"

        config = load_config()
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("id"), "test@example.com")
        self.assertEqual(config.get("token"), "secret123")
        self.assertEqual(config.get("ttl"), "300")
        self.assertEqual(config.get("extra_custom_field"), "custom_value")

    def test_env_extra_case_insensitive(self):
        """Test that DDNS_EXTRA_XXX is case-insensitive"""
        os.environ["ddns_extra_field1"] = "value1"
        os.environ["DDNS_EXTRA_FIELD2"] = "value2"
        os.environ["Ddns_Extra_Field3"] = "value3"

        config = load_config()
        self.assertEqual(config.get("extra_field1"), "value1")
        self.assertEqual(config.get("extra_field2"), "value2")
        self.assertEqual(config.get("extra_field3"), "value3")

    def test_env_extra_with_underscores(self):
        """Test DDNS_EXTRA_XXX with underscores in field name"""
        os.environ["DDNS_EXTRA_CUSTOM_FIELD_NAME"] = "value1"
        os.environ["DDNS_EXTRA_ANOTHER_FIELD"] = "value2"

        config = load_config()
        self.assertEqual(config.get("extra_custom_field_name"), "value1")
        self.assertEqual(config.get("extra_another_field"), "value2")

    def test_env_extra_with_dots(self):
        """Test DDNS_EXTRA.XXX format (dots converted to underscores)"""
        os.environ["DDNS_EXTRA.FIELD1"] = "value1"
        os.environ["DDNS_EXTRA.FIELD2"] = "value2"

        config = load_config()
        # Dots should be converted to underscores
        self.assertEqual(config.get("extra_field1"), "value1")
        self.assertEqual(config.get("extra_field2"), "value2")

    def test_env_extra_numeric_values(self):
        """Test DDNS_EXTRA_XXX with numeric values"""
        os.environ["DDNS_EXTRA_PRIORITY"] = "100"
        os.environ["DDNS_EXTRA_WEIGHT"] = "0.5"

        config = load_config()
        self.assertEqual(config.get("extra_priority"), "100")
        self.assertEqual(config.get("extra_weight"), "0.5")

    def test_env_extra_empty_value(self):
        """Test DDNS_EXTRA_XXX with empty value"""
        os.environ["DDNS_EXTRA_COMMENT"] = ""

        config = load_config()
        self.assertEqual(config.get("extra_comment"), "")

    def test_env_no_extra_vars(self):
        """Test that config works without any extra environment variables"""
        # Clear all DDNS env vars first
        self._clear_env_prefix("DDNS_")

        os.environ["DDNS_DNS"] = "cloudflare"
        os.environ["DDNS_ID"] = "test@example.com"

        config = load_config()
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("id"), "test@example.com")
        # No extra_* keys should exist (only from this test)
        extra_keys = [k for k in config.keys() if k.startswith("extra_")]
        # Should have no extra keys from this test's environment variables
        self.assertEqual(len(extra_keys), 0, "Found unexpected extra keys: {}".format(extra_keys))

    def test_env_extra_json_array(self):
        """Test DDNS_EXTRA_XXX with JSON array format"""
        os.environ["DDNS_EXTRA_TAGS"] = '["tag1", "tag2", "tag3"]'

        config = load_config()
        self.assertEqual(config.get("extra_tags"), ["tag1", "tag2", "tag3"])

    def test_env_extra_special_characters(self):
        """Test DDNS_EXTRA_XXX with special characters"""
        os.environ["DDNS_EXTRA_URL"] = "https://example.com/path?key=value&foo=bar"

        config = load_config()
        self.assertEqual(config.get("extra_url"), "https://example.com/path?key=value&foo=bar")


if __name__ == "__main__":
    unittest.main()
