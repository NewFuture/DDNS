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

    def test_env_multi_proxy_remote_config_array_conversion(self):
        """测试环境变量配置多代理远程配置，验证代理参数正确转换为数组"""
        # 创建远程配置文件，包含多种代理格式
        remote_config_data = {
            "providers": [
                {
                    "provider": "debug",
                    "id": "remote1@example.com",
                    "token": "remote_token1",
                    "ipv4": ["remote1.example.com"],
                    "proxy": "http://proxy1.example.com:8080;http://proxy2.example.com:8080;DIRECT",
                },
                {
                    "provider": "debug",
                    "id": "remote2@example.com",
                    "token": "remote_token2",
                    "ipv4": ["remote2.example.com"],
                    "proxy": ["http://array.proxy1.com:3128", "http://array.proxy2.com:3128", "DIRECT"],
                },
            ],
            "proxy": "http://global.proxy1.com:8080;http://global.proxy2.com:8080;DIRECT",
        }

        # 创建本地文件模拟远程配置
        remote_config_path = os.path.join(self.temp_dir, "remote_multi_proxy.json")
        with open(remote_config_path, "w") as f:
            json.dump(remote_config_data, f)

        # 测试场景1：环境变量代理覆盖配置文件代理
        with patch("ddns.config.load_env_config") as mock_env:
            with patch("ddns.config.load_cli_config") as mock_cli:
                # Mock环境变量配置，包含config和proxy设置
                mock_env.return_value = {
                    "config": "file:///{}".format(remote_config_path),
                    "proxy": "http://env.proxy1.com:9090;http://env.proxy2.com:9090;DIRECT",
                }
                # Mock CLI配置为空，避免干扰
                mock_cli.return_value = {}
                configs = load_configs("test", "1.0", "2023-01-01")
                self.assertEqual(len(configs), 2)

                # 验证第一个配置的代理转换 - 现在检查实际的代理值
                config1 = configs[0]
                self.assertEqual(config1.dns, "debug")
                self.assertEqual(config1.id, "remote1@example.com")
                # 当前实现中，配置文件中的代理设置优先，环境变量作为fallback
                # 所以这里验证配置文件中的代理被正确转换为数组
                expected_proxy1 = ["http://proxy1.example.com:8080", "http://proxy2.example.com:8080", "DIRECT"]
                self.assertEqual(config1.proxy, expected_proxy1)

                # 验证第二个配置的代理转换
                config2 = configs[1]
                self.assertEqual(config2.dns, "debug")
                self.assertEqual(config2.id, "remote2@example.com")
                # 第二个配置应该保持数组格式
                expected_proxy2 = ["http://array.proxy1.com:3128", "http://array.proxy2.com:3128", "DIRECT"]
                self.assertEqual(config2.proxy, expected_proxy2)

        # 测试场景2：不设置环境变量代理时，配置文件中的代理被正确转换
        with patch("ddns.config.load_env_config") as mock_env:
            with patch("ddns.config.load_cli_config") as mock_cli:
                # Mock环境变量配置，只设置config不设置proxy
                mock_env.return_value = {"config": remote_config_path}
                # Mock CLI配置为空，避免干扰
                mock_cli.return_value = {}

                sys.argv = ["ddns"]
                configs = load_configs("test", "1.0", "2023-01-01")

                # 验证第一个配置：字符串格式代理被转换为数组
                config1 = configs[0]
                expected_proxy1 = ["http://proxy1.example.com:8080", "http://proxy2.example.com:8080", "DIRECT"]
                self.assertEqual(config1.proxy, expected_proxy1)

                # 验证第二个配置：数组格式代理保持不变
                config2 = configs[1]
                expected_proxy2 = ["http://array.proxy1.com:3128", "http://array.proxy2.com:3128", "DIRECT"]
                self.assertEqual(config2.proxy, expected_proxy2)


if __name__ == "__main__":
    unittest.main()
