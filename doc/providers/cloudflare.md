# Cloudflare DNS 配置指南

## 概述

Cloudflare 是全球领先的 CDN 和网络安全服务提供商。本 DDNS 项目支持通过 Cloudflare API 进行 DNS 记录的自动管理。

## 认证方式

### API Token 认证（推荐）

```json
{
    "dns": "cloudflare",
    "token": "your_api_token_here",
}
```

### API Key 认证

```json
{
    "id": "your_email@example.com",
    "token": "your_global_api_key",
    "dns": "cloudflare",
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

```json
{
    "dns": "cloudflare",
    "token": "your_api_token_here",
    "index4": ["default"],
    "index6": ["default"],
    "ipv4": ["ddns.example.com", "www.example.com"],
    "ipv6": ["ddns.example.com"],
    "ttl": 600
}
```

## 可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `ttl` | DNS记录的TTL值 | 300 |
| `endpoint` | 自定义API端点地址 | `https://api.cloudflare.com` |

### 自定义API端点

```json
{
    "endpoint": "https://api.cloudflare.com"
}
```

Cloudflare使用单一的全球API端点，但在特殊情况下可能需要自定义：

#### 特殊用途端点

- **企业版/私有云部署**：根据具体部署环境配置
- **代理/镜像服务**：第三方API代理服务地址

> **注意**：Cloudflare官方推荐使用默认的全球端点 `https://api.cloudflare.com`，该端点通过Cloudflare的全球网络自动优化路由。只有在使用企业版私有部署或第三方代理服务时才需要自定义端点。

## 故障排除

### 常见错误

- **"Invalid API token"** - 检查 Token 是否正确及权限
- **"Zone not found"** - 确认域名已添加到 Cloudflare
- **"Record creation failed"** - 检查记录格式和 TTL 值（60-86400秒）

### 调试模式

```sh
ddns -c config.json --debug
```

## 相关链接

- [Cloudflare API 文档](https://developers.cloudflare.com/api/)
- [Cloudflare 控制台](https://dash.cloudflare.com/)

> 建议使用 API Token 而非 Global API Key，权限更精细更安全。
