# DNS Provider Configuration Guide

This directory contains detailed configuration guides for various DNS providers. DDNS supports multiple mainstream DNS providers, each with specific configuration requirements and API characteristics.

## 🚀 Quick Navigation

| Provider | Service Provider | Chinese Doc | Configuration Doc | Features |
|----------|------------------|-------------|-------------------|----------|
| `alidns` | [Alibaba Cloud DNS](https://dns.console.aliyun.com/) | [alidns 中文文档](../../providers/alidns.md) | [alidns English Doc](alidns.md) | Alibaba Cloud ecosystem integration |
| `aliesa` | [Alibaba Cloud ESA](https://esa.console.aliyun.com/) | [aliesa 中文文档](../../providers/aliesa.md) | [aliesa English Doc](aliesa.md) | Alibaba Cloud Edge Security Acceleration |
| `callback` | Custom API (Webhook) | [callback 中文文档](../../providers/callback.md) | [callback English Doc](callback.md) | Custom HTTP API |
| `cloudflare` | [Cloudflare](https://www.cloudflare.com/) | [cloudflare 中文文档](../../providers/cloudflare.md) | [cloudflare English Doc](cloudflare.md) | Global CDN and DNS service |
| `cloudns` | [ClouDNS](https://www.cloudns.net/) | [cloudns 中文文档](../../providers/cloudns.md) | [cloudns English Doc](cloudns.md) | Global DNS hosting service |
| `debug` | Debug Provider | [debug 中文文档](../../providers/debug.md) | [debug English Doc](debug.md) | IP address printing for debugging |
| `dnscom` | [DNS.COM](https://www.dns.com/) | [51dns 中文文档](../../providers/51dns.md) | [51DNS English Doc](51dns.md) | ⚠️ Pending verification |
| `dnspod_com` | [DNSPod Global](https://www.dnspod.com/) | [dnspod_com 中文文档](../../providers/dnspod_com.md) | [dnspod_com English Doc](dnspod_com.md) | ⚠️ Pending verification |
| `dnspod` | [DNSPod China](https://www.dnspod.cn/) | [dnspod 中文文档](../../providers/dnspod.md) | [dnspod English Doc](dnspod.md) | Largest DNS provider in China |
| `he` | [HE.net](https://dns.he.net/) | [he 中文文档](../../providers/he.md) | [he English Doc](he.md) | ⚠️ Pending verification, no auto-record creation |
| `huaweidns` | [Huawei Cloud DNS](https://www.huaweicloud.com/product/dns.html) | [huaweidns 中文文档](../../providers/huaweidns.md) | [huaweidns English Doc](huaweidns.md) | ⚠️ Pending verification |
| `noip` | [No-IP](https://www.noip.com/) | [noip 中文文档](../../providers/noip.md) | [noip English Doc](noip.md) | Popular dynamic DNS service |
| `tencentcloud` | [Tencent Cloud DNSPod](https://cloud.tencent.com/product/dns) | [tencentcloud 中文文档](../../providers/tencentcloud.md) | [tencentcloud English Doc](tencentcloud.md) | Tencent Cloud DNSPod service |
| `edgeone` | [Tencent Cloud EdgeOne](https://edgeone.ai) | [edgeone 中文文档](../../providers/edgeone.md) | [edgeone English Doc](edgeone.md) | Tencent Cloud Edge Security Platform (Acceleration Domains) |
| `edgeone_dns` | [Tencent Cloud EdgeOne DNS](https://edgeone.ai) | [edgeone_dns 中文文档](../../providers/edgeone_dns.md) | [edgeone_dns English Doc](edgeone_dns.md) | Tencent Cloud EdgeOne DNS Records |

> To add a new provider, [create an issue and fill in the template](https://github.com/NewFuture/DDNS/issues/new?template=new-dns-provider.md)

### Automatic Record Creation Support

Most providers support automatic creation of non-existent DNS records, with exceptions:

- ⚠️**he**: Does not support automatic record creation, records must be manually created in the control panel
- ⚠️**noip**: Does not support automatic record creation, records must be manually created in the control panel

## 📝 Configuration Examples

### Command Line Configuration

[CLI provides command line configuration](../config/cli.md), here are some common command line examples:

```bash
# DNSPod China
ddns --dns dnspod --id 12345 --token your_token --ipv4 ddns.newfuture.cc

# Alibaba Cloud DNS
ddns --dns alidns --id your_access_key --token your_secret --ipv4 ddns.newfuture.cc

# Cloudflare (using email)
ddns --dns cloudflare --id user@example.com --token your_api_key --ipv4 ddns.newfuture.cc

# Cloudflare (using Token)
ddns --dns cloudflare --token your_api_token --ipv4 ddns.newfuture.cc

# No-IP
ddns --dns noip --id your_username --token your_password --ipv4 ddns.newfuture.cc
```

### JSON Configuration File

[JSON configuration file](../config/json.md) provides a more flexible configuration method, here are some common JSON configuration examples:

#### Traditional Single-Provider Format

```jsonc
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
  "dns": "dnspod",
  "id": "12345",
  "token": "your_token_here",
  "ipv4": ["ddns.newfuture.cc", "*.newfuture.cc"],
  "index4": ["default"],
  "ttl": 600
}
```

#### Multi-Provider Format

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

### Multiple Configuration Files Method

#### Command Line Specification

```bash
# Use multiple independent configuration files
ddns -c cloudflare.json -c dnspod.json -c alidns.json

# Use environment variable to specify multiple configuration files
export DDNS_CONFIG="cloudflare.json,dnspod.json,alidns.json"
ddns
```

#### Multiple Configuration Files Example

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

### Environment Variable Configuration

[Environment variable configuration](../config/env.md) provides another configuration method, here are some common environment variable examples:

```bash
export DDNS_DNS=dnspod
export DDNS_ID=12345
export DDNS_TOKEN=your_token_here
export DDNS_IPV4=ddns.newfuture.cc
export DDNS_INDEX4=default
ddns --debug
```

## 📚 Related Documentation

- [Command Line Configuration](../config/cli.md) - Detailed command line parameter documentation
- [JSON Configuration](../config/json.md) - JSON configuration file format documentation
- [Environment Variable Configuration](../config/env.md) - Environment variable configuration method
- [Provider Development Guide](../dev/provider.md) - How to develop new providers
- [JSON Schema](../../schema/v4.1.json) - Configuration file validation schema

---

If you have questions or need help, please check the [FAQ](../../#FAQ) or ask in [GitHub Issues](https://github.com/NewFuture/DDNS/issues).
