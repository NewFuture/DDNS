# Alibaba Cloud Edge Security Acceleration (ESA) Configuration Guide

## Overview

Alibaba Cloud Edge Security Acceleration (ESA) is an edge security acceleration service provided by Alibaba Cloud, supporting dynamic management of DNS records. This DDNS project uses AccessKey ID and AccessKey Secret to update ESA DNS records.

Official Links:

- Official Website: <https://www.alibabacloud.com/product/esa>
- Service Console: <https://esa.console.aliyun.com/>

## Authentication Information

### AccessKey Authentication (Recommended)

Use Alibaba Cloud AccessKey ID and AccessKey Secret for authentication.

#### Obtaining Authentication Information

1. Login to [Alibaba Cloud Console](https://console.aliyun.com/)
2. Navigate to "Resource Access Management (RAM)" > "Users"
3. Create or view AccessKey in user details page
4. Copy the generated **AccessKey ID** and **AccessKey Secret**, please keep them safe
5. Ensure the account has Edge Security Acceleration (`AliyunESAFullAccess`) permissions

```jsonc
{
    "dns": "aliesa",
    "id": "your_access_key_id",      // AccessKey ID
    "token": "your_access_key_secret" // AccessKey Secret
}
```

## Permission Requirements

Ensure the Alibaba Cloud account has the following permissions:

- **AliyunESAFullAccess**: Full access to Edge Security Acceleration (Recommended)
- **ESA Site Query Permission + ESA DNS Record Management Permission**: Fine-grained permission control

You can view and configure permissions in the [RAM Console](https://ram.console.aliyun.com/).

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "aliesa",                    // Current provider
    "id": "your_access_key_id",              // AccessKey ID
    "token": "your_access_key_secret",              // AccessKey Secret
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 domains
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 domains
    "endpoint": "https://esa.cn-hangzhou.aliyuncs.com",   // API endpoint
    "ttl": 600                                 // DNS record TTL (seconds)
}
```

### Parameter Description

| Parameter | Description | Type | Range/Options | Default | Parameter Type |
| :-------: | :---------- | :--- | :------------ | :------ | :------------- |
| dns | Provider identifier | String | `aliesa` | None | Provider Parameter |
| id | Authentication ID | String | Alibaba Cloud AccessKey ID | None | Provider Parameter |
| token | Authentication key | String | Alibaba Cloud AccessKey Secret | None | Provider Parameter |
| index4 | IPv4 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| index6 | IPv6 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| ipv4 | IPv4 domains | Array | Domain list | None | Common Config |
| ipv6 | IPv6 domains | Array | Domain list | None | Common Config |
| endpoint | API endpoint | URL | [See below](#endpoint) | `https://esa.cn-hangzhou.aliyuncs.com` | Provider Parameter |
| ttl | TTL time | Integer (seconds) | 1-86400 | None | Provider Parameter |
| proxy | Proxy settings | Array | [Reference](../config/json.en.md#proxy) | None | Common Network |
| ssl | SSL verification | Boolean/String | `auto`, `true`, `false` | `auto` | Common Network |
| cache | Cache settings | Boolean/String | `true`, `false`, `filepath` | `true` | Common Config |
| log | Log configuration | Object | [Reference](../config/json.en.md#log) | None | Common Config |

> **Parameter Type Description**:
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers  
> - **Provider Parameter**: Supported by current provider, values related to current provider

### endpoint

Alibaba Cloud ESA supports multiple regional endpoints, you can choose the optimal node based on region and network environment:

#### China Mainland Nodes

- **East China (Hangzhou)**: `https://esa.cn-hangzhou.aliyuncs.com` (Default)

#### International Nodes

- **Asia Pacific Southeast 1 (Singapore)**: `https://esa.ap-southeast-1.aliyuncs.com`

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

#### "Site not found for domain"

- Check if the domain has been added to the ESA service
- Confirm the domain format is correct (without protocol prefix)
- Verify AccessKey permissions

#### "Failed to create/update record"

- Check if the DNS record type is supported
- Confirm the record value format is correct
- Verify the TTL value is within the allowed range

#### "API call failed"

- Check if AccessKey ID and Secret are correct
- Confirm network connectivity is normal
- View detailed error logs

## Support and Resources

- [Alibaba Cloud ESA Product Documentation](https://www.alibabacloud.com/help/en/esa)
- [Alibaba Cloud ESA Console](https://esa.console.aliyun.com/)
- [Alibaba Cloud Technical Support](https://www.alibabacloud.com/support)
- [GitHub Issues](https://github.com/NewFuture/DDNS/issues)

> **Recommendation**: Use RAM sub-accounts and regularly rotate AccessKeys to improve account security.
