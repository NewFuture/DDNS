# coding=utf-8
# type: ignore[index,operator,assignment]
"""
Unit tests for multi-config functionality
@author: GitHub Copilot
"""
from __init__ import unittest, patch
import tempfile
import json
import os
import sys
from ddns.config import load_configs
from ddns.config.file import load_config as load_file_config, _process_multi_providers


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
        config_data = {"dns": "cloudflare", "id": "test@example.com", "token": "secret123"}

        config_path = os.path.join(self.temp_dir, "single_config.json")
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        result = load_file_config(config_path)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["dns"], "cloudflare")
        self.assertEqual(result["id"], "test@example.com")
        self.assertEqual(result["token"], "secret123")

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

    def test_env_multiple_configs_integration(self):
        """Test environment variable support for multiple config files using real CLI/env loading"""
        # Create two config files
        config1_data = {"dns": "debug", "id": "test1@example.com", "token": "secret1"}
        config2_data = {"dns": "debug", "id": "test2@example.com", "token": "secret2"}

        config1_path = os.path.join(self.temp_dir, "config1.json")
        config2_path = os.path.join(self.temp_dir, "config2.json")

        with open(config1_path, "w") as f:
            json.dump(config1_data, f)
        with open(config2_path, "w") as f:
            json.dump(config2_data, f)

        # Test via environment variable
        old_env = os.environ.get("DDNS_CONFIG")
        try:
            os.environ["DDNS_CONFIG"] = "{},{}".format(config1_path, config2_path)
            sys.argv = ["ddns"]

            configs = load_configs("test", "1.0", "2023-01-01")

            self.assertEqual(len(configs), 2)
            self.assertEqual(configs[0].dns, "debug")
            self.assertEqual(configs[1].dns, "debug")
            self.assertEqual(configs[0].id, "test1@example.com")
            self.assertEqual(configs[1].id, "test2@example.com")
        finally:
            if old_env is not None:
                os.environ["DDNS_CONFIG"] = old_env
            elif "DDNS_CONFIG" in os.environ:
                del os.environ["DDNS_CONFIG"]

    def test_multi_provider_proxy_individual_settings(self):
        """测试每个provider可以有独立的proxy设置"""
        config = {
            "providers": [
                {
                    "provider": "cloudflare",
                    "id": "user@example.com",
                    "token": "cf_token",
                    "ipv4": ["cf.example.com"],
                    "proxy": "http://127.0.0.1:1080",
                },
                {
                    "provider": "alidns",
                    "id": "access_key",
                    "token": "secret_key",
                    "ipv4": ["ali.example.com"],
                    "proxy": "http://proxy.internal:8080;DIRECT",
                },
                {
                    "provider": "dnspod",
                    "id": "12345",
                    "token": "dnspod_token",
                    "ipv4": ["dp.example.com"],
                    # 没有proxy设置，应该继承全局或为None
                },
            ],
            "cache": True,
            "ttl": 600,
        }

        result = _process_multi_providers(config)

        # 验证返回3个独立配置
        self.assertEqual(len(result), 3)

        # 验证cloudflare配置
        cf_config = result[0]
        self.assertEqual(cf_config["dns"], "cloudflare")
        self.assertEqual(cf_config["proxy"], "http://127.0.0.1:1080")
        self.assertEqual(cf_config["ipv4"], ["cf.example.com"])

        # 验证alidns配置
        ali_config = result[1]
        self.assertEqual(ali_config["dns"], "alidns")
        self.assertEqual(ali_config["proxy"], "http://proxy.internal:8080;DIRECT")
        self.assertEqual(ali_config["ipv4"], ["ali.example.com"])

        # 验证dnspod配置（无proxy）
        dp_config = result[2]
        self.assertEqual(dp_config["dns"], "dnspod")
        self.assertNotIn("proxy", dp_config)  # 没有设置proxy
        self.assertEqual(dp_config["ipv4"], ["dp.example.com"])

        # 验证全局配置继承
        for config_item in result:
            self.assertEqual(config_item["cache"], True)
            self.assertEqual(config_item["ttl"], 600)

    def test_multi_provider_with_global_proxy_override(self):
        """测试provider级别的proxy覆盖全局proxy"""
        config = {
            "proxy": "http://global.proxy:8080",  # 全局proxy
            "providers": [
                {
                    "provider": "cloudflare",
                    "id": "user@example.com",
                    "token": "cf_token",
                    "ipv4": ["cf.example.com"],
                    "proxy": "http://127.0.0.1:1080",  # provider级别proxy覆盖全局
                },
                {
                    "provider": "alidns",
                    "id": "access_key",
                    "token": "secret_key",
                    "ipv4": ["ali.example.com"],
                    # 没有provider级别proxy，使用全局proxy
                },
            ],
        }

        result = _process_multi_providers(config)

        # cloudflare使用provider级别的proxy
        cf_config = result[0]
        self.assertEqual(cf_config["proxy"], "http://127.0.0.1:1080")

        # alidns使用全局proxy
        ali_config = result[1]
        self.assertEqual(ali_config["proxy"], "http://global.proxy:8080")

    def test_multi_provider_proxy_array_format(self):
        """测试provider级别的数组格式proxy配置"""
        config = {
            "providers": [
                {
                    "provider": "cloudflare",
                    "id": "user@example.com",
                    "token": "cf_token",
                    "ipv4": ["cf.example.com"],
                    "proxy": ["http://127.0.0.1:1080", "DIRECT"],
                }
            ]
        }

        result = _process_multi_providers(config)
        cf_config = result[0]
        self.assertEqual(cf_config["proxy"], ["http://127.0.0.1:1080", "DIRECT"])


if __name__ == "__main__":
    unittest.main()
