# Callback Provider 配置指南

Callback Provider 是一个通用的自定义回调接口，允许您将 DDNS 更新请求转发到任何自定义的 HTTP API 端点或者webhook。这个 Provider 非常灵活，支持 GET 和 POST 请求，并提供变量替换功能。

## 基本配置

### 配置参数

| 参数 | 说明 | 必填 | 示例 |
|------|------|------|------|
| `id` | 回调URL地址，支持变量替换 | ✅ | `https://api.example.com/ddns?domain=__DOMAIN__&ip=__IP__` |
| `token` | POST 请求参数（JSON对象或JSON字符串），为空时使用GET请求 | 可选 | `{"api_key": "your_key"}` 或 `"{\"api_key\": \"your_key\"}"` |

### 最小配置示例

```json
{
    "id": "https://api.example.com/ddns?domain=__DOMAIN__&ip=__IP__",
    "token": "",
    "dns": "callback",
    "ipv4": ["sub.example.com"],
    "ipv6": ["ipv6.example.com"]
}
```

## 请求方式

### GET 请求（推荐简单场景）

当 `token` 为空或未设置时，使用 GET 请求方式：

```json
{
    "id": "https://api.example.com/update?domain=__DOMAIN__&ip=__IP__&type=__RECORDTYPE__",
    "token": "",
    "dns": "callback"
}
```

**实际请求示例：**

```http
GET https://api.example.com/update?domain=sub.example.com&ip=192.168.1.100&type=A
```

### POST 请求（推荐复杂场景）

当 `token` 不为空时，使用 POST 请求方式。`token` 可以是 JSON 对象或 JSON 字符串，作为 POST 请求体：

**JSON 对象格式：**

```json
{
    "id": "https://api.example.com/ddns",
    "token": {
        "api_key": "your_secret_key",
        "domain": "__DOMAIN__",
        "value": "__IP__",
        "type": "__RECORDTYPE__",
        "ttl": "__TTL__"
    },
    "dns": "callback"
}
```

**JSON 字符串格式：**

```json
{
    "id": "https://api.example.com/ddns",
    "token": "{\"api_key\": \"your_secret_key\", \"domain\": \"__DOMAIN__\", \"value\": \"__IP__\"}",
    "dns": "callback"
}
```

**实际请求示例：**

```http
POST https://api.example.com/ddns
Content-Type: application/json

{
    "api_key": "your_secret_key",
    "domain": "sub.example.com",
    "value": "192.168.1.100",
    "type": "A",
    "ttl": "300"
}
```

## 变量替换

Callback Provider 支持以下内置变量，在请求时会自动替换：

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `__DOMAIN__` | 完整域名 | `sub.example.com` |
| `__IP__` | IP地址（IPv4或IPv6） | `192.168.1.100` 或 `2001:db8::1` |
| `__RECORDTYPE__` | DNS记录类型 | `A`、`AAAA`、`CNAME` |
| `__TTL__` | 生存时间（秒） | `300`、`600` |
| `__LINE__` | 解析线路 | `default`、`unicom` |
| `__TIMESTAMP__` | 当前时间戳 | `1634567890.123` |

### 变量替换示例

**配置：**

```json
{
    "id": "https://api.example.com/ddns/__DOMAIN__?ip=__IP__&ts=__TIMESTAMP__",
    "token": {
        "domain": "__DOMAIN__",
        "record_type": "__RECORDTYPE__",
        "ttl": "__TTL__",
        "timestamp": "__TIMESTAMP__"
    },
    "dns": "callback"
}
```

**实际请求：**

```http
POST https://api.example.com/ddns/sub.example.com?ip=192.168.1.100&ts=1634567890.123
Content-Type: application/json

{
    "domain": "sub.example.com",
    "record_type": "A",
    "ttl": 300,
    "timestamp": 1634567890.123
}
```

## 使用场景

### 1. 自定义 Webhook

将 DDNS 更新通知发送到自定义 webhook：

```json
{
    "id": "https://hooks.example.com/ddns",
    "token": {
        "event": "ddns_update",
        "domain": "__DOMAIN__",
        "new_ip": "__IP__",
        "record_type": "__RECORDTYPE__",
        "timestamp": "__TIMESTAMP__"
    },
    "dns": "callback",
    "index4": ["default"]
}
```

### 2. 使用字符串格式的 token

当需要动态构造复杂的 JSON 字符串时：

```json
{
    "id": "https://api.example.com/ddns",
    "token": "{\"auth\": \"your_key\", \"record\": {\"name\": \"__DOMAIN__\", \"value\": \"__IP__\", \"type\": \"__RECORDTYPE__\"}}",
    "dns": "callback"
}
```

## 高级配置

### 错误处理

Callback Provider 会记录详细的日志信息：

- **成功**：记录回调结果
- **失败**：记录错误信息和原因
- **空响应**：记录警告信息

### 安全考虑

1. **HTTPS**: 建议使用 HTTPS 协议保护数据传输
2. **认证**: 在 token 中包含必要的认证信息
3. **验证**: 服务端应验证请求的合法性
4. **日志**: 避免在日志中暴露敏感信息

## 完整配置示例

### GET方式回调

```json
{
    "id": "https://api.example.com/update?key=your_api_key&domain=__DOMAIN__&ip=__IP__&type=__RECORDTYPE__",
    "token": "",
    "dns": "callback",
    "ipv4": ["home.example.com", "server.example.com"],
    "index4": ["default"]
}
```

### POST方式回调（集成第三方DNS服务）

```json
{
    "id": "https://api.third-party-dns.com/v1/records",
    "token": {
        "auth_token": "your_api_token",
        "zone": "example.com",
        "name": "__DOMAIN__",
        "content": "__IP__",
        "type": "__RECORDTYPE__",
        "ttl": "__TTL__"
    },
    "dns": "callback",
    "ipv4": ["*.example.com"],
    "index4": ["default"]
}
```

## 故障排除

### 常见问题

1. **URL无效**: 确保 `id` 包含完整的HTTP/HTTPS URL
2. **JSON格式错误**: 检查 `token` 的JSON格式是否正确
   - 对象格式：`{"key": "value"}`
   - 字符串格式：`"{\"key\": \"value\"}"`（注意转义双引号）
3. **变量未替换**: 确保变量名拼写正确（注意双下划线）
4. **请求失败**: 检查目标服务器是否可访问
5. **认证失败**: 验证API密钥或认证信息是否正确

### 调试方法

1. **启用调试**: 在配置中设置 `"debug": true`
2. **查看日志**: 检查DDNS运行日志中的详细信息
3. **测试API**: 使用curl或Postman测试回调API
4. **网络检查**: 确保网络连通性和DNS解析正常

### 测试工具

可以使用在线工具测试回调功能：

```bash
# 使用 curl 测试 GET 请求
curl "https://httpbin.org/get?domain=test.example.com&ip=192.168.1.1"

# 使用 curl 测试 POST 请求
curl -X POST "https://httpbin.org/post" \
  -H "Content-Type: application/json" \
  -d '{"domain": "test.example.com", "ip": "192.168.1.1"}'
```

## 相关链接

- [DDNS 项目首页](../../README.md)
- [配置文件格式](../json.md)
- [命令行使用](../cli.md)
- [开发者指南](../dev/provider.md)
