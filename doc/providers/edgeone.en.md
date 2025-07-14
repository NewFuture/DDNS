# Tencent Cloud EdgeOne Configuration Guide

## Overview

Tencent Cloud EdgeOne (边缘安全速平台) is an edge computing and acceleration service provided by Tencent Cloud, supporting dynamic management of acceleration domain origin server IP addresses. This DDNS project dynamically updates origin server IP addresses of acceleration domains through the EdgeOne API.

Official Links:

- Official Website: <https://cloud.tencent.com/product/teo>
- Service Console: <https://console.cloud.tencent.com/edgeone>

## Authentication

### SecretId/SecretKey Authentication

Uses Tencent Cloud SecretId and SecretKey for authentication, same as Tencent Cloud DNS.

#### Getting Authentication Information

1. Log in to [Tencent Cloud Console](https://console.cloud.tencent.com/)
2. Visit [API Key Management](https://console.cloud.tencent.com/cam/capi)
3. Click "Create Key" button
4. Copy the generated **SecretId** and **SecretKey**, keep them secure
5. Ensure the account has EdgeOne operation permissions

```json
{
    "dns": "edgeone",
    "id": "SecretId",          // Tencent Cloud SecretId
    "token": "SecretKey"       // Tencent Cloud SecretKey
}
```

## Permission Requirements

Ensure the Tencent Cloud account has the following permissions:

- **QcloudTEOFullAccess**: EdgeOne full access permission (recommended)
- **QcloudTEOReadOnlyAccess + Custom write permissions**: Fine-grained permission control

Permissions can be viewed and configured in [Access Management](https://console.cloud.tencent.com/cam/policy).

## Complete Configuration Example

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "edgeone",                       // Current provider
    "id": "your_secret_id",                 // Tencent Cloud SecretId
    "token": "your_secret_key",             // Tencent Cloud SecretKey
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],          // IPv4 domains
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 domains
    "ttl": 600                              // DNS record TTL (seconds)
}
```

### Parameter Description

| Parameter | Description       | Type           | Value Range/Options                    | Default   | Parameter Type |
| :-------: | :---------------- | :------------- | :------------------------------------- | :-------- | :------------- |
| dns       | Provider ID       | String         | `edgeone`, `teo`, `tencentedgeone`     | None      | Provider       |
| id        | Authentication ID | String         | Tencent Cloud SecretId                 | None      | Provider       |
| token     | Authentication Key| String         | Tencent Cloud SecretKey                | None      | Provider       |
| index4    | IPv4 Source       | Array          | [Reference](../json.en.md#ipv4-ipv6)  | `default` | Common Config  |
| index6    | IPv6 Source       | Array          | [Reference](../json.en.md#ipv4-ipv6)  | `default` | Common Config  |
| ipv4      | IPv4 Domains      | Array          | Domain list                            | None      | Common Config  |
| ipv6      | IPv6 Domains      | Array          | Domain list                            | None      | Common Config  |
| ttl       | TTL Time          | Integer (sec)  | [Reference below](#ttl)                | None      | Provider       |
| proxy     | Proxy Settings    | Array          | [Reference](../json.en.md#proxy)       | None      | Common Network |
| ssl       | SSL Verification  | Boolean/String | `"auto"`, `true`, `false`              | `auto`    | Common Network |
| cache     | Cache Settings    | Boolean/String | `true`, `false`, `filepath`            | `true`    | Common Config  |
| log       | Log Configuration | Object         | [Reference](../json.en.md#log)        | None      | Common Config  |

> **Parameter Type Description**:  
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers  
> - **Common Network**: Network setting parameters applicable to all supported DNS providers  
> - **Provider**: Parameters specific to the current provider

### ttl

EdgeOne TTL configuration is mainly used for configuration documentation. The actual caching strategy is managed by the EdgeOne platform.

## Usage Instructions

EdgeOne DDNS implements dynamic DNS functionality by updating the origin server IP addresses of acceleration domains. Unlike traditional DNS record management, EdgeOne manages acceleration domains and their corresponding origin server configurations.

### Supported Domain Formats

- **Complete domains**: `www.example.com`, `api.example.com`
- **Root domain**: Supports using `@` to represent root domain

### Working Principle

1. Query EdgeOne site information to get ZoneId
2. Query existing acceleration domain configurations
3. Update or create origin server IP addresses for acceleration domains

## Troubleshooting

### Debug Mode

Enable debug logging for detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Authentication failure**: Check if SecretId and SecretKey are correct, confirm account permissions
- **Site not found**: Ensure domain has been added to EdgeOne site with normal status
- **Acceleration domain does not exist**: Confirm domain has been configured as acceleration domain in EdgeOne
- **Insufficient permissions**: Ensure account has EdgeOne management permissions

## Support and Resources

- [Tencent Cloud EdgeOne Product Documentation](https://cloud.tencent.com/document/product/1552)
- [EdgeOne API Documentation](https://cloud.tencent.com/document/api/1552)
- [EdgeOne Console](https://console.cloud.tencent.com/edgeone)
- [Tencent Cloud Technical Support](https://cloud.tencent.com/document/product/282)

> **Note**: EdgeOne is primarily designed for edge acceleration scenarios. For traditional DNS resolution services, consider using [Tencent Cloud DNS](./tencentcloud.en.md).