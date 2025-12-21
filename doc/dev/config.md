# DDNS 配置系统开发文档

本文档面向开发者，详细说明如何扩展和修改 DDNS 配置系统。

## 系统架构

DDNS 配置系统采用分层架构，支持多种配置源：

```text
┌─────────────────────────────────────────────┐
│               配置源（优先级）                │
├─────────────────────────────────────────────┤
│ CLI 参数 > JSON 文件 > 环境变量 > 默认值      │
├─────────────────────────────────────────────┤
│                Config 类                     │
│            统一配置访问接口                   │
├─────────────────────────────────────────────┤
│            Provider 和应用模块               │
└─────────────────────────────────────────────┘
```

**核心模块：**

- `ddns/config/cli.py` - 命令行参数解析
- `ddns/config/json.py` - JSON 配置文件处理
- `ddns/config/env.py` - 环境变量解析
- `ddns/config/config.py` - Config 类实现

## Config 类核心实现

Config 类是配置系统的核心，负责合并多个配置源：

```python
class Config(object):
    def __init__(self, cli_config=None, json_config=None, env_config=None):
        self._cli_config = cli_config or {}
        self._json_config = json_config or {}  
        self._env_config = env_config or {}
        
        # 配置属性初始化
        self.dns = self._get("dns", "debug")
        self.endpoint = self._get("endpoint")  # 新增的端点配置
        
    def _get(self, key, default=None):
        """按优先级获取配置值：CLI > JSON > ENV > default"""
        return (
            self._cli_config.get(key) or 
            self._json_config.get(key) or 
            self._env_config.get(key) or 
            default
        )
```

## 配置参数概览

### 必需参数

- `id` - DNS 服务商认证 ID
- `token` - DNS 服务商 API Token

### 主要参数

- `dns` - DNS 服务商标识 (默认: "debug")
- `endpoint` - 自定义 API 端点 (覆盖默认端点)
- `ipv4`/`ipv6` - 域名列表
- `ttl` - DNS TTL 值
- `proxy` - HTTP 代理设置
- `log_level` - 日志级别

### 支持的 DNS 服务商

```python
SUPPORTED_PROVIDERS = [
    "alidns", "callback", "cloudflare", "debug", "dnscom", 
    "dnspod_com", "dnspod", "he", "huaweidns", "noip", "tencentcloud"
]
```

## 开发指南：添加新配置参数

### 完整开发流程

添加新配置参数需要修改 4 个文件：

#### 1. 更新 JSON Schema (`schema/v4.0.json`)

```json
{
  "properties": {
    "my_param": {
      "type": "string",
      "title": "My Parameter", 
      "description": "Description of my parameter",
      "default": "default_value"
    }
  }
}
```

#### 2. 添加 CLI 参数 (`ddns/config/cli.py`)

```python
def create_parser(description, doc, version, date):
    # ...existing code...
    parser.add_argument(
        "--my-param",
        help="Description of my parameter",
        default=None
    )
```

#### 3. 更新 Config 类 (`ddns/config/config.py`)

```python
class Config(object):
    def __init__(self, cli_config=None, json_config=None, env_config=None):
        # ...existing code...
        self.my_param = self._get("my_param", "default_value")
        
    def dict(self):
        return {
            # ...existing fields...
            "my_param": self.my_param,
        }
```

#### 4. 添加单元测试 (`tests/test_config_config.py`)

```python
def test_my_param_configuration(self):
    """Test my_param configuration from different sources"""
    # CLI 配置测试
    config = Config(cli_config={"my_param": "cli_value"})
    self.assertEqual(config.my_param, "cli_value")
    
    # JSON 配置测试
    config = Config(json_config={"my_param": "json_value"})
    self.assertEqual(config.my_param, "json_value")
    
    # 优先级测试
    config = Config(
        cli_config={"my_param": "cli_value"},
        json_config={"my_param": "json_value"}
    )
    self.assertEqual(config.my_param, "cli_value")  # CLI 优先
```

### 环境变量支持

新参数自动支持环境变量，命名规则：`DDNS_PARAM_NAME`

```bash
export DDNS_MY_PARAM=value
```

## 特殊类型处理

### 数组参数

需要在 `SIMPLE_ARRAY_PARAMS` 中注册：

