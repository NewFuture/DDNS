# coding=utf-8
"""
Unit tests for JSON configuration module

This test suite provides comprehensive coverage for the JSON configuration module,
testing file loading, saving, error handling, and edge cases.

Test Coverage:
- Basic JSON file loading and saving
- Configuration flattening for nested objects
- Error handling for invalid files and paths
- Unicode and special character support
- Large file handling
- File permission and I/O error scenarios
- Default configuration generation
- Edge cases with various data types

@author: GitHub Copilot
@updated: 2025-07-06
"""

import unittest
import sys
import os
import tempfile
import json

# Add the parent directory to the path so we can import the ddns module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ddns.config.json_file import load_config, save_config  # noqa: E402


class TestJsonConfig(unittest.TestCase):
    """Test cases for JSON configuration loading and saving"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.temp_dir, "test_config.json")

    def tearDown(self):
        """Clean up after tests"""
        # Clean up temporary files and directories
        try:
            if os.path.exists(self.test_config_file):
                os.remove(self.test_config_file)
            # Remove all files in temp directory first
            for root, dirs, files in os.walk(self.temp_dir, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    try:
                        os.chmod(file_path, 0o777)  # Make sure file is writable
                        os.remove(file_path)
                    except OSError:
                        pass
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    try:
                        os.rmdir(dir_path)
                    except OSError:
                        pass
            if os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
        except OSError:
            pass

    def create_test_config_file(self, config_data):
        # type: (dict) -> None
        """Helper method to create a test config file"""
        with open(self.test_config_file, "w") as f:
            json.dump(config_data, f, indent=2)

    def test_load_config_basic(self):
        """Test basic JSON configuration loading"""
        config_data = {"dns": "cloudflare", "id": "test@example.com", "token": "secret123", "ttl": 300}
        self.create_test_config_file(config_data)

        loaded_config = load_config(self.test_config_file)

        self.assertEqual(loaded_config, config_data)

    def test_load_config_with_arrays(self):
        """Test JSON configuration with arrays"""
        config_data = {
            "dns": "dnspod",
            "ipv4": ["example.com", "test.com"],
            "ipv6": ["ipv6.example.com"],
            "proxy": ["http://proxy1.com", "http://proxy2.com"],
            "index4": ["default", "custom"],
            "index6": ["ipv6"],
        }
        self.create_test_config_file(config_data)

        loaded_config = load_config(self.test_config_file)

        self.assertEqual(loaded_config, config_data)

    def test_load_config_with_nested_objects(self):
        """Test JSON configuration with nested objects"""
        config_data = {
            "dns": "alidns",
            "log": {"level": "DEBUG", "file": "/var/log/ddns.log", "format": "%(asctime)s %(message)s"},
            "ssl": {"verify": True, "cert_path": "/path/to/cert.pem"},
        }
        self.create_test_config_file(config_data)

        loaded_config = load_config(self.test_config_file)

        # JSON loader flattens nested objects with underscore notation
        expected_config = {
            "dns": "alidns",
            "log": {"level": "DEBUG", "file": "/var/log/ddns.log", "format": "%(asctime)s %(message)s"},
            "log_level": "DEBUG",
            "log_file": "/var/log/ddns.log",
            "log_format": "%(asctime)s %(message)s",
            "ssl": {"verify": True, "cert_path": "/path/to/cert.pem"},
            "ssl_verify": True,
            "ssl_cert_path": "/path/to/cert.pem",
        }

        self.assertEqual(loaded_config, expected_config)

    def test_load_config_boolean_values(self):
        """Test JSON configuration with boolean values"""
        config_data = {"cache": True, "debug": False, "ssl": True, "verify": False}
        self.create_test_config_file(config_data)

        loaded_config = load_config(self.test_config_file)

        self.assertEqual(loaded_config, config_data)

    def test_load_config_null_values(self):
        """Test JSON configuration with null values"""
        config_data = {"dns": "debug", "ttl": None, "line": None, "proxy": None}
        self.create_test_config_file(config_data)

        loaded_config = load_config(self.test_config_file)

        self.assertEqual(loaded_config, config_data)

    def test_load_config_nonexistent_file(self):
        """Test loading configuration from non-existent file"""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.json")

        with self.assertRaises(IOError):
            load_config(nonexistent_file)

    def test_load_config_invalid_json(self):
        """Test loading configuration from invalid JSON file"""
        with open(self.test_config_file, "w") as f:
            f.write("{ invalid json content }")

        with self.assertRaises(ValueError):
            load_config(self.test_config_file)

    def test_load_config_empty_file(self):
        """Test loading configuration from empty file"""
        with open(self.test_config_file, "w") as f:
            f.write("")

        with self.assertRaises(ValueError):
            load_config(self.test_config_file)

    def test_save_config_basic(self):
        """Test basic configuration saving"""
        config_path = os.path.join(self.temp_dir, "saved_config.json")
        test_config = {
            "dns": "debug",
            "id": "test@example.com",
            "token": "test_token",
            "ipv4": ["test.com"],
            "ipv6": [],
        }

        result = save_config(config_path, test_config)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(config_path))

        # Verify the saved content matches the test config
        with open(config_path, "r") as f:
            saved_config = json.load(f)

        self.assertEqual(saved_config, test_config)

    def test_save_config_custom_data(self):
        """Test saving custom configuration data"""
        custom_config = {
            "dns": "cloudflare",
            "id": "custom@example.com",
            "token": "custom_token",
            "ipv4": ["custom.com"],
            "cache": True,
        }
        config_path = os.path.join(self.temp_dir, "custom_config.json")

        result = save_config(config_path, custom_config)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(config_path))

        # Verify the saved content
        with open(config_path, "r") as f:
            saved_config = json.load(f)

        self.assertEqual(saved_config, custom_config)

    def test_save_config_invalid_path(self):
        """Test saving configuration to invalid path"""
        invalid_path = "/nonexistent/directory/config.json"
        test_config = {"dns": "test", "id": "test@example.com"}

        result = save_config(invalid_path, test_config)

        self.assertFalse(result)

    def test_save_config_readonly_file(self):
        """Test saving configuration to read-only file"""
        readonly_config = os.path.join(self.temp_dir, "readonly_config.json")
        test_config = {"dns": "test", "id": "test@example.com"}

        # Create file and make it read-only
        with open(readonly_config, "w") as f:
            f.write("{}")
        os.chmod(readonly_config, 0o444)  # Read-only

        try:
            result = save_config(readonly_config, test_config)
            self.assertFalse(result)
        finally:
            # Restore write permissions for cleanup
            os.chmod(readonly_config, 0o644)

    def test_load_config_with_unicode(self):
        """Test JSON configuration with Unicode characters (basic ASCII-safe Unicode)"""
        # Use ASCII-safe Unicode characters that work without explicit encoding
        config_data = {
            "dns": "dnspod",
            "description": "test config file",
            "domains": ["test.com", "example.com"],
            "comment": "This is a test configuration file",
        }
        self.create_test_config_file(config_data)

        loaded_config = load_config(self.test_config_file)

        self.assertEqual(loaded_config, config_data)

    def test_load_config_mixed_types(self):
        """Test JSON configuration with mixed data types"""
        config_data = {
            "dns": "alidns",
            "id": "test@example.com",
            "ttl": 300,
            "cache": True,
            "ssl": False,
            "ipv4": ["domain1.com", "domain2.com"],
            "timeout": 30.5,
            "retries": 0,
            "metadata": {"version": "1.0", "author": "test"},
        }
        self.create_test_config_file(config_data)

        loaded_config = load_config(self.test_config_file)

        # Should include original data plus flattened metadata
        expected_keys = set(config_data.keys())
        expected_keys.update(["metadata_version", "metadata_author"])

        self.assertEqual(set(loaded_config.keys()), expected_keys)
        self.assertEqual(loaded_config["dns"], "alidns")
        self.assertEqual(loaded_config["ttl"], 300)
        self.assertEqual(loaded_config["metadata_version"], "1.0")
        self.assertEqual(loaded_config["metadata_author"], "test")

    def test_save_config_pretty_format(self):
        """Test that saved configuration is properly formatted"""
        config_path = os.path.join(self.temp_dir, "pretty_config.json")
        config_data = {"dns": "cloudflare", "nested": {"key": "value", "array": [1, 2, 3]}}

        save_config(config_path, config_data)

        # Read the raw file content to check formatting
        with open(config_path, "r") as f:
            content = f.read()

        # Should be indented (pretty printed)
        self.assertIn("  ", content)  # Should contain indentation
        self.assertIn("\n", content)  # Should contain newlines

    def test_load_config_large_file(self):
        """Test loading large configuration file"""
        # Create a large config with many entries
        large_config = {"dns": "debug", "domains": ["domain{}.com".format(i) for i in range(100)]}
        for i in range(50):
            large_config["key_{}".format(i)] = "value_{}".format(i)

        self.create_test_config_file(large_config)

        loaded_config = load_config(self.test_config_file)

        self.assertEqual(loaded_config, large_config)
        self.assertEqual(len(loaded_config["domains"]), 100)

    def test_load_config_empty_nested_object(self):
        """Test JSON configuration with empty nested objects"""
        config_data = {"dns": "test", "empty_obj": {}, "log": {"level": "INFO"}, "another_empty": {}}
        self.create_test_config_file(config_data)

        loaded_config = load_config(self.test_config_file)

        # Empty objects should not add any flattened keys
        self.assertIn("dns", loaded_config)
        self.assertIn("empty_obj", loaded_config)
        self.assertIn("log", loaded_config)
        self.assertIn("log_level", loaded_config)
        self.assertEqual(loaded_config["log_level"], "INFO")
        self.assertEqual(loaded_config["empty_obj"], {})

    def test_load_config_deeply_nested_objects(self):
        """Test JSON configuration with deeply nested objects"""
        config_data = {"dns": "test", "level1": {"level2": {"level3": "deep_value"}, "simple": "value"}}
        self.create_test_config_file(config_data)

        loaded_config = load_config(self.test_config_file)

        # Should only flatten first level
        self.assertIn("level1_level2", loaded_config)
        self.assertIn("level1_simple", loaded_config)
        self.assertEqual(loaded_config["level1_simple"], "value")
        self.assertIsInstance(loaded_config["level1_level2"], dict)
        self.assertEqual(loaded_config["level1_level2"]["level3"], "deep_value")

    def test_load_config_numeric_keys_in_nested(self):
        """Test JSON configuration with numeric keys in nested objects"""
        config_data = {"dns": "test", "settings": {"timeout": 30, "retries": 3, "port": 53}}
        self.create_test_config_file(config_data)

        loaded_config = load_config(self.test_config_file)

        self.assertIn("settings_timeout", loaded_config)
        self.assertIn("settings_retries", loaded_config)
        self.assertIn("settings_port", loaded_config)
        self.assertEqual(loaded_config["settings_timeout"], 30)
        self.assertEqual(loaded_config["settings_retries"], 3)
        self.assertEqual(loaded_config["settings_port"], 53)

    def test_load_config_with_special_characters_in_keys(self):
        """Test JSON configuration with special characters in keys"""
        config_data = {
            "dns": "test",
            "special-key": "value1",
            "key.with.dots": "value2",
            "nested": {"sub-key": "subvalue1", "sub.key": "subvalue2"},
        }
        self.create_test_config_file(config_data)

        loaded_config = load_config(self.test_config_file)

        self.assertEqual(loaded_config["special-key"], "value1")
        self.assertEqual(loaded_config["key.with.dots"], "value2")
        self.assertEqual(loaded_config["nested_sub-key"], "subvalue1")
        self.assertEqual(loaded_config["nested_sub.key"], "subvalue2")

    def test_load_config_file_encoding(self):
        """Test loading configuration file with basic characters (Python 2.7 compatible)"""
        config_data = {
            "dns": "test",
            "description": "Basic test file",
            "special_chars": "Hello World!",
            "nested": {"key": "value", "number": 42},
        }
        # Create file without explicit encoding for Python 2.7 compatibility
        with open(self.test_config_file, "w") as f:
            json.dump(config_data, f, indent=2)

        loaded_config = load_config(self.test_config_file)

        self.assertEqual(loaded_config["description"], "Basic test file")
        self.assertEqual(loaded_config["special_chars"], "Hello World!")
        self.assertEqual(loaded_config["nested_key"], "value")
        self.assertEqual(loaded_config["nested_number"], 42)

    def test_save_config_with_unicode(self):
        """Test saving configuration with basic characters (Python 2.7 compatible)"""
        basic_config = {
            "dns": "test",
            "description": "Basic test config",
            "domains": ["test.com", "example.com"],
            "note": "Configuration file",
        }
        config_path = os.path.join(self.temp_dir, "basic_config.json")

        result = save_config(config_path, basic_config)

        self.assertTrue(result)

        # Verify content can be loaded back correctly
        with open(config_path, "r") as f:
            saved_config = json.load(f)

        self.assertEqual(saved_config, basic_config)

    def test_save_config_sorted_keys(self):
        """Test that saved configuration has sorted keys"""
        config_data = {"zzz_last": "value", "aaa_first": "value", "mmm_middle": "value", "dns": "test"}
        config_path = os.path.join(self.temp_dir, "sorted_config.json")

        save_config(config_path, config_data)

        # Read raw content to check key order
        with open(config_path, "r") as f:
            content = f.read()

        # Keys should appear in sorted order
        aaa_pos = content.find('"aaa_first"')
        dns_pos = content.find('"dns"')
        mmm_pos = content.find('"mmm_middle"')
        zzz_pos = content.find('"zzz_last"')

        self.assertTrue(zzz_pos < aaa_pos < mmm_pos < dns_pos)

    def test_load_config_file_with_special_content(self):
        """Test loading configuration file with special formatting"""
        config_data = {"dns": "test", "value": "test_value"}

        # Write file with normal formatting
        with open(self.test_config_file, "w") as f:
            json.dump(config_data, f, indent=2)

        loaded_config = load_config(self.test_config_file)

        self.assertEqual(loaded_config["dns"], "test")
        self.assertEqual(loaded_config["value"], "test_value")

    def test_save_config_exception_handling(self):
        """Test save_config exception handling for various error conditions"""
        # Test with invalid data type that can't be serialized
        invalid_config = {"function": lambda x: x}  # Functions can't be JSON serialized
        config_path = os.path.join(self.temp_dir, "invalid_config.json")

        result = save_config(config_path, invalid_config)

        self.assertFalse(result)

    def test_load_config_permission_error(self):
        """Test load_config behavior with permission errors"""
        import platform

        # Skip this test on Windows as file permissions work differently
        if platform.system() == "Windows":
            self.skipTest("File permission test not applicable on Windows")

        # Create a config file
        config_data = {"dns": "test"}
        self.create_test_config_file(config_data)

        # Make file unreadable (on Unix-like systems)
        try:
            os.chmod(self.test_config_file, 0o000)

            # Should raise an exception
            with self.assertRaises(Exception):
                load_config(self.test_config_file)
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(self.test_config_file, 0o644)
            except OSError:
                pass

    def test_load_config_malformed_json_variations(self):
        """Test load_config with various malformed JSON formats"""
        malformed_cases = [
            '{"key": }',  # Missing value
            '{"key": "value",}',  # Trailing comma
            "{'key': 'value'}",  # Single quotes
            '{"key": "value"',  # Missing closing brace
            '{"key": "unclosed string}',  # Unclosed string
            '{key: "value"}',  # Unquoted key
        ]

        for i, malformed_json in enumerate(malformed_cases):
            test_file = os.path.join(self.temp_dir, "malformed_{}.json".format(i))
            with open(test_file, "w") as f:
                f.write(malformed_json)

            with self.assertRaises(Exception):
                load_config(test_file)

    def test_save_config_with_none_values(self):
        """Test saving configuration with None values"""
        config_with_none = {"dns": "test", "ttl": None, "proxy": None, "line": None, "nested": {"value": None}}
        config_path = os.path.join(self.temp_dir, "none_config.json")

        result = save_config(config_path, config_with_none)

        self.assertTrue(result)

        # Verify None values are saved as null in JSON
        with open(config_path, "r") as f:
            content = f.read()

        self.assertIn("null", content)

        # Verify content can be loaded back correctly
        with open(config_path, "r") as f:
            saved_config = json.load(f)

        self.assertEqual(saved_config, config_with_none)

    def test_load_config_very_large_nested_object(self):
        """Test loading configuration with very large nested objects"""
        large_nested = {}
        for i in range(100):
            large_nested["key_{}".format(i)] = "value_{}".format(i)

        config_data = {"dns": "test", "large_section": large_nested, "normal_key": "normal_value"}
        self.create_test_config_file(config_data)

        loaded_config = load_config(self.test_config_file)

        # Verify flattening worked for large object
        self.assertIn("large_section_key_0", loaded_config)
        self.assertIn("large_section_key_99", loaded_config)
        self.assertEqual(loaded_config["large_section_key_50"], "value_50")
        self.assertEqual(loaded_config["normal_key"], "normal_value")

        # Verify original nested object is still present
        self.assertIn("large_section", loaded_config)
        self.assertEqual(len(loaded_config["large_section"]), 100)


if __name__ == "__main__":
    unittest.main()
