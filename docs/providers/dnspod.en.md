# DNSPod China Configuration Guide

> For International DNSPod, see [DNSPod Global Configuration Guide](dnspod_com.en.md).

## Overview

DNSPod (dnspod.cn) is an authoritative DNS resolution service under Tencent Cloud, widely used in mainland China, supporting dynamic DNS record creation and updates. This DDNS project supports multiple authentication methods to connect to DNSPod for dynamic DNS record management.

Official Links:

- Official Website: <https://www.dnspod.cn/>
- Service Console: <https://console.dnspod.cn/>

## Authentication Information

### 1. API Token Authentication (Recommended)

API Token method is more secure and is the recommended integration method by DNSPod.

#### Obtaining API Token

1. Login to [DNSPod Console](https://console.dnspod.cn/)
2. Go to "User Center" > "API Key" or visit <https://console.dnspod.cn/account/token/token>
3. Click "Create Key", fill in description, select domain management permissions, and complete creation
4. Copy the **ID** (numeric) and **Token** (string). The key is only displayed once, please save it securely

```jsonc
{
    "dns": "dnspod",
    "id": "123456",            // DNSPod API Token ID
    "token": "Your-API-TOKEN"  // DNSPod API Token Secret
}
```

### 2. Email Password Authentication (Not Recommended)

Uses DNSPod account email and password. Lower security, only recommended for special scenarios.

```jsonc
{
    "dns": "dnspod",
    "id": "your-email@example.com",  // DNSPod account email
    "token": "your-account-password" // DNSPod account password
}
```

### 3. Tencent Cloud AccessKey Method

For users using Tencent Cloud AccessKey, please refer to [Tencent Cloud DNSPod Configuration Guide](tencentcloud.en.md).

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "dnspod",                    // Current provider
    "id": "123456",                     // DNSPod API Token ID
    "token": "Your-API-TOKEN",           // DNSPod API Token
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 domains
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 domains
    "line": "默认",                          // Resolution line
    "ttl": 600                              // DNS record TTL (seconds)
}
```

### Parameter Description

| Parameter | Description | Type | Range/Options | Default | Parameter Type |
| :-------: | :---------- | :--- | :------------ | :------ | :------------- |
| dns | Provider identifier | String | `dnspod` | None | Provider Parameter |
| id | Authentication ID | String | DNSPod API Token ID or email | None | Provider Parameter |
| token | Authentication key | String | DNSPod API Token secret or password | None | Provider Parameter |
| index4 | IPv4 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| index6 | IPv6 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| ipv4 | IPv4 domains | Array | Domain list | None | Common Config |
| ipv6 | IPv6 domains | Array | Domain list | None | Common Config |
| line | Resolution line | String | [Reference below](#line) | `默认` | Provider Parameter |
| ttl | TTL time | Integer (seconds) | [Reference below](#ttl) | `600` | Provider Parameter |
| proxy | Proxy settings | Array | [Reference](../config/json.en.md#proxy) | None | Common Network |
| ssl | SSL verification | Boolean/String | `"auto"`, `true`, `false` | `auto` | Common Network |
| cache | Cache settings | Boolean/String | `true`, `false`, `filepath` | `true` | Common Config |
| log | Log configuration | Object | [Reference](../config/json.en.md#log) | None | Common Config |

> **Parameter Type Description**:
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers
> - **Provider Parameter**: Supported by current provider, values related to current provider
> **Note**: `ttl` and `line` supported values may vary by service plan.

### ttl

The `ttl` parameter specifies the Time To Live (TTL) of DNS records in seconds. DNSPod supports TTL range from 1 to 604800 seconds (7 days). If not set, the default value is used.

| Plan Type | Supported TTL Range (seconds) |
| --------- | :---------------------------: |
| Free | 600 - 604800 |
| Professional | 60 - 604800 |
| Enterprise | 1 - 604800 |
| Premium | 1 - 604800 |

> Reference: [DNSPod TTL Documentation](https://docs.dnspod.cn/dns/help-ttl/)

### line

The `line` parameter specifies DNS resolution lines. DNSPod supported lines:

| Line Identifier | Description |
| :-------------- | :---------- |
| 默认 | Default |
| 电信 | China Telecom |
| 联通 | China Unicom |
| 移动 | China Mobile |
| 教育网 | China Education Network |
| 搜索引擎 | Search Engine |
| 境外 | Overseas |

> More lines reference: [DNSPod Resolution Line Documentation](https://docs.dnspod.cn/dns/dns-record-line)

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Authentication Failed**: Check if API Token or email/password are correct, confirm domain management permissions
- **Domain Not Found**: Ensure domain has been added to DNSPod account, configuration spelling is correct, domain is in active state
- **Record Creation Failed**: Check if subdomain has conflicting records, TTL settings are reasonable, confirm modification permissions
- **Request Rate Limit**: DNSPod has API call rate limits, reduce request frequency

## Support and Resources

- [DNSPod Product Documentation](https://docs.dnspod.cn/)
- [DNSPod API Reference](https://docs.dnspod.cn/api/)
- [DNSPod Console](https://console.dnspod.cn/)
- [Tencent Cloud DNSPod (AccessKey Method)](./tencentcloud.en.md)

> **Recommendation**: Use API Token method to improve security and management convenience, avoid using email/password method.
