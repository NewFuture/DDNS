# coding=utf-8
"""
Unit tests for extra field support in ddns.config.config module
@author: GitHub Copilot
"""

from __init__ import unittest
from ddns.config.config import Config  # noqa: E402


class TestConfigExtra(unittest.TestCase):
    """Test extra field collection from various config sources"""

    def test_extra_from_cli(self):
        """Test extra fields from CLI config with extra_ prefix"""
        cli_config = {
            "dns": "cloudflare",
            "id": "test@example.com",
            "extra_proxied": "true",
            "extra_comment": "Test comment",
            "extra_custom_field": "custom_value",
        }
        config = Config(cli_config=cli_config)
        self.assertEqual(config.dns, "cloudflare")
        self.assertIsInstance(config.extra, dict)
        self.assertEqual(config.extra.get("proxied"), "true")
        self.assertEqual(config.extra.get("comment"), "Test comment")
        self.assertEqual(config.extra.get("custom_field"), "custom_value")

    def test_extra_from_json(self):
        """Test extra fields from JSON config as extra object"""
        json_config = {
            "dns": "alidns",
            "id": "test_id",
            "extra": {"proxied": False, "comment": "JSON comment", "tags": ["tag1", "tag2"]},
        }
        config = Config(json_config=json_config)
        self.assertEqual(config.dns, "alidns")
        self.assertIsInstance(config.extra, dict)
        self.assertFalse(config.extra.get("proxied"))
        self.assertEqual(config.extra.get("comment"), "JSON comment")
        self.assertEqual(config.extra.get("tags"), ["tag1", "tag2"])

    def test_extra_from_json_undefined_fields(self):
        """Test undefined fields in JSON config are collected as extra"""
        json_config = {"dns": "dnspod", "id": "test_id", "custom_field": "custom_value", "another_field": 123}
        config = Config(json_config=json_config)
        self.assertEqual(config.dns, "dnspod")
        self.assertEqual(config.extra.get("custom_field"), "custom_value")
        self.assertEqual(config.extra.get("another_field"), 123)

    def test_extra_from_env(self):
        """Test extra fields from environment config"""
        env_config = {"dns": "cloudflare", "extra_proxied": "true", "extra_ttl_override": "300"}
        config = Config(env_config=env_config)
        self.assertEqual(config.dns, "cloudflare")
        self.assertEqual(config.extra.get("proxied"), "true")
        self.assertEqual(config.extra.get("ttl_override"), "300")

    def test_extra_from_env_undefined_fields(self):
        """Test undefined fields in env config are collected as extra"""
        env_config = {"dns": "dnspod", "custom_env_field": "env_value", "another_env_field": "another_value"}
        config = Config(env_config=env_config)
        self.assertEqual(config.dns, "dnspod")
        self.assertEqual(config.extra.get("custom_env_field"), "env_value")
        self.assertEqual(config.extra.get("another_env_field"), "another_value")

    def test_extra_priority_cli_over_json(self):
        """Test CLI extra fields have priority over JSON"""
        cli_config = {"extra_comment": "CLI comment", "extra_field1": "cli_value"}
        json_config = {"extra": {"comment": "JSON comment", "field1": "json_value", "field2": "json_only"}}
        config = Config(cli_config=cli_config, json_config=json_config)
        self.assertEqual(config.extra.get("comment"), "CLI comment")
        self.assertEqual(config.extra.get("field1"), "cli_value")
        self.assertEqual(config.extra.get("field2"), "json_only")

    def test_extra_priority_json_over_env(self):
        """Test JSON extra fields have priority over ENV"""
        json_config = {"extra": {"comment": "JSON comment", "field1": "json_value"}}
        env_config = {"extra_comment": "ENV comment", "extra_field1": "env_value", "extra_field2": "env_only"}
        config = Config(json_config=json_config, env_config=env_config)
        self.assertEqual(config.extra.get("comment"), "JSON comment")
        self.assertEqual(config.extra.get("field1"), "json_value")
        self.assertEqual(config.extra.get("field2"), "env_only")

    def test_extra_priority_all_sources(self):
        """Test complete priority chain: CLI > JSON > ENV"""
        cli_config = {"extra_field1": "cli_value"}
        json_config = {"extra": {"field1": "json_value", "field2": "json_value"}}
        env_config = {"extra_field1": "env_value", "extra_field2": "env_value", "extra_field3": "env_value"}
        config = Config(cli_config=cli_config, json_config=json_config, env_config=env_config)
        self.assertEqual(config.extra.get("field1"), "cli_value")
        self.assertEqual(config.extra.get("field2"), "json_value")
        self.assertEqual(config.extra.get("field3"), "env_value")

    def test_extra_empty_by_default(self):
        """Test extra is empty dict when no extra fields provided"""
        config = Config()
        self.assertIsInstance(config.extra, dict)
        self.assertEqual(len(config.extra), 0)

    def test_extra_does_not_include_known_fields(self):
        """Test that known configuration fields are not collected as extra"""
        cli_config = {
            "dns": "cloudflare",
            "id": "test@example.com",
            "token": "secret",
            "ttl": "300",
            "extra_custom": "custom_value",
        }
        config = Config(cli_config=cli_config)
        # Known fields should not be in extra
        self.assertNotIn("dns", config.extra)
        self.assertNotIn("id", config.extra)
        self.assertNotIn("token", config.extra)
        self.assertNotIn("ttl", config.extra)
        # Only custom field should be in extra
        self.assertEqual(config.extra.get("custom"), "custom_value")

    def test_extra_does_not_include_schema_field(self):
        """Test that $schema field from JSON config is not collected as extra"""
        json_config = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
            "dns": "tencentcloud",
            "id": "test_id",
            "token": "test_token",
            "ipv4": ["example.com"],
            "extra": {"proxied": True},
        }
        config = Config(json_config=json_config)
        # $schema should not be in extra
        self.assertNotIn("$schema", config.extra)
        # Other extra fields should be collected
        self.assertTrue(config.extra.get("proxied"))
        # Known fields should be accessible
        self.assertEqual(config.dns, "tencentcloud")
        self.assertEqual(config.id, "test_id")

    def test_extra_with_json_extra_object_and_undefined_fields(self):
        """Test JSON config with both extra object and undefined fields"""
        json_config = {
            "dns": "cloudflare",
            "extra": {"proxied": True, "comment": "From extra object"},
            "custom_field": "From undefined field",
            "another_field": 123,
        }
        config = Config(json_config=json_config)
        # Both should be collected
        self.assertTrue(config.extra.get("proxied"))
        self.assertEqual(config.extra.get("comment"), "From extra object")
        self.assertEqual(config.extra.get("custom_field"), "From undefined field")
        self.assertEqual(config.extra.get("another_field"), 123)

    def test_extra_in_md5_hash(self):
        """Test that extra fields are included in MD5 hash"""
        config1 = Config(cli_config={"dns": "cloudflare", "extra_field": "value1"})
        config2 = Config(cli_config={"dns": "cloudflare", "extra_field": "value1"})
        config3 = Config(cli_config={"dns": "cloudflare", "extra_field": "value2"})

        # Same extra should produce same hash
        self.assertEqual(config1.md5(), config2.md5())
        # Different extra should produce different hash
        self.assertNotEqual(config1.md5(), config3.md5())

    def test_extra_with_complex_values(self):
        """Test extra fields with complex data types"""
        json_config = {
            "dns": "cloudflare",
            "extra": {
                "tags": ["tag1", "tag2", "tag3"],
                "settings": {"key1": "value1", "key2": "value2"},
                "enabled": True,
                "priority": 10,
            },
        }
        config = Config(json_config=json_config)
        self.assertEqual(config.extra.get("tags"), ["tag1", "tag2", "tag3"])
        self.assertEqual(config.extra.get("settings"), {"key1": "value1", "key2": "value2"})
        self.assertTrue(config.extra.get("enabled"))
        self.assertEqual(config.extra.get("priority"), 10)

    def test_extra_env_with_extra_object(self):
        """Test env config with extra object (dict)"""
        env_config = {"dns": "cloudflare", "extra": {"field1": "value1", "field2": "value2"}}
        config = Config(env_config=env_config)
        self.assertEqual(config.extra.get("field1"), "value1")
        self.assertEqual(config.extra.get("field2"), "value2")

    def test_extra_mixed_prefix_and_object(self):
        """Test mixing extra_ prefix and extra object in same source"""
        json_config = {
            "dns": "cloudflare",
            "extra": {"from_object": "object_value"},
            "undefined_field": "undefined_value",
        }
        cli_config = {"extra_from_prefix": "prefix_value"}
        config = Config(cli_config=cli_config, json_config=json_config)
        self.assertEqual(config.extra.get("from_object"), "object_value")
        self.assertEqual(config.extra.get("undefined_field"), "undefined_value")
        self.assertEqual(config.extra.get("from_prefix"), "prefix_value")


if __name__ == "__main__":
    unittest.main()
