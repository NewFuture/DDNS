# ClouDNS 配置指南

## 概述

ClouDNS 是一个全球性的 DNS 托管服务提供商，提供免费和付费的 DNS 解析服务，支持动态 DNS 记录的创建与更新。本 DDNS 项目通过 ClouDNS API 进行 DNS 记录的自动管理。

官网链接：

- 官方网站：<https://www.cloudns.net/>
- 控制面板：<https://www.cloudns.net/dns-zones/>
- API 文档：<https://www.cloudns.net/wiki/>

## 认证信息

ClouDNS 使用 **Auth-ID** 和 **Auth-Password** 进行 API 认证。

### 获取认证信息

1. 登录 [ClouDNS 控制面板](https://www.cloudns.net/login/)
2. 进入 "API" 设置页面或访问 <https://www.cloudns.net/api-settings/>
3. 如果尚未启用 API 访问，点击"启用 API"
4. 复制您的 **Auth-ID**（通常是数字 ID）
5. 创建或查看您的 **Auth-Password**（API 密码）

> **安全提示**：为了提高安全性，建议创建一个子账号专门用于 DDNS API 访问，并仅授予必要的 DNS 管理权限。

```jsonc
{
    "dns": "cloudns",
    "id": "12345",                    // ClouDNS Auth-ID
    "token": "your_auth_password"     // ClouDNS Auth-Password
}
```

## 权限要求

确保使用的 ClouDNS 账号具有以下权限：

- **DNS 区域管理**：能够列出和访问 DNS 区域
- **DNS 记录管理**：能够创建、读取、更新 DNS 记录

如果使用子账号，请在主账号中为子账号分配相应的权限。

## 完整配置示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.1.json", // 格式验证
    "dns": "cloudns",                       // 当前服务商
    "id": "12345",                          // ClouDNS Auth-ID
    "token": "your_auth_password",          // ClouDNS Auth-Password
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.example.com"],           // IPv4 域名
    "ipv6": ["ddns.example.com", "ipv6.example.com"], // IPv6 域名
    "ttl": 60                               // DNS记录TTL（秒）
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `cloudns`                          | 无        | 服务商参数 |
| id      | Auth-ID      | 字符串/数字    | ClouDNS Auth-ID                    | 无        | 服务商参数 |
| token   | Auth-Password | 字符串        | ClouDNS Auth-Password              | 无        | 服务商参数 |
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ttl     | TTL 时间      | 整数（秒）     | 60 - 2592000（30天）               | 60        | 服务商参数 |
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数  
> - **服务商参数**：当前服务商支持，值与当前服务商相关

### TTL

`ttl` 参数指定 DNS 记录的生存时间（TTL），单位为秒。

ClouDNS 支持的 TTL 范围：

| 套餐类型 | 支持的 TTL 范围（秒） | 说明                   |
| -------- | :-------------------: | :--------------------- |
| 免费版   |     60 - 86400        | 最低 60 秒，最高 1 天  |
| 高级版   |     60 - 2592000      | 最低 60 秒，最高 30 天 |

默认 TTL 为 **60 秒**（最小值），适合快速更新 DDNS 记录。

> 参考：[ClouDNS TTL 说明](https://www.cloudns.net/wiki/article/12/)

### 根域名记录

ClouDNS 使用空字符串 `""` 或 `"@"` 表示根域名记录。DDNS 会自动处理这两种表示方式。

- 如果您想更新 `example.com` 的记录，使用域名 `example.com` 即可
- 如果您想更新 `www.example.com` 的记录，使用域名 `www.example.com`

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### 常见问题

- **Invalid authentication**：检查 Auth-ID 和 Auth-Password 是否正确
- **Zone not found**：确保域名已添加到 ClouDNS 账号，域名处于活跃状态
- **Record creation failed**：检查记录格式和 TTL 值，确认账号权限
- **API limit exceeded**：API 调用频率超限，降低请求频率或升级套餐

### 免费套餐限制

ClouDNS 免费套餐有以下限制：

- 每个账号最多 4 个 DNS 区域
- 每个区域最多 50 条记录
- API 请求频率限制（具体限制请参考官方文档）

如需更多资源，请考虑升级到付费套餐。

## 支持与资源

- [ClouDNS 官方网站](https://www.cloudns.net/)
- [ClouDNS API 文档](https://www.cloudns.net/wiki/)
- [ClouDNS 控制面板](https://www.cloudns.net/dns-zones/)
- [ClouDNS 支持中心](https://www.cloudns.net/support/)

> **建议**：使用子账号进行 API 访问，以提高账号安全性。定期检查 API 访问日志以监控异常活动。
