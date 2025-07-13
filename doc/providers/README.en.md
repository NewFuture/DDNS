# DNS Provider Configuration Guide

This directory contains detailed configuration guides for various DNS service providers. DDNS supports multiple mainstream DNS providers, each with specific configuration requirements and API features.

## 🚀 Quick Navigation

### Providers with Detailed Configuration Documentation

| Provider | Service Provider | Chinese Doc | Configuration Doc | Features |
|----------|------------------|-------------|-------------------|----------|
| `alidns` | [Alibaba Cloud DNS](https://dns.console.aliyun.com/) | [alidns 中文文档](alidns.md) | [alidns English Doc](alidns.en.md) | Alibaba Cloud ecosystem integration |
| `aliesa` | [Alibaba Cloud ESA](https://esa.console.aliyun.com/) | [aliesa 中文文档](aliesa.md) | [aliesa English Doc](aliesa.en.md) | Alibaba Cloud Edge Security Acceleration |
| `callback` | Custom API (Webhook) | [callback 中文文档](callback.md) | [callback English Doc](callback.en.md) | Custom HTTP API |
| `cloudflare` | [Cloudflare](https://www.cloudflare.com/) | [cloudflare 中文文档](cloudflare.md) | [cloudflare English Doc](cloudflare.en.md) | Global CDN and DNS service |
| `debug` | Debug Provider | [debug 中文文档](debug.md) | [debug English Doc](debug.en.md) | IP address printing for debugging |
| `dnscom` | [DNS.COM](https://www.dns.com/) | [dnscom 中文文档](dnscom.md) | [dnscom English Doc](dnscom.en.md) | ⚠️ Pending verification |
| `dnspod_com` | [DNSPod Global](https://www.dnspod.com/) | [dnspod_com 中文文档](dnspod_com.md) | [dnspod_com English Doc](dnspod_com.en.md) | ⚠️ Pending verification |
| `dnspod` | [DNSPod China](https://www.dnspod.cn/) | [dnspod 中文文档](dnspod.md) | [dnspod English Doc](dnspod.en.md) | Largest DNS provider in China |
| `he` | [HE.net](https://dns.he.net/) | [he 中文文档](he.md) | [he English Doc](he.en.md) | ⚠️ Pending verification, no auto-record creation |
| `huaweidns` | [Huawei Cloud DNS](https://www.huaweicloud.com/product/dns.html) | [huaweidns 中文文档](huaweidns.md) | [huaweidns English Doc](huaweidns.en.md) | ⚠️ Pending verification |
| `noip` | [No-IP](https://www.noip.com/) | [noip 中文文档](noip.md) | [noip English Doc](noip.en.md) | Popular dynamic DNS service |
| `tencentcloud` | [Tencent Cloud DNSPod](https://cloud.tencent.com/product/dns) | [tencentcloud 中文文档](tencentcloud.md) | [tencentcloud English Doc](tencentcloud.en.md) | Tencent Cloud DNSPod service |
| `edgeone` | [Tencent Cloud EdgeOne](https://edgeone.ai/) | [edgeone 中文文档](edgeone.md) | [edgeone English Doc](edgeone.en.md) | Tencent Cloud EdgeOne Edge Computing DNS |

## ⚙️ Special Configuration Notes

### Auto-Record Creation Support

Most providers support automatically creating non-existent DNS records, with exceptions:

- ❌ **he**: Does not support auto-record creation, records must be created manually in the control panel
- ❌ **noip**: Does not support auto-record creation, records must be created manually in the control panel

<!-- ## 🔧 Domain Name Format Support

### Standard Format

```text
subdomain.example.com
```

### Custom Separator Format

Supports using `~` or `+` to separate subdomain and main domain:

```text
subdomain~example.com
subdomain+example.com
``` -->

## 📝 Configuration Examples

### Command Line Configuration

```bash
# DNSPod China
ddns --dns dnspod --id 12345 --token your_token --ipv4 example.com

# Alibaba Cloud DNS
ddns --dns alidns --id your_access_key --token your_secret --ipv4 example.com

# Cloudflare (using email)
ddns --dns cloudflare --id user@example.com --token your_api_key --ipv4 example.com

# Cloudflare (using token)
ddns --dns cloudflare --token your_api_token --ipv4 example.com

# No-IP
ddns --dns noip --id your_username --token your_password --ipv4 example.com
```

### JSON Configuration File

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

### Environment Variable Configuration

```bash
export DDNS_DNS=dnspod
export DDNS_ID=12345
export DDNS_TOKEN=your_token_here
export DDNS_IPV4=ddns.example.com
export DDNS_INDEX4=default
ddns --debug
```

## 📚 Related Documentation

- [Command Line Configuration](../cli.en.md) - Detailed command line parameter descriptions
- [JSON Configuration](../json.en.md) - JSON configuration file format description
- [Environment Variable Configuration](../env.en.md) - Environment variable configuration method
- [Provider Development Guide](../dev/provider.en.md) - How to develop new providers
- [JSON Schema](../../schema/v4.0.json) - Configuration file validation schema

---

If you have questions or need help, please check the [FAQ](../../README.md#FAQ) or ask in [GitHub Issues](https://github.com/NewFuture/DDNS/issues).
