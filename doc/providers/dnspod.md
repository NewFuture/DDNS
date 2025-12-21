# DNSPod 中国版 配置指南

## 概述

DNSPod (dnspod.cn) 是腾讯云旗下的权威 DNS 解析服务，在中国大陆地区广泛使用，支持动态 DNS 记录的创建与更新。本 DDNS 项目支持多种认证方式连接 DNSPod 进行动态 DNS 记录管理。

官网链接：

- 官方网站：<https://www.dnspod.cn/>
- 服务商控制台：<https://console.dnspod.cn/>

## 认证信息

### 1. API Token 认证（推荐）

API Token 方式更安全，是 DNSPod 推荐的集成方法。

#### 获取认证信息

1. 登录 [DNSPod 控制台](https://console.dnspod.cn/)
2. 进入"用户中心" > "API 密钥"或访问 <https://console.dnspod.cn/account/token/token>
3. 点击"创建密钥"，填写描述，选择域名管理权限，完成创建
4. 复制 **ID**（数字）和 **Token**（字符串），密钥只显示一次，请妥善保存

```jsonc
{
    "dns": "dnspod",
    "id": "123456",               // DNSPod API Token ID
    "token": "YOUR_DNSPOD_TOKEN"  // DNSPod API Token 密钥
}
```

### 2. 邮箱密码认证（不推荐）

使用 DNSPod 账号邮箱和密码，**安全性较低**，仅建议特殊场景使用。

```jsonc
{
    "dns": "dnspod",
    "id": "your-email@example.com",  // DNSPod 账号邮箱
    "token": "your-account-password" // DNSPod 账号密码
}
```

### 3. 腾讯云 AccessKey 方式

对于使用腾讯云 AccessKey 的用户，请参考 [腾讯云 DNSPod 配置指南](tencentcloud.md)。

## 完整配置示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "dnspod",                    // 当前服务商
    "id": "123456",                     // DNSPod API Token ID
    "token": "abcdef1234567890abcdef1234567890", // DNSPod API Token 密钥
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 域名
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 域名
    "line": "默认",                          // 解析线路
    "ttl": 600                              // DNS记录TTL（秒）
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `dnspod`                           | 无        | 服务商参数 |
| id      | 认证 ID      | 字符串         | DNSPod API Token ID 或邮箱         | 无        | 服务商参数 |
| token   | 认证密钥     | 字符串         | DNSPod API Token 密钥或密码        | 无        | 服务商参数 |
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| line    | 解析线路      | 字符串         | [参考下方](#line)                   | `默认`    | 服务商参数 |
| ttl     | TTL 时间      | 整数（秒）     | [参考下方](#ttl)                    | `600`     | 服务商参数 |
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数  
> - **服务商参数**：当前服务商支持,值与当前服务商相关
> **注意**：`ttl` 和 `line` 不同套餐支持的值可能不同。

### ttl

`ttl` 参数指定 DNS 记录的生存时间（TTL），单位为秒。DNSPod 支持的 TTL 范围为 1 到 604800 秒（即 7 天）。如果不设置，则使用默认值。

| 套餐类型 | 支持的 TTL 范围（秒） |
| :------ | :------------------- |
| 免费版   | 600 ~ 604800          |
| 专业版   | 60 ~ 604800           |
| 企业版   | 1 ~ 604800            |
| 尊享版   | 1 ~ 604800            |

> 参考：[DNSPod TTL 说明](https://docs.dnspod.cn/dns/help-ttl/)

### line

`line` 参数指定 DNS 解析线路，DNSPod 支持的线路：

| 线路标识         | 说明         |
| :-------------- | :----------- |
| 默认            | 默认         |
| 电信            | 中国电信     |
| 联通            | 中国联通     |
| 移动            | 中国移动     |
| 教育网          | 中国教育网   |
| 搜索引擎        | 搜索引擎     |
| 境外            | 境外         |

> 更多线路参考：[DNSPod 解析线路说明](https://docs.dnspod.cn/dns/dns-record-line)

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### 常见问题

- **认证失败**：检查 API Token 或邮箱/密码是否正确，确认有域名管理权限
- **域名未找到**：确保域名已添加到 DNSPod 账号，配置拼写无误，域名处于活跃状态
- **记录创建失败**：检查子域名是否有冲突记录，TTL 设置合理，确认有修改权限
- **请求频率限制**：DNSPod 有 API 调用频率限制，降低请求频率

## 支持与资源

- [DNSPod 产品文档](https://docs.dnspod.cn/)
- [DNSPod API 参考](https://docs.dnspod.cn/api/)
- [DNSPod 控制台](https://console.dnspod.cn/)
- [腾讯云 DNSPod (AccessKey 方式)](./tencentcloud.md)

> **建议**：推荐使用 API Token 方式，提升安全性与管理便捷性，避免使用邮箱密码方式。
