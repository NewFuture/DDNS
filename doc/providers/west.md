# 西部数码 (west.cn) DNS 配置指南

## 概述

西部数码（West.cn）提供标准 DNS 托管并支持动态解析。DDNS 使用官方 `dnsrec.update` 接口更新记录，接口同时支持 IPv4 与 IPv6。

- 官网：<https://www.west.cn/>
- 控制台：<https://www.west.cn/CustomerCenter/index.asp>
- API 文档：<https://www.west.cn/CustomerCenter/doc/apiV2.html>

## 认证方式

西部数码支持两种认证方式，任选其一：

1. **域名级密钥 (`apidomainkey`)**
   - 在域名详情页获取「域名管理 KEY」
   - 适合单域名或已启用 API 的域名
   - 配置时 **留空 `id`**，`token` 填写 `apidomainkey`

2. **账户级密钥 (`username` + `apikey`)**
   - 在代理/会员后台获取账户 API Key（32 位 MD5）
   - 适合多域名统一管理
   - 配置时 `id` 填写账户用户名，`token` 填写 `apikey`

> 建议先在控制台为目标子域名创建一条解析记录，再启用 DDNS。

## 配置示例

### 域名密钥方式（推荐）

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "dns": "west",
  "token": "your_apidomainkey",
  "ipv4": ["ddns.example.com"],
  "ipv6": ["ddns.example.com"]
}
```

### 账户密钥方式

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "dns": "west",
  "id": "your_username",
  "token": "your_apikey_md5",
  "ipv4": ["ddns.example.com"]
}
```

## 参数说明

| 参数   | 说明 | 类型 | 取值范围/选项 | 默认值 | 参数类型 |
| :----: | :--- | :--- | :------------ | :----- | :------- |
| dns | 服务商标识 | 字符串 | `west` | 无 | 服务商参数 |
| id | 账户用户名（账户密钥方式必填） | 字符串 | 账户名 | `""` | 服务商参数 |
| token | `apidomainkey` 或 `apikey` | 字符串 | 控制台生成的密钥 | 无 | 服务商参数 |
| index4 | IPv4 来源 | 数组/字符串 | [参考配置](../config/json.md#ipv4-ipv6) | `default` | 公用配置 |
| index6 | IPv6 来源 | 数组/字符串 | [参考配置](../config/json.md#ipv4-ipv6) | `default` | 公用配置 |
| ipv4 | IPv4 域名 | 数组 | 域名列表 | 无 | 公用配置 |
| ipv6 | IPv6 域名 | 数组 | 域名列表 | 无 | 公用配置 |
| proxy | 代理设置 | 数组/字符串 | [参考配置](../config/json.md#proxy) | 无 | 公用网络 |
| ssl | SSL 验证方式 | 布尔/字符串 | `\"auto\"`、`true`、`false` | `auto` | 公用网络 |
| cache | 缓存设置 | 布尔/字符串 | `true`、`false`、文件路径 | `true` | 公用配置 |
| log | 日志配置 | 对象 | [参考配置](../config/json.md#log) | 无 | 公用配置 |

> **注意**：接口 `dnsrec.update` 主要用于 DDNS 更新，不支持自定义 TTL/线路，平台使用控制台默认设置。

## 故障排除

- **认证失败**：确认使用的密钥类型与配置一致；域名密钥仅适用于对应域名。
- **记录未更新**：确保目标子域名已在控制台存在；检查 IP 是否变化。
- **频率限制**：避免过于频繁请求，建议更新间隔 ≥ 5 分钟。

启用调试日志：

```sh
ddns -c config.json --debug
```

## 支持与资源

- 官方文档：<https://www.west.cn/CustomerCenter/doc/apiV2.html>
- 帮助中心：<https://api.west.cn/faq/list.asp?Unid=2522>
- 参考配置：[参考配置](../config/json.md)
