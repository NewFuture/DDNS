# 腾讯云 EdgeOne 配置指南

## 概述

腾讯云 EdgeOne（边缘安全速平台）是腾讯云提供的边缘计算和加速服务，支持动态管理加速域名的源站 IP 地址。本 DDNS 项目通过 EdgeOne API 进行加速域名的源站 IP 地址动态更新。

官网链接：

- 官方网站：<https://cloud.tencent.com/product/teo>
- 服务商控制台：<https://console.cloud.tencent.com/edgeone>

## 认证信息

### SecretId/SecretKey 认证

使用腾讯云 SecretId 和 SecretKey 进行认证，与腾讯云 DNS 使用相同的认证方式。

#### 获取认证信息

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
2. 访问 [API密钥管理](https://console.cloud.tencent.com/cam/capi)
3. 点击"新建密钥"按钮
4. 复制生成的 **SecretId** 和 **SecretKey**，请妥善保存
5. 确保账号具有 EdgeOne 的操作权限

```json
{
    "dns": "edgeone",
    "id": "SecretId",          // 腾讯云 SecretId
    "token": "SecretKey"       // 腾讯云 SecretKey
}
```

## 权限要求

确保使用的腾讯云账号具有以下权限：

- **QcloudTEOFullAccess**：EdgeOne 完全访问权限（推荐）
- **QcloudTEOReadOnlyAccess + 自定义写权限**：精细化权限控制

可以在 [访问管理](https://console.cloud.tencent.com/cam/policy) 中查看和配置权限。

## 完整配置示例

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "edgeone",                       // 当前服务商
    "id": "your_secret_id",                 // 腾讯云 SecretId
    "token": "your_secret_key",             // 腾讯云 SecretKey
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],          // IPv4 域名
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 域名
    "ttl": 600                              // DNS记录TTL（秒）
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `edgeone`、`teo`、`tencentedgeone` | 无        | 服务商参数 |
| id      | 认证 ID      | 字符串         | 腾讯云 SecretId                    | 无        | 服务商参数 |
| token   | 认证密钥     | 字符串         | 腾讯云 SecretKey                   | 无        | 服务商参数 |
| index4  | IPv4 来源     | 数组           | [参考配置](../json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ttl     | TTL 时间      | 整数（秒）     | [参考下方](#ttl)                   | 无        | 服务商参数 |
| proxy   | 代理设置      | 数组           | [参考配置](../json.md#proxy)        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../json.md#log)             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数  
> - **服务商参数**：当前服务商支持,值与当前服务商相关

### ttl

EdgeOne 的 TTL 配置主要用于配置说明，实际的缓存策略由 EdgeOne 平台管理。

## 使用说明

EdgeOne DDNS 支持通过更新加速域名的源站 IP 地址来实现动态 DNS 功能。与传统 DNS 记录管理不同，EdgeOne 管理的是加速域名和其对应的源站配置。

### 支持的域名格式

- **完整域名**：`www.example.com`、`api.example.com`
- **根域名**：支持使用 `@` 表示根域名

### 工作原理

1. 查询 EdgeOne 站点信息获取 ZoneId
2. 查询现有的加速域名配置
3. 更新或创建加速域名的源站 IP 地址

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### 常见问题

- **认证失败**：检查 SecretId 和 SecretKey 是否正确，确认账号权限
- **站点未找到**：确保域名已添加到 EdgeOne 站点，域名状态正常
- **加速域名不存在**：确认域名已在 EdgeOne 中配置为加速域名
- **权限不足**：确保账号具有 EdgeOne 的管理权限

## 支持与资源

- [腾讯云 EdgeOne 产品文档](https://cloud.tencent.com/document/product/1552)
- [EdgeOne API 文档](https://cloud.tencent.com/document/api/1552)
- [EdgeOne 控制台](https://console.cloud.tencent.com/edgeone)
- [腾讯云技术支持](https://cloud.tencent.com/document/product/282)

> **注意**：EdgeOne 主要用于边缘加速场景，如需传统 DNS 解析服务，建议使用 [腾讯云 DNS](./tencentcloud.md)。