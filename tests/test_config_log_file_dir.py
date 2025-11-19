# coding=utf-8
# type: ignore[index,operator,assignment]
"""
Unit tests for log file directory creation issue
Reproduces the issue where log_file path has non-existent parent directories
@author: GitHub Copilot
"""

from __init__ import unittest
import tempfile
import json
import os
import sys
import shutil
from ddns.config import load_configs


class TestLogFileDirectory(unittest.TestCase):
    """测试日志文件目录创建问题"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_argv = sys.argv[:]

    def tearDown(self):
        sys.argv = self.original_argv
        # Clean up temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_file_with_nonexistent_directory_single_config(self):
        """测试单个配置时，log文件所在目录不存在的情况"""
        # 创建一个不存在的目录路径
        log_dir = os.path.join(self.temp_dir, "nonexistent", "subdir")
        log_file = os.path.join(log_dir, "ddns.log")

        # 确保目录不存在
        self.assertFalse(os.path.exists(log_dir))

        config_data = {
            "dns": "debug",
            "id": "test@example.com",
            "token": "secret123",
            "ipv4": ["test.example.com"],
            "log": {"file": log_file, "level": "INFO"},
        }

        config_path = os.path.join(self.temp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        sys.argv = ["ddns", "-c", config_path]

        # 加载配置，应该自动创建目录
        configs = load_configs("test", "1.0", "2023-01-01")

        # 验证目录被创建
        self.assertTrue(os.path.exists(log_dir), "Log directory should be created")
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].log_file, log_file)

    def test_log_file_with_nonexistent_directory_multi_provider(self):
        """测试多个provider配置时，log文件所在目录不存在的情况（复现issue中的问题）"""
        # 创建一个不存在的目录路径
        log_dir = os.path.join(self.temp_dir, "ddns")
        log_file = os.path.join(log_dir, "ddns.log")

        # 确保目录不存在
        self.assertFalse(os.path.exists(log_dir))

        # 模拟issue中的配置：多个provider，共享同一个log文件
        config_data = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
            "ssl": "auto",
            "cache": os.path.join(self.temp_dir, "cache"),
            "log": {"level": "INFO", "file": log_file},
            "index4": "default",
            "index6": "default",
            "providers": [
                {
                    "provider": "debug",
                    "token": "token1",
                    "ipv6": ["test1.xyz"],
                },
                {
                    "provider": "debug",
                    "token": "token2",
                    "ipv6": ["test2.org"],
                },
            ],
        }

        config_path = os.path.join(self.temp_dir, "multi_config.json")
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        sys.argv = ["ddns", "-c", config_path]

        # 加载配置，应该自动创建目录
        configs = load_configs("test", "1.0", "2023-01-01")

        # 验证目录被创建
        self.assertTrue(os.path.exists(log_dir), "Log directory should be created")
        self.assertEqual(len(configs), 2)

        # 验证两个配置都使用同一个log文件
        for config in configs:
            self.assertEqual(config.log_file, log_file)

    def test_log_file_with_nested_nonexistent_directory(self):
        """测试log文件路径有多级不存在的目录"""
        # 创建多级不存在的目录路径
        log_file = os.path.join(self.temp_dir, "a", "b", "c", "d", "ddns.log")

        config_data = {
            "dns": "debug",
            "id": "test@example.com",
            "token": "secret123",
            "log": {"file": log_file},
        }

        config_path = os.path.join(self.temp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        sys.argv = ["ddns", "-c", config_path]

        # 加载配置，应该自动创建所有父目录
        configs = load_configs("test", "1.0", "2023-01-01")

        # 验证所有父目录被创建
        self.assertTrue(os.path.exists(os.path.dirname(log_file)), "All parent directories should be created")
        self.assertEqual(configs[0].log_file, log_file)

    def test_log_file_with_existing_directory(self):
        """测试log文件所在目录已存在的情况（不应该出错）"""
        # 创建目录
        log_dir = os.path.join(self.temp_dir, "existing_dir")
        os.makedirs(log_dir)
        log_file = os.path.join(log_dir, "ddns.log")

        config_data = {
            "dns": "debug",
            "id": "test@example.com",
            "token": "secret123",
            "log": {"file": log_file},
        }

        config_path = os.path.join(self.temp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        sys.argv = ["ddns", "-c", config_path]

        # 加载配置，应该正常工作
        configs = load_configs("test", "1.0", "2023-01-01")

        self.assertTrue(os.path.exists(log_dir))
        self.assertEqual(configs[0].log_file, log_file)


if __name__ == "__main__":
    unittest.main()
