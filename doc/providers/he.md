# HE.net (Hurricane Electric) 配置指南

## 概述

Hurricane Electric (HE.net) 是知名的网络服务商，提供免费�?DNS 托管服务，支持动�?DNS 记录更新。本 DDNS 项目通过 HE.net 的动�?DNS 密码进行认证�?

> ⚠️ **注意**：HE.net Provider 目前处于**待验�?*状态，缺少充分的真实环境测试。请通过 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 反馈�?

**重要限制**：HE.net **不支持自动创建记�?*，必须先�?HE.net 控制面板中手动创�?DNS 记录�?

官网链接�?

- 官方网站�?https://he.net/>
- 服务商控制台�?https://dns.he.net/>

## 认证信息

### 动�?DNS 密码认证

HE.net 使用专门的动�?DNS 密码进行认证，不使用账户登录密码�?

需要提前创建DNS记录和开启DNS

1. �?[HE.net DNS 管理面板](https://dns.he.net)中选择要管理的域名
2. **创建DNS记录**：手动创�?A (ipv4)�?AAAA (ipv6)记录
3. **启用DDNS**：为记录启用动�?DNS 功能
4. **获取密码**：点击旁边的 `Generate a DDNS key` �?`Enable entry for DDNS`

```json
{
    "dns": "he",
    "token": "your_ddns_key" // HE.net 动�?DNS 密码,不需要ID
}
```

## 完整配置示例

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "he",                        // 当前服务�?
    "token": "your_ddns_key",      // HE.net 动�?DNS 密码
    "index4": ["public", 0],       // IPv4地址来源, 与A记录值对�?
    "ipv4": "ddns.newfuture.cc"    // IPv4 域名, 与A记录对应
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范�?选项                       | 默认�?   | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标�?  | 字符�?        | `he`                               | �?       | 服务商参�?|
| token   | 认证密钥     | 字符�?        | HE.net DDNS 密码               | �?       | 服务商参�?|
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | �?       | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | �?       | 公用配置   |
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
> **注意**：HE.net 不支�?`id` 参数，仅使用 `token` (DDNS Key)进行认证; ttl固定�?00s�?

## 使用限制

- �?**不支持自动创建记�?*：必须先�?HE.net 控制面板中手动创�?DNS 记录
- ⚠️ **仅支持更�?*：只能更新现有记录的 IP 地址，不能创建新记录
- 🔑 **专用密码**：每个记录都有独立的 DDNS 密码

## 故障排除

### 调试模式

启用调试日志查看详细信息�?

```sh
ddns -c config.json --debug
```

### 常见问题

- **认证失败**：检查动�?DNS 密码是否正确，确认记录已启用 DDNS 功能
- **域名未找�?*：确保记录已�?HE.net 控制面板中手动创建，域名拼写无误
- **记录更新失败**：检查记录是否已启用动�?DNS，确认密码对应正确的记录
- **请求频率限制**：HE.net 建议更新间隔不少�?5 分钟，避免频繁更�?

### HE.net 响应代码

| 响应代码        | 说明             | 解决方案           |
| :------------- | :--------------- | :----------------- |
| `good <ip>`    | 更新成功         | 操作成功           |
| `nochg <ip>`   | IP地址无变�?    | 操作成功           |
| `nohost`       | 主机名不存在     | 检查记录和DDNS设置 |
| `badauth`      | 认证失败         | 检查动态DNS密码    |
| `badagent`     | 客户端被禁用     | 联系HE.net支持    |
| `abuse`        | 更新过于频繁     | 增加更新间隔       |

## 支持与资�?

- [HE.net 官网](https://he.net/)
- [HE.net DNS 管理](https://dns.he.net/)
- [HE.net DDNS 文档](https://dns.he.net/docs.html)
- [HE.net 技术支持](https://he.net/contact.html)

> ⚠️ **待验证状�?*：HE.net Provider 缺少充分的真实环境测试，建议在生产环境使用前进行充分测试。如遇问题请通过 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 反馈�?
