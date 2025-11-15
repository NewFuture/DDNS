# Tencent Cloud EdgeOne DNS Configuration Guide

## Overview

The Tencent Cloud EdgeOne DNS provider is used to manage DNS records for non-accelerated domains. After fully hosting your domain with EdgeOne, you can use this provider to manage regular DNS records in addition to acceleration domains.

> **Difference from EdgeOne Acceleration Domains**:
>
> - **EdgeOne (Acceleration Domains)**: Manages origin server IP addresses for edge acceleration domains, primarily used in CDN acceleration scenarios. Use `edgeone`, `edgeone_acc`, `neo_acc`, or `neo` as the dns parameter value.
> - **EdgeOne DNS (Non-Acceleration Domains)**: Manages regular DNS records, similar to traditional DNS resolution services. Use `edgeone_dns` or `edgeone_noacc` as the dns parameter value.

Official Links:

- EdgeOne International: <https://edgeone.ai>
- Official Website: <https://cloud.tencent.com/product/teo>
- Service Console: <https://console.cloud.tencent.com/edgeone>

## Authentication

### SecretId/SecretKey Authentication

Uses Tencent Cloud SecretId and SecretKey for authentication, same as Tencent Cloud DNS.

> Same as [Tencent Cloud DNS](tencentcloud.en.md), EdgeOne uses SecretId and SecretKey for authentication. However, the permission requirements are different, and you need to ensure that the account has EdgeOne operation permissions.

#### Getting Authentication Information

1. Log in to [Tencent Cloud Console](https://console.cloud.tencent.com/)
2. Visit [API Key Management](https://console.cloud.tencent.com/cam/capi)
3. Click "Create Key" button
4. Copy the generated **SecretId** and **SecretKey**, keep them secure
5. Ensure the account has EdgeOne operation permissions

```jsonc
{
    "dns": "edgeone_dns",      // Use EdgeOne DNS provider
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

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "edgeone_dns",                   // EdgeOne DNS provider (non-accelerated domains)
    "id": "your_secret_id",                 // Tencent Cloud SecretId
    "token": "your_secret_key",             // Tencent Cloud SecretKey
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],          // IPv4 domains
    "ipv6": ["ipv6.ddns.newfuture.cc"],     // IPv6 domains
    "endpoint": "https://teo.tencentcloudapi.com" // API endpoint
}
```

### Parameter Description

| Parameter | Description       | Type           | Value Range/Options                    | Default   | Parameter Type |
| :-------: | :---------------- | :------------- | :------------------------------------- | :-------- | :------------- |
| dns       | Provider ID       | String         | `edgeone_dns`, `teo_dns`, `edgeone_noacc` | None      | Provider       |
| id        | Authentication ID | String         | Tencent Cloud SecretId                 | None      | Provider       |
| token     | Authentication Key| String         | Tencent Cloud SecretKey                | None      | Provider       |
| index4    | IPv4 Source       | Array          | [Reference](../config/json.en.md#ipv4-ipv6)  | `default` | Common Config  |
| index6    | IPv6 Source       | Array          | [Reference](../config/json.en.md#ipv4-ipv6)  | `default` | Common Config  |
| ipv4      | IPv4 Domains      | Array          | Domain list                            | None      | Common Config  |
| ipv6      | IPv6 Domains      | Array          | Domain list                            | None      | Common Config  |
| endpoint  | API Endpoint      | URL            | [Reference below](#endpoint)           | `https://teo.tencentcloudapi.com` | Provider  |
| proxy     | Proxy Settings    | Array          | [Reference](../config/json.en.md#proxy)       | None      | Common Network |
| ssl       | SSL Verification  | Boolean/String | `"auto"`, `true`, `false`              | `auto`    | Common Network |
| cache     | Cache Settings    | Boolean/String | `true`, `false`, `filepath`            | `true`    | Common Config  |
| log       | Log Configuration | Object         | [Reference](../config/json.en.md#log)        | None      | Common Config  |

> **Parameter Type Description**:  
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers  
> - **Common Network**: Network setting parameters applicable to all supported DNS providers  
> - **Provider**: Parameters specific to the current provider

### endpoint

Tencent Cloud EdgeOne supports domestic and international API endpoints, which can be selected based on region and account type:

#### Domestic Version

- **Default (Recommended)**: `https://teo.tencentcloudapi.com`

#### International Version

- **International**: `https://teo.intl.tencentcloudapi.com`

> **Note**: Please choose the corresponding endpoint according to your Tencent Cloud account type. Domestic accounts use the domestic endpoint, and international accounts use the international endpoint. If you are unsure, it is recommended to use the default domestic endpoint.

## DNS Provider Comparison

| Provider ID | Purpose | API Operations | Use Cases |
| :---------: | :------ | :------------- | :-------- |
| `edgeone`, `edgeone_acc`, `teo_acc` | Acceleration Domains | `CreateAccelerationDomain`, `ModifyAccelerationDomain`, `DescribeAccelerationDomains` | CDN edge acceleration, update origin IP |
| `edgeone_dns`, `teo_dns`, `edgeone_noacc` | DNS Records | `CreateDnsRecord`, `ModifyDnsRecords`, `DescribeDnsRecords` | Regular DNS resolution service |

## Troubleshooting

### Debug Mode

Enable debug logging for detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Authentication failure**: Check if SecretId and SecretKey are correct, confirm account permissions
- **Site not found**: Ensure domain has been added to EdgeOne site with normal status
- **DNS record does not exist**: Confirm domain is properly hosted in EdgeOne
- **Insufficient permissions**: Ensure account has EdgeOne management permissions

## Support and Resources

- [Tencent Cloud EdgeOne Product Documentation](https://cloud.tencent.com/document/product/1552)
- [EdgeOne API Documentation](https://cloud.tencent.com/document/api/1552)
- [EdgeOne DNS Records API](https://cloud.tencent.com/document/api/1552/86336)
- [EdgeOne Console](https://console.cloud.tencent.com/edgeone)
- [Tencent Cloud Technical Support](https://cloud.tencent.com/document/product/282)

> **Tip**: To use EdgeOne's edge acceleration features, use the [EdgeOne Acceleration Domain Provider](./edgeone.en.md). For traditional DNS resolution services without EdgeOne, consider using [Tencent Cloud DNS](./tencentcloud.en.md).
