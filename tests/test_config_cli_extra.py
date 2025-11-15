# coding=utf-8
"""
Unit tests for CLI extra field support in ddns.config.cli module
@author: GitHub Copilot
"""

import sys
from __init__ import unittest
from ddns.config.cli import load_config  # noqa: E402


class TestCliExtraFields(unittest.TestCase):
    """Test CLI extra field parsing"""

    def setUp(self):
        """Save original sys.argv"""
        self.original_argv = sys.argv

    def tearDown(self):
        """Restore original sys.argv"""
        sys.argv = self.original_argv

    def test_cli_extra_single_field(self):
        """Test single --extra.xxx argument"""
        sys.argv = ["ddns", "--dns", "cloudflare", "--extra.proxied", "true"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("extra_proxied"), "true")

    def test_cli_extra_multiple_fields(self):
        """Test multiple --extra.xxx arguments"""
        sys.argv = [
            "ddns",
            "--dns",
            "cloudflare",
            "--extra.proxied",
            "true",
            "--extra.comment",
            "Test comment",
            "--extra.priority",
            "10",
        ]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("extra_proxied"), "true")
        self.assertEqual(config.get("extra_comment"), "Test comment")
        self.assertEqual(config.get("extra_priority"), "10")

    def test_cli_extra_with_standard_args(self):
        """Test --extra.xxx mixed with standard arguments"""
        sys.argv = [
            "ddns",
            "--dns",
            "alidns",
            "--id",
            "test@example.com",
            "--token",
            "secret123",
            "--extra.custom_field",
            "custom_value",
            "--ttl",
            "300",
        ]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config.get("dns"), "alidns")
        self.assertEqual(config.get("id"), "test@example.com")
        self.assertEqual(config.get("token"), "secret123")
        self.assertEqual(config.get("ttl"), 300)
        self.assertEqual(config.get("extra_custom_field"), "custom_value")

    def test_cli_extra_flag_without_value(self):
        """Test --extra.xxx without a value (should be treated as True)"""
        sys.argv = ["ddns", "--dns", "cloudflare", "--extra.enabled"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertTrue(config.get("extra_enabled"))

    def test_cli_extra_with_dots_in_name(self):
        """Test --extra.xxx.yyy format (nested key)"""
        sys.argv = ["ddns", "--dns", "cloudflare", "--extra.settings.key1", "value1"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config.get("dns"), "cloudflare")
        # The key should be settings.key1 (not nested object)
        self.assertEqual(config.get("extra_settings.key1"), "value1")

    def test_cli_extra_empty_value(self):
        """Test --extra.xxx with empty string value"""
        sys.argv = ["ddns", "--dns", "cloudflare", "--extra.comment", ""]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("extra_comment"), "")

    def test_cli_extra_numeric_values(self):
        """Test --extra.xxx with numeric string values"""
        sys.argv = ["ddns", "--dns", "cloudflare", "--extra.priority", "100", "--extra.weight", "0.5"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config.get("extra_priority"), "100")
        self.assertEqual(config.get("extra_weight"), "0.5")

    def test_cli_extra_special_characters(self):
        """Test --extra.xxx with special characters in value"""
        sys.argv = ["ddns", "--dns", "cloudflare", "--extra.url", "https://example.com/path?key=value"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config.get("extra_url"), "https://example.com/path?key=value")

    def test_cli_no_extra_args(self):
        """Test that config works without any extra arguments"""
        sys.argv = ["ddns", "--dns", "cloudflare", "--id", "test@example.com"]
        config = load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
        self.assertEqual(config.get("dns"), "cloudflare")
        self.assertEqual(config.get("id"), "test@example.com")
        # No extra_* keys should exist
        extra_keys = [k for k in config.keys() if k.startswith("extra_")]
        self.assertEqual(len(extra_keys), 0)


if __name__ == "__main__":
    unittest.main()
