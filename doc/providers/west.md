# 西部数码 (West.cn) 配置指南

## 概述

西部数码 (West.cn) 是国内知名的域名注册商和DNS解析服务提供商，提供稳定可靠的DNS解析服务。本 DDNS 项目支持西部数码的动态域名解析接口，可实现域名IP地址的自动更新。

官网链接：

- 官方网站：<https://www.west.cn/>
- 管理控制台：<https://www.west.cn/web/mi/>
- API文档：<https://www.west.cn/CustomerCenter/doc/domain_v2.html>

## 认证信息

西部数码支持两种认证方式，您可以根据实际需要选择：

### 1. 域名级认证（推荐，适合单个域名）

域名级认证方式更安全，适合个人用户或单个域名的DDNS更新。

#### 获取认证信息

1. 登录 [西部数码管理控制台](https://www.west.cn/web/mi/)
2. 进入"域名管理"，找到需要解析的域名
3. 点击域名进入详情页
4. 在域名详情页找到"API Key"或"域名密钥"选项
5. 复制域名密钥（apidomainkey）

#### 配置示例

```json
{
    "dns": "west",
    "id": "example.com",           // 您的主域名
    "token": "YOUR_API_DOMAIN_KEY" // 域名密钥
}
```

### 2. 用户级认证（适合代理商，支持多域名）

用户级认证方式适合代理商或需要管理多个域名的用户。

#### 获取认证信息

1. 登录 [西部数码管理控制台](https://www.west.cn/web/mi/)
2. 进入"用户中心" > "API接口"或"API配置"
3. 获取您的用户名和 API Key
4. 确保账号已开通 API 权限（通常代理商账号默认开通）

#### 配置示例

```json
{
    "dns": "west",
    "id": "your_username",    // 西部数码用户名
    "token": "YOUR_API_KEY"   // 用户级API密钥
}
```

## 完整配置示例

### 域名级认证配置

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "west",
    "id": "example.com",
    "token": "your_api_domain_key_here",
    "index4": ["url:http://api.ipify.cn", "public"],
    "index6": "public",
    "ipv4": ["ddns.example.com", "www.example.com"],
    "ipv6": ["ipv6.example.com"],
    "ttl": 600
}
```

### 用户级认证配置

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "west",
    "id": "your_username",
    "token": "your_api_key_here",
    "index4": ["default"],
    "ipv4": ["ddns.example.com", "www.example.com"],
    "ttl": 600
}
```

## 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `west`, `west_cn`, `westcn`        | 无        | 服务商参数 |
| id      | 认证 ID      | 字符串         | 域名或用户名                        | 无        | 服务商参数 |
| token   | 认证密钥     | 字符串         | 域名密钥或用户API密钥               | 无        | 服务商参数 |
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ttl     | TTL 时间      | 整数（秒）     | 不支持通过DDNS API设置              | 无        | 服务商参数 |
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数  
> - **服务商参数**：当前服务商支持,值与当前服务商相关

### 支持的记录类型

西部数码 DDNS API 支持以下记录类型：

- **A 记录**：IPv4 地址解析
- **AAAA 记录**：IPv6 地址解析

> **注意**：西部数码的 DDNS API 不支持 CNAME、MX 等其他记录类型。如需管理其他类型的记录，请使用西部数码管理控制台手动配置。

### TTL 说明

西部数码的 DDNS API 不支持通过接口设置 TTL 值。如需修改 TTL，请登录西部数码管理控制台手动设置。

## 使用说明

### 认证方式自动识别

DDNS 工具会根据 `id` 参数自动识别认证方式：

- **域名级认证**：当 `id` 包含 `.`（点）或 `@` 符号时，自动识别为域名级认证
- **用户级认证**：当 `id` 为简单用户名（不包含 `.` 或 `@`）时，自动识别为用户级认证

### API 行为说明

西部数码的 DDNS API 使用 `dnsrec.update` 接口，该接口的行为特点：

1. **自动创建或更新**：如果记录不存在，会自动创建；如果记录已存在，会更新记录值
2. **记录替换**：更新时会删除同名的旧记录，然后创建新记录
3. **单次操作**：每次调用只更新一条记录
4. **编码要求**：API 使用 GB2312/GBK 编码

### 最佳实践

1. **首次使用**：建议先在西部数码控制台手动创建一条DNS记录，然后通过 DDNS 工具进行更新
2. **更新频率**：避免频繁调用 API，建议更新间隔不少于 5 分钟
3. **域名级认证**：对于个人用户和单个域名，推荐使用域名级认证，安全性更高
4. **用户级认证**：对于需要管理多个域名的代理商用户，使用用户级认证更方便

## 故障排查

### 常见问题

#### 1. API 返回错误："权限不足"或"认证失败"

**可能原因**：
- 域名密钥或 API 密钥不正确
- 账号未开通 API 权限（用户级认证）
- 域名不在当前账号下

**解决方法**：
- 检查 `id` 和 `token` 配置是否正确
- 确认域名是否在当前账号下管理
- 代理商用户需确认已开通 API 权限

#### 2. API 返回错误："域名格式错误"

**可能原因**：
- `id` 配置的域名格式不正确
- 主域名与实际域名不匹配

**解决方法**：
- 域名级认证时，`id` 应填写主域名（如 `example.com`），而非完整域名（如 `www.example.com`）
- 检查域名拼写是否正确

#### 3. 记录更新成功但不生效

**可能原因**：
- DNS 缓存未刷新
- DNS 服务器同步延迟

**解决方法**：
- 等待 DNS 缓存过期（通常几分钟到几小时）
- 使用 `nslookup` 或 `dig` 命令检查 DNS 解析结果
- 尝试清除本地 DNS 缓存

#### 4. 不支持的记录类型

**可能原因**：
- DDNS API 仅支持 A 和 AAAA 记录

**解决方法**：
- 确认 `record_type` 参数为 `A` 或 `AAAA`
- 其他类型记录需要在控制台手动配置

### 调试建议

1. **查看日志**：运行时添加 `--log-level DEBUG` 参数查看详细日志
2. **测试 API**：可以使用 curl 命令直接测试 API 是否正常工作
3. **联系客服**：如遇到无法解决的问题，可联系西部数码技术支持

## 技术支持

如需更多帮助，请访问：

- 西部数码帮助中心：<https://www.west.cn/docs/>
- 西部数码 API 文档：<https://www.west.cn/CustomerCenter/doc/domain_v2.html>
- 技术支持邮箱：58851879@west.cn

## 相关链接

- [DDNS JSON 配置文档](../config/json.md)
- [DDNS CLI 配置文档](../config/cli.md)
- [环境变量配置文档](../config/env.md)
- [Provider 列表](README.md)
