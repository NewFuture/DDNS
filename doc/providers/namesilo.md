# NameSilo DNS 配置指南

## 概述

NameSilo 是美国知名的域名注册商和 DNS 服务提供商，提供可靠的域名管理和 DNS 解析服务，支持动�?DNS 记录的创建与更新。本 DDNS 项目通过 API Key 进行认证�?

> ⚠️ **注意**：NameSilo Provider 目前处于**待验�?*状态，缺少充分的真实环境测试。请通过 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 反馈�?

官网链接�?

- 官方网站�?https://www.namesilo.com/>
- 服务商控制台�?https://www.namesilo.com/account_home.php>

## 认证信息

### API Key 认证

NameSilo 使用 API Key 进行身份验证，这是唯一的认证方式�?

#### 获取认证信息

1. 登录 [NameSilo 控制台](https://www.namesilo.com/account_home.php)
2. 进入「Account Options」→「API Manager」或访问 <https://www.namesilo.com/account/api-manager>
3. 生成新的 API Key

> **注意**：API Key 具有账户的完整权限，请确保妥善保管，不要泄露给他人�?

```json
{
    "dns": "namesilo",
    "token": "your_api_key_here" // NameSilo API Key, ID 不需�?
}
```

## 完整配置示例

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "namesilo",                  // 当前服务�?
    "token": "c40031261ee449dda629d2df14e9cb63", // NameSilo API Key
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 域名
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 域名
    "ttl": 3600                             // DNS记录TTL（秒�?
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范�?选项                       | 默认�?   | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标�?  | 字符�?        | `namesilo`                         | �?       | 服务商参�?|
| token   | 认证密钥     | 字符�?        | NameSilo API Key                   | �?       | 服务商参�?|
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | �?       | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | �?       | 公用配置   |
| ttl     | TTL 时间      | 整数（秒�?    | 300 ~ 2592000                | `7200`    | 服务商参�?|
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
> **注意**：NameSilo 不支�?`id` 参数，仅使用 `token` 进行认证�?
> **注意**：NameSilo 官方 API 端点�?`https://www.namesilo.com`，除非使用代理服务，否则不建议修改�?

## 故障排除

### 调试模式

启用调试日志查看详细信息�?

```sh
ddns -c config.json --debug
```

### 常见问题

- **认证失败**：检�?API Key 是否正确，确�?API Key 没有被禁用，验证账户状态是否正�?
- **域名未找�?*：确保域名已添加�?NameSilo 账户，配置拼写无误，域名处于活跃状�?
- **记录创建失败**：检查子域名格式是否正确，TTL 值在允许范围内（300-2592000秒），验证是否存在冲突记�?
- **请求频率限制**：NameSilo �?API 调用频率限制（建议每分钟不超�?60 次），降低请求频�?

### API 响应代码

| 响应代码 | 说明         | 解决方案           |
| :------ | :----------- | :----------------- |
| 300     | 成功         | 操作成功           |
| 110     | 域名不存�?  | 检查域名配�?      |
| 280     | 无效的域名格�?| 检查域名格�?      |
| 200     | 无效的API Key | 检查API密钥        |

## API 限制

- **请求频率**：建议每分钟不超�?60 次请�?
- **域名数量**：根据账户类型不同而限�?
- **记录数量**：每个域名最�?100 �?DNS 记录

## 支持与资�?

- [NameSilo 官网](https://www.namesilo.com/)
- [NameSilo API 文档](https://www.namesilo.com/api-reference)
- [NameSilo 控制台](https://www.namesilo.com/account_home.php)
- [NameSilo API Manager](https://www.namesilo.com/account/api-manager)

> ⚠️ **待验证状�?*：NameSilo Provider 缺少充分的真实环境测试，建议在生产环境使用前进行充分测试。如遇问题请通过 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 反馈�?
