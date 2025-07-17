# 阿里�?DNS (AliDNS)  配置指南

## 概述

阿里�?DNS（AliDNS）是阿里云提供的权威 DNS 解析服务，支持动�?DNS 记录的创建与更新。本 DDNS 项目通过 AccessKey ID �?AccessKey Secret 进行 API 认证�?

官网链接�?

- 官方网站�?https://www.aliyun.com/product/dns>
- 服务商控制台�?https://dns.console.aliyun.com/>

## 认证信息

### AccessKey 认证

使用阿里�?AccessKey ID �?AccessKey Secret 进行认证�?

#### 获取认证信息

1. 登录 [阿里云控制台](https://ecs.console.aliyun.com/)
2. 访问 [AccessKey管理](https://usercenter.console.aliyun.com/#/manage/ak)
3. 点击"创建AccessKey"按钮
4. 复制生成�?**AccessKey ID** �?**AccessKey Secret**，请妥善保存
5. 确保账号具有云解�?`AliyunDNSFullAccess`)的操作权�?

```json
{
    "dns": "alidns",
    "id": "AccessKey_ID",     // 阿里�?AccessKey ID
    "token": "AccessKey_Secret" // 阿里�?AccessKey Secret
}
```

## 权限要求

确保使用的阿里云账号具有以下权限�?

- **AliyunDNSFullAccess**：云解析 DNS 完全访问权限（推荐）
- **AliyunDNSReadOnlyAccess + 自定义写权限**：精细化权限控制

可以�?[RAM访问控制](https://ram.console.aliyun.com/policies) 中查看和配置权限�?

## 完整配置示例

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "alidns",                    // 当前服务�?
    "id": "your_access_key_id",              // AccessKey ID
    "token": "your_access_key_secret",              // AccessKey Secret
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 域名
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 域名
    "endpoint": "https://alidns.aliyuncs.com",   // API端点
    "line": "default",                       // 解析线路
    "ttl": 600                                 // DNS记录TTL（秒�?
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范�?选项                       | 默认�?   | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标�?  | 字符�?        | `alidns`                           | �?       | 服务商参�?|
| id      | 认证 ID      | 字符�?        | 阿里�?AccessKey ID                 | �?       | 服务商参�?|
| token   | 认证密钥     | 字符�?        | 阿里�?AccessKey Secret             | �?       | 服务商参�?|
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | �?       | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | �?       | 公用配置   |
| endpoint| API 端点      | URL            | [参考下方](#endpoint)              | `https://alidns.aliyuncs.com` | 服务商参�?|
| line    | 解析线路      | 字符�?        | [参考下方](#line)                   | `default`        | 服务商参�?|
| ttl     | TTL 时间      | 整数（秒�?    | [参考下方](#ttl)                    | �?       | 服务商参�?|
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | �?       | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符�?   | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符�?   | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | �?       | 公用配置   |

> **参数类型说明**�? 
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数参�? 
> - **服务商参�?*：前服务商支�?值与当前服务商相�?
> **注意**：`ttl` �?`line` 不同套餐支持的值可能不同�?

### endpoint

阿里�?DNS 支持多个区域端点，可根据区域和网络环境选择最优节点：

#### 国内节点

- **默认（推荐）**：`https://alidns.aliyuncs.com`
- **华东1（杭州）**：`https://alidns.cn-hangzhou.aliyuncs.com`
- **华东2（上海）**：`https://alidns.cn-shanghai.aliyuncs.com`
- **华北1（青岛）**：`https://alidns.cn-qingdao.aliyuncs.com`
- **华北2（北京）**：`https://alidns.cn-beijing.aliyuncs.com`
- **华北3（张家口�?*：`https://alidns.cn-zhangjiakou.aliyuncs.com`
- **华南1（深圳）**：`https://alidns.cn-shenzhen.aliyuncs.com`
- **西南1（成都）**：`https://alidns.cn-chengdu.aliyuncs.com`

#### 海外节点

- **亚太东南1（新加坡�?*：`https://alidns.ap-southeast-1.aliyuncs.com`
- **亚太东南2（悉尼）**：`https://alidns.ap-southeast-2.aliyuncs.com`
- **亚太东南3（吉隆坡�?*：`https://alidns.ap-southeast-3.aliyuncs.com`
- **亚太南部1（孟买）**：`https://alidns.ap-south-1.aliyuncs.com`
- **亚太东北1（东京）**：`https://alidns.ap-northeast-1.aliyuncs.com`
- **美国东部1（弗吉尼亚）**：`https://alidns.us-east-1.aliyuncs.com`
- **美国西部1（硅谷）**：`https://alidns.us-west-1.aliyuncs.com`
- **欧洲中部1（法兰克福）**：`https://alidns.eu-central-1.aliyuncs.com`
- **欧洲西部1（伦敦）**：`https://alidns.eu-west-1.aliyuncs.com`

> **注意**：建议使用默认端�?`https://alidns.aliyuncs.com`，阿里云会自动路由到最优节点。只有在特殊网络环境下才需要指定特定区域端点�?

### ttl

`ttl` 参数指定 DNS 记录的生存时间（TTL），单位为秒。阿里云支持�?TTL 范围�?1 �?86400 秒（�?1 天）。如果不设置，则使用默认值�?

| 套餐类型     | 支持�?TTL 范围（秒�?|
| ------------ | :-------------------: |
| 免费�?      |    600 - 86400        |
| 个人�?      |    600 - 86400        |
| 企业标准�?  |     60 - 86400        |
| 企业旗舰�?  |      1 - 86400        |

> 参考：[阿里�?DNS TTL 说明](https://help.aliyun.com/zh/dns/ttl-definition)

### line

`line` 参数指定 DNS 解析线路，阿里云支持的线路：

| 线路标识         | 说明         |
| :-------------- | :----------- |
| default         | 默认         |
| telecom         | 中国电信     |
| unicom          | 中国联�?    |
| mobile          | 中国移动     |
| edu             | 中国教育�?  |
| aliyun          | 阿里�?      |
| oversea         | 境外         |
| internal        | 中国地区     |

> 更多线路参考：[阿里�?DNS 解析线路枚举](https://help.aliyun.com/zh/dns/resolve-line-enumeration/)

## 故障排除

### 调试模式

启用调试日志查看详细信息�?

```sh
ddns -c config.json --debug
```

### 常见问题

- **InvalidAccessKeyId.NotFound**：AccessKey 不存�?
- **SignatureDoesNotMatch**：签名错误，检�?AccessKey Secret
- **DomainNotExists**：域名未添加到阿里云 DNS
- **Throttling.User**：请求过于频繁，降低 QPS,(个人版：20 QPS，企业版�?0 QPS)

## 支持与资�?

- [阿里云DNS产品文档](https://help.aliyun.com/product/29697.html)
- [阿里云DNS API文档](https://help.aliyun.com/document_detail/29739.html)
- [阿里云DNS控制台](https://dns.console.aliyun.com/)
- [阿里云技术支持](https://selfservice.console.aliyun.com/ticket)

> **建议**：使�?RAM 子账号并定期轮换 AccessKey，提升账号安全性�?
