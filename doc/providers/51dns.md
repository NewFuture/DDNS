# 51DNS(dns.com) 配置指南

## 概述

51DNS (DNSCOM)（原dns.com，现51dns.com）是中国知名的域名解析服务商，提供权威 DNS 解析服务，支持动态 DNS 记录的创建与更新。本 DDNS 项目通过 API Key 和 Secret Key 进行 API 认证。

> ⚠️ **注意**：51DNS(DNSCOM) Provider 目前处于**待验证**状态，缺少充分的真实环境测试。请通过 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 反馈。

官方网站：<https://www.51dns.com/>

## 认证信息

### API Key + Secret Key 认证

51DNS 使用 API Key 和 Secret Key 进行 API 认证，这是官方推荐的认证方式。

#### 获取认证信息

1. 登录 [51DNS/DNS.COM 控制台](https://www.51dns.com/)
2. 进入"API管理"页面
3. 点击"创建API密钥"
4. 记录生成的 **API Key** 和 **Secret Key**，请妥善保存

```jsonc
{
    "dns": "dnscom",
    "id": "your_api_key",      // 51DNS API Key
    "token": "your_secret_key" // 51DNS Secret Key
}
```

## 完整配置示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "dnscom",                    // 当前服务商
    "id": "your_api_key",               // 51DNS API Key
    "token": "your_secret_key",         // 51DNS Secret Key
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 域名
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 域名
    "line": "1",                            // 解析线路
    "ttl": 600                              // DNS记录TTL（秒）
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `dnscom`                           | 无        | 服务商参数 |
| id      | 认证 ID      | 字符串         | 51DNS API Key                      | 无        | 服务商参数 |
| token   | 认证密钥     | 字符串         | 51DNS Secret Key                   | 无        | 服务商参数 |
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| line    | 解析线路      | 字符串         | [参考下方](#line)                   | `1`       | 服务商参数 |
| ttl     | TTL 时间      | 整数（秒）     | [参考下方](#ttl)                    | `600`     | 服务商参数 |
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数参数  
> - **服务商参数**：前服务商支持,值与当前服务商相关
>
> **注意**：`ttl` 和 `line` 不同套餐支持的值可能不同。

### ttl

`ttl` 参数指定 DNS 记录的生存时间（TTL），单位为秒。51dns 支持的 TTL 范围为 60 到 86400 秒（即 1 天）。如果不设置，则使用默认值。

| 套餐类型     | 支持的 TTL 范围（秒） |
| :---------- | :-------------------: |
| 免费版       |     600 - 86400       |
| 专业版       |      60 - 86400       |
| 企业版       |      10 - 86400       |
| 旗舰版       |      1 - 86400       |

> **注意**：具体TTL范围请参考[51dns官方文档](https://www.51dns.com/service.html)

### line

`line` 参数指定 DNS 解析线路，51dns 支持的线路：

| 线路标识         | 说明         |
| :-------------- | :----------- |
| 1               | 默认         |
| 2               | 中国电信     |
| 3               | 中国联通     |
| 4               | 中国移动     |
| 5               | 海外         |
| 6               | 教育网       |

> 更多线路参考：参考文档 [官方文档 ViewID](https://www.51dns.com/document/api/index.html)

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### 常见问题

- **认证失败**：检查 API Key 和 Secret Key 是否正确，确认 API 密钥状态为启用
- **域名未找到**：确保域名已添加到 51dns 账号，配置拼写无误，域名处于活跃状态
- **记录创建失败**：检查子域名是否有冲突记录，TTL 设置合理，确认有修改权限
- **请求频率限制**：51dns 有 API 调用频率限制（每分钟最多100次），降低请求频率

### API 错误代码

| 错误代码 | 说明         | 解决方案       |
| :------ | :----------- | :------------- |
| 0       | 成功         | 操作成功       |
| 1       | 参数错误     | 检查请求参数   |
| 2       | 认证失败     | 检查API密钥    |
| 3       | 权限不足     | 检查API权限    |
| 4       | 记录不存在   | 检查域名和记录 |
| 5       | 域名不存在   | 检查域名配置   |

## 支持与资源

- [51dns 官网](https://www.51dns.com/)
- [51dns API 文档](https://www.51dns.com/document/api/index.html)
- [51dns 控制台](https://www.51dns.com/)

> ⚠️ **待验证状态**：51dns Provider 缺少充分的真实环境测试，建议在生产环境使用前进行充分测试。如遇问题请通过 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 反馈。
