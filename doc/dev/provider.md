# 开发指南：如何实现一个新的 DNS Provider

本指南介绍如何基于不同的抽象基类，快速实现一个自定义的 DNS 服务商适配类，支持动态 DNS 记录的创建与更新。

## 📦 目录结构

```text
ddns/
├── provider/
│   ├── _base.py         # 抽象基类 SimpleProvider 和 BaseProvider
│   └── myprovider.py    # 你的新服务商实现
tests/
├── test_base.py         # 共享测试工具和基类
├── test_provider_*.py   # 各个Provider的单元测试文件
└── README.md            # 测试指南
```

---

## 🚀 快速开始

DDNS 提供两种抽象基类，根据DNS服务商的API特性选择合适的基类：

### 1. SimpleProvider - 简单DNS服务商

适用于只提供简单更新接口，不支持查询现有记录的DNS服务商。

**必须实现的方法：**
| 方法 | 说明 | 是否必须 |
|------|------|----------|
| `set_record(domain, value, record_type="A", ttl=None, line=None, **extra)` | **更新或创建DNS记录** | ✅ 必须 |
| `_validate()` | **验证认证信息** | ❌ 可选（有默认实现） |

**适用场景：**
- 只提供更新接口的DNS服务商（如HE.net）
- 不需要查询现有记录的简单场景
- 调试和测试用途
- 回调(Webhook)类型的DNS更新

### 2. BaseProvider - 完整DNS服务商  ⭐️ 推荐

适用于提供完整CRUD操作的标准DNS服务商API。

**必须实现的方法：**

| 方法 | 说明 | 是否必须 |
|------|------|----------|
| `_query_zone_id(domain)` | **查询主域名的Id** (zone_id) | ✅ 必须 |
| `_query_record(zone_id, sub_domain, main_domain, record_type, line=None, extra=None)` | **查询当前 DNS 记录** | ✅ 必须 |
| `_create_record(zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra=None)` | **创建新记录** | ✅ 必须 |
| `_update_record(zone_id, old_record, value, record_type, ttl=None, line=None, extra=None)` | **更新现有记录** | ✅ 必须 |
| `_validate()` | **验证认证信息** | ❌ 可选（有默认id和token必填） |

**内置功能：**
- ✅ SimpleProvider的所有功能
- 🎯 自动记录管理（查询→创建/更新的完整流程）
- 💾 缓存机制
- 📝 详细的操作日志和错误处理

**适用场景：**
- 提供完整REST API的DNS服务商（如Cloudflare、阿里云DNS）
- 需要查询现有记录状态的场景
- 支持精确的记录管理和状态跟踪

## 🔧 实现示例

### SimpleProvider 示例

适用于简单DNS服务商，参考现有实现：
- [`provider/he.py`](/ddns/provider/he.py): Hurricane Electric DNS更新
- [`provider/debug.py`](/ddns/provider/debug.py): 调试用途，打印IP地址
- [`provider/callback.py`](/ddns/provider/callback.py): 回调/Webhook类型DNS更新

> provider/mysimpleprovider.py
```python
# coding=utf-8
"""
自定义简单 DNS 服务商示例
@author: YourGithubUsername
"""
from ._base import SimpleProvider, TYPE_FORM

class MySimpleProvider(SimpleProvider):
    """
    示例SimpleProvider实现
    支持简单的DNS记录更新，适用于大多数简单DNS API
    """
    API = 'https://api.simpledns.com'
    ContentType = TYPE_FORM          # 或 TYPE_JSON
    DecodeResponse = False           # 如果返回纯文本而非JSON，设为False

    def _validate(self):
        """验证认证信息（可选重写）"""
        super(MySimpleProvider, self)._validate()
        # 添加特定的验证逻辑，如检查API密钥格式
        if not self.auth_token or len(self.auth_token) < 16:
            raise ValueError("Invalid API token format")

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        """更新DNS记录 - 必须实现"""
        # logic to update DNS record
```


### BaseProvider 示例

适用于标准DNS服务商，参考现有实现：
- [`provider/dnspod.py`](/ddns/provider/dnspod.py): POST 表单数据，无签名
- [`provider/cloudflare.py`](/ddns/provider/cloudflare.py): RESTful JSON，无签名
- [`provider/alidns.py`](/ddns/provider/alidns.py): POST 表单+sha256参数签名
- [`provider/huaweidns.py`](/ddns/provider/huaweidns.py): RESTful JSON，参数header签名

