# 开发指南：如何实现一个新的 DNS Provider

本指南介绍如何基于不同的抽象基类，快速实现一个自定义的 DNS 服务商适配类，支持动态 DNS 记录的创建与更新。

## 📦 目录结构

```text
ddns/
├── provider/
│   ├── _base.py         # 抽象基类 SimpleProvider 和 BaseProvider，签名认证函数
│   └── myprovider.py    # 你的新服务商实现
tests/
├── base_test.py         # 共享测试工具和基类
├── test_provider_*.py   # 各个Provider的单元测试文件
├── test_module_*.py     # 其他测试
└── README.md            # 测试指南
doc/dev/
└── provider.md          # Provider开发指南 (本文档)
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
| `_query_record(zone_id, subdomain, main_domain, record_type, line=None, extra=None)` | **查询当前 DNS 记录** | ✅ 必须 |
| `_create_record(zone_id, subdomain, main_domain, value, record_type, ttl=None, line=None, extra=None)` | **创建新记录** | ✅ 必须 |
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
    content_type = TYPE_FORM          # 或 TYPE_JSON
    decode_response = False           # 如果返回纯文本而非JSON，设为False

    def _validate(self):
        """验证认证信息（可选重写）"""
        super(MySimpleProvider, self)._validate()
        # 添加特定的验证逻辑，如检查API密钥格式
        if not self.token or len(self.token) < 16:
            raise ValueError("Invalid API token format")

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        # type: (str, str, str, int | None, str | None) -> bool
        """更新或创建DNS记录 https://doc.simpledns.com/update"""
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
from ._base import BaseProvider, TYPE_JSON, hmac_sha256_authorization, sha256_hash

class MyProvider(BaseProvider):
    """
    示例BaseProvider实现
    适用于提供完整CRUD API的DNS服务商
    """
    API = 'https://api.exampledns.com'
    content_type = TYPE_JSON  # 或 TYPE_FORM

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """查询Zone信息 ZoneId https://doc.exmaple.com/api/query_zone"""
        res = self._request("ZoneInfo", key=value...)
        ...
        self.logger.debug("domain not found for: %s", domain)
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """查询记录信息 https://doc.exmaple.com/api/list_records"""
        res = self._request("DescribeRecords", ZoneId=zone_id, Key=value...)
        ...
        self.logger.warning("No record found for: %s", res)
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int, str | None, dict) -> bool
        """创建新record https://doc.exmaple.com/api/create_record"""
        res = self._request("CreateRecord", ZoneId=zone_id, DomainName=domain, OriginInfo=origin, **extra)
        ...
        self.logger.error("Failed to create record: %s", res)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, Any, str, str, int, str | None, dict) -> bool
        """更新record https://doc.exmaple.com/api/update_record"""
        res = self._request("ModifyRecord", ZoneId=zone_id, DomainName=domain, OriginInfo=origin)
        ...
        self.logger.error("Failed to update record: %s", res)
        return False
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
    if not self.token or len(self.token) < 16:
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
from base_test import BaseProviderTestCase, unittest, patch, MagicMock
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
├── base_test.py              # 共享测试基类
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

---

## 🔐 云服务商认证签名算法

对于需要签名认证的云服务商（如阿里云、华为云、腾讯云等），DDNS 提供了通用的 HMAC-SHA256 签名认证函数。

### 签名认证工具函数

#### `hmac_sha256_authorization()` - 通用签名生成器

通用的云服务商API认证签名生成函数，支持阿里云、华为云、腾讯云等多种云服务商。
使用HMAC-SHA256算法生成符合各云服务商规范的Authorization头部。
所有云服务商的差异通过模板参数传递，实现完全的服务商无关性。

```python
from ddns.provider._base import hmac_sha256_authorization, sha256_hash

