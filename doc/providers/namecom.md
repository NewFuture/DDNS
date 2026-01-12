# Name.com DNS 配置指南

## 概述

Name.com 是一家知名的域名注册商和 DNS 服务提供商，提供完整的 DNS 管理 API（Core API），支持动态 DNS 记录的创建与更新。本 DDNS 项目通过 Name.com Core API 进行 DNS 记录的自动管理。

官网链接：

- 官方网站：<https://www.name.com/>
- 服务商控制台：<https://www.name.com/account>
- API 文档：<https://docs.name.com/>

## 认证信息

Name.com API 使用 HTTP Basic 认证，需要用户名和 API Token。

### 获取 API Token

1. 登录 [Name.com 账户](https://www.name.com/account)
2. 点击右上角用户名，进入"Account Settings"
3. 在左侧菜单中找到"API Token"或访问 <https://www.name.com/account/settings/api>
4. 点击"Generate Token"生成新的 API Token
5. 复制并保存生成的 **API Token**，令牌只显示一次，请妥善保存

> **注意**：如果账户启用了两步验证（2FA），需要先在账户设置中启用 API 访问权限。

```json
{
    "dns": "namecom",
    "id": "your_username",           // Name.com 账户用户名
    "token": "your_api_token"        // Name.com API Token
}
```

## 权限要求

确保使用的 Name.com 账号具有以下权限：

- **域名管理权限**：需要对目标域名拥有完整的管理权限
- **API 访问权限**：账户需要开启 API 访问功能

可以在 [Name.com 账户设置](https://www.name.com/account/settings) 中查看和配置权限。

## 完整配置示例

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "namecom",                   // 当前服务商
    "id": "your_username",              // Name.com 账户用户名
    "token": "your_api_token",          // Name.com API Token
    "index4": ["url:http://api.ipify.cn", "public"],  // IPv4地址来源
    "index6": "public",                 // IPv6地址来源
    "ipv4": ["ddns.example.com"],       // IPv4 域名
    "ipv6": ["ddns.example.com", "ipv6.example.com"],  // IPv6 域名
    "ttl": 300                          // DNS记录TTL（秒）
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `namecom`、`name.com`、`name_com`  | 无        | 服务商参数 |
| id      | 账户用户名   | 字符串         | Name.com 账户用户名                | 无        | 服务商参数 |
| token   | API Token    | 字符串         | Name.com API Token                 | 无        | 服务商参数 |
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ttl     | TTL 时间      | 整数（秒）     | 最小值 300 秒                      | 300       | 服务商参数 |
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`          | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数  
> - **服务商参数**：当前服务商支持, 值与当前服务商相关

### TTL 说明

Name.com API 要求 TTL 最小值为 **300 秒**（5 分钟）。如果设置的 TTL 小于 300 秒，将自动调整为 300 秒。

### 测试环境

Name.com 提供沙盒测试环境用于 API 开发和测试：

- **沙盒 API 地址**：`https://api.dev.name.com`
- **沙盒用户名**：在正常用户名后添加 `-test`（如 `username-test`）
- **沙盒 Token**：使用沙盒环境专用的 API Token

可以通过 `endpoint` 参数配置使用沙盒环境：

```json
{
    "dns": "namecom",
    "id": "username-test",
    "token": "sandbox_api_token",
    "endpoint": "https://api.dev.name.com",
    "ipv4": ["test.example.com"]
}
```

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### 常见问题

- **Invalid credentials**：检查用户名和 API Token 是否正确
- **Domain not found**：确保域名已添加到 Name.com 账号，且拥有管理权限
- **Record creation failed**：检查记录格式和 TTL 值，确认权限设置
- **2FA required**：如果启用了两步验证，需要在账户设置中启用 API 访问
- **Rate limit exceeded**：API 调用频率超限（最大 20 请求/秒，3000 请求/小时），降低请求频率

## 支持与资源

- [Name.com 官方网站](https://www.name.com/)
- [Name.com Core API 文档](https://docs.name.com/)
- [Name.com 账户管理](https://www.name.com/account)
- [Name.com 支持中心](https://www.name.com/support)

> **提示**：请妥善保管 API Token，避免泄露。如果怀疑 Token 泄露，请立即在账户设置中重新生成。
