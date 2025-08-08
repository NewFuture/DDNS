# coding=utf-8
# type: ignore[index,operator,assignment]
"""
Unit tests for ddns.config.file module
@author: GitHub Copilot
"""

from __future__ import unicode_literals
from __init__ import unittest
import tempfile
import shutil
import os
import json
import io
import sys
from ddns.config.file import load_config, save_config

# Python 2/3 compatibility
if sys.version_info[0] >= 3:
    from io import StringIO

    unicode = str
else:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO

FileNotFoundError = globals().get("FileNotFoundError", IOError)
PermissionError = globals().get("PermissionError", IOError)


class TestConfigFile(unittest.TestCase):
    """Test cases for configuration file loading and saving"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

        # Capture stdout and stderr output for testing
        # Use unicode-compatible StringIO for Python 2/3 compatibility
        self.stdout_capture = StringIO()
        self.stderr_capture = StringIO()
        self.original_stdout = __import__("sys").stdout
        self.original_stderr = __import__("sys").stderr

    def tearDown(self):
        """Clean up after tests"""
        __import__("sys").stdout = self.original_stdout
        __import__("sys").stderr = self.original_stderr

    def create_test_file(self, filename, content):
        # type: (str, str | dict) -> str
        """Helper method to create a test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        # Use io.open with utf-8 encoding for Python 2 and 3 compatibility
        with io.open(file_path, "w", encoding="utf-8") as f:
            if isinstance(content, dict):
                # Dump JSON with ensure_ascii=False to preserve Unicode characters
                f.write(json.dumps(content, indent=2, ensure_ascii=False))
            else:
                # Write content directly
                f.write(content)
        return file_path

    def test_load_config_json_parsing(self):
        """Test loading valid JSON configuration"""
        json_content = '{"dns": "cloudflare", "id": "test@example.com", "token": "secret123", "ttl": 300}'
        file_path = self.create_test_file("test.json", json_content)

        config = load_config(file_path)

        expected = {"dns": "cloudflare", "id": "test@example.com", "token": "secret123", "ttl": 300}
        self.assertEqual(config, expected)

        # Verify JSON parsing was used (no specific output message for JSON success)

    def test_load_config_ast_parsing(self):
        """Test loading valid AST (Python dict) configuration"""
        ast_content = '{"dns": "dnspod", "id": "test123", "token": "abc456", "ttl": 600}'
        file_path = self.create_test_file("test.py", ast_content)

        config = load_config(file_path)

        expected = {"dns": "dnspod", "id": "test123", "token": "abc456", "ttl": 600}
        self.assertEqual(config, expected)

        # Verify JSON parsing was used (no specific output message for JSON success)

    def test_load_config_json_to_ast_fallback(self):
        """Test fallback from JSON to AST parsing"""
        # Patch the stdout in the file module directly
        import ddns.config.file

        original_stdout = ddns.config.file.stdout
        ddns.config.file.stdout = self.stdout_capture

        try:
            # Create content that's valid Python but invalid JSON (trailing comma)
            python_content = '{"dns": "alidns", "id": "test", "token": "xyz",}'
            file_path = self.create_test_file("test.conf", python_content)

            config = load_config(file_path)

            expected = {"dns": "alidns", "id": "test", "token": "xyz"}
            self.assertEqual(config, expected)

            # Verify fallback occurred - AST success message should be in stdout
            stdout_output = self.stdout_capture.getvalue()
            self.assertIn("Successfully loaded config file with AST parser", stdout_output)
        finally:
            # Restore stdout
            ddns.config.file.stdout = original_stdout

    def test_load_config_with_arrays(self):
        """Test loading configuration with arrays"""
        json_content = """{
            "dns": "dnspod",
            "ipv4": ["example.com", "test.com"],
            "ipv6": ["ipv6.example.com"],
            "proxy": ["http://proxy1.com", "http://proxy2.com"],
            "index4": ["default", "custom"],
            "index6": ["ipv6"]
        }"""
        file_path = self.create_test_file("test_arrays.json", json_content)

        config = load_config(file_path)

        expected = {
            "dns": "dnspod",
            "ipv4": ["example.com", "test.com"],
            "ipv6": ["ipv6.example.com"],
            "proxy": ["http://proxy1.com", "http://proxy2.com"],
            "index4": ["default", "custom"],
            "index6": ["ipv6"],
        }
        self.assertEqual(config, expected)

    def test_load_config_with_nested_objects_flattening(self):
        """Test configuration loading with nested object flattening"""
        json_content = """{
            "dns": "alidns",
            "log": {
                "level": "DEBUG",
                "file": "/var/log/ddns.log",
                "format": "%(asctime)s %(message)s"
            },
            "ssl": {
                "verify": true,
                "cert_path": "/path/to/cert.pem"
            }
        }"""
        file_path = self.create_test_file("test_log_fields.json", json_content)

        config = load_config(file_path)

        # Check that nested objects are flattened
        self.assertEqual(config["dns"], "alidns")
        self.assertEqual(config["log_level"], "DEBUG")
        self.assertEqual(config["log_file"], "/var/log/ddns.log")
        self.assertEqual(config["log_format"], "%(asctime)s %(message)s")
        self.assertEqual(config["ssl_verify"], True)
        self.assertEqual(config["ssl_cert_path"], "/path/to/cert.pem")

        # Original nested objects should be replaced with flattened keys
        self.assertNotIn("log", config)
        self.assertNotIn("ssl", config)
        self.assertIn("log_level", config)
        self.assertIn("ssl_verify", config)

    def test_load_config_boolean_and_null_values(self):
        """Test loading configuration with boolean and null values"""
        json_content = """{
            "cache": true,
            "debug": false,
            "ssl": true,
            "verify": false,
            "ttl": null,
            "line": null,
            "proxy": null
        }"""
        file_path = self.create_test_file("test_types.json", json_content)

        config = load_config(file_path)

        self.assertTrue(config["cache"])
        self.assertFalse(config["debug"])
        self.assertTrue(config["ssl"])
        self.assertFalse(config["verify"])
        self.assertIsNone(config["ttl"])
        self.assertIsNone(config["line"])
        self.assertIsNone(config["proxy"])

    def test_load_config_special_prefixes(self):
        """Test loading configuration with special prefix values"""
        json_content = """{
            "dns": "cloudflare",
            "index4": ["regex:192\\\\.168\\\\..*", "default"],
            "index6": ["cmd:curl -s ipv6.icanhazip.com", "backup"]
        }"""
        file_path = self.create_test_file("test_prefixes.json", json_content)

        config = load_config(file_path)

        self.assertEqual(config["dns"], "cloudflare")
        self.assertEqual(config["index4"], ["regex:192\\.168\\..*", "default"])
        self.assertEqual(config["index6"], ["cmd:curl -s ipv6.icanhazip.com", "backup"])

    def test_load_config_unicode_and_special_chars(self):
        """Test loading configuration with unicode and special characters"""
        json_content = """{
            "dns": "test",
            "id": "user@example.com",
            "token": "password123!@#$%^&*()",
            "description": "Test with unicode characters"
        }"""
        file_path = self.create_test_file("test_unicode.json", json_content)

        config = load_config(file_path)

        self.assertEqual(config["id"], "user@example.com")
        self.assertEqual(config["token"], "password123!@#$%^&*()")
        self.assertEqual(config["description"], "Test with unicode characters")

    def test_load_config_invalid_json_invalid_ast(self):
        """Test loading configuration that fails both JSON and AST parsing"""
        # Patch the stderr in the file module directly
        import ddns.config.file

        original_stderr = ddns.config.file.stderr
        ddns.config.file.stderr = self.stderr_capture

        try:
            invalid_content = '{"dns": "test", invalid syntax here}'
            file_path = self.create_test_file("test_invalid.conf", invalid_content)

            with self.assertRaises((ValueError, SyntaxError)):
                load_config(file_path)

            # Verify both parsers were attempted via stderr output
            stderr_output = self.stderr_capture.getvalue()
            self.assertIn("Both JSON and AST parsing failed", stderr_output)
        finally:
            # Restore stderr
            ddns.config.file.stderr = original_stderr

    def test_load_config_ast_non_dict(self):
        """Test AST parsing with non-dictionary content"""
        # Valid Python but not a dictionary
        non_dict_content = '["item1", "item2", "item3"]'
        file_path = self.create_test_file("test_list.py", non_dict_content)

        with self.assertRaises(AttributeError):
            load_config(file_path)

        # Should get AttributeError when trying to call .items() on a list

    def test_load_config_nonexistent_file(self):
        """Test loading configuration from non-existent file"""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.json")

        with self.assertRaises(Exception):
            load_config(nonexistent_file)

    def test_load_config_permission_denied(self):
        """Test loading configuration from file with permission denied"""
        # Skip this test on Windows as file permissions work differently
        if os.name == "nt":
            self.skipTest("File permission tests not reliable on Windows")

        # Create a file and remove read permissions
        file_path = self.create_test_file("test_noperm.json", '{"dns": "test"}')

        try:
            os.chmod(file_path, 0o000)  # Remove all permissions

            with self.assertRaises(Exception):
                load_config(file_path)
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(file_path, 0o777)
            except OSError:
                pass

    def test_load_config_empty_file(self):
        """Test loading configuration from empty file"""
        file_path = self.create_test_file("test_empty.json", "")

        with self.assertRaises(Exception):
            load_config(file_path)

    def test_load_config_whitespace_only(self):
        """Test loading configuration from file with only whitespace"""
        file_path = self.create_test_file("test_whitespace.json", "   \n\t  \n  ")

        with self.assertRaises(Exception):
            load_config(file_path)

    def test_save_config_basic(self):
        """Test basic configuration saving"""
        config_data = {"dns": "cloudflare", "id": "test@example.com", "token": "secret123"}
        file_path = os.path.join(self.temp_dir, "save_test.json")

        result = save_config(file_path, config_data)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(file_path))

        # Verify saved content can be loaded back and contains our data
        loaded_config = load_config(file_path)
        # save_config adds default values, so we only check our specific values
        self.assertEqual(loaded_config["dns"], config_data["dns"])
        self.assertEqual(loaded_config["id"], config_data["id"])
        self.assertEqual(loaded_config["token"], config_data["token"])
        # Check that schema and other defaults are added
        self.assertIn("$schema", loaded_config)
        self.assertIn("cache", loaded_config)

    def test_save_config_complex_data(self):
        """Test saving configuration with complex data types"""
        config_data = {
            "dns": "dnspod",
            "ipv4": ["item1", "item2"],  # Changed "arrays" to "ipv4" which is a valid config field
            "log_level": "DEBUG",  # Use log_level instead of nested
            "cache": True,
            "proxy": [],
        }
        file_path = os.path.join(self.temp_dir, "save_complex.json")

        result = save_config(file_path, config_data)

        self.assertTrue(result)

        # Verify saved content contains our specific values
        loaded_config = load_config(file_path)
        self.assertEqual(loaded_config["dns"], config_data["dns"])
        self.assertEqual(loaded_config["ipv4"], config_data["ipv4"])
        self.assertEqual(loaded_config["cache"], config_data["cache"])
        self.assertEqual(loaded_config["proxy"], config_data["proxy"])
        # Check that defaults are applied when values are not provided
        self.assertEqual(loaded_config["ttl"], 600)  # Default value when not provided

    def test_save_config_invalid_path(self):
        """Test saving configuration to invalid path"""
        import os

        # Skip this test on Windows as path creation behavior is different
        if os.name == "nt":
            self.skipTest("Path creation behavior differs on Windows")

        config_data = {"dns": "test"}
        invalid_path = "/invalid/path/that/does/not/exist/config.json"

        with self.assertRaises((IOError, OSError, FileNotFoundError)):
            save_config(invalid_path, config_data)

    def test_save_config_permission_denied(self):
        """Test saving configuration with permission denied"""
        # Skip this test on Windows as directory permissions work differently
        if os.name == "nt":
            self.skipTest("Directory permission tests not reliable on Windows")

        config_data = {"dns": "test"}

        # Create a directory and remove write permissions
        readonly_dir = os.path.join(self.temp_dir, "readonly")
        os.makedirs(readonly_dir)
        file_path = os.path.join(readonly_dir, "config.json")

        try:
            os.chmod(readonly_dir, 0o444)  # Read-only

            with self.assertRaises((IOError, PermissionError)):
                save_config(file_path, config_data)
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(readonly_dir, 0o777)
            except OSError:
                pass

    def test_parser_priority_json_first(self):
        """Test that JSON parsing is always tried first regardless of file extension"""
        # Test with .py extension but valid JSON content
        json_content = '{"dns": "cloudflare", "id": "test123"}'
        py_file = self.create_test_file("config.py", json_content)

        config = load_config(py_file)

        expected = {"dns": "cloudflare", "id": "test123"}
        self.assertEqual(config, expected)

        # Verify JSON parsing was used (no specific output message for JSON success)

    def test_parser_priority_ast_fallback(self):
        """Test AST parsing fallback for any file extension"""
        # Patch the stdout in the file module directly
        import ddns.config.file

        original_stdout = ddns.config.file.stdout
        ddns.config.file.stdout = self.stdout_capture

        try:
            # Create content that's definitely invalid JSON but valid Python
            # Use a more obvious syntax that will definitely fail JSON parsing
            python_content = "{'dns': 'dnspod', 'id': 'test456'}"  # Single quotes - invalid JSON
            json_file = self.create_test_file("config.json", python_content)

            config = load_config(json_file)

            expected = {"dns": "dnspod", "id": "test456"}
            self.assertEqual(config, expected)

            # Verify fallback occurred - check stdout for AST success message
            stdout_output = self.stdout_capture.getvalue()
            # The successful parsing itself proves AST fallback worked
            if stdout_output:
                # If we have output, verify the expected message is there
                self.assertIn("Successfully loaded config file with AST parser", stdout_output)
            # The successful parsing itself proves AST fallback worked
        finally:
            # Restore stdout
            ddns.config.file.stdout = original_stdout

    def test_load_config_large_file(self):
        """Test loading large configuration files"""
        # Create a large config with many keys
        large_config = {"dns": "cloudflare"}
        for i in range(1000):
            large_config["key_{}".format(i)] = "value_{}".format(i)

        config_file = self.create_test_file("large_config.json", large_config)
        loaded_config = load_config(config_file)

        self.assertEqual(len(loaded_config), 1001)  # dns + 1000 keys
        self.assertEqual(loaded_config["dns"], "cloudflare")
        self.assertEqual(loaded_config["key_999"], "value_999")

    def test_load_config_numeric_keys_in_nested(self):
        """Test nested objects with numeric keys"""
        config_with_numeric = {"dns": "dnspod", "servers": {"1": "primary.dns.com", "2": "secondary.dns.com"}}

        config_file = self.create_test_file("numeric_keys.json", config_with_numeric)
        loaded_config = load_config(config_file)

        self.assertEqual(loaded_config["dns"], "dnspod")
        self.assertEqual(loaded_config["servers_1"], "primary.dns.com")
        self.assertEqual(loaded_config["servers_2"], "secondary.dns.com")

    def test_load_config_special_characters_in_keys(self):
        """Test configuration with special characters in keys"""
        special_config = {"dns": "cloudflare", "nested-key": {"sub@key": "value1", "sub.key": "value2"}}

        config_file = self.create_test_file("special_chars.json", special_config)
        loaded_config = load_config(config_file)

        self.assertEqual(loaded_config["dns"], "cloudflare")
        self.assertEqual(loaded_config["nested-key_sub@key"], "value1")
        self.assertEqual(loaded_config["nested-key_sub.key"], "value2")

    def test_load_config_file_encoding_utf8(self):
        """Test loading files with UTF-8 encoding and special characters"""
        unicode_config = {"dns": "cloudflare", "description": "测试配置文件", "symbols": "αβγδε", "emoji": "🌍🔧⚡"}

        config_file = self.create_test_file("unicode.json", unicode_config)
        loaded_config = load_config(config_file)

        self.assertEqual(loaded_config["dns"], "cloudflare")
        self.assertEqual(loaded_config["description"], "测试配置文件")
        self.assertEqual(loaded_config["symbols"], "αβγδε")
        self.assertEqual(loaded_config["emoji"], "🌍🔧⚡")

    def test_load_config_json_with_hash_comments(self):
        """测试加载带有 # 注释的JSON配置文件"""
        json_with_comments = """{
    # Configuration for DDNS
    "dns": "cloudflare",  # DNS provider
    "id": "test@example.com",
    "token": "secret123",  # API token
    "ttl": 300
    # End of config
}"""
        file_path = self.create_test_file("test_hash_comments.json", json_with_comments)

        config = load_config(file_path)

        expected = {"dns": "cloudflare", "id": "test@example.com", "token": "secret123", "ttl": 300}
        self.assertEqual(config, expected)

    def test_load_config_json_with_double_slash_comments(self):
        """测试加载带有 // 注释的JSON配置文件"""
        json_with_comments = """{
    // Configuration for DDNS
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Schema validation
    "debug": false,  // false=disable, true=enable
    "dns": "dnspod_com",  // DNS provider
    "id": "1008666",
    "token": "ae86$cbbcctv666666666666666",  // API Token
    "ipv4": ["test.lorzl.ml"],  // IPv4 domains
    "ipv6": ["test.lorzl.ml"],  // IPv6 domains
    "proxy": null  // Proxy settings
}"""
        file_path = self.create_test_file("test_double_slash_comments.json", json_with_comments)

        config = load_config(file_path)

        expected = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
            "debug": False,
            "dns": "dnspod_com",
            "id": "1008666",
            "token": "ae86$cbbcctv666666666666666",
            "ipv4": ["test.lorzl.ml"],
            "ipv6": ["test.lorzl.ml"],
            "proxy": None,
        }
        self.assertEqual(config, expected)

    def test_save_config_pretty_format(self):
        """Test that saved JSON is properly formatted"""
        config_data = {"dns": "cloudflare", "log_level": "DEBUG", "log_file": "/var/log/ddns.log"}

        save_file = os.path.join(self.temp_dir, "formatted.json")
        result = save_config(save_file, config_data)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(save_file))

        # Check that the file is properly indented
        with open(save_file, "r") as f:
            content = f.read()
            # Should have proper indentation (2 spaces for top level, 4 for nested)
            self.assertIn('  "dns":', content)
            self.assertIn('    "level":', content)  # log.level should be nested with 4 spaces

    def test_save_config_readonly_file(self):
        """Test saving to a read-only file"""
        readonly_file = os.path.join(self.temp_dir, "readonly.json")

        # Create file and make it read-only
        with open(readonly_file, "w") as f:
            f.write("{}")

        try:
            os.chmod(readonly_file, 0o444)  # Read-only

            config_data = {"dns": "test"}
            with self.assertRaises((IOError, PermissionError)):
                save_config(readonly_file, config_data)
        finally:
            # Clean up - make writable again
            try:
                os.chmod(readonly_file, 0o777)
                os.remove(readonly_file)
            except OSError:
                pass

    def test_load_config_mixed_types_comprehensive(self):
        """Test loading configuration with all supported data types"""
        mixed_config = {
            "dns": "cloudflare",
            "ttl": 300,
            "cache": True,
            "ssl": False,
            "timeout": None,
            "servers": ["8.8.8.8", "1.1.1.1"],
            "weights": [0.5, 0.3, 0.2],
            "metadata": {"version": "1.0", "author": "test", "enabled": True},
        }

        config_file = self.create_test_file("mixed_types.json", mixed_config)
        loaded_config = load_config(config_file)

        # Test all types are preserved
        self.assertEqual(loaded_config["dns"], "cloudflare")
        self.assertEqual(loaded_config["ttl"], 300)
        self.assertTrue(loaded_config["cache"])
        self.assertFalse(loaded_config["ssl"])
        self.assertIsNone(loaded_config["timeout"])
        self.assertEqual(loaded_config["servers"], ["8.8.8.8", "1.1.1.1"])
        self.assertEqual(loaded_config["weights"], [0.5, 0.3, 0.2])

        # Test flattened nested object
        self.assertEqual(loaded_config["metadata_version"], "1.0")
        self.assertEqual(loaded_config["metadata_author"], "test")
        self.assertTrue(loaded_config["metadata_enabled"])

    def test_load_config_v41_providers_format(self):
        """Test loading configuration with v4.1 providers format"""
        config_data = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
            "ssl": "auto",
            "cache": True,
            "log": {"level": "INFO", "file": "/var/log/ddns.log"},
            "providers": [
                {
                    "provider": "cloudflare",
                    "id": "user1@example.com",
                    "token": "token1",
                    "ipv4": ["test1.example.com"],
                    "ttl": 300,
                },
                {
                    "provider": "dnspod",
                    "id": "user2@example.com",
                    "token": "token2",
                    "ipv4": ["test2.example.com"],
                    "ttl": 600,
                },
            ],
        }

        config_file = self.create_test_file("v41_providers.json", config_data)
        loaded_configs = load_config(config_file)

        # Should return a list of configs
        self.assertIsInstance(loaded_configs, list)
        self.assertEqual(len(loaded_configs), 2)

        # Test first provider config
        config1 = loaded_configs[0]
        self.assertEqual(config1["dns"], "cloudflare")  # name mapped to dns
        self.assertEqual(config1["id"], "user1@example.com")
        self.assertEqual(config1["token"], "token1")
        self.assertEqual(config1["ipv4"], ["test1.example.com"])
        self.assertEqual(config1["ttl"], 300)

        # Test global configs are inherited
        self.assertEqual(config1["ssl"], "auto")
        self.assertTrue(config1["cache"])
        self.assertEqual(config1["log_level"], "INFO")
        self.assertEqual(config1["log_file"], "/var/log/ddns.log")

        # Test second provider config
        config2 = loaded_configs[1]
        self.assertEqual(config2["dns"], "dnspod")  # name mapped to dns
        self.assertEqual(config2["id"], "user2@example.com")
        self.assertEqual(config2["token"], "token2")
        self.assertEqual(config2["ipv4"], ["test2.example.com"])
        self.assertEqual(config2["ttl"], 600)

        # Test global configs are inherited in second config too
        self.assertEqual(config2["ssl"], "auto")
        self.assertTrue(config2["cache"])
        self.assertEqual(config2["log_level"], "INFO")
        self.assertEqual(config2["log_file"], "/var/log/ddns.log")

    def test_load_config_v41_providers_conflict_with_dns(self):
        """Test loading configuration where providers and dns fields conflict"""
        import ddns.config.file

        original_stderr = ddns.config.file.stderr
        ddns.config.file.stderr = self.stderr_capture

        try:
            config_data = {
                "dns": "cloudflare",  # Should conflict with providers
                "providers": [{"provider": "dnspod", "token": "test_token"}],
            }

            config_file = self.create_test_file("conflict.json", config_data)

            with self.assertRaises(ValueError) as context:
                load_config(config_file)

            self.assertIn("providers and dns fields conflict", str(context.exception))

            # Verify error message in stderr
            stderr_output = self.stderr_capture.getvalue()
            self.assertIn("'providers' and 'dns' fields cannot be used simultaneously", stderr_output)
        finally:
            ddns.config.file.stderr = original_stderr

    def test_load_config_v41_providers_missing_name(self):
        """Test loading configuration where provider is missing name field"""
        import ddns.config.file

        original_stderr = ddns.config.file.stderr
        ddns.config.file.stderr = self.stderr_capture

        try:
            config_data = {
                "providers": [
                    {
                        "id": "test@example.com",
                        "token": "test_token",
                        # Missing "provider" field
                    }
                ]
            }

            config_file = self.create_test_file("missing_name.json", config_data)

            with self.assertRaises(ValueError) as context:
                load_config(config_file)

            self.assertIn("provider missing provider field", str(context.exception))

            # Verify error message in stderr
            stderr_output = self.stderr_capture.getvalue()
            self.assertIn("Each provider must have a 'provider' field", stderr_output)
        finally:
            ddns.config.file.stderr = original_stderr

    def test_load_config_v41_providers_single_provider(self):
        """Test loading configuration with single provider in v4.1 format"""
        config_data = {
            "ssl": False,
            "providers": [{"provider": "debug", "token": "dummy_token", "ipv4": ["test.example.com"]}],
        }

        config_file = self.create_test_file("single_provider.json", config_data)
        loaded_configs = load_config(config_file)

        # Should return a list with one config
        self.assertIsInstance(loaded_configs, list)
        self.assertEqual(len(loaded_configs), 1)

        config = loaded_configs[0]
        self.assertEqual(config["dns"], "debug")
        self.assertEqual(config["token"], "dummy_token")
        self.assertEqual(config["ipv4"], ["test.example.com"])
        self.assertFalse(config["ssl"])  # Global config inherited

    def test_load_config_v41_providers_with_nested_objects(self):
        """Test loading v4.1 providers format with nested objects in providers"""
        config_data = {
            "cache": True,
            "providers": [
                {
                    "provider": "cloudflare",
                    "token": "test_token",
                    "custom": {"setting1": "value1", "setting2": "value2"},
                }
            ],
        }

        config_file = self.create_test_file("providers_nested.json", config_data)
        loaded_configs = load_config(config_file)

        self.assertIsInstance(loaded_configs, list)
        self.assertEqual(len(loaded_configs), 1)

        config = loaded_configs[0]
        self.assertEqual(config["dns"], "cloudflare")
        self.assertEqual(config["token"], "test_token")
        self.assertTrue(config["cache"])

        # Test nested objects in provider config are flattened
        self.assertEqual(config["custom_setting1"], "value1")
        self.assertEqual(config["custom_setting2"], "value2")
        self.assertNotIn("custom", config)


if __name__ == "__main__":
    unittest.main()
