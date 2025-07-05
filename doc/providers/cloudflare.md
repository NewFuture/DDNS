# Cloudflare DNS 配置指南

## 概述

Cloudflare 是全球领先的 CDN 和网络安全服务提供商。本 DDNS 项目支持通过 Cloudflare API 进行 DNS 记录的自动管理。

## 认证方式

### API Token 认证（推荐）

```json
{
    "dns": "cloudflare",
    "token": "your_api_token_here",
    "ipv4": ["ddns.example.com"]
}
```

### API Key 认证

```json
{
    "id": "your_email@example.com",
    "token": "your_global_api_key",
    "dns": "cloudflare",
    "ipv4": ["ddns.example.com"]
}
```

## 获取认证信息

### API Token

1. 登录 [Cloudflare 控制台](https://dash.cloudflare.com/)
2. 进入「我的个人资料」→「API 令牌」
3. 创建自定义令牌，配置权限：
   - **区域:读取** 和 **DNS:编辑**
4. 选择要管理的域名

### Global API Key

1. 登录 [Cloudflare 控制台](https://dash.cloudflare.com/)
2. 进入「我的个人资料」→「API 令牌」
3. 查看「Global API Key」

## 配置示例

### 基础配置

```json
{
    "dns": "cloudflare",
    "token": "your_api_token_here",
    "ipv4": ["ddns.example.com", "www.example.com"],
    "ipv6": ["ddns.example.com"]
}
```

### 高级配置

```json
{
    "dns": "cloudflare",
    "token": "your_api_token_here",
    "ipv4": ["ddns.example.com"],
    "ttl": 300,
    "comment": "动态DNS更新"
}
```

## 可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `ttl` | DNS记录的TTL值 | 300 |
| `comment` | DNS记录备注 | "DDNS" |

## 故障排除

### 常见错误

- **"Invalid API token"** - 检查 Token 是否正确及权限
- **"Zone not found"** - 确认域名已添加到 Cloudflare
- **"Record creation failed"** - 检查记录格式和 TTL 值（60-86400秒）

### 调试模式

```json
{
    "dns": "cloudflare",
    "token": "your_api_token_here",
    "debug": true,
    "ipv4": ["ddns.example.com"]
}
```

## 相关链接

- [Cloudflare API 文档](https://developers.cloudflare.com/api/)
- [Cloudflare 控制台](https://dash.cloudflare.com/)

> 建议使用 API Token 而非 Global API Key，权限更精细更安全。
