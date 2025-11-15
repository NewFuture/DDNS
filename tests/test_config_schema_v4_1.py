# -*- coding:utf-8 -*-
# type: ignore[index,operator,assignment]
"""
Integration test for all config formats including v4.1 providers
@author: GitHub Copilot
"""

from __future__ import unicode_literals
from __init__ import unittest
import tempfile
import shutil
import os
import json
import logging
import sys
from ddns.config import load_configs


class TestAllConfigFormatsIntegration(unittest.TestCase):
    """Integration test for all supported config formats"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

    def create_test_file(self, filename, content):
        # type: (str, dict) -> str
        """Helper method to create a test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, "w") as f:
            if isinstance(content, dict):
                f.write(json.dumps(content, indent=2))
            else:
                f.write(content)
        return file_path

    def test_all_config_formats_integration(self):
        """Test loading v4.1 config formats"""
        # Create single object config
        single_config = {
            "dns": "cloudflare",
            "id": "single@example.com",
            "token": "single_token",
            "ipv4": ["single.example.com"],
            "ssl": True,
        }
        single_file = self.create_test_file("single.json", single_config)

        # Create v4.1 providers format
        providers_config = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
            "ssl": "auto",
            "cache": True,
            "providers": [
                {"provider": "debug", "token": "provider_token1", "ipv4": ["provider1.example.com"], "ttl": 300},
                {"provider": "debug", "token": "provider_token2", "ipv4": ["provider2.example.com"], "ttl": 600},
            ],
        }
        providers_file = self.create_test_file("providers.json", providers_config)

        # Mock sys.argv to control CLI parsing
        import sys

        original_argv = sys.argv

        try:
            # Set fake argv with our config files
            sys.argv = ["ddns", "-c", single_file, "-c", providers_file]

            # Load all configs
            all_configs = load_configs("test", "1.0.0", "2025-07-17")

            # Should have 3 total configs: 1 single + 2 from providers
            self.assertEqual(len(all_configs), 3)

            # Test single config
            self.assertEqual(all_configs[0].dns, "cloudflare")
            self.assertEqual(all_configs[0].id, "single@example.com")
            self.assertEqual(all_configs[0].ssl, True)

            # Test first provider config
            self.assertEqual(all_configs[1].dns, "debug")
            self.assertEqual(all_configs[1].token, "provider_token1")
            self.assertEqual(all_configs[1].ipv4, ["provider1.example.com"])
            self.assertEqual(all_configs[1].ttl, 300)
            # Inherited from global - handle Python 2.7 unicode strings
            self.assertEqual(str(all_configs[1].ssl), "auto")
            # Inherited from global
            self.assertEqual(all_configs[1].cache, True)

            # Test second provider config
            self.assertEqual(all_configs[2].dns, "debug")
            self.assertEqual(all_configs[2].token, "provider_token2")
            self.assertEqual(all_configs[2].ipv4, ["provider2.example.com"])
            self.assertEqual(all_configs[2].ttl, 600)
            # Inherited from global - handle Python 2.7 unicode strings
            self.assertEqual(str(all_configs[2].ssl), "auto")
            # Inherited from global
            self.assertEqual(all_configs[2].cache, True)

        finally:
            # Restore original argv
            sys.argv = original_argv

    def test_v41_backward_compatibility(self):
        """Test that v4.1 format is backward compatible with existing
        single config"""
        # Create a traditional single config
        old_config = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
            "dns": "cloudflare",
            "id": "old@example.com",
            "token": "old_token",
            "ipv4": ["old.example.com"],
            "ssl": "auto",
        }
        old_file = self.create_test_file("old_format.json", old_config)

        # Mock sys.argv to control CLI parsing
        import sys

        original_argv = sys.argv

        try:
            # Set fake argv with our config file
            sys.argv = ["ddns", "-c", old_file]

            configs = load_configs("test", "1.0.0", "2025-01-01")

            # Should load exactly one config
            self.assertEqual(len(configs), 1)
            config = configs[0]
            self.assertEqual(config.dns, "cloudflare")
            self.assertEqual(config.id, "old@example.com")
            self.assertEqual(config.token, "old_token")
            self.assertEqual(str(config.ssl), "auto")

        finally:
            sys.argv = original_argv

    def test_v41_schema_reference(self):
        """Test that save_config uses v4.1 schema by default"""
        from ddns.config.file import save_config, load_config

        test_config = {"dns": "debug", "token": "test"}
        save_file = os.path.join(self.temp_dir, "new_config.json")

        # Save config
        result = save_config(save_file, test_config)
        self.assertTrue(result)

        # Load it back and check schema
        loaded = load_config(save_file)
        expected_schema = "https://ddns.newfuture.cc/schema/v4.1.json"
        self.assertEqual(loaded["$schema"], expected_schema)
        self.assertEqual(loaded["dns"], "debug")
        self.assertEqual(loaded["token"], "test")

    def test_v40_to_v41_compatibility(self):
        """Test v4.0 config is compatible with v4.1 processing"""
        from ddns.config.file import load_config

        # Create v4.0 schema config
        v40_config = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
            "dns": "cloudflare",
            "id": "v40@example.com",
            "token": "v40_token",
            "ipv4": ["v40.example.com"],
            "ttl": 300,
            "ssl": True,
            "log": {"level": "DEBUG", "file": "test.log"},
        }
        v40_file = self.create_test_file("v40_config.json", v40_config)

        # Load and check it processes correctly
        loaded = load_config(v40_file)
        self.assertEqual(loaded["dns"], "cloudflare")
        self.assertEqual(loaded["id"], "v40@example.com")
        self.assertEqual(loaded["token"], "v40_token")
        self.assertEqual(loaded["ipv4"], ["v40.example.com"])
        self.assertEqual(loaded["ttl"], 300)
        self.assertEqual(loaded["ssl"], True)
        # Check flattened log properties
        self.assertEqual(loaded["log_level"], "DEBUG")
        self.assertEqual(loaded["log_file"], "test.log")

    def test_v41_providers_complex_inheritance(self):
        """Test complex inheritance scenarios in v4.1 providers format"""
        from ddns.config.file import load_config

        # Create complex v4.1 config with nested objects
        complex_config = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
            "ssl": "auto",
            "ttl": 600,
            "cache": False,
            "log": {"level": "INFO", "format": "[%(levelname)s] %(message)s"},
            "providers": [
                {
                    "provider": "cloudflare",
                    "id": "provider1@example.com",
                    "token": "cf_token",
                    "ipv4": ["cf.example.com"],
                    "ttl": 300,  # Override global ttl
                    "ssl": True,  # Override global ssl
                },
                {
                    "provider": "debug",
                    "token": "debug_token",
                    "ipv4": ["debug.example.com"],
                    # Uses global ttl and ssl
                    "log": {"level": "DEBUG"},  # Override log level
                },
            ],
        }
        complex_file = self.create_test_file("complex_v41.json", complex_config)

        # Load config
        configs = load_config(complex_file)
        self.assertEqual(len(configs), 2)

        # Test first provider inheritance and overrides
        cf_config = configs[0]
        self.assertEqual(cf_config["dns"], "cloudflare")
        self.assertEqual(cf_config["id"], "provider1@example.com")
        self.assertEqual(cf_config["token"], "cf_token")
        self.assertEqual(cf_config["ttl"], 300)  # Overridden
        self.assertEqual(cf_config["ssl"], True)  # Overridden
        self.assertEqual(cf_config["cache"], False)  # Inherited
        self.assertEqual(cf_config["log_level"], "INFO")  # Inherited
        self.assertEqual(cf_config["log_format"], "[%(levelname)s] %(message)s")

        # Test second provider inheritance
        debug_config = configs[1]
        self.assertEqual(debug_config["dns"], "debug")
        self.assertEqual(debug_config["token"], "debug_token")
        self.assertEqual(debug_config["ttl"], 600)  # Inherited
        self.assertEqual(debug_config["ssl"], "auto")  # Inherited
        self.assertEqual(debug_config["cache"], False)  # Inherited
        self.assertEqual(debug_config["log_level"], "DEBUG")  # Overridden
        self.assertEqual(debug_config["log_format"], "[%(levelname)s] %(message)s")

    def test_v41_providers_error_cases(self):
        """Test error handling in v4.1 providers format"""
        from ddns.config.file import load_config

        # Test providers without provider field
        invalid_config1 = {"providers": [{"id": "missing_provider@example.com", "token": "token"}]}
        invalid_file1 = self.create_test_file("invalid1.json", invalid_config1)

        with self.assertRaises(ValueError) as cm:
            load_config(invalid_file1)
        self.assertIn("provider missing provider field", str(cm.exception))

        # Test dns and providers conflict
        invalid_config2 = {"dns": "cloudflare", "providers": [{"provider": "debug", "token": "token"}]}
        invalid_file2 = self.create_test_file("invalid2.json", invalid_config2)

        with self.assertRaises(ValueError) as cm:
            load_config(invalid_file2)
        self.assertIn("providers and dns fields conflict", str(cm.exception))

    def test_v41_multi_provider_log_config(self):
        """Test that log configuration works with multiple providers in v4.1 format.

        This is a regression test for issue where log.file was ignored when
        using multiple providers in v4.1 format.
        """
        # Create a temp log file path
        log_file_path = os.path.join(self.temp_dir, "ddns.log")

        # Create v4.1 config with multiple providers and log configuration
        multi_provider_config = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
            "ssl": "auto",
            "cache": True,
            "log": {
                "level": "INFO",
                "file": log_file_path,
                "format": "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d]: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "providers": [
                {"provider": "debug", "id": "user1@example.com", "token": "token1", "ipv4": ["test1.example.com"]},
                {"provider": "debug", "id": "user2@example.com", "token": "token2", "ipv4": ["test2.example.com"]},
            ],
        }
        config_file = self.create_test_file("multi_provider_log.json", multi_provider_config)

        # Mock sys.argv to load this config
        original_argv = sys.argv

        # Reset logging handlers before test
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        try:
            sys.argv = ["ddns", "-c", config_file]

            # Load configs using load_configs which calls _setup_logging
            configs = load_configs("test", "1.0.0", "2025-01-01")

            # Should have 2 configs (one per provider)
            self.assertEqual(len(configs), 2)

            # Both configs should have the log settings inherited from global config
            for i, config in enumerate(configs):
                self.assertEqual(
                    config.log_file, log_file_path, "Config %d should have log_file from global config" % i
                )
                # Check log_level - in Python 2.7, getLevelName may return string, so check both
                self.assertIn(
                    config.log_level,
                    [20, logging.INFO, "INFO"],
                    "Config %d should have log_level from global config" % i,
                )
                self.assertEqual(
                    config.log_format,
                    "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d]: %(message)s",
                    "Config %d should have log_format from global config" % i,
                )
                self.assertEqual(
                    config.log_datefmt, "%Y-%m-%d %H:%M:%S", "Config %d should have log_datefmt from global config" % i
                )

            # Verify that log file was actually created (proving logging.basicConfig was called with filename)
            self.assertTrue(os.path.exists(log_file_path), "Log file should have been created by logging.basicConfig")

        finally:
            sys.argv = original_argv
            # Clean up logging handlers
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)


if __name__ == "__main__":
    unittest.main()