```python
# config.py
SIMPLE_ARRAY_PARAMS = ["ipv4", "ipv6", "proxy", "my_array_param"]

def split_array_string(value):
    """支持多种分隔符：逗号、分号"""
    if isinstance(value, list):
        return value
    # 支持 "a,b" 或 "a;b" 格式
    if "," in str(value):
        return [item.strip() for item in value.split(",")]
    elif ";" in str(value):
        return [item.strip() for item in value.split(";")]
    return [value]
```

### 布尔值处理

使用 `str_bool()` 函数：

```python
def str_bool(value):
    """将字符串转换为布尔值"""
    if isinstance(value, bool):
        return value
    if str(value).lower() in ["true", "yes", "1", "on"]:
        return True
    if str(value).lower() in ["false", "no", "0", "off"]:
        return False
    return bool(value)
```

### 类型转换示例

```python
# 在 Config.__init__ 中
self.ttl = int(self._get("ttl")) if self._get("ttl") else None
self.cache = str_bool(self._get("cache", True))
self.proxy = self._get("proxy", [])  # 自动处理数组
```

## 配置使用示例

### CLI 基本用法

```bash
python -m ddns --dns=cloudflare --endpoint=https://api.custom.com/v4/
```

### JSON 配置

```jsonc
{
  "dns": "cloudflare",
  "endpoint": "https://api.custom.com/v4/",
  "ipv4": ["example.com"]
}
```

### 环境变量

```bash
export DDNS_DNS=cloudflare
export DDNS_ENDPOINT=https://api.custom.com/v4/
```

## 开发和调试

### 配置验证

```python
def validate_config(config):
    """验证配置完整性"""
    errors = []
    
    if not config.id or not config.token:
        errors.append("id and token are required")
        
    if config.dns not in SUPPORTED_DNS_PROVIDERS:
        errors.append("Unsupported DNS provider: {}".format(config.dns))
    
    if config.ttl and (config.ttl < 1 or config.ttl > 86400):
        errors.append("TTL must be between 1 and 86400 seconds")
            
    return errors
```

### 配置调试

```python
def debug_config(config):
    """输出配置信息（隐藏敏感数据）"""
    config_dict = config.dict()
    for key, value in config_dict.items():
        if key == "token" and value:
            value = value[:2] + "***" + value[-2:]
        print("{}: {}".format(key, value))
```

### 开发测试

```bash
# 运行配置相关测试
python -m unittest discover tests -k "test_config" -v

# 测试特定功能
python -m unittest tests.test_config_config.TestConfigPriority -v
```

### 测试工具

```python
def create_test_config(**overrides):
    """创建测试配置"""
    default_config = {
        "dns": "debug",
        "id": "test_id", 
        "token": "test_token"
    }
    default_config.update(overrides)
    return Config(json_config=default_config)

# 使用
config = create_test_config(dns="cloudflare", endpoint="https://api.test.com")
```

## 开发最佳实践

### 添加新参数的检查清单

1. ✅ **JSON Schema** - 在 `schema/v4.0.json` 中定义
2. ✅ **CLI 参数** - 在 `cli.py` 中添加 `--param-name`
3. ✅ **Config 类** - 在 `config.py` 中添加属性和 `dict()` 方法
4. ✅ **单元测试** - 测试配置优先级和类型转换
5. ✅ **向后兼容** - 提供合理的默认值

### 代码规范

- **类型安全**：使用 `str_bool()`, `int()` 等转换函数
- **默认值**：所有新参数必须有默认值
- **命名规范**：参数名使用下划线，CLI 使用连字符
- **文档同步**：更新 JSON Schema 和相关文档

### endpoint 参数特性

`endpoint` 参数是 v4.0 新增功能，主要用于：

- 覆盖 DNS Provider 的默认 API 端点
- 支持测试环境和自定义域名
- 在 Provider 初始化时优先于类的 API 属性

### 配置系统架构优势

- **多源融合**：CLI、JSON、环境变量无缝合并
- **优先级明确**：CLI > JSON > ENV > 默认值
- **类型安全**：自动类型转换和验证
- **易于扩展**：添加新参数只需 4 步
- **向后兼容**：新参数不影响现有功能

通过这个配置系统，开发者可以快速添加新功能参数，保持代码的一致性和可维护性。
