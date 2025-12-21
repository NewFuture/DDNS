# DNSPod Global Configuration Guide

## Overview

DNSPod Global (dnspod.com) is an authoritative DNS resolution service for international users, widely used in overseas regions, supporting dynamic DNS record creation and updates. This DDNS project supports multiple authentication methods to connect to DNSPod Global for dynamic DNS record management.

Official Links:

- Official Website: <https://www.dnspod.com/>

## Authentication Information

### 1. API Token Authentication (Recommended)

API Token method is more secure and is the recommended integration method by DNSPod.

#### Obtaining Authentication Information

1. Login to [DNSPod Global Console](https://www.dnspod.com/)
2. Go to "User Center" > "API Token" or visit <https://www.dnspod.com/console/user/security>
3. Click "Create Token", fill in description, select domain management permissions, and complete creation
4. Copy the **ID** (numeric) and **Token** (string). The token is only displayed once, please save it securely

```jsonc
{
    "dns": "dnspod_com",
    "id": "123456",            // DNSPod International API Token ID
    "token": "YOUR_API_TOKEN"  // DNSPod International API Token Secret
}
```

### 2. Email Password Authentication (Not Recommended)

Uses DNSPod account email and password. Lower security, only recommended for special scenarios.

```jsonc
{
    "dns": "dnspod_com",
    "id": "your-email@example.com",  // DNSPod account email
    "token": "your-account-password" // DNSPod account password
}
```

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "dnspod_com",                // Current provider
    "id": "123456",                     // DNSPod International API Token ID
    "token": "YOUR_API_TOKEN",           // DNSPod International API Token Secret
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 domains
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 domains
    "line": "default",                       // Resolution line
    "ttl": 600                              // DNS record TTL (seconds)
}
```

### Parameter Description

| Parameter | Description | Type | Range/Options | Default | Parameter Type |
| :-------: | :---------- | :--- | :------------ | :------ | :------------- |
| dns | Provider identifier | String | `dnspod_com` | None | Provider Parameter |
| id | Authentication ID | String | DNSPod API Token ID or email | None | Provider Parameter |
| token | Authentication key | String | DNSPod API Token secret or password | None | Provider Parameter |
| index4 | IPv4 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| index6 | IPv6 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| ipv4 | IPv4 domains | Array | Domain list | None | Common Config |
| ipv6 | IPv6 domains | Array | Domain list | None | Common Config |
| line | Resolution line | String | [Reference below](#line) | `default` | Provider Parameter |
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
>
> **Note**: `ttl` and `line` supported values may vary by service plan.

### ttl

The `ttl` parameter specifies the Time To Live (TTL) of DNS records in seconds. DNSPod International supports TTL range from 1 to 604800 seconds (7 days). If not set, the default value is used.

| Plan Type | Supported TTL Range (seconds) |
| :-------- | :---------------------------: |
| Free | 600 ~ 604800 |
| Professional | 120 ~ 604800 |
| Enterprise | 60 ~ 604800 |
| Premium | 1 ~ 604800 |

> Reference: [DNSPod International TTL Documentation](https://docs.dnspod.com/dns/help-ttl)

### line

The `line` parameter specifies DNS resolution lines. DNSPod International supported lines (using English identifiers):

| Line Identifier | Description |
| :-------------- | :---------- |
| Default | Default |
| China Telecom | China Telecom |
| China Unicom | China Unicom |
| China Mobile | China Mobile |
| CERNET | China Education Network |
| Chinese mainland | Chinese mainland |
| Search engine | Search engine |

> More lines reference: [DNSPod International Resolution Line Documentation](https://docs.dnspod.com/dns/help-line)

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Authentication Failed**: Check if API Token or email/password are correct, confirm domain management permissions
- **Domain Not Found**: Ensure domain has been added to DNSPod International account, configuration spelling is correct, domain is in active state
- **Record Creation Failed**: Check if subdomain has conflicting records, TTL settings are reasonable, confirm modification permissions
- **Request Rate Limit**: DNSPod has API call rate limits, reduce request frequency
- **Regional Access Restrictions**: DNSPod International may have access restrictions in certain regions

## Support and Resources

- [DNSPod International Product Documentation](https://www.dnspod.com/docs/)
- [DNSPod International API Reference](https://www.dnspod.com/docs/index.html)
- [DNSPod International Console](https://www.dnspod.com/)
- [DNSPod China Configuration Guide](./dnspod.en.md)

> **Recommendation**: Use API Token method to improve security and management convenience, avoid using email/password method. For mainland China users, it is recommended to use [DNSPod China version](./dnspod.en.md).