# 通用签名函数调用示例
authorization = hmac_sha256_authorization(
    secret_key=secret_key,                    # 签名密钥（已派生处理）
    method="POST",                            # HTTP方法
    path="/v1/domains/records",               # API路径
    query="limit=20&offset=0",                # 查询字符串
    headers=request_headers,                  # 请求头部字典
    body_hash=sha256_hash(request_body),      # 请求体哈希
    signing_string_format=signing_template,   # 待签名字符串模板
    authorization_format=auth_template        # Authorization头部模板
)
```

**函数参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `secret_key` | `str \| bytes` | 签名密钥，已经过密钥派生处理 |
| `method` | `str` | HTTP请求方法 (GET, POST, etc.) |
| `path` | `str` | API请求路径 |
| `query` | `str` | URL查询字符串 |
| `headers` | `dict[str, str]` | HTTP请求头部 |
| `body_hash` | `str` | 请求体的SHA256哈希值 |
| `signing_string_format` | `str` | 待签名字符串模板，包含 `{HashedCanonicalRequest}` 占位符 |
| `authorization_format` | `str` | Authorization头部模板，包含 `{SignedHeaders}`, `{Signature}` 占位符 |

**模板变量：**

- `{HashedCanonicalRequest}` - 规范请求的SHA256哈希值
- `{SignedHeaders}` - 按字母顺序排列的签名头部列表
- `{Signature}` - 最终的HMAC-SHA256签名值

### 各云服务商签名实现示例

#### 阿里云 (ACS3-HMAC-SHA256)

```python
def _request(self, action, **params):
    # 构建请求头部
    headers = {
        "host": "alidns.aliyuncs.com",
        "x-acs-action": action,
        "x-acs-content-sha256": sha256_hash(body),
        "x-acs-date": timestamp,
        "x-acs-signature-nonce": nonce,
        "x-acs-version": "2015-01-09"
    }
    
    # 阿里云签名模板
    auth_template = (
        "ACS3-HMAC-SHA256 Credential={access_key},"
        "SignedHeaders={{SignedHeaders}},Signature={{Signature}}"
    )
    signing_template = "ACS3-HMAC-SHA256\n{timestamp}\n{{HashedCanonicalRequest}}"
    
    # 生成签名
    authorization = hmac_sha256_authorization(
        secret_key=self.token,
        method="POST",
        path="/",
        query=query_string,
        headers=headers,
        body_hash=sha256_hash(body),
        signing_string_format=signing_template,
        authorization_format=auth_template
    )
    
    headers["authorization"] = authorization
    return self._http("POST", "/", body=body, headers=headers)
```

#### 腾讯云 (TC3-HMAC-SHA256)

```python
def _request(self, action, **params):
    # 腾讯云需要派生密钥
    derived_key = self._derive_signing_key(date, service, self.token)
    
    # 构建请求头部
    headers = {
        "content-type": "application/json",
        "host": "dnspod.tencentcloudapi.com",
        "x-tc-action": action,
        "x-tc-timestamp": timestamp,
        "x-tc-version": "2021-03-23"
    }
    
    # 腾讯云签名模板
    auth_template = (
        "TC3-HMAC-SHA256 Credential={secret_id}/{date}/{service}/tc3_request, "
        "SignedHeaders={{SignedHeaders}}, Signature={{Signature}}"
    )
    signing_template = "TC3-HMAC-SHA256\n{timestamp}\n{date}/{service}/tc3_request\n{{HashedCanonicalRequest}}"
    
    # 生成签名
    authorization = hmac_sha256_authorization(
        secret_key=derived_key,  # 注意：使用派生密钥
        method="POST",
        path="/",
        query="",
        headers=headers,
        body_hash=sha256_hash(body),
        signing_string_format=signing_template,
        authorization_format=auth_template
    )
    
    headers["authorization"] = authorization
    return self._http("POST", "/", body=body, headers=headers)
```

### 辅助工具函数

#### `sha256_hash()` - SHA256哈希计算

```python
from ddns.provider._base import sha256_hash

# 计算字符串的SHA256哈希
hash_value = sha256_hash("request body content")
# 计算字节数据的SHA256哈希  
hash_value = sha256_hash(b"binary data")
```

#### `hmac_sha256()` - HMAC-SHA256签名对象

```python
from ddns.provider._base import hmac_sha256

# 生成HMAC-SHA256字节签名
# 获取 HMAC 对象，可调用 .digest() 获取字节或 .hexdigest() 获取十六进制字符串
hmac_obj = hmac_sha256("secret_key", "message_to_sign")
signature_bytes = hmac_obj.digest()        # 字节格式
signature_hex = hmac_obj.hexdigest()       # 十六进制字符串格式
```

---

### 🛠️ 开发工具推荐

- 本地开发环境：VSCode
- 在线代码编辑器：GitHub Codespaces 或 github.dev

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

## Happy Coding! 🚀
