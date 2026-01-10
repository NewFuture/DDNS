# 51DNS (DNS.COM) Configuration Guide

## Overview

51DNS (DNSCOM) (formerly dns.com, now 51dns.com) is a domain name resolution service provider that provides authoritative DNS resolution services and supports the creation and updating of dynamic DNS records. This DDNS project uses API Key and Secret Key for API authentication.

> ⚠️ **Notice**: 51DNS (DNSCOM) Provider is currently in **pending verification** status, lacking sufficient real-world testing. Please report issues via [GitHub Issues](https://github.com/NewFuture/DDNS/issues).

Official Website: <https://www.51dns.com/>

## Authentication Information

### API Key + Secret Key Authentication

51DNS uses API Key and Secret Key for API authentication, which is the official recommended authentication method.

#### Obtaining Authentication Information

1. Log into [51DNS/DNS.COM Console](https://www.51dns.com/)
2. Navigate to "API Management" page
3. Click "Create API Key"
4. Record the generated **API Key** and **Secret Key**, please keep them safe

```jsonc
{
    "dns": "dnscom",
    "id": "your_api_key",      // 51DNS API Key
    "token": "your_secret_key" // 51DNS Secret Key
}
```

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "dnscom",                    // Current provider
    "id": "your_api_key",               // 51DNS API Key
    "token": "your_secret_key",         // 51DNS Secret Key
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 domains
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 domains
    "line": "1",                            // Resolution line
    "ttl": 600                              // DNS record TTL (seconds)
}
```

### Parameter Description

| Parameter | Description      | Type           | Range/Options                       | Default   | Parameter Type |
| :-------: | :--------------- | :------------- | :--------------------------------- | :-------- | :------------- |
| dns       | Provider ID      | String         | `dnscom`                           | None      | Provider       |
| id        | Authentication ID| String         | 51DNS API Key                      | None      | Provider       |
| token     | Authentication Key| String        | 51DNS Secret Key                   | None      | Provider       |
| index4    | IPv4 source      | Array          | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config  |
| index6    | IPv6 source      | Array          | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config  |
| ipv4      | IPv4 domains     | Array          | Domain list                        | None      | Common Config  |
| ipv6      | IPv6 domains     | Array          | Domain list                        | None      | Common Config  |
| line      | Resolution line  | String         | [See below](#line)                 | `1`       | Provider       |
| ttl       | TTL time         | Integer (seconds) | [See below](#ttl)               | `600`     | Provider       |
| proxy     | Proxy settings   | Array          | [Reference](../config/json.en.md#proxy)   | None      | Common Network |
| ssl       | SSL verification | Boolean/String | `"auto"`, `true`, `false`          | `auto`    | Common Network |
| cache     | Cache settings   | Boolean/String | `true`, `false`, `filepath`        | `true`    | Common Config  |
| log       | Log configuration| Object         | [Reference](../config/json.en.md#log)     | None      | Common Config  |

> **Parameter Type Description**:  
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers  
> - **Common Network**: Network setting parameters applicable to all supported DNS providers  
> - **Provider**: Supported by current provider, values related to current provider
>
> **Note**: Values supported for `ttl` and `line` may vary depending on your service plan.

### ttl

The `ttl` parameter specifies the Time To Live (TTL) of DNS records in seconds. 51DNS supports TTL ranges from 60 to 86400 seconds (1 day). If not set, the default value is used.

| Plan Type    | Supported TTL Range (seconds) |
| :---------- | :---------------------------: |
| Free        |         600 - 86400           |
| Professional|          60 - 86400           |
| Enterprise  |          10 - 86400           |
| Premium     |           1 - 86400           |

> **Note**: For specific TTL ranges, please refer to [51DNS official documentation](https://www.51dns.com/service.html)

### line

The `line` parameter specifies DNS resolution lines. 51DNS supported lines:

| Line ID         | Description      |
| :-------------- | :--------------- |
| 1               | Default          |
| 2               | China Telecom    |
| 3               | China Unicom     |
| 4               | China Mobile     |

> For more lines reference: [Official Documentation ViewID](https://www.51dns.com/document/api/index.html)

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Authentication Failed**: Check if API Key and Secret Key are correct, ensure API key status is enabled
- **Domain Not Found**: Ensure domain is added to 51DNS account, configuration spelling is correct, domain is in active status
- **Record Creation Failed**: Check if subdomain has conflicting records, TTL settings are reasonable, confirm modification permissions
- **Request Rate Limit**: 51DNS has API call rate limits (maximum 100 times per minute), reduce request frequency

### API Error Codes

| Error Code | Description      | Solution           |
| :--------- | :--------------- | :----------------- |
| 0          | Success          | Operation successful |
| 1          | Parameter error  | Check request parameters |
| 2          | Authentication failed | Check API credentials |
| 3          | Insufficient permissions | Check API permissions |
| 4          | Record not found | Check domain and record |
| 5          | Domain not found | Check domain configuration |

## Support & Resources

- [51DNS Official Website](https://www.51dns.com/)
- [51DNS API Documentation](https://www.51dns.com/document/api/index.html)
- [51DNS Console](https://www.51dns.com/)

> ⚠️ **Pending Verification**: 51DNS Provider lacks sufficient real-world testing. It is recommended to thoroughly test before using in production environments. Please report any issues via [GitHub Issues](https://github.com/NewFuture/DDNS/issues).
