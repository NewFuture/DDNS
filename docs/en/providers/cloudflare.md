# Cloudflare DNS 配置指南

## 概述

Cloudflare 是全球领先的 CDN 和网络安全服务提供商，提供权威 DNS 解析服务，支持动态 DNS 记录的创建与更新。本 DDNS 项目通过 Cloudflare API 进行 DNS 记录的自动管理。

官网链接：

- 官方网站：<https://www.cloudflare.com/>
- 服务商控制台：<https://dash.cloudflare.com/>

## 认证信息

### 1. API Token 认证（推荐）

API Token 方式更安全，支持精细化权限控制，是 Cloudflare 推荐的集成方法。

#### 获取认证信息

1. 登录 [Cloudflare 控制台](https://dash.cloudflare.com/)
2. 进入"我的个人资料" > "API 令牌"或访问 <https://dash.cloudflare.com/profile/api-tokens>
3. 点击"创建令牌"，选择"自定义令牌"模板
4. 配置权限：
   - **区域：读取** (Zone:Read)
   - **DNS：编辑** (Zone:DNS:Edit)
5. 选择要管理的域名区域
6. 复制生成的 **API Token**，令牌只显示一次，请妥善保存

```jsonc
{
    "dns": "cloudflare",
    "token": "your_cloudflare_api_token"  // Cloudflare API Token, ID 留空或者不填
}
```

### 2. Global API Key 认证（不推荐）

使用 Cloudflare 账户邮箱和 Global API Key，权限过大，**安全性较低**，仅建议特殊场景使用。

#### 获取 Global API Key

1. 登录 [Cloudflare 控制台](https://dash.cloudflare.com/)
2. 进入"我的个人资料" > "API 令牌"
3. 查看"Global API Key"并复制

```jsonc
{
    "dns": "cloudflare",
    "id": "your-email@example.com",    // Cloudflare 账户邮箱
    "token": "your_global_api_key"     // Cloudflare Global API Key
}
```

## 权限要求

确保使用的 Cloudflare 账号具有以下权限：

### API Token 权限

- **Zone:Read**：区域读取权限，用于列出和获取域名区域信息
- **Zone:DNS:Edit**：DNS 编辑权限，用于创建、更新和删除 DNS 记录

### Global API Key 权限

- **完全访问权限**：拥有账户下所有资源的完全控制权限

可以在 [Cloudflare API 令牌管理](https://dash.cloudflare.com/profile/api-tokens) 中查看和配置权限。

## 完整配置示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "cloudflare",                // 当前服务商
    "token": "your_cloudflare_api_token", // Cloudflare API Token
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 域名
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 域名
    "ttl": 300,                             // DNS记录TTL（秒）
    "proxied": false                        // 是否启用 Cloudflare 代理
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `cloudflare`                       | 无        | 服务商参数 |
| id      | 认证邮箱     | 字符串         | Cloudflare 账户邮箱（仅 Global API Key） | 无   | 服务商参数 |
| token   | 认证密钥     | 字符串         | Cloudflare API Token 或 Global API Key | 无  | 服务商参数 |
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ttl     | TTL 时间      | 整数（秒）     | [参考下方](#ttl)                    | 300/auto | 服务商参数 |
| proxied | 代理状态      | 布尔           | `true`、`false`                    | 无        | 服务商参数 |
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数  
> - **服务商参数**：当前服务商支持, 值与当前服务商相关

### proxied

`proxied` 参数控制 DNS 记录是否通过 Cloudflare 代理。这是 Cloudflare 特有的功能，用于启用或禁用其 CDN 和安全保护功能。

#### 查询记录匹配逻辑

当配置了 `proxied` 参数时，DDNS 会按照以下优先级查询现有的 DNS 记录：

1. **优先使用 `proxied` 过滤**：首先尝试查询匹配指定 `proxied` 状态的记录
2. **回退到无过滤查询**：如果带有 `proxied` 过滤的查询没有找到记录，将自动重试不带 `proxied` 过滤的查询

这种回退机制确保了以下场景的正确处理：

- **场景1**: 配置文件从 `"proxied": true` 改为 `"proxied": false`
  - 即使原记录是 `proxied=true`，系统也能找到并更新它
  
- **场景2**: 配置文件从 `"proxied": false` 改为 `"proxied": true`
  - 即使原记录是 `proxied=false`，系统也能找到并更新它

- **场景3**: 配置文件新增 `"proxied": true/false` 参数
  - 能够找到不带 `proxied` 过滤创建的记录并进行更新

> **注意**：如果查询时带 `proxied` 过滤找到了记录，则不会执行回退查询，直接使用匹配的记录。

### ttl

`ttl` 参数指定 DNS 记录的生存时间（TTL），单位为秒。Cloudflare 的 TTL 设置根据记录是否启用代理而有所不同。

#### 代理记录 (Proxied Records)

所有代理记录的 TTL 默认为 **Auto**，固定设置为 **300 秒**（5 分钟），此值**无法编辑**。

由于只有用于 IP 地址解析的记录才能被代理，此设置确保分配的任播 IP 地址的潜在变化能够快速生效，因为递归解析器不会将其缓存超过 300 秒。

> **注意**：实际体验记录变化可能需要超过 5 分钟，因为本地 DNS 缓存可能需要更长时间才能更新。

#### 非代理记录 (Unproxied Records)

对于仅 DNS 记录，您可以选择以下 TTL 范围：

| 套餐类型     | 支持的 TTL 范围（秒） | 说明 |
| ------------ | :-------------------: | :--- |
| Free/Pro/Business | 60 - 86400 | 最低 TTL 为 1 分钟 |
| Enterprise   | 30 - 86400 | 最低 TTL 为 30 秒 |

> 参考：[Cloudflare TTL 说明](https://developers.cloudflare.com/dns/manage-dns-records/reference/ttl/)

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### 常见问题

- **Invalid API token**：检查 API Token 是否正确，确认权限配置
- **Zone not found**：确保域名已添加到 Cloudflare 账号，域名处于活跃状态
- **Record creation failed**：检查记录格式和 TTL 值，确认权限设置
- **Rate limit exceeded**：API 调用频率超限，降低请求频率

## 支持与资源

- [Cloudflare 开发者文档](https://developers.cloudflare.com/)
- [Cloudflare API 参考](https://developers.cloudflare.com/api/)
- [Cloudflare 控制台](https://dash.cloudflare.com/)
- [Cloudflare 社区支持](https://community.cloudflare.com/)

> **建议**：推荐使用 API Token 方式，支持精细化权限控制，提升账号安全性，避免使用 Global API Key。
