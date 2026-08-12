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

## 端到端测试 / End-to-End Tests

E2E 测试通过真实子进程覆盖 CLI 与本机 Web 控制台，但使用回环 HTTP 服务模拟公网 IP、远程配置和 Callback Provider。因此不需要真实 DNS 凭据，也不会访问公网。

The E2E suite exercises the CLI and local Web dashboard through real child processes. A loopback HTTP server simulates public IP discovery, remote configuration, and the Callback Provider, so the suite needs no DNS credentials or Internet access.

```bash
# 独立运行离线 CLI 与 Web E2E / Run the offline CLI and Web E2E suite
python3 -m unittest tests.e2e -v

# 对已构建的二进制运行同一套 E2E / Run the same suite against a built binary
DDNS_E2E_EXECUTABLE=./dist/ddns python3 -m unittest tests.e2e -v
```

`tests/e2e.py` 不匹配常规 `test_*.py` discovery 规则，由 CI 中独立的 Python 3.12 E2E Job 运行。覆盖范围包括双栈更新、配置优先级、多 Provider、缓存、失败退出码、Web 鉴权、配置 API、同步 API 和 Web 调度器。

`tests/e2e.py` intentionally does not match the regular `test_*.py` discovery pattern. A dedicated Python 3.12 CI job runs it and covers dual-stack updates, configuration precedence, multiple providers, caching, failure exit codes, Web authentication, configuration and synchronization APIs, and the Web scheduler.

Nuitka 的 Windows、Linux、macOS onefile 构建会通过 `DDNS_E2E_EXECUTABLE` 运行全部相同场景；Windows standalone ZIP 中的可执行文件也会单独运行一次完整 E2E。

Nuitka onefile builds for Windows, Linux, and macOS run the same complete suite through `DDNS_E2E_EXECUTABLE`. The executable packaged in the Windows standalone ZIP is tested separately as well.

Linux systemd 生命周期测试会真实安装、停用、启用并卸载 `ddns.service` 和 `ddns.timer`。它要求运行中的 systemd、免交互 `sudo`，以及测试开始前不存在 DDNS 系统任务；无论成功或失败，脚本都会清理本次创建的任务。

The Linux systemd lifecycle test installs, disables, enables, and uninstalls `ddns.service` and `ddns.timer`. It requires a running systemd instance, passwordless `sudo`, and no pre-existing DDNS system task. The script cleans up the task it creates on both success and failure.

```bash
bash tests/scripts/test-task-systemd.sh "$(command -v python3) -m ddns"
```

## 测试结构 / Test Structure

```
tests/
├── __init__.py         # 测试包初始化 / Makes tests a package
├── base_test.py        # 共享测试工具和基类 / Shared test utilities and base classes
├── e2e.py              # 独立离线端到端测试 / Dedicated offline E2E tests
├── scripts/            # 系统任务生命周期脚本 / System task lifecycle scripts
├── test_provider_*.py  # 各个提供商的测试文件 / Tests for each provider  
└── README.md           # 本测试指南 / This testing guide
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
