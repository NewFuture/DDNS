# 西部数码 (West.cn) DNS 配置指南

## 概述

西部数码是国内标准 DNS 服务商，提供域名解析及动态解析（DDNS）能力，支持 IPv4/IPv6 记录更新。本项目通过官方 API `https://api.west.cn/API/v2/domain/dns/` 进行记录的查询、创建和更新。

- 官网：<https://www.west.cn/>
- 控制台：<https://www.west.cn/manager/>
- API 文档：<https://www.west.cn/CustomerCenter/doc/apiV2.html>

## 认证信息

西部数码支持两种认证方式，任选其一：

1. **域名级 API Key（推荐给单域名用户）**
   - 参数：`apidomainkey`
   - 获取方式：进入域名详情页，打开 **API 接口** 或 **动态解析** 页面复制域名 ApiKey。
2. **用户级 API Key（适合多域名/代理商）**
   - 参数：`username`（账户名） + `apikey`
   - 获取方式：登录控制台 -> **API 接口配置** -> 生成用户级 API 密钥。

```json
{
  "dns": "west",
  "id": "your_username (可选，域名级认证可留空)",
  "token": "your_apikey_or_apidomainkey",
  "ipv4": ["ddns.example.com"],
  "ttl": 600
}
```

## 完整配置示例

### 域名级 ApiKey 示例

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "dns": "west",
  "token": "apidomainkey-from-domain",
  "ipv4": ["ddns.example.com"],
  "ipv6": ["ddns6.example.com"],
  "ttl": 600
}
```

### 用户级 ApiKey 示例

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "dns": "west",
  "id": "your_username",
  "token": "user_apikey",
  "ipv4": ["ddns.example.com"],
  "index4": ["public"],
  "ttl": 600
}
```

### 参数说明

| 参数   | 说明            | 类型   | 取值范围/选项                         | 默认值   | 参数类型 |
| :----: | :-------------- | :----- | :----------------------------------- | :------- | :------- |
| dns    | 服务商标识      | 字符串 | `west`                               | 无       | 服务商参数 |
| id     | 用户名          | 字符串 | 用户级认证时必填，域名级可留空        | 空       | 服务商参数 |
| token  | API 密钥        | 字符串 | 用户级 `apikey` 或域名级 `apidomainkey` | 无       | 服务商参数 |
| index4 | IPv4 来源       | 数组   | [参考配置](../config/json.md#ipv4-ipv6) | `default` | 公用配置 |
| index6 | IPv6 来源       | 数组   | [参考配置](../config/json.md#ipv4-ipv6) | `default` | 公用配置 |
| ipv4   | IPv4 域名列表   | 数组   | 域名/子域名列表                       | 无       | 公用配置 |
| ipv6   | IPv6 域名列表   | 数组   | 域名/子域名列表                       | 无       | 公用配置 |
| ttl    | TTL             | 整数   | 300~86400（单位秒，按官方限制为准）    | 官方默认 | 服务商参数 |
| proxy  | 代理设置        | 数组   | [参考配置](../config/json.md#proxy)      | 无       | 公用网络 |
| ssl    | SSL 验证方式    | 布尔/字符串 | `"auto"`、`true`、`false`            | `auto`   | 公用网络 |
| cache  | 缓存设置        | 布尔/字符串 | `true`、`false`、`filepath`          | `true`   | 公用配置 |
| log    | 日志配置        | 对象   | [参考配置](../config/json.md#log)        | 无       | 公用配置 |

> **注意事项**  
> - 认证失败通常与密钥或域名授权不足有关，请确认 ApiKey 对应的域名或账户权限。  
> - 若使用域名级 ApiKey，`id` 可留空。  
> - 支持自动创建和更新 A/AAAA 记录，线路参数 `record_line` 留空即使用默认线路。

## 故障排除

- **认证失败/返回 401 或 code≠1**：检查 `token` 是否正确、是否对应当前域名；如为用户级认证，确认账户已开通 API 权限。  
- **域名未找到**：确认域名托管在西部数码账户内，且 ApiKey 与域名匹配。  
- **记录未更新**：检查子域名格式（如 `www.example.com`），确认未被解析锁定；必要时先在控制台创建初始记录再使用 DDNS。  
- **字符集问题**：接口使用 `application/x-www-form-urlencoded`，若出现乱码可尝试 UTF-8 或 GBK 编码提交。

## 支持与资源

- [西部数码官网](https://www.west.cn/)
- [API 文档](https://www.west.cn/CustomerCenter/doc/apiV2.html)
- [控制台](https://www.west.cn/manager/)
- 遇到问题可提交 [GitHub Issues](https://github.com/NewFuture/DDNS/issues)