> provider/myprovider.py
```python
# coding=utf-8
"""
自定义标准 DNS 服务商示例
@author: YourGithubUsername
"""
from ._base import BaseProvider, TYPE_JSON

class MyProvider(BaseProvider):
    """
    示例BaseProvider实现
    适用于提供完整CRUD API的DNS服务商
    """
    API = 'https://api.exampledns.com'
    ContentType = TYPE_JSON  # 或 TYPE_FORM

    def _request(self, action, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict
        """[推荐]封装通用请求逻辑，处理认证和公共参数"""


    def _query_zone_id(self, domain):
        # type: (str) -> str
        """查询主域名的Zone ID"""
        # 精确查找 或者 list匹配

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line=None, extra=None):
        # type: (str, str, str, int | None, str | None, dict | None) -> Any
        """查询现有DNS记录"""


    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, str, str, str, int | None, str | None, dict | None) -> bool
        """创建新的DNS记录"""

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, str, str, str, int | None, str | None, dict | None) -> bool
        """更新现有DNS记录"""
```

---

## ✅ 开发最佳实践

### 选择合适的基类

1. **SimpleProvider** - 功能不完整的DNS服务商
   - ✅ DNS服务商只提供更新API
   - ✅ 不需要查询现有记录

2. **BaseProvider** - 适合标准和复杂场景
   - ✅ DNS服务商提供完整查询,创建，修改 API
   - ✅ 需要精确的记录状态管理
   - ✅ 支持复杂的域名解析逻辑

### 通用开发建议


#### 🌐 HTTP请求处理
```python
# 使用内置的_http方法，自动处理代理、编码、日志
response = self._http("POST", path, params=params, headers=headers)

```

#### 🔒 格式验证
```python
def _validate(self):
    """认证信息验证示例"""
    super(MyProvider, self)._validate()
    # 检查API密钥格式
    if not self.auth_token or len(self.auth_token) < 16:
        raise ValueError("API token must be at least 16 characters")
```

#### 📝 日志记录
```python
if result:
    self.logger.info("DNS record got: %s", result.get("id"))
    return True
else:
    self.logger.warning("DNS record update returned false")

```

---

## 🧪 测试和调试

### 单元测试

每个Provider都应该有完整的单元测试。项目提供统一的测试基类和工具：

```python
# tests/test_provider_myprovider.py
from test_base import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.myprovider import MyProvider

class TestMyProvider(BaseProviderTestCase):
    def setUp(self):
        super(TestMyProvider, self).setUp()
        # Provider特定的setup
    
    def test_init_with_basic_config(self):
        """测试基本初始化"""
   
```

### 运行测试

```bash
# 运行所有测试
python -m unittest discover tests -v

# 运行特定Provider测试
python -m unittest tests.test_provider_myprovider -v

# 运行特定测试方法
python tests/test_provider_myprovider.py
```

---

## 📚 更多资源和最佳实践

### 🏗️ 项目结构建议

```text
ddns/
├── provider/
│   ├── _base.py              # 基类定义
│   ├── myprovider.py         # 你的Provider实现
│   └── __init__.py           # 导入和注册
tests/
├── test_base.py              # 共享测试基类
├── test_provider_myprovider.py  # 你的Provider测试
└── README.md                 # 测试指南
```

### 📖 参考实现

**SimpleProvider 参考：**
- [`provider/he.py`](/ddns/provider/he.py) - Hurricane Electric (简单表单提交)
- [`provider/debug.py`](/ddns/provider/debug.py) - 调试工具 (仅打印信息)
- [`provider/callback.py`](/ddns/provider/callback.py) - 回调/Webhook模式

**BaseProvider 参考：**
- [`provider/cloudflare.py`](/ddns/provider/cloudflare.py) - RESTful JSON API
- [`provider/alidns.py`](/ddns/provider/alidns.py) - POST+签名认证
- [`provider/dnspod.py`](/ddns/provider/dnspod.py) - POST表单数据提交

### 🛠️ 开发工具推荐

* 本地开发环境：VSCode
* 在线代码编辑器：GitHub Codespaces 或 github.dev

### 🎯 常见问题解决

1. **Q: 为什么选择SimpleProvider而不是BaseProvider？**
   - A: 如果DNS服务商只提供更新API，没有查询API，选择SimpleProvider更简单高效

---

## 🎉 总结

### 快速检查清单

- [ ] 选择了合适的基类（`SimpleProvider` vs `BaseProvider`）
- [ ] 实现了所有必需的方法(GPT或者Copilot辅助)
- [ ] 添加了适当的错误处理和日志记录
- [ ] 编写了完整的单元测试(使用GPT或Copilot生成)
- [ ] 测试了各种边界情况和错误场景
- [ ] 更新了相关文档

**Happy Coding! 🚀**
