# DNSPod 国际版 配置指南

> 中国版（dnspod.cn）请参阅 [DNSPod 中国版配置指南](dnspod.md)

## 概述

DNSPod 国际版（dnspod.com）为中国大陆以外地区提供 DNS 服务，使用与 DNSPod 中国版相同的 API 接口。本 DDNS 项目支持 dnspod_com Provider，配置参数与 [DNSPod 中国版](dnspod.md) 完全一致，唯一区别在于可选线路名称。

## 认证方式

### 1. API Token（推荐）

国际版使用与中国版相同的 API Token 认证方式，获取步骤：

1. 登录 [DNSPod 国际版控制台](https://www.dnspod.com/)
2. 进入“用户中心”→“API Token”或访问：[https://www.dnspod.com/account/token/token](https://www.dnspod.com/account/token/token)
3. 点击“创建 Token”，填写描述，选择域名管理权限，完成创建
4. 复制页面中显示的 **ID**（数字）和 **Token**（字符串），Token 仅展示一次，请妥善保存

```json
{
  "dns": "dnspod_com",
  "id": "123456",
  "token": "abcdef1234567890abcdef1234567890"
}
```

- `id`：API Token ID
- `token`：API Token 密钥
- `dns`：固定为 `"dnspod_com"`

## 配置参数

有关 `id`、`token`、`dns`、`index4`、`index6`、`ipv4`、`ipv6`、`ttl` 等参数，请参阅 DNSPod 中国版配置指南：[dnspod.md](./dnspod.md)

## 支持的线路名称

国际版 `line` 参数使用英文标识：

| 线路名称 | 描述             |
|----------|------------------|
| default  | 默认公共线路     |
| telecom  | 电信线路         |
| unicom   | 联通线路         |
| mobile   | 移动线路         |
| oversea  | 海外线路         |

示例：

```json
{
  "id": "123456",
  "token": "abcdef1234567890abcdef1234567890abcdef12",
  "dns": "dnspod_com",
  "index4": ["public"],
  "index6": ["public"],
  "ipv4": ["home.example.com"],
  "ipv6": ["home.example.com", "nas.example.com"],
  "line": "oversea",
  "ttl": 600
}
```

## 支持与资源

- [DNSPod 国际版 API 文档](https://www.dnspod.com/docs/)
- [DNSPod 中国版 配置指南](./dnspod.md)
