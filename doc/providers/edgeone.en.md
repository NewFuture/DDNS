# Tencent Cloud EdgeOne Configuration Guide

## Overview

Tencent Cloud EdgeOne is an edge computing and acceleration service provided by Tencent Cloud, supporting dynamic management of acceleration domain origin server IP addresses. This DDNS project dynamically updates origin server IP addresses of acceleration domains through the EdgeOne API.

> **Note**: This provider is for managing EdgeOne acceleration domains. For managing regular DNS records of non-accelerated domains, please use the [EdgeOne DNS Provider](./edgeone_dns.en.md).

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

### Acceleration Domain Configuration (Default)

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "edgeone",                       // Current provider
    "id": "your_secret_id",                 // Tencent Cloud SecretId
    "token": "your_secret_key",             // Tencent Cloud SecretKey
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],          // IPv4 domains
    "ipv6": ["ipv6.ddns.newfuture.cc"],     // IPv6 domains
    "endpoint": "https://teo.intl.tencentcloudapi.com" // API endpoint
}
```

### Switching Domain Type via extra Parameter

The EdgeOne provider supports flexible switching between acceleration domains and regular DNS record management using the `extra.teoDomainType` parameter:

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "edgeone",
    "id": "your_secret_id",
    "token": "your_secret_key",
    "ipv4": ["ddns.newfuture.cc"],
    "extra": {
        "teoDomainType": "dns"  // Switch to DNS record mode (non-accelerated domains)
    }
}
```

Or configure via initialization parameters:

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "edgeone",
    "id": "your_secret_id",
    "token": "your_secret_key",
    "ipv4": ["ddns.newfuture.cc"],
    "teoDomainType": "dns"  // Configure domain type at initialization
}
```

#### teoDomainType Parameter Description

| Value          | Description                              | Corresponding API                           |
| :------------- | :-------------------------------------- | :----------------------------------------- |
| `acceleration` | Acceleration domains (default)          | DescribeAccelerationDomains, CreateAccelerationDomain, ModifyAccelerationDomain |
| `dns`         | DNS records (non-accelerated domains)   | DescribeDnsRecords, CreateDnsRecord, ModifyDnsRecords |

> **Note**:
>
> - `teoDomainType` parameter is case-insensitive (`dns`, `DNS`, `Dns` are all valid)
> - `extra` parameter takes priority over initialization parameter
> - It is recommended to use the dedicated [EdgeOne DNS Provider](./edgeone_dns.en.md) for cleaner and clearer code

### Parameter Description

| Parameter      | Description       | Type           | Value Range/Options                    | Default   | Parameter Type |
| :------------: | :---------------- | :------------- | :------------------------------------- | :-------- | :------------- |
| dns            | Provider ID       | String         | `edgeone`, `edgeone_acc`, `teo_acc` | None      | Provider       |
| id             | Authentication ID | String         | Tencent Cloud SecretId                 | None      | Provider       |
| token          | Authentication Key| String         | Tencent Cloud SecretKey                | None      | Provider       |
| teoDomainType  | Domain Type       | String         | `acceleration`, `dns`                  | `acceleration` | Provider  |
| index4         | IPv4 Source       | Array          | [Reference](../config/json.en.md#ipv4-ipv6)  | `default` | Common Config  |
| index6         | IPv6 Source       | Array          | [Reference](../config/json.en.md#ipv4-ipv6)  | `default` | Common Config  |
| ipv4           | IPv4 Domains      | Array          | Domain list                            | None      | Common Config  |
| ipv6           | IPv6 Domains      | Array          | Domain list                            | None      | Common Config  |
| extra          | Extra Parameters  | Object         | `{"teoDomainType": "dns"}` etc.        | None      | Provider       |
| endpoint       | API Endpoint      | URL            | [Reference below](#endpoint)           | `https://teo.tencentcloudapi.com` | Provider  |
| proxy          | Proxy Settings    | Array          | [Reference](../config/json.en.md#proxy)       | None      | Common Network |
| ssl            | SSL Verification  | Boolean/String | `"auto"`, `true`, `false`              | `auto`    | Common Network |
| cache          | Cache Settings    | Boolean/String | `true`, `false`, `filepath`            | `true`    | Common Config  |
| log            | Log Configuration | Object         | [Reference](../config/json.en.md#log)        | None      | Common Config  |

> **Parameter Type Description**:  
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers  
> - **Common Network**: Network setting parameters applicable to all supported DNS providers  
> - **Provider**: Parameters specific to the current provider
>
> EdgeOne TTL actual caching strategy is managed by the EdgeOne platform.

### endpoint

Tencent Cloud EdgeOne supports domestic and international API endpoints, which can be selected based on region and account type:

#### Domestic Version

- **Default (Recommended)**: `https://teo.tencentcloudapi.com`

#### International Version

- **International**: `https://teo.intl.tencentcloudapi.com`

> **Note**: Please choose the corresponding endpoint according to your Tencent Cloud account type. Domestic accounts use the domestic endpoint, and international accounts use the international endpoint. If you are unsure, it is recommended to use the default domestic endpoint.

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

> **Note**: EdgeOne is primarily designed for edge acceleration scenarios. For traditional DNS resolution services, consider using [Tencent Cloud DNS](./tencentcloud.en.md). For managing DNS records of non-accelerated domains hosted in EdgeOne, please use the [EdgeOne DNS Provider](./edgeone_dns.en.md).
