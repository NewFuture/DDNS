# 西部数码 配置指南

## 概述

西部数码 (west.cn) 是中国知名的域名服务商，提供域名注册、DNS解析等服务。本 DDNS 项目支持西部数码的动态 DNS 记录管理。

官网链接：

- 官方网站：<https://www.west.cn/>
- API文档：<https://console-docs.apipost.cn/preview/bf57a993975b67e0/7b363d9b8808faa2>

> **注意**：三五互联 (35.cn) 使用相同的 API，可以使用 `35` 或 `35cn` 作为服务商标识。

## 认证信息

西部数码支持两种认证方式：

### 1. 域名认证方式（推荐）

使用域名管理密码进行认证，只需要 `token`（apidomainkey）。

#### 获取认证信息

1. 登录 [西部数码会员中心](https://www.west.cn/manager/)
2. 进入"域名管理" > 选择域名 > "管理密码"
3. 复制 **APIkey**（32位 MD5 值），这是域名管理密码的 MD5 哈希值

```json
{
    "dns": "west",
    "token": "ec4c66e34561428b2e9ad65048f9bsed"  // 域名 APIkey
}
```

### 2. 账号认证方式

使用会员账号和 API 密码进行认证。

#### 获取认证信息

1. 登录 [西部数码会员中心](https://www.west.cn/manager/)
2. 进入"账号管理" > "API接口设置"
3. 设置 API 密码
4. `id` 填写您的会员账号
5. `token` 填写 API 密码的 32 位 MD5 值

```json
{
    "dns": "west",
    "id": "your_username",                      // 会员账号
    "token": "md5_of_your_api_password"         // API密码的MD5值
}
```

## 完整配置示例

### 域名认证方式

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "west",
    "token": "ec4c66e34561428b2e9ad65048f9bsed",
    "index4": ["url:http://api.ipify.cn", "public"],
    "index6": "public",
    "ipv4": ["ddns.example.com"],
    "ipv6": ["ipv6.example.com"],
    "ttl": 900
}
```

### 账号认证方式

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "west",
    "id": "your_username",
    "token": "md5_of_your_api_password",
    "index4": ["url:http://api.ipify.cn", "public"],
    "index6": "public",
    "ipv4": ["ddns.example.com"],
    "ipv6": ["ipv6.example.com"],
    "ttl": 900
}
```

### 三五互联配置

三五互联使用相同的 API，只需更改 `dns` 参数或使用 `endpoint` 参数：

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "35",
    "token": "your_apidomainkey",
    "endpoint": "https://api.35.cn/API/v2/domain/dns/",
    "ipv4": ["ddns.example.com"]
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `west`, `west_cn`, `35`, `35cn`    | 无        | 服务商参数 |
| id      | 会员账号     | 字符串         | 账号认证时必填                      | 无        | 服务商参数 |
| token   | 认证密钥     | 字符串         | apidomainkey 或 MD5(API密码)       | 无        | 服务商参数 |
| endpoint | API地址     | 字符串         | 自定义API端点                       | 西部数码  | 服务商参数 |
| index4  | IPv4 来源    | 数组           | [参考配置](../config/json.md#ipv4-ipv6) | `default` | 公用配置   |
| index6  | IPv6 来源    | 数组           | [参考配置](../config/json.md#ipv4-ipv6) | `default` | 公用配置   |
| ipv4    | IPv4 域名    | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名    | 数组           | 域名列表                           | 无        | 公用配置   |
| line    | 解析线路     | 字符串         | [参考下方](#line)                   | 默认      | 服务商参数 |
| ttl     | TTL 时间     | 整数（秒）     | 60 ~ 86400                         | `900`     | 服务商参数 |
| proxy   | 代理设置     | 数组           | [参考配置](../config/json.md#proxy) | 无        | 公用网络   |
| ssl     | SSL 验证方式 | 布尔/字符串    | `"auto"`、`true`、`false`          | `auto`    | 公用网络   |
| cache   | 缓存设置     | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置     | 对象           | [参考配置](../config/json.md#log)  | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数  
> - **服务商参数**：当前服务商支持，值与当前服务商相关

### line

`line` 参数指定 DNS 解析线路，西部数码支持的线路：

| 线路标识   | 线路代码 | 说明         |
| :-------- | :------- | :----------- |
| 默认      | （空）   | 默认线路     |
| 电信      | LTEL     | 中国电信     |
| 联通      | LCNC     | 中国联通     |
| 移动      | LMOB     | 中国移动     |
| 教育网    | LEDU     | 中国教育网   |
| 搜索引擎  | LSEO     | 搜索引擎     |
| 境外      | LFOR     | 境外访问     |

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### 常见问题

- **认证失败**：检查 APIkey 或账号密码是否正确，确认 token 是 32 位 MD5 值
- **域名未找到**：确保域名已在西部数码账号下，配置拼写无误
- **记录创建失败**：检查子域名是否有冲突记录，TTL 设置是否合理
- **请求频率限制**：降低请求频率

## 支持与资源

- [西部数码官网](https://www.west.cn/)
- [西部数码会员中心](https://www.west.cn/manager/)
- [API 文档](https://console-docs.apipost.cn/preview/bf57a993975b67e0/7b363d9b8808faa2)
- [三五互联官网](https://www.35.cn/)

> **建议**：推荐使用域名认证方式（apidomainkey），配置更简单且更安全。
