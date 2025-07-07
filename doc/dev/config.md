# DDNS 配置系统开发文档

本文档介绍 DDNS 配置系统的架构和扩展方法，重点说明如何修改和添加配置参数。

## 系统架构

DDNS 配置系统采用分层架构，支持多种配置源的融合：

```text
┌─────────────────────────────────────────────┐
│               配置源（优先级从高到低）              │
├─────────────────────────────────────────────┤
│ 1. CLI 参数   │ 2. JSON 文件  │ 3. 环境变量   │
├─────────────────────────────────────────────┤
│                Config 类                     │
│            统一配置访问接口                   │
├─────────────────────────────────────────────┤
│            Provider 和应用模块               │
└─────────────────────────────────────────────┘
```

**核心模块：**

- `ddns/config/cli.py` - 命令行参数解析
- `ddns/config/json.py` - JSON 配置文件读写  
- `ddns/config/env.py` - 环境变量解析
- `ddns/config/config.py` - Config 类，统一配置接口

## 配置优先级

配置值按以下优先级合并：**CLI > JSON > ENV > 默认值**

```python
# 示例：TTL 配置的优先级
# 环境变量: DDNS_TTL=300
# JSON: {"ttl": 600}  
# CLI: --ttl=900
# 最终结果: ttl = 900 (CLI 优先级最高)
```

## Config 类核心实现

```python
class Config(object):
    def __init__(self, cli_config=None, json_config=None, env_config=None):
        # 存储三种配置源
        self._cli_config = cli_config or {}
        self._json_config = json_config or {}  
        self._env_config = env_config or {}
        
        # 配置属性初始化
        self.dns = self._get("dns", "debug")
        self.id = self._get("id")
        self.token = self._get("token")
        self.endpoint = self._get("endpoint")  # 新增的端点配置
        
    def _get(self, key, default=None):
        """按优先级获取配置值"""
        return (
            self._cli_config.get(key) or 
            self._json_config.get(key) or 
            self._env_config.get(key) or 
            default
        )
```

## 主要配置参数

### DNS 服务商参数  

- `dns` - DNS 服务商标识 (默认: "debug")
- `endpoint` - 自定义 API 端点 (可覆盖服务商默认端点)
- `id` - DNS 服务商认证 ID
- `token` - DNS 服务商 API Token

### 域名和 IP 参数

- `ipv4` - IPv4 域名列表
- `ipv6` - IPv6 域名列表  
- `index4` - IPv4 获取方式
- `index6` - IPv6 获取方式

### DNS 记录参数

- `ttl` - DNS TTL 值
- `line` - DNS 解析线路

### 网络和系统参数

- `proxy` - HTTP 代理设置
- `ssl` - SSL 证书验证方式
- `cache` - 启用缓存

### 日志参数

- `log_level` - 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- `log_format` - 日志格式
- `log_file` - 日志文件路径
- `log_datefmt` - 日期格式

## 如何添加新的配置参数

### 1. 更新 JSON Schema

编辑 `schema/v4.0.json` 添加新参数定义：

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

### 2. 更新 CLI 参数

在 `ddns/config/cli.py` 中添加命令行选项：

```python
def create_parser(...):
    parser.add_argument(
        "--my-param",
        help="Description of my parameter",
        default=None
    )
```

### 3. 更新 Config 类

在 `ddns/config/config.py` 中添加新属性：

```python
class Config(object):
    def __init__(self, ...):
        # ...existing code...
        self.my_param = self._get("my_param", "default_value")
        
    def dict(self):
        return {
            # ...existing fields...
            "my_param": self.my_param,
        }
```

### 4. 环境变量支持

新参数自动支持环境变量：`DDNS_MY_PARAM=value`

### 5. 添加测试

在 `tests/test_config_config.py` 中添加测试：

```python
def test_my_param_configuration(self):
    """Test my_param configuration"""
    config = Config(cli_config={"my_param": "test_value"})
    self.assertEqual(config.my_param, "test_value")
```

## 特殊类型处理

### 数组参数

```python
# 在 config.py 的 SIMPLE_ARRAY_PARAMS 中注册
DDNS_SIMPLE_ARRAY_PARAMS = ["ipv4", "ipv6", "proxy", "my_array_param"]

# 支持多种分隔符
"domain1.com,domain2.com"  # 逗号分隔
"domain1.com;domain2.com"  # 分号分隔
```

## 配置使用示例

### 通过 CLI 设置

```bash
python run.py --dns=cloudflare --endpoint=https://api.custom.com/v4/ --ttl=600
```

### 通过 JSON 设置  

```json
{
  "dns": "cloudflare",
  "endpoint": "https://api.custom.com/v4/",
  "ttl": 600,
  "ipv4": ["example.com"],
  "log_level": "DEBUG"
}
```

### 通过环境变量设置

```bash
export DDNS_DNS=cloudflare
export DDNS_ENDPOINT=https://api.custom.com/v4/
export DDNS_TTL=600
export DDNS_LOG_LEVEL=DEBUG
```

## 配置验证和调试

### 配置验证

```python
def validate_config(config):
    """验证配置完整性"""
    if not config.id or not config.token:
        raise ValueError("id and token are required")
    if config.dns not in SUPPORTED_DNS_PROVIDERS:
        raise ValueError("Unsupported DNS provider: {}".format(config.dns))
```

### 配置调试

```python
# 输出配置信息（隐藏敏感数据）
config_dict = config.dict()
for key, value in config_dict.items():
    if key == "token" and value:
        value = value[:2] + "***" + value[-2:]
    print("{}: {}".format(key, value))
```

## 测试

### 运行配置测试

```bash
# 运行所有配置测试
python -m unittest discover tests -k "test_config" -v

# 运行特定测试文件
python -m unittest tests.test_config_config -v
```

### 测试工具函数

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
```

## 最佳实践

1. **新参数添加流程**：JSON Schema → CLI → Config 类 → 测试
2. **保持向后兼容**：新参数应有合理的默认值
3. **类型安全**：使用适当的类型转换函数
4. **文档同步**：更新参数时同步更新文档
5. **完整测试**：覆盖各种配置源和边界情况

通过这个架构，DDNS 配置系统提供了灵活、可扩展的配置管理，支持多种配置源和优先级合并，方便开发者添加新功能和参数。
