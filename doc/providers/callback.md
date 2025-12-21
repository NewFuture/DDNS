# Callback Provider 配置指南

Callback Provider 是一个通用的自定义回调接口，允许您将 DDNS 更新请求转发到任何自定义的 HTTP API 端点或者webhook。这个 Provider 非常灵活，支持 GET 和 POST 请求，并提供变量替换功能。

## 基本配置

| 参数 | 说明 | 必填 | 示例 |
|------|------|------|------|
| `id` | 回调URL地址，支持变量替换 | - | `https://api.example.com/ddns?domain=__DOMAIN__&ip=__IP__` |
| `token` | POST 请求参数（JSON对象或JSON字符串），为空时使用GET请求 | 可选 | `{"api_key": "your_key"}` 或 `"{\"api_key\": \"your_key\"}"` |
| `endpoint` | 可选，API端点地址，不会参与变量替换 | - | `https://api.example.com/ddns` |
| `dns` | 固定值 `"callback"`，表示使用回调方式 | ✅ | `"callback"` |

## 完整配置示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "callback",
    "endpoint": "https://api.example.com", // endpoint 可以和 Id 参数合并
    "id": "/ddns?domain=__DOMAIN__&ip=__IP__", //  endpoint 可以和 Id 不能同时为空
    "token": "", // 空字符串表示使用 GET 请求， 有值时使用 POST 请求
    "index4": ["url:http://api.ipify.cn", "public"],
    "index6": "public",
    "ipv4": "ddns.newfuture.cc",
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"]
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | 无        | 公用配置   |

## 请求方式

| 方法 | 条件       | 描述               |
|------|------------|--------------------|
| GET  | token 为空 | 使用 URL 查询参数  |
| POST | token 非空 | 使用 JSON 请求体   |

### GET 请求示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "callback",
    "id": "https://api.example.com/update?domain=__DOMAIN__&ip=__IP__&type=__RECORDTYPE__",
    "index4": ["url:http://api.ipify.cn", "public"],
    "ipv4": "ddns.newfuture.cc",
}
```

```http
GET https://api.example.com/update?domain=ddns.newfuture.cc&ip=192.168.1.100&type=A
```

### POST 请求示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "callback",
    "endpoint": "https://api.example.com",
    "token": {
        "api_key": "your_secret_key",
        "domain": "__DOMAIN__",
        "value": "__IP__"
    },
    "index4": ["url:http://api.ipify.cn", "public"],
    "ipv4": "ddns.newfuture.cc",
}
```http
POST https://api.example.com
Content-Type: application/json

{
  "api_key": "your_secret_key",
  "domain": "ddns.newfuture.cc",
  "value": "192.168.1.100",
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

## 使用场景

### 1. 自定义 Webhook

将 DDNS 更新通知发送到自定义 webhook：

```jsonc
{
    "endpoint": "https://hooks.example.com",
    "id":"/webhook",
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

```jsonc
{
    "id": "https://api.example.com/ddns",
    "token": "{\"auth\": \"your_key\", \"record\": {\"name\": \"__DOMAIN__\", \"value\": \"__IP__\", \"type\": \"__RECORDTYPE__\"}}",
    "dns": "callback"
}
```

## 故障排除

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
- [配置文件格式](../config/json.md)
- [命令行使用](../config/cli.md)
- [开发者指南](../dev/provider.md)
