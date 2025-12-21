# No-IP 配置指南

## 概述

No-IP 是流行的动态 DNS 服务提供商，支持标准的 DDNS 动态更新协议，采用 Basic Auth 认证，支持动态 DNS 记录的创建与更新。本 DDNS 项目支持通过用户名密码或 DDNS KEY 进行认证。

官网链接：

- 官方网站：<https://www.noip.com/>
- 服务商控制台：<https://www.noip.com/members/>

## 认证信息

### 1. DDNS KEY + ID 认证（推荐）

使用 DDNS ID 和 DDNS KEY 进行认证，更加安全。

#### 获取DDNS KEY

1. 登录 [No-IP 官网](https://www.noip.com/)
2. 进入 **Dynamic DNS** > **No-IP Hostnames**
3. 创建或编辑动态 DNS 主机名
4. 生成 DDNS KEY 用于 API 认证

```jsonc
{
    "dns": "noip",
    "id": "your_ddns_id",    // DDNS ID
    "token": "your_ddns_key" // DDNS KEY
}
```

### 2. 用户名密码认证

使用 No-IP 账户用户名和密码进行认证，这是最简单的认证方式。

#### 账号密码

1. 注册或登录 [No-IP 官网](https://www.noip.com/)
2. 使用注册的用户名和密码
3. 在控制面板中创建主机名（hostname）

```jsonc
{
    "dns": "noip",
    "id": "your_username",    // No-IP 用户名
    "token": "your_password"  // No-IP 密码
}
```

## 完整配置示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "noip",                      // 当前服务商
    "id": "myusername",                 // No-IP 用户名或 DDNS ID
    "token": "mypassword",              // No-IP 密码或 DDNS KEY
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["all.ddnskey.com"],           // IPv4 域名
    "ipv6": ["all.ddnskey.com"], // IPv6 域名
    "endpoint": "https://dynupdate.no-ip.com" // API端点
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `noip`                             | 无        | 服务商参数 |
| id      | 认证 ID      | 字符串         | No-IP 用户名或 DDNS ID             | 无        | 服务商参数 |
| token   | 认证密钥     | 字符串         | No-IP 密码或 DDNS KEY              | 无        | 服务商参数 |
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | `all.ddnskey.com`        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | `all.ddnskey.com`        | 公用配置   |
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数  
> - **服务商参数**：前服务商支持,值与当前服务商相关

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### 常见问题

- **认证失败**：检查用户名和密码是否正确，确认账户没有被禁用
- **主机名未找到**：确保主机名已在 No-IP 控制面板中创建，配置拼写无误
- **更新失败**：检查主机名状态是否正常，确认账户权限足够
- **请求频率限制**：No-IP 建议更新间隔不少于 5 分钟，避免频繁更新

### No-IP 响应代码

| 响应代码        | 说明             | 解决方案           |
| :------------- | :--------------- | :----------------- |
| `good <ip>`    | 更新成功         | 操作成功           |
| `nochg <ip>`   | IP地址无变化     | 操作成功           |
| `nohost`       | 主机名不存在     | 检查主机名设置     |
| `badauth`      | 认证失败         | 检查用户名密码     |
| `badagent`     | 客户端被禁用     | 联系No-IP支持     |
| `!donator`     | 需要付费账户功能 | 升级账户类型       |
| `abuse`        | 账户被封禁或滥用 | 联系No-IP支持     |

## API 限制

- **更新频率**：建议间隔不少于 5 分钟
- **免费账户**：30 天内需至少一次登录确认
- **主机名数量**：免费账户限制 3 个主机名

## 支持与资源

- [No-IP 官网](https://www.noip.com/)
- [No-IP API 文档](https://www.noip.com/integrate/request)
- [No-IP 控制面板](https://www.noip.com/members/)
- [No-IP 技术支持](https://www.noip.com/support)

> **建议**：推荐使用 DDNS KEY 认证方式以提高安全性，定期检查主机名状态确保服务正常运行。
