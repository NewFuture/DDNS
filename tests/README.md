# DDNS 测试指南 / DDNS Testing Guide

本文档说明如何运行DDNS项目的测试。**unittest** 是默认的测试框架，因为它是Python内置的，无需额外依赖。

This document explains how to run tests for the DDNS project. **unittest** is the default testing framework as it's built into Python and requires no additional dependencies.

## 快速开始 / Quick Start

### 默认方法 unittest / Default Method (unittest)

```bash
# 运行所有测试（推荐）/ Run all tests (recommended)
python -m unittest discover tests -v

# 运行基础测试文件 / Run base test file
python tests/base_test.py -v  

# 运行特定测试文件 / Run specific test file
python -m unittest tests.test_provider_he -v
python -m unittest tests.test_provider_dnspod -v

# 运行特定测试类 / Run specific test class
python -m unittest tests.test_provider_he.TestHeProvider -v

# 运行特定测试方法 / Run specific test method
python -m unittest tests.test_provider_he.TestHeProvider.test_init_with_basic_config -v
```

### 可选：使用 pytest / Optional: Using pytest (Advanced Users)

如果你偏好pytest的特性，需要先安装：

If you prefer pytest features, install it first:

```bash
# 或者直接安装 / or directly: 
pip install pytest

# 运行所有测试 / Run all tests
pytest tests/ -v

# 运行特定测试文件 / Run specific test file
pytest tests/test_provider_he.py -v

```

## 测试结构 / Test Structure

```
tests/
├── __init__.py                  # 测试包初始化 / Makes tests a package
├── base_test.py                 # 共享测试工具和基类 / Shared test utilities and base classes
├── test_provider_*.py           # 各个提供商的测试文件 / Tests for each provider  
├── scripts/                     # 测试脚本 / Test scripts
│   ├── test-openwrt-install.sh  # OpenWRT 安装和定时任务测试 / OpenWRT install & task test
│   ├── test-task-cron.sh        # Cron 定时任务测试 / Cron task management test
│   ├── test-task-systemd.sh     # Systemd 定时任务测试 / Systemd task management test
│   ├── test-task-macos.sh       # macOS 定时任务测试 / macOS task management test
│   ├── test-task-windows.bat    # Windows 定时任务测试 / Windows task management test
│   └── test-in-docker.sh        # Docker 容器测试 / Docker container test
└── README.md                    # 本测试指南 / This testing guide
```

## 测试配置 / Test Configuration

项目同时支持unittest（默认）和pytest测试框架：

The project supports both unittest (default) and pytest testing frameworks:

## 编写测试 / Writing Tests

### 使用基础测试类 / Using the Base Test Class

所有提供商测试都应该继承`BaseProviderTestCase`：

All provider tests should inherit from `BaseProviderTestCase`:

```python
from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.your_provider import YourProvider

class TestYourProvider(BaseProviderTestCase):
    def setUp(self):
        super(TestYourProvider, self).setUp()
        # 提供商特定的设置 / Provider-specific setup
        
    def test_your_feature(self):
        provider = YourProvider(self.id, self.token)
        # 测试实现 / Test implementation
```

### 测试命名约定 / Test Naming Convention

- 测试文件 / Test files: `test_provider_*.py`
- 测试类 / Test classes: `Test*Provider`  
- 测试方法 / Test methods: `test_*`

## Python版本兼容性 / Python Version Compatibility

测试设计为同时兼容Python 2.7和Python 3.x：

Tests are designed to work with both Python 2.7 and Python 3.x:

- `mock` vs `unittest.mock`的导入处理 / Import handling for `mock` vs `unittest.mock`
- 字符串类型兼容性 / String type compatibility
- 异常处理兼容性 / Exception handling compatibility  
- print语句/函数兼容性 / Print statement/function compatibility

### 常见问题 / Common Issues

1. **导入错误 / Import errors**: 确保从项目根目录运行测试 / Ensure you're running tests from the project root directory
2. **找不到Mock / Mock not found**: 为Python 2.7安装`mock`包：`pip install mock` / Install `mock` package for Python 2.7: `pip install mock==3.0.5`
3. **找不到pytest / pytest not found**: 安装pytest：`pip install pytest` / Install pytest: `pip install pytest`

**注意**: 项目已通过修改 `tests/__init__.py` 解决了模块导入路径问题，现在所有运行方式都能正常工作。

**Note**: The project has resolved module import path issues by modifying `tests/__init__.py`, and now all running methods work correctly.

## 集成测试 / Integration Tests

### OpenWRT 安装和定时任务测试 / OpenWRT Install & Task Test

测试 DDNS 在 OpenWRT 系统上的完整安装流程和定时任务管理：

Test complete DDNS installation and scheduled task management on OpenWRT:

```bash
# 在 Docker 容器中运行 OpenWRT 测试 / Run OpenWRT test in Docker container
docker run --rm -v "$(pwd):/workspace" openwrt/rootfs:x86_64 \
    sh -c "cd /workspace/tests/scripts && sh test-openwrt-install.sh ../../docs/public/install.sh"

# 或在本地 OpenWRT 系统上运行 / Or run on local OpenWRT system
cd tests/scripts
sh test-openwrt-install.sh ../../docs/public/install.sh
```

该测试验证以下内容 / This test verifies:
- ✅ 一键安装脚本在 OpenWRT 上正常工作 / One-click install script works on OpenWRT
- ✅ 安装路径正确 (`/usr/local/bin/ddns`) / Correct installation path
- ✅ 二进制文件可执行且功能正常 / Binary is executable and functional
- ✅ 定时任务可以安装和管理 / Scheduled tasks can be installed and managed
- ✅ Cron 集成正常工作 / Cron integration works correctly
- ✅ 任务启用/禁用功能正常 / Task enable/disable functions properly

### 其他平台测试脚本 / Other Platform Test Scripts

```bash
# Linux (systemd)
tests/scripts/test-task-systemd.sh

# Linux/Unix (cron)
tests/scripts/test-task-cron.sh /usr/local/bin/ddns

# macOS (launchd)
tests/scripts/test-task-macos.sh

# Windows (Task Scheduler)
tests/scripts/test-task-windows.bat

# Docker 容器测试 / Docker container test
tests/scripts/test-in-docker.sh linux/amd64 musl dist/ddns
```
