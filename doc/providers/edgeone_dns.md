# 腾讯云 EdgeOne DNS 配置指南

## 概述

腾讯云 EdgeOne DNS 提供商用于管理非加速域名的 DNS 记录。当您的域名完全托管给 EdgeOne 后，除了管理加速域名外，还可以使用此提供商来管理普通的 DNS 记录。

> **与 EdgeOne 加速域名的区别**：
>
> - **EdgeOne (加速域名)**: 用于管理边缘加速域名的源站 IP 地址，主要用于 CDN 加速场景。使用 `edgeone`、`edgeone_acc`、`neo_acc` 或 `neo` 作为 dns 参数值。
> - **EdgeOne DNS (非加速域名)**: 用于管理普通 DNS 记录，类似于传统 DNS 解析服务。使用 `edgeone_dns` 或 `edgeone_noacc` 作为 dns 参数值。

官网链接：

- 官方网站：<https://cloud.tencent.com/product/teo>
- EdgeOne 国际版：<https://edgeone.ai>
- 服务商控制台：<https://console.cloud.tencent.com/edgeone>

## 认证信息

### SecretId/SecretKey 认证

使用腾讯云 SecretId 和 SecretKey 进行认证，与腾讯云 DNS 使用相同的认证方式。

> 与[腾讯云 DNS](tencentcloud.md) 相同，EdgeOne 使用 SecretId 和 SecretKey 进行认证。但是权限要求不同，需要确保账号具有 EdgeOne 的操作权限。

#### 获取认证信息

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
2. 访问 [API密钥管理](https://console.cloud.tencent.com/cam/capi)
3. 点击"新建密钥"按钮
4. 复制生成的 **SecretId** 和 **SecretKey**，请妥善保存
5. 确保账号具有 EdgeOne 的操作权限

```jsonc
{
    "dns": "edgeone_dns",      // 使用 EdgeOne DNS 提供商
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

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "edgeone_dns",                   // EdgeOne DNS 提供商（非加速域名）
    "id": "your_secret_id",                 // 腾讯云 SecretId
    "token": "your_secret_key",             // 腾讯云 SecretKey
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],          // IPv4 域名
    "ipv6": ["ipv6.ddns.newfuture.cc"],     // IPv6 域名
    "endpoint": "https://teo.tencentcloudapi.com" // API端点
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `edgeone_dns`, `edgeone_noacc`     | 无        | 服务商参数 |
| id      | 认证 ID      | 字符串         | 腾讯云 SecretId                    | 无        | 服务商参数 |
| token   | 认证密钥     | 字符串         | 腾讯云 SecretKey                   | 无        | 服务商参数 |
| index4  | IPv4 来源     | 数组           | <a>参考配置</a>  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | <a>参考配置</a>   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| endpoint| API 端点      | URL            | [参考下方](#endpoint)              | `https://teo.tencentcloudapi.com` | 服务商参数 |
| proxy   | 代理设置      | 数组           | <a>参考配置</a>        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | <a>参考配置</a>             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数  
> - **服务商参数**：当前服务商支持,值与当前服务商相关

### endpoint

腾讯云 EdgeOne 支持国内和国际版API端点，可根据区域和账号类型选择：

#### 国内版

- **默认（推荐）**：`https://teo.tencentcloudapi.com`

#### 国际版

- **国际版**：`https://teo.intl.tencentcloudapi.com`

> **注意**：请根据您的腾讯云账号类型选择对应的端点。国内账号使用国内版端点，国际账号使用国际版端点。如果不确定，建议使用默认的国内版端点。

## DNS 提供商对比

| 提供商标识 | 用途 | API 操作 | 适用场景 |
| :--------: | :--- | :------- | :------- |
| `edgeone`、`edgeone_acc`、`neo_acc`、`neo` | 加速域名 | `CreateAccelerationDomain`, `ModifyAccelerationDomain`, `DescribeAccelerationDomains` | CDN 边缘加速，更新源站 IP |
| `edgeone_dns`、`edgeone_noacc` | DNS 记录 | `CreateDnsRecord`, `ModifyDnsRecords`, `DescribeDnsRecords` | 普通 DNS 解析服务 |

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### 常见问题

- **认证失败**：检查 SecretId 和 SecretKey 是否正确，确认账号权限
- **站点未找到**：确保域名已添加到 EdgeOne 站点，域名状态正常
- **DNS 记录不存在**：确认域名已在 EdgeOne 中正确托管
- **权限不足**：确保账号具有 EdgeOne 的管理权限

## 支持与资源

- [腾讯云 EdgeOne 产品文档](https://cloud.tencent.com/document/product/1552)
- [EdgeOne API 文档](https://cloud.tencent.com/document/api/1552)
- [EdgeOne DNS 记录 API](https://cloud.tencent.com/document/api/1552/86336)
- [EdgeOne 控制台](https://console.cloud.tencent.com/edgeone)
- [腾讯云技术支持](https://cloud.tencent.com/document/product/282)

> **提示**：如需使用 EdgeOne 的边缘加速功能，请使用 [EdgeOne 加速域名提供商](./edgeone.md)。如需传统 DNS 解析服务且不使用 EdgeOne，建议使用 [腾讯云 DNS](./tencentcloud.md)。
