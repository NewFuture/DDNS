# -*- coding:utf-8 -*-
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
        with open(file_path, "w", encoding="utf-8") as f:
            if isinstance(content, dict):
                f.write(json.dumps(content, indent=2, ensure_ascii=False))
            else:
                f.write(content)
        return file_path

    def test_all_config_formats_integration(self):
        """Test loading all three config formats in a single operation"""
        # Create single object config
        single_config = {
            "dns": "cloudflare",
            "id": "single@example.com",
            "token": "single_token",
            "ipv4": ["single.example.com"],
            "ssl": True
        }
        single_file = self.create_test_file("single.json", single_config)

        # Create configs array format
        configs_array = {
            "configs": [
                {
                    "dns": "dnspod",
                    "id": "configs1@example.com",
                    "token": "configs_token1",
                    "ipv4": ["configs1.example.com"]
                },
                {
                    "dns": "alidns",
                    "id": "configs2@example.com",
                    "token": "configs_token2",
                    "ipv4": ["configs2.example.com"]
                }
            ]
        }
        configs_file = self.create_test_file("configs.json", configs_array)

        # Create v4.1 providers format
        providers_config = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
            "ssl": "auto",
            "cache": True,
            "providers": [
                {
                    "name": "debug",
                    "token": "provider_token1",
                    "ipv4": ["provider1.example.com"],
                    "ttl": 300
                },
                {
                    "name": "debug",
                    "token": "provider_token2", 
                    "ipv4": ["provider2.example.com"],
                    "ttl": 600
                }
            ]
        }
        providers_file = self.create_test_file("providers.json", providers_config)

        # Mock sys.argv to control CLI parsing
        import sys
        original_argv = sys.argv
        
        try:
            # Set fake argv with our config files
            sys.argv = ["ddns", "-c", single_file, "-c", configs_file, "-c", providers_file]
            
            # Load all configs
            all_configs = load_configs("test", "1.0.0", "2025-01-01")
            
            # Should have 5 total configs: 1 single + 2 from configs + 2 from providers
            self.assertEqual(len(all_configs), 5)
            
            # Test single config
            single = all_configs[0]
            self.assertEqual(single.dns, "cloudflare")
            self.assertEqual(single.id, "single@example.com")
            self.assertEqual(single.token, "single_token")
            self.assertEqual(single.ipv4, ["single.example.com"])
            
            # Test configs array configs
            configs1 = all_configs[1]
            self.assertEqual(configs1.dns, "dnspod")
            self.assertEqual(configs1.id, "configs1@example.com")
            self.assertEqual(configs1.token, "configs_token1")
            
            configs2 = all_configs[2]
            self.assertEqual(configs2.dns, "alidns")
            self.assertEqual(configs2.id, "configs2@example.com")
            self.assertEqual(configs2.token, "configs_token2")
            
            # Test providers configs
            provider1 = all_configs[3]
            self.assertEqual(provider1.dns, "debug")  # name mapped to dns
            self.assertEqual(provider1.token, "provider_token1")
            self.assertEqual(provider1.ipv4, ["provider1.example.com"])
            self.assertEqual(provider1.ttl, 300)
            self.assertEqual(provider1.ssl, "auto")  # Global config inherited
            self.assertTrue(provider1.cache)  # Global config inherited
            
            provider2 = all_configs[4]
            self.assertEqual(provider2.dns, "debug")  # name mapped to dns
            self.assertEqual(provider2.token, "provider_token2")
            self.assertEqual(provider2.ipv4, ["provider2.example.com"])
            self.assertEqual(provider2.ttl, 600)
            self.assertEqual(provider2.ssl, "auto")  # Global config inherited
            self.assertTrue(provider2.cache)  # Global config inherited
            
        finally:
            # Restore original argv
            sys.argv = original_argv

    def test_v41_backward_compatibility(self):
        """Test that v4.1 format is backward compatible with existing single config"""
        # Create a traditional single config
        old_config = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
            "dns": "cloudflare",
            "id": "old@example.com",
            "token": "old_token",
            "ipv4": ["old.example.com"],
            "ssl": "auto"
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
            self.assertEqual(config.ssl, "auto")
            
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
        self.assertEqual(loaded["$schema"], "https://ddns.newfuture.cc/schema/v4.1.json")
        self.assertEqual(loaded["dns"], "debug")
        self.assertEqual(loaded["token"], "test")


if __name__ == "__main__":
    unittest.main()