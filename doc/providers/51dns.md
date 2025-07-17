# 51DNS(dns.com) 配置指南

## 概述

51DNS (DNSCOM)（原dns.com，现51dns.com）是中国知名的域名解析服务商，提供权�?DNS 解析服务，支持动�?DNS 记录的创建与更新。本 DDNS 项目通过 API Key �?Secret Key 进行 API 认证�?

> ⚠️ **注意**�?1DNS(DNSCOM) Provider 目前处于**待验�?*状态，缺少充分的真实环境测试。请通过 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 反馈�?

官方网站�?https://www.51dns.com/>

## 认证信息

### API Key + Secret Key 认证

51DNS 使用 API Key �?Secret Key 进行 API 认证，这是官方推荐的认证方式�?

#### 获取认证信息

1. 登录 [51DNS/DNS.COM 控制台](https://www.51dns.com/)
2. 进入"API管理"页面
3. 点击"创建API密钥"
4. 记录生成�?**API Key** �?**Secret Key**，请妥善保存

```json
{
    "dns": "dnscom",
    "id": "your_api_key",      // 51DNS API Key
    "token": "your_secret_key" // 51DNS Secret Key
}
```

## 完整配置示例

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "dnscom",                    // 当前服务�?
    "id": "your_api_key",               // 51DNS API Key
    "token": "your_secret_key",         // 51DNS Secret Key
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 域名
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 域名
    "line": "1",                            // 解析线路
    "ttl": 600                              // DNS记录TTL（秒�?
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范�?选项                       | 默认�?   | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标�?  | 字符�?        | `dnscom`                           | �?       | 服务商参�?|
| id      | 认证 ID      | 字符�?        | 51DNS API Key                      | �?       | 服务商参�?|
| token   | 认证密钥     | 字符�?        | 51DNS Secret Key                   | �?       | 服务商参�?|
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | �?       | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | �?       | 公用配置   |
| line    | 解析线路      | 字符�?        | [参考下方](#line)                   | `1`       | 服务商参�?|
| ttl     | TTL 时间      | 整数（秒�?    | [参考下方](#ttl)                    | `600`     | 服务商参�?|
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | �?       | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符�?   | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符�?   | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | �?       | 公用配置   |

> **参数类型说明**�? 
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数参�? 
> - **服务商参�?*：前服务商支�?值与当前服务商相�?
>
> **注意**：`ttl` �?`line` 不同套餐支持的值可能不同�?

### ttl

`ttl` 参数指定 DNS 记录的生存时间（TTL），单位为秒�?1dns 支持�?TTL 范围�?60 �?86400 秒（�?1 天）。如果不设置，则使用默认值�?

| 套餐类型     | 支持�?TTL 范围（秒�?|
| :---------- | :-------------------: |
| 免费�?      |     600 - 86400       |
| 专业�?      |      60 - 86400       |
| 企业�?      |      10 - 86400       |
| 旗舰�?      |      1 - 86400       |

> **注意**：具体TTL范围请参考[51dns官方文档](https://www.51dns.com/service.html)

### line

`line` 参数指定 DNS 解析线路�?1dns 支持的线路：

| 线路标识         | 说明         |
| :-------------- | :----------- |
| 1               | 默认         |
| 2               | 中国电信     |
| 3               | 中国联�?    |
| 4               | 中国移动     |
| 5               | 海外         |
| 6               | 教育�?      |

> 更多线路参考：参考文�?[官方文档 ViewID](https://www.51dns.com/document/api/index.html)

## 故障排除

### 调试模式

启用调试日志查看详细信息�?

```sh
ddns -c config.json --debug
```

### 常见问题

- **认证失败**：检�?API Key �?Secret Key 是否正确，确�?API 密钥状态为启用
- **域名未找�?*：确保域名已添加�?51dns 账号，配置拼写无误，域名处于活跃状�?
- **记录创建失败**：检查子域名是否有冲突记录，TTL 设置合理，确认有修改权限
- **请求频率限制**�?1dns �?API 调用频率限制（每分钟最�?00次），降低请求频�?

### API 错误代码

| 错误代码 | 说明         | 解决方案       |
| :------ | :----------- | :------------- |
| 0       | 成功         | 操作成功       |
| 1       | 参数错误     | 检查请求参�?  |
| 2       | 认证失败     | 检查API密钥    |
| 3       | 权限不足     | 检查API权限    |
| 4       | 记录不存�?  | 检查域名和记录 |
| 5       | 域名不存�?  | 检查域名配�?  |

## 支持与资�?

- [51dns 官网](https://www.51dns.com/)
- [51dns API 文档](https://www.51dns.com/document/api/index.html)
- [51dns 控制台](https://www.51dns.com/)

> ⚠️ **待验证状�?*�?1dns Provider 缺少充分的真实环境测试，建议在生产环境使用前进行充分测试。如遇问题请通过 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 反馈�?
