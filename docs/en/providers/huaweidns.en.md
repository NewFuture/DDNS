# Huawei Cloud DNS Configuration Guide

## Overview

Huawei Cloud DNS is an authoritative DNS resolution service provided by Huawei Cloud, featuring high availability, high scalability, and high security, supporting dynamic DNS record creation and updates. This DDNS project authenticates through Access Key ID and Secret Access Key.

> ⚠️ **Important Note**: Huawei Cloud DNS Provider is currently in **verification pending** status, lacking sufficient real-world testing. Please provide feedback through [GitHub Issues](https://github.com/NewFuture/DDNS/issues).

Official Links:

- Official Website: <https://www.huaweicloud.com/product/dns.html>
- Provider Console: <https://console.huaweicloud.com/dns/>

## Authentication Information

### Access Key Authentication

Use Huawei Cloud Access Key ID and Secret Access Key for authentication.

#### Obtaining Authentication Information

1. Log in to [Huawei Cloud Console](https://www.huaweicloud.com/)
2. Go to **My Credentials** > **Access Keys**
3. Click "Add Access Key" button
4. Copy the generated **Access Key ID** and **Secret Access Key**, please keep them safe
5. Ensure the account has operation permissions for Cloud DNS

```jsonc
{
    "dns": "huaweidns",
    "id": "your_access_key_id",     // Huawei Cloud Access Key ID
    "token": "your_secret_access_key" // Huawei Cloud Secret Access Key
}
```

## Permission Requirements

Ensure the Huawei Cloud account has the following permissions:

- **DNS Administrator**: Full management permissions for Cloud DNS (recommended)
- **DNS ReadOnlyAccess + Custom Write Permissions**: Fine-grained permission control

You can view and configure permissions in [Identity and Access Management](https://console.huaweicloud.com/iam/).

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "huaweidns",                 // Current provider
    "id": "your_access_key_id",         // Huawei Cloud Access Key ID
    "token": "your_secret_access_key",  // Huawei Cloud Secret Access Key
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 domain
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 domain
    "endpoint": "https://dns.myhuaweicloud.com", // API endpoint
    "line": "default",                      // Resolution line
    "ttl": 600                              // DNS record TTL (seconds)
}
```

### Parameter Description

| Parameter | Description      | Type           | Value Range/Options                     | Default                        | Parameter Type |
| :-------: | :--------------- | :------------- | :------------------------------------- | :----------------------------- | :------------- |
| dns       | Provider ID      | String         | `huaweidns`                            | None                           | Provider Param |
| id        | Authentication ID| String         | Huawei Cloud Access Key ID             | None                           | Provider Param |
| token     | Authentication Key| String        | Huawei Cloud Secret Access Key         | None                           | Provider Param |
| index4    | IPv4 Source      | Array          | [Reference](../config/json.en.md#ipv4-ipv6)  | `default`                      | Common Config  |
| index6    | IPv6 Source      | Array          | [Reference](../config/json.en.md#ipv4-ipv6)  | `default`                      | Common Config  |
| ipv4      | IPv4 Domain      | Array          | Domain list                            | None                           | Common Config  |
| ipv6      | IPv6 Domain      | Array          | Domain list                            | None                           | Common Config  |
| endpoint  | API Endpoint     | URL            | [Reference below](#endpoint)           | `https://dns.myhuaweicloud.com`| Provider Param |
| line      | Resolution Line  | String         | [Reference below](#line)               | `default`                      | Provider Param |
| ttl       | TTL Time         | Integer (seconds)| 1~2147483647                         | `300`                          | Provider Param |
| proxy     | Proxy Settings   | Array          | [Reference](../config/json.en.md#proxy)      | None                           | Common Network |
| ssl       | SSL Verification | Boolean/String | `"auto"`, `true`, `false`              | `auto`                         | Common Network |
| cache     | Cache Settings   | Boolean/String | `true`, `false`, `filepath`            | `true`                         | Common Config  |
| log       | Log Config       | Object         | [Reference](../config/json.en.md#log)        | None                           | Common Config  |

> **Parameter Type Description**:
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers
> - **Provider Param**: Supported by current provider, values related to current provider
>
> **Note**: The supported values for `ttl` and `line` may vary depending on different service plans.

### endpoint

Huawei Cloud DNS supports multiple regional endpoints. You can choose the optimal node based on region and network environment:

#### Domestic Nodes

- **Global Service (Recommended)**: `https://dns.myhuaweicloud.com`
- **North China-Beijing 4**: `https://dns.cn-north-4.myhuaweicloud.com`
- **East China-Shanghai 1**: `https://dns.cn-east-3.myhuaweicloud.com`
- **South China-Guangzhou**: `https://dns.cn-south-1.myhuaweicloud.com`
- **North China-Ulanqab 1**: `https://dns.cn-north-9.myhuaweicloud.com`
- **Southwest-Guiyang 1**: `https://dns.cn-southwest-2.myhuaweicloud.com`

#### Overseas Nodes

- **Asia Pacific-Singapore**: `https://dns.ap-southeast-3.myhuaweicloud.com`
- **Asia Pacific-Hong Kong**: `https://dns.ap-southeast-1.myhuaweicloud.com`
- **Asia Pacific-Bangkok**: `https://dns.ap-southeast-2.myhuaweicloud.com`
- **Africa-Johannesburg**: `https://dns.af-south-1.myhuaweicloud.com`
- **Latin America-Santiago**: `https://dns.la-south-2.myhuaweicloud.com`
- **Latin America-Mexico City 1**: `https://dns.la-north-2.myhuaweicloud.com`
- **Latin America-São Paulo 1**: `https://dns.sa-brazil-1.myhuaweicloud.com`

> **Note**: It is recommended to use the default endpoint `https://dns.myhuaweicloud.com`, as Huawei Cloud will automatically route to the optimal node. Specific regional endpoints are only needed in special network environments.

### line

The `line` parameter specifies DNS resolution lines. For supported lines in Huawei Cloud: [Configure Custom Line Resolution](https://support.huaweicloud.com/usermanual-dns/dns_usermanual_0018.html).

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Authentication Failed**: Check if Access Key ID and Secret Access Key are correct, confirm the keys have not been deleted or disabled
- **Domain Not Found**: Ensure the domain has been added to Huawei Cloud DNS resolution, check spelling accuracy, and confirm the domain is active
- **Record Creation Failed**: Check for conflicting records on subdomain, ensure reasonable TTL settings, and confirm modification permissions
- **Request Rate Limiting**: Huawei Cloud API has call frequency limits, reduce request frequency

### Common Error Codes

| Error Code     | Description          | Solution                |
| :------------- | :------------------- | :---------------------- |
| APIGW.0301     | Authentication failed| Check access keys       |
| DNS.0101       | Domain not found     | Check domain configuration |
| DNS.0102       | Record set not found | Check record settings   |
| DNS.0103       | Record set exists    | Check conflicting records |
| DNS.0203       | Request rate too high| Reduce request frequency |

## Support and Resources

- [Huawei Cloud DNS Product Documentation](https://support.huaweicloud.com/dns/)
- [Huawei Cloud DNS API Documentation](https://support.huaweicloud.com/api-dns/)
- [Huawei Cloud Console](https://console.huaweicloud.com/dns/)
- [Huawei Cloud Technical Support](https://support.huaweicloud.com/)

> ⚠️ **Verification Pending Status**: Huawei Cloud DNS Provider lacks sufficient real-world testing. It is recommended to conduct thorough testing before using in production environments. If you encounter issues, please provide feedback through [GitHub Issues](https://github.com/NewFuture/DDNS/issues).
