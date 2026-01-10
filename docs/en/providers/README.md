# DNS Provider 配置指南

本目录包含各个DNS服务商的详细配置指南。DDNS支持多个主流DNS服务商，每个服务商都有其特定的配置要求和API特性。

## 🚀 快速导航

| Provider | 服务商 | 配置文档 | 英文文档 | 特点 |
|----------|--------|----------|----------|------|
| `alidns` | [阿里云DNS](https://dns.console.aliyun.com/) | [alidns 中文文档](alidns.md) | [alidns English Doc](alidns.en.md) | 阿里云生态集成 |
| `aliesa` | [阿里云ESA](https://esa.console.aliyun.com/) | [aliesa 中文文档](aliesa.md) | [aliesa English Doc](aliesa.en.md) | 阿里云边缘安全加速 |
| `callback` | 自定义API (Webhook) | [callback 中文文档](callback.md) | [callback English Doc](callback.en.md) | 自定义HTTP API |
| `cloudflare` | [Cloudflare](https://www.cloudflare.com/) | [cloudflare 中文文档](cloudflare.md) | [cloudflare English Doc](cloudflare.en.md) | 全球CDN和DNS服务 |
| `debug` | 调试Provider | [debug 中文文档](debug.md) | [debug English Doc](debug.en.md) | 仅打印IP地址，用于调试|
| `dnscom`(51dns) | [51DNS](https://www.51dns.com/) | [51dns 中文文档](51dns.md) | [51dns English Doc](51dns.en.md) | ⚠️ 等待验证  |
| `dnspod_com` | [DNSPod Global](https://www.dnspod.com/) | [dnspod_com 中文文档](dnspod_com.md) | [dnspod_com English Doc](dnspod_com.en.md) | ⚠️ 等待验证  |
| `dnspod` | [DNSPod 中国版](https://www.dnspod.cn/) | [dnspod 中文文档](dnspod.md) | [dnspod English Doc](dnspod.en.md) | 国内最大DNS服务商|
| `he` | [HE.net](https://dns.he.net/) | [he 中文文档](he.md) | [he English Doc](he.en.md) | ⚠️ 等待验证，不支持自动创建记录 |
| `huaweidns` | [华为云 DNS](https://www.huaweicloud.com/product/dns.html) | [huaweidns 中文文档](huaweidns.md) | [huaweidns English Doc](huaweidns.en.md) | ⚠️ 等待验证 |
| `namesilo` | [NameSilo](https://www.namesilo.com/) | [namesilo 中文文档](namesilo.md) | [namesilo English Doc](namesilo.en.md) | ⚠️ 等待验证 |
| `noip` | [No-IP](https://www.noip.com/) | [noip 中文文档](noip.md) | [noip English Doc](noip.en.md) | 不支持自动创建记录 |
| `tencentcloud` | [腾讯云DNSPod](https://cloud.tencent.com/product/dns) | [tencentcloud 中文文档](tencentcloud.md) | [tencentcloud English Doc](tencentcloud.en.md) | 腾讯云DNSPod服务 |
| `edgeone` | [腾讯云EdgeOne](https://cloud.tencent.com/product/teo) | [edgeone 中文文档](edgeone.md) | [edgeone English Doc](edgeone.en.md) | 腾讯云边缘安全加速平台（加速域名） |
| `edgeone_dns` | [腾讯云EdgeOne DNS](https://cloud.tencent.com/product/teo) | [edgeone_dns 中文文档](edgeone_dns.md) | [edgeone_dns English Doc](edgeone_dns.en.md) | 腾讯云EdgeOne DNS记录管理 |

> 添加新的Provider, [创建Issue,并按照模板填好链接](https://github.com/NewFuture/DDNS/issues/new?template=new-dns-provider.md)

### 支持自动创建记录

大部分provider支持自动创建不存在的DNS记录，但有例外：

- ⚠️ **he**: 不支持自动创建记录，需要手动在控制面板中预先创建
- ⚠️ **noip**: 不支持自动创建记录，需要手动在控制面板中预先创建

## 📝 配置示例

### 命令行配置

[cli 提供了命令行配置方式](../config/cli.md)，以下是一些常用的命令行示例：

```bash
# DNSPod中国版
ddns --dns dnspod --id 12345 --token your_token --ipv4 ddns.newfuture.cc

# 阿里云DNS
ddns --dns alidns --id your_access_key --token your_secret --ipv4 ddns.newfuture.cc

# Cloudflare (使用邮箱)
ddns --dns cloudflare --id user@example.com --token your_api_key --ipv4 ddns.newfuture.cc

# Cloudflare (使用Token)
ddns --dns cloudflare --token your_api_token --ipv4 ddns.newfuture.cc

# 腾讯云EdgeOne
ddns --dns edgeone --id your_secret_id --token your_secret_key --ipv4 ddns.newfuture.cc

# No-IP
ddns --dns noip --id your_username --token your_password --ipv4 ddns.newfuture.cc
```

### JSON配置文件

[JSON配置文件](../config/json.md)提供了更灵活的配置方式，以下是一些常用的JSON配置示例：

#### 单Provider格式

```jsonc
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "dns": "dnspod",
  "id": "12345",
  "token": "your_token_here",
  "ipv4": ["ddns.newfuture.cc", "*.newfuture.cc"],
  "index4": ["default"],
  "ttl": 600
}
```

#### 多Provider格式

```jsonc
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
  "ssl": "auto",
  "cache": true,
  "log": {"level": "INFO"},
  "providers": [
    {
      "provider": "cloudflare",
      "id": "user@example.com",
      "token": "cloudflare-token",
      "ipv4": ["cf.example.com"],
      "ttl": 300
    },
    {
      "provider": "dnspod", 
      "id": "12345",
      "token": "dnspod-token",
      "ipv4": ["dnspod.example.com"],
      "ttl": 600
    }
  ]
}
```

### 多配置文件方式

#### 命令行指定多个配置文件

```bash
# 使用多个独立的配置文件
ddns -c cloudflare.json -c dnspod.json -c alidns.json

# 使用环境变量指定多个配置文件
export DDNS_CONFIG="cloudflare.json,dnspod.json,alidns.json"
ddns
```

#### 多配置文件示例

**cloudflare.json**:

```json
{
  "dns": "cloudflare",
  "id": "user@example.com",
  "token": "your-cloudflare-token",
  "ipv4": ["cf.example.com"]
}
```

**dnspod.json**:

```json
{
  "dns": "dnspod",
  "id": "12345", 
  "token": "your-dnspod-token",
  "ipv4": ["dnspod.example.com"]
}
```

### 环境变量配置

[环境变量配置](../config/env.md)提供了另一种配置方式，以下是一些常用的环境变量示例：

```bash
export DDNS_DNS=dnspod
export DDNS_ID=12345
export DDNS_TOKEN=your_token_here
export DDNS_IPV4=ddns.newfuture.cc
export DDNS_INDEX4=default
ddns --debug
```

## 📚 相关文档

- [命令行配置](../config/cli.md) - 命令行参数详细说明
- [JSON配置](../config/json.md) - JSON配置文件格式说明  
- [环境变量配置](../config/env.md) - 环境变量配置方式
- [Provider开发指南](../dev/provider.md) - 如何开发新的provider
- [JSON Schema](../../schema/v4.0.json) - 配置文件验证架构

---

如有疑问或需要帮助，请查看[FAQ](../../README.md#FAQ) 或在 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 中提问。
