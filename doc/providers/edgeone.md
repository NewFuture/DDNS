# 腾讯�?EdgeOne 配置指南

## 概述

腾讯�?EdgeOne（边缘安全速平台）是腾讯云提供的边缘计算和加速服务，支持动态管理加速域名的源站 IP 地址。本 DDNS 项目通过 EdgeOne API 进行加速域名的源站 IP 地址动态更新�?

官网链接�?

- 官方网站�?https://cloud.tencent.com/product/teo>
- EdgeOne 国际版：<https://edgeone.ai>
- 服务商控制台�?https://console.cloud.tencent.com/edgeone>

## 认证信息

### SecretId/SecretKey 认证

使用腾讯�?SecretId �?SecretKey 进行认证，与腾讯�?DNS 使用相同的认证方式�?

> 与[腾讯�?DNS](tencentcloud.md) 相同，EdgeOne 使用 SecretId �?SecretKey 进行认证。但是权限要求不同，需要确保账号具�?EdgeOne 的操作权限�?

#### 获取认证信息

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
2. 访问 [API密钥管理](https://console.cloud.tencent.com/cam/capi)
3. 点击"新建密钥"按钮
4. 复制生成�?**SecretId** �?**SecretKey**，请妥善保存
5. 确保账号具有 EdgeOne 的操作权�?

```jsonc
{
    "dns": "edgeone",
    "id": "SecretId",     // 腾讯�?SecretId
    "token": "SecretKey"  // 腾讯�?SecretKey
}
```

## 权限要求

确保使用的腾讯云账号具有以下权限�?

- **QcloudTEOFullAccess**：EdgeOne 完全访问权限（推荐）
- **QcloudTEOReadOnlyAccess + 自定义写权限**：精细化权限控制

可以�?[访问管理](https://console.cloud.tencent.com/cam/policy) 中查看和配置权限�?

## 完整配置示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "edgeone",                       // 当前服务�?
    "id": "your_secret_id",                 // 腾讯�?SecretId
    "token": "your_secret_key",             // 腾讯�?SecretKey
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],          // IPv4 域名
    "ipv6": ["ipv6.ddns.newfuture.cc"],     // IPv6 域名
    "endpoint": "https://teo.tencentcloudapi.com" // API端点
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范�?选项                       | 默认�?   | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标�?  | 字符�?        | `edgeone`                          | �?       | 服务商参�?|
| id      | 认证 ID      | 字符�?        | 腾讯�?SecretId                    | �?       | 服务商参�?|
| token   | 认证密钥     | 字符�?        | 腾讯�?SecretKey                   | �?       | 服务商参�?|
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | �?       | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | �?       | 公用配置   |
| endpoint| API 端点      | URL            | [参考下方](#endpoint)              | `https://teo.tencentcloudapi.com` | 服务商参�?|
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | �?       | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符�?   | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符�?   | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | �?       | 公用配置   |

> **参数类型说明**�? 
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参�? 
> - **服务商参�?*：当前服务商支持,值与当前服务商相�?
>
> EdgeOne �?TTL 实际的缓存策略由 EdgeOne 平台管理�?

### endpoint

腾讯�?EdgeOne 支持国内和国际版API端点，可根据区域和账号类型选择�?

#### 国内�?

- **默认（推荐）**：`https://teo.tencentcloudapi.com`

#### 国际�?

- **国际�?*：`https://teo.intl.tencentcloudapi.com`

> **注意**：请根据您的腾讯云账号类型选择对应的端点。国内账号使用国内版端点，国际账号使用国际版端点。如果不确定，建议使用默认的国内版端点�?

## 故障排除

### 调试模式

启用调试日志查看详细信息�?

```sh
ddns -c config.json --debug
```

### 常见问题

- **认证失败**：检�?SecretId �?SecretKey 是否正确，确认账号权�?
- **站点未找�?*：确保域名已添加�?EdgeOne 站点，域名状态正�?
- **加速域名不存在**：确认域名已�?EdgeOne 中配置为加速域�?
- **权限不足**：确保账号具�?EdgeOne 的管理权�?

## 支持与资�?

- [腾讯�?EdgeOne 产品文档](https://cloud.tencent.com/document/product/1552)
- [EdgeOne API 文档](https://cloud.tencent.com/document/api/1552)
- [EdgeOne 控制台](https://console.cloud.tencent.com/edgeone)
- [腾讯云技术支持](https://cloud.tencent.com/document/product/282)

> **注意**：EdgeOne 主要用于边缘加速场景，如需传统 DNS 解析服务，建议使�?[腾讯�?DNS](./tencentcloud.md)�?
