# 阿里云边缘安全加速 (ESA) 配置指南

## 概述

阿里云边缘安全加速（ESA）是阿里云提供的边缘安全加速服务，支持 DNS 记录的动态管理。本 DDNS 项目通过 AccessKey ID 和 AccessKey Secret 更新 ESA DNS 记录。

官网链接：

- 官方网站：<https://www.aliyun.com/product/esa>
- 服务商控制台：<https://esa.console.aliyun.com/>

## 认证信息

### AccessKey 认证

使用阿里云 AccessKey ID 和 AccessKey Secret 进行认证。

#### 获取认证信息

1. 登录 [阿里云控制台](https://ecs.console.aliyun.com/)
2. 访问 [AccessKey管理](https://usercenter.console.aliyun.com/#/manage/ak)
3. 点击"创建AccessKey"按钮
4. 复制生成的 **AccessKey ID** 和 **AccessKey Secret**，请妥善保存
5. 确保账号具有边缘安全加速 (`AliyunESAFullAccess`) 的操作权限

```jsonc
{
    "dns": "aliesa",
    "id": "your_access_key_id",      // AccessKey ID
    "token": "your_access_key_secret" // AccessKey Secret
}
```

## 权限要求

确保使用的阿里云账号具有以下权限：

- **AliyunESAFullAccess**：边缘安全加速完全访问权限（推荐）
- **ESA站点查询权限 + ESA DNS记录管理权限**：精细化权限控制
  - `esa:ListSites`：查询站点列表
  - `esa:ListRecords`：查询 DNS 记录
  - `esa:CreateRecord`：创建 DNS 记录
  - `esa:UpdateRecord`：更新 DNS 记录

可以在 [RAM控制台](https://ram.console.aliyun.com/policies) 中查看和配置权限。

## 完整配置示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "aliesa",                    // 当前服务商
    "id": "your_access_key_id",              // AccessKey ID
    "token": "your_access_key_secret",              // AccessKey Secret
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 域名
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 域名
    "endpoint": "https://esa.cn-hangzhou.aliyuncs.com",   // API端点
    "ttl": 600                                 // DNS记录TTL（秒）
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `aliesa`                           | 无        | 服务商参数 |
| id      | 认证 ID      | 字符串         | 阿里云 AccessKey ID                 | 无        | 服务商参数 |
| token   | 认证密钥     | 字符串         | 阿里云 AccessKey Secret             | 无        | 服务商参数 |
| index4  | IPv4 来源     | 数组           | [参考](../config/json.md#ipv4-ipv6)       | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考](../config/json.md#ipv4-ipv6)       | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| endpoint| API 端点      | URL            | [参考下方](#endpoint)                           | `https://esa.cn-hangzhou.aliyuncs.com`         | 服务商参数 |
| ttl     | TTL 时间      | 整数（秒）     | 30~86400                           | 1(自动)        | 服务商参数 |
| proxy   | 代理设置      | 数组           | [参考](../config/json.md#proxy)           | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `auto`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考](../config/json.md#log)             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数参数  
> - **服务商参数**：前服务商支持,值与当前服务商相关

### endpoint

阿里云 ESA 支持多个区域端点，可根据区域和网络环境选择最优节点：

#### 国内节点

- **华东（杭州）**：`https://esa.cn-hangzhou.aliyuncs.com`（默认）

#### 国际节点

- **亚太东南1（新加坡）**：`https://esa.ap-southeast-1.aliyuncs.com`

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### 常见问题

#### "Site not found for domain"

- 检查域名是否已添加到ESA服务
- 确认域名格式正确（不包含协议前缀）
- 验证AccessKey权限

#### "Failed to create/update record"

- 检查DNS记录类型是否支持
- 确认记录值格式正确
- 验证TTL值在允许范围内

#### "API调用失败"

- 检查AccessKey ID和Secret是否正确
- 确认网络连接正常
- 查看详细错误日志

## 支持与资源

- [阿里云ESA产品文档](https://help.aliyun.com/product/122312.html)
- [阿里云ESA API文档](https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-overview)
- [阿里云ESA控制台](https://esa.console.aliyun.com/)
- [阿里云技术支持](https://selfservice.console.aliyun.com/ticket)

> **建议**：使用 RAM 子账号并定期轮换 AccessKey，提升账号安全性。
