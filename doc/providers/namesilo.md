# NameSilo DNS 配置指南

## 概述

NameSilo 是一家美国域名注册商和DNS服务提供商，提供可靠的域名管理和DNS解析服务。本 DDNS 项目支持通过 NameSilo API 进行 DNS 记录的自动管理。

## 认证方式

### API Key 认证

NameSilo 使用 API Key 进行身份验证，这是唯一的认证方式。

```json
{
    "dns": "namesilo",
    "token": "your_api_key_here"
}
```

## 获取认证信息

### API Key

1. 登录 [NameSilo 控制台](https://www.namesilo.com/account_home.php)
2. 进入「Account Options」→「API Manager」或访问 <https://www.namesilo.com/account/api-manager>
3. 生成新的 API Key
4. 记录下生成的 API Key，请妥善保存

> **注意**：API Key 具有账户的完整权限，请确保妥善保管，不要泄露给他人。

## 权限要求

NameSilo API Key 具有以下权限：
- **域名管理**：查看和管理您账户下的所有域名
- **DNS记录管理**：创建、读取、更新和删除DNS记录
- **域名信息查询**：获取域名注册信息和状态

## 配置示例

### 基本配置

```json
{
    "dns": "namesilo",
    "token": "c40031261ee449dda629d2df14e9cb63",
    "ipv4": ["ddns.example.com", "www.example.com"],
    "index4": ["default"]
}
```

### 完整配置示例

```json
{
    "dns": "namesilo",
    "token": "c40031261ee449dda629d2df14e9cb63",
    "index4": ["default"],
    "index6": ["default"],
    "ipv4": ["ddns.example.com", "www.example.com"],
    "ipv6": ["ddns.example.com"],
    "ttl": 3600
}
```

## 可选参数

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|-------|
| `ttl` | DNS记录的TTL值（秒） | int | 7207 |

> **注意**：NameSilo TTL 最小值为 300 秒（5分钟），最大值为 2592000 秒（30天）。

### 自定义API端点

在特殊情况下可能需要自定义端点：

```json
{
    "endpoint": "https://www.namesilo.com"
}
```

> **注意**：NameSilo 官方 API 端点为 `https://www.namesilo.com`，除非使用代理服务，否则不建议修改。

## 支持的记录类型

NameSilo API 支持以下 DNS 记录类型：
- **A记录**：IPv4 地址解析
- **AAAA记录**：IPv6 地址解析
- **CNAME记录**：域名别名
- **MX记录**：邮件交换记录
- **TXT记录**：文本记录
- **NS记录**：名称服务器记录
- **SRV记录**：服务记录

## 故障排除

### 常见错误

#### "Invalid API key"
- 检查 API Key 是否正确
- 确认 API Key 没有被禁用
- 验证账户状态是否正常

#### "Domain not found" 
- 确认域名已添加到 NameSilo 账户
- 检查域名拼写是否正确
- 验证域名状态是否为 Active

#### "Record creation failed"
- 检查子域名格式是否正确
- 确认 TTL 值在允许范围内（300-2592000秒）
- 验证是否存在冲突的记录

#### "API request limit exceeded"
- NameSilo 有 API 调用频率限制
- 适当增加更新间隔
- 避免并发调用 API

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### API 响应代码

- **300**：成功
- **110**：域名不存在
- **280**：无效的域名格式
- **200**：无效的 API Key

## API 限制

- **请求频率**：建议每分钟不超过 60 次请求
- **域名数量**：根据账户类型不同而限制
- **记录数量**：每个域名最多 100 条 DNS 记录

## 相关链接

- [NameSilo API 文档](https://www.namesilo.com/api-reference)
- [NameSilo 控制台](https://www.namesilo.com/account_home.php)
- [NameSilo API Manager](https://www.namesilo.com/account/api-manager)

> **安全提示**：建议定期轮换 API Key，并监控账户活动日志，确保 API 使用安全。

> **重要说明**：NameSilo 提供商实现正在等待验证，请在生产环境使用前进行充分测试。