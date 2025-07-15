# coding=utf-8
"""
Unit tests for multi-config functionality
@author: GitHub Copilot
"""
from __init__ import unittest, patch, MagicMock
import tempfile
import json
import os
import sys
from ddns.config import load_configs
from ddns.config.file import load_config as load_file_config


class TestMultiConfig(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_argv = sys.argv[:]

    def tearDown(self):
        sys.argv = self.original_argv
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_loader_single_object(self):
        """Test that file loader works with single object configs"""
        config_data = {
            "dns": "cloudflare",
            "id": "test@example.com",
            "token": "secret123"
        }
        
        config_path = os.path.join(self.temp_dir, "single_config.json")
        with open(config_path, "w") as f:
            json.dump(config_data, f)
        
        result = load_file_config(config_path)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["dns"], "cloudflare")
        self.assertEqual(result["id"], "test@example.com")
        self.assertEqual(result["token"], "secret123")

    def test_file_loader_array_config(self):
        """Test that file loader works with array config format"""
        config_data = [
            {
                "dns": "cloudflare",
                "id": "test1@example.com",
                "token": "secret123"
            },
            {
                "dns": "dnspod",
                "id": "test2@example.com", 
                "token": "secret456"
            }
        ]
        
        config_path = os.path.join(self.temp_dir, "array_config.json")
        with open(config_path, "w") as f:
            json.dump(config_data, f)
        
        result = load_file_config(config_path)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["dns"], "cloudflare")
        self.assertEqual(result[1]["dns"], "dnspod")

    def test_cli_multiple_configs(self):
        """Test CLI support for multiple config files"""
        # Create two config files
        config1_data = {"dns": "cloudflare", "id": "test1@example.com", "token": "secret1"}
        config2_data = {"dns": "dnspod", "id": "test2@example.com", "token": "secret2"}
        
        config1_path = os.path.join(self.temp_dir, "config1.json")
        config2_path = os.path.join(self.temp_dir, "config2.json")
        
        with open(config1_path, "w") as f:
            json.dump(config1_data, f)
        with open(config2_path, "w") as f:
            json.dump(config2_data, f)
        
        # Mock CLI args
        sys.argv = ["ddns", "-c", config1_path, "-c", config2_path]
        
        with patch("ddns.config.cli.load_config") as mock_cli:
            mock_cli.return_value = {"config": [config1_path, config2_path]}
            
            with patch("ddns.config.env.load_config") as mock_env:
                mock_env.return_value = {}
                
                configs = load_configs("test", "1.0", "2023-01-01")
                
                self.assertEqual(len(configs), 2)
                self.assertEqual(configs[0].dns, "cloudflare")
                self.assertEqual(configs[1].dns, "dnspod")

    def test_env_multiple_configs(self):
        """Test environment variable support for multiple config files"""
        # Create two config files
        config1_data = {"dns": "cloudflare", "id": "test1@example.com", "token": "secret1"}
        config2_data = {"dns": "dnspod", "id": "test2@example.com", "token": "secret2"}
        
        config1_path = os.path.join(self.temp_dir, "config1.json")
        config2_path = os.path.join(self.temp_dir, "config2.json")
        
        with open(config1_path, "w") as f:
            json.dump(config1_data, f)
        with open(config2_path, "w") as f:
            json.dump(config2_data, f)
        
        # Mock sys.argv to avoid argparse conflicts
        sys.argv = ["ddns"]
        
        with patch("ddns.config.cli.load_config") as mock_cli:
            mock_cli.return_value = {}
            
            with patch("ddns.config.env.load_config") as mock_env:
                mock_env.return_value = {"config": [config1_path, config2_path]}
                
                configs = load_configs("test", "1.0", "2023-01-01")
                
                self.assertEqual(len(configs), 2)
                self.assertEqual(configs[0].dns, "cloudflare")
                self.assertEqual(configs[1].dns, "dnspod")

    def test_mixed_single_and_array_configs(self):
        """Test mixing single object configs and array configs"""
        # Single config file
        single_config_data = {"dns": "cloudflare", "id": "test1@example.com", "token": "secret1"}
        
        # Array config file
        array_config_data = [
            {"dns": "dnspod", "id": "test2@example.com", "token": "secret2"},
            {"dns": "alidns", "id": "test3@example.com", "token": "secret3"}
        ]
        
        single_config_path = os.path.join(self.temp_dir, "single.json")
        array_config_path = os.path.join(self.temp_dir, "array.json")
        
        with open(single_config_path, "w") as f:
            json.dump(single_config_data, f)
        with open(array_config_path, "w") as f:
            json.dump(array_config_data, f)
        
        # Mock sys.argv to avoid argparse conflicts
        sys.argv = ["ddns"]
        
        with patch("ddns.config.cli.load_config") as mock_cli:
            mock_cli.return_value = {"config": [single_config_path, array_config_path]}
            
            with patch("ddns.config.env.load_config") as mock_env:
                mock_env.return_value = {}
                
                configs = load_configs("test", "1.0", "2023-01-01")
                
                self.assertEqual(len(configs), 3)
                self.assertEqual(configs[0].dns, "cloudflare")
                self.assertEqual(configs[1].dns, "dnspod")
                self.assertEqual(configs[2].dns, "alidns")

    def test_nested_object_flattening_in_array(self):
        """Test that nested objects are properly flattened in array configs"""
        config_data = [
            {
                "dns": "cloudflare",
                "id": "test@example.com",
                "token": "secret123",
                "log": {
                    "level": "DEBUG",
                    "file": "/tmp/ddns.log"
                }
            }
        ]
        
        config_path = os.path.join(self.temp_dir, "nested_array.json")
        with open(config_path, "w") as f:
            json.dump(config_data, f)
        
        result = load_file_config(config_path)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        
        config = result[0]
        self.assertEqual(config["dns"], "cloudflare")
        self.assertEqual(config["log_level"], "DEBUG")
        self.assertEqual(config["log_file"], "/tmp/ddns.log")


if __name__ == "__main__":
    unittest.main()