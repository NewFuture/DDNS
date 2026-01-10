# 华为云 DNS 配置指南

## 概述

华为云 DNS 是华为云提供的权威 DNS 解析服务，具有高可用性、高扩展性和高安全性，支持动态 DNS 记录的创建与更新。本 DDNS 项目通过 Access Key ID 和 Secret Access Key 进行 API 认证。

> ⚠️ **注意**：华为云 DNS Provider 目前处于**待验证**状态，缺少充分的真实环境测试。请通过 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 反馈。

官网链接：

- 官方网站：<https://www.huaweicloud.com/product/dns.html>
- 服务商控制台：<https://console.huaweicloud.com/dns/>

## 认证信息

### Access Key 认证

使用华为云 Access Key ID 和 Secret Access Key 进行认证。

#### 获取认证信息

1. 登录 [华为云控制台](https://www.huaweicloud.com/)
2. 进入 **我的凭证** > **访问密钥**
3. 点击"新增访问密钥"按钮
4. 复制生成的 **Access Key ID** 和 **Secret Access Key**，请妥善保存
5. 确保账号具有云解析 DNS 的操作权限

```jsonc
{
    "dns": "huaweidns",
    "id": "your_access_key_id",     // 华为云 Access Key ID
    "token": "your_secret_access_key" // 华为云 Secret Access Key
}
```

## 权限要求

确保使用的华为云账号具有以下权限：

- **DNS Administrator**：云解析 DNS 完全管理权限（推荐）
- **DNS ReadOnlyAccess + 自定义写权限**：精细化权限控制

可以在 [统一身份认证服务](https://console.huaweicloud.com/iam/) 中查看和配置权限。

## 完整配置示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "huaweidns",                 // 当前服务商
    "id": "your_access_key_id",         // 华为云 Access Key ID
    "token": "your_secret_access_key",  // 华为云 Secret Access Key
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 域名
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 域名
    "endpoint": "https://dns.myhuaweicloud.com", // API端点
    "line": "default",                      // 解析线路
    "ttl": 600                              // DNS记录TTL（秒）
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `huaweidns`                        | 无        | 服务商参数 |
| id      | 认证 ID      | 字符串         | 华为云 Access Key ID               | 无        | 服务商参数 |
| token   | 认证密钥     | 字符串         | 华为云 Secret Access Key           | 无        | 服务商参数 |
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| endpoint| API 端点      | URL            | [参考下方](#endpoint)              | `https://dns.myhuaweicloud.com` | 服务商参数 |
| line    | 解析线路      | 字符串         | [参考下方](#line)                   | `default` | 服务商参数 |
| ttl     | TTL 时间      | 整数（秒）     | 1~2147483647                   | `300`     | 服务商参数 |
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数  
> - **服务商参数**：当前服务商支持,值与当前服务商相关
>
> **注意**：`ttl` 和 `line` 不同套餐支持的值可能不同。

### endpoint

华为云 DNS 支持多个区域端点，可根据区域和网络环境选择最优节点：

#### 国内节点

- **全球服务（推荐）**：`https://dns.myhuaweicloud.com`
- **华北-北京四**：`https://dns.cn-north-4.myhuaweicloud.com`
- **华东-上海一**：`https://dns.cn-east-3.myhuaweicloud.com`
- **华南-广州**：`https://dns.cn-south-1.myhuaweicloud.com`
- **华北-乌兰察布一**：`https://dns.cn-north-9.myhuaweicloud.com`
- **西南-贵阳一**：`https://dns.cn-southwest-2.myhuaweicloud.com`

#### 海外节点

- **亚太-新加坡**：`https://dns.ap-southeast-3.myhuaweicloud.com`
- **亚太-香港**：`https://dns.ap-southeast-1.myhuaweicloud.com`
- **亚太-曼谷**：`https://dns.ap-southeast-2.myhuaweicloud.com`
- **非洲-约翰内斯堡**：`https://dns.af-south-1.myhuaweicloud.com`
- **拉美-圣地亚哥**：`https://dns.la-south-2.myhuaweicloud.com`
- **拉美-墨西哥城一**：`https://dns.la-north-2.myhuaweicloud.com`
- **拉美-圣保罗一**：`https://dns.sa-brazil-1.myhuaweicloud.com`

> **注意**：建议使用默认端点 `https://dns.myhuaweicloud.com`，华为云会自动路由到最优节点。只有在特殊网络环境下才需要指定特定区域端点。

### line

`line` 参数指定 DNS 解析线路，华为云支持的线路：[配置自定义线路解析](https://support.huaweicloud.com/usermanual-dns/dns_usermanual_0018.html)。

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### 常见问题

- **认证失败**：检查 Access Key ID 和 Secret Access Key 是否正确，确认密钥没有被删除或禁用
- **域名未找到**：确保域名已添加到华为云 DNS 解析，配置拼写无误，域名处于活跃状态
- **记录创建失败**：检查子域名是否有冲突记录，TTL 设置合理，确认有修改权限
- **请求频率限制**：华为云 API 有调用频率限制，降低请求频率

### 常见错误代码

| 错误代码        | 说明           | 解决方案           |
| :------------- | :------------- | :----------------- |
| APIGW.0301     | 认证失败       | 检查访问密钥       |
| DNS.0101       | 域名不存在     | 检查域名配置       |
| DNS.0102       | 记录集不存在   | 检查记录设置       |
| DNS.0103       | 记录集已存在   | 检查冲突记录       |
| DNS.0203       | 请求频率过高   | 降低请求频率       |

## 支持与资源

- [华为云 DNS 产品文档](https://support.huaweicloud.com/dns/)
- [华为云 DNS API 文档](https://support.huaweicloud.com/api-dns/)
- [华为云控制台](https://console.huaweicloud.com/dns/)
- [华为云技术支持](https://support.huaweicloud.com/)

> ⚠️ **待验证状态**：华为云 DNS Provider 缺少充分的真实环境测试，建议在生产环境使用前进行充分测试。如遇问题请通过 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 反馈。
