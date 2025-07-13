# DNS Provider 配置指南

本目录包含各个DNS服务商的详细配置指南。DDNS支持多个主流DNS服务商，每个服务商都有其特定的配置要求和API特性。

## 🚀 快速导航

| Provider | 服务商 | 配置文档 | 英文文档 | 特点 |
|----------|--------|----------|----------|------|
| `alidns` | [阿里云 DNS](https://dns.console.aliyun.com/) | [alidns 中文文档](alidns.md) | [alidns English Doc](alidns.en.md) | 阿里云生态集成 |
| `aliesa` | [阿里云 ESA](https://esa.console.aliyun.com/) | [aliesa 中文文档](aliesa.md) | [aliesa English Doc](aliesa.en.md) | 阿里云边缘安全加速 |
| `callback` | 自定义API (Webhook) | [callback 中文文档](callback.md) | [callback English Doc](callback.en.md) | 自定义HTTP API |
| `cloudflare` | [Cloudflare](https://www.cloudflare.com/) | [cloudflare 中文文档](cloudflare.md) | [cloudflare English Doc](cloudflare.en.md) | 全球CDN和DNS服务 |
| `debug` | 调试Provider | [debug 中文文档](debug.md) | [debug English Doc](debug.en.md) | 仅打印IP地址，用于调试 |
| `dnscom`(51dns) | [51DNS](https://www.51dns.com/) | [dnscom 中文文档](dnscom.md) | [dnscom English Doc](dnscom.en.md) | ⚠️ 等待验证  |
| `dnspod_com` | [DNSPod Global](https://www.dnspod.com/) | [dnspod_com 中文文档](dnspod_com.md) | [dnspod_com English Doc](dnspod_com.en.md) | ⚠️ 等待验证  |
| `dnspod` | [DNSPod 中国版](https://www.dnspod.cn/) | [dnspod 中文文档](dnspod.md) | [dnspod English Doc](dnspod.en.md) | 国内最大DNS服务商 |
| `he` | [HE.net](https://dns.he.net/) | [he 中文文档](he.md) | [he English Doc](he.en.md) | ⚠️ 等待验证，不支持自动创建记录 |
| `huaweidns` | [华为云 DNS](https://www.huaweicloud.com/product/dns.html) | [huaweidns 中文文档](huaweidns.md) | [huaweidns English Doc](huaweidns.en.md) | ⚠️ 等待验证 |
| `namesilo` | [NameSilo](https://www.namesilo.com/) | [namesilo 中文文档](namesilo.md) | [namesilo English Doc](namesilo.en.md) | ⚠️ 等待验证 |
| `noip` | [No-IP](https://www.noip.com/) | [noip 中文文档](noip.md) | [noip English Doc](noip.en.md) | 不支持自动创建记录 |
| `tencentcloud` | [腾讯云 DNSPod](https://cloud.tencent.com/product/dns) | [tencentcloud 中文文档](tencentcloud.md) | [tencentcloud English Doc](tencentcloud.en.md) | 腾讯云DNSPod服务 |
| `edgeone` | [腾讯云 EdgeOne](https://edgeone.ai/) | [edgeone 中文文档](edgeone.md) | [edgeone English Doc](edgeone.en.md) | 腾讯云EdgeOne边缘计算DNS |

## ⚙️ 特殊配置说明

### 支持自动创建记录

大部分provider支持自动创建不存在的DNS记录，但有例外：

- ❌ **he**: 不支持自动创建记录，需要手动在控制面板中预先创建
- ❌ **noip**: 不支持自动创建记录，需要手动在控制面板中预先创建

<!-- ## 🔧 域名格式支持

### 标准格式

```text
subdomain.example.com
```

### 自定义分隔符格式

支持使用 `~` 或 `+` 分隔子域名和主域名：

```text
subdomain~example.com
subdomain+example.com
``` -->

## 📝 配置示例

### 命令行配置

```bash
# DNSPod中国版
ddns --dns dnspod --id 12345 --token your_token --ipv4 example.com

# 阿里云DNS
ddns --dns alidns --id your_access_key --token your_secret --ipv4 example.com

# Cloudflare (使用邮箱)
ddns --dns cloudflare --id user@example.com --token your_api_key --ipv4 example.com

# Cloudflare (使用Token)
ddns --dns cloudflare --token your_api_token --ipv4 example.com

# No-IP
ddns --dns noip --id your_username --token your_password --ipv4 example.com
```

### JSON配置文件

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "dns": "dnspod",
  "id": "12345",
  "token": "your_token_here",
  "ipv4": ["ddns.example.com", "*.example.com"],
  "index4": ["default"],
  "ttl": 600
}
```

### 环境变量配置

```bash
export DDNS_DNS=dnspod
export DDNS_ID=12345
export DDNS_TOKEN=your_token_here
export DDNS_IPV4=ddns.example.com
export DDNS_INDEX4=default
ddns --debug
```

## 📚 相关文档

- [命令行配置](../cli.md) - 命令行参数详细说明
- [JSON配置](../json.md) - JSON配置文件格式说明  
- [环境变量配置](../env.md) - 环境变量配置方式
- [Provider开发指南](../dev/provider.md) - 如何开发新的provider
- [JSON Schema](../../schema/v4.0.json) - 配置文件验证架构

---

如有疑问或需要帮助，请查看 [FAQ](../../README.md#FAQ) 或在 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 中提问。
