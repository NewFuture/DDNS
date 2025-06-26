# DDNS 测试指南 / DDNS Testing Guide

本文档说明如何运行DDNS项目的测试。**unittest** 是默认的测试框架，因为它是Python内置的，无需额外依赖。

This document explains how to run tests for the DDNS project. **unittest** is the default testing framework as it's built into Python and requires no additional dependencies.

## 快速开始 / Quick Start

### 默认方法 unittest / Default Method (unittest)
```bash
# 运行所有测试（推荐）/ Run all tests (recommended)
python -m unittest discover tests -v

# 运行特定测试文件 / Run specific test file
python -m unittest tests.test_provider_he -v

# 运行特定测试类 / Run specific test class
python -m unittest tests.test_provider_he.TestHeProvider -v

# 运行特定测试方法 / Run specific test method
python -m unittest tests.test_provider_he.TestHeProvider.test_init_with_basic_config -v
```

### 可选：使用 pytest / Optional: Using pytest (Advanced Users)
如果你偏好pytest的特性，需要先安装：

If you prefer pytest features, install it first:
```bash
# 安装pytest支持 / Install pytest support
pip install -e .[pytest]
# 或者直接安装 / or directly: 
pip install pytest

# 运行所有测试 / Run all tests
pytest tests/ -v

# 运行特定测试文件 / Run specific test file
pytest tests/test_provider_he.py -v

# 运行匹配模式的测试 / Run tests matching pattern
pytest tests/ -k "test_init" -v
```

## 测试结构 / Test Structure

```
tests/
├── __init__.py                 # 测试包初始化 / Makes tests a package
├── test_base.py               # 共享测试工具和基类 / Shared test utilities and base classes
├── test_provider_base.py      # BaseProvider测试 / Tests for BaseProvider
├── test_provider_callback.py  # CallbackProvider测试 / Tests for CallbackProvider  
├── test_provider_debug.py     # DebugProvider测试 / Tests for DebugProvider
├── test_provider_he.py        # HeProvider测试 / Tests for HeProvider
└── README.md                  # 本测试指南 / This testing guide
```

## 测试配置 / Test Configuration

项目同时支持unittest（默认）和pytest测试框架：

The project supports both unittest (default) and pytest testing frameworks:


## 编写测试 / Writing Tests

### 使用基础测试类 / Using the Base Test Class
所有提供商测试都应该继承`BaseProviderTestCase`：

All provider tests should inherit from `BaseProviderTestCase`:

```python
from test_base import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.your_provider import YourProvider

class TestYourProvider(BaseProviderTestCase):
    def setUp(self):
        super(TestYourProvider, self).setUp()
        # 提供商特定的设置 / Provider-specific setup
        
    def test_your_feature(self):
        provider = YourProvider(self.auth_id, self.auth_token)
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

## 持续集成 / Continuous Integration

测试在以下环境自动运行：

Tests run automatically on:
- GitHub Actions多个Python版本 / GitHub Actions for multiple Python versions
- 所有支持的Python版本（2.7, 3.6-3.13）/ All supported Python versions (2.7, 3.6-3.13)
- unittest和pytest框架（如果可用）/ Both unittest and pytest frameworks (where available)

## 故障排除 / Troubleshooting

### 常见问题 / Common Issues

1. **导入错误 / Import errors**: 确保从项目根目录运行测试 / Ensure you're running tests from the project root directory
2. **找不到Mock / Mock not found**: 为Python 2.7安装`mock`包：`pip install mock` / Install `mock` package for Python 2.7: `pip install mock==3.0.5`
3. **找不到pytest / pytest not found**: 安装pytest：`pip install pytest` / Install pytest: `pip install pytest`

### 调试测试失败 / Debug Test Failures
```bash
# 运行更详细的输出 / Run with more verbose output
python -m unittest discover tests -v

# 运行单个失败的测试 / Run single failing test
python -m unittest tests.test_provider_he.TestHeProvider.failing_test -v

# 添加print语句或使用pdb调试 / Add print statements or use pdb for debugging
```

## 测试覆盖目标 / Test Coverage Goals

当前测试覆盖包括：

Current test coverage includes:
- ✅ BaseProvider核心功能 / BaseProvider core functionality  
- ✅ 所有提供商实现（callback, debug, he）/ All provider implementations (callback, debug, he)
- ✅ 错误处理和边界情况 / Error handling and edge cases
- ✅ Python 2/3兼容性 / Python 2/3 compatibility
- ✅ 日志记录和敏感数据屏蔽 / Logging and sensitive data masking

目标：为所有提供商实现保持>90%的代码覆盖率。

Target: Maintain >90% code coverage for all provider implementations.
