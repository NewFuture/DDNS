# Alibaba Cloud DNS (AliDNS) Configuration Guide

## Overview

Alibaba Cloud DNS (AliDNS) is an authoritative DNS resolution service provided by Alibaba Cloud, supporting dynamic creation and updating of DNS records. This DDNS project uses AccessKey ID and AccessKey Secret for API authentication.

Official Links:

- Official Website: <https://www.alibabacloud.com/product/dns>
- Service Console: <https://dns.console.aliyun.com/>

## Authentication Information

### AccessKey Authentication

Use Alibaba Cloud AccessKey ID and AccessKey Secret for authentication.

#### Obtaining Authentication Information

1. Login to [Alibaba Cloud Console](https://console.aliyun.com/)
2. Navigate to "Resource Access Management (RAM)" > "Users"  
3. Create or view AccessKey in user details page
4. Copy the generated **AccessKey ID** and **AccessKey Secret**, please keep them safe
5. Ensure the account has `AliyunDNSFullAccess` permission

```jsonc
{
    "dns": "alidns",
    "id": "your_access_key_id",      // AccessKey ID
    "token": "your_access_key_secret" // AccessKey Secret
}
```

## Permission Requirements

Ensure the Alibaba Cloud account has the following permissions:

- **AliyunDNSFullAccess**: Full access to Cloud DNS (Recommended)
- **AliyunDNSReadOnlyAccess + Custom Write Permissions**: Fine-grained permission control

You can view and configure permissions in the [RAM Console](https://ram.console.aliyun.com/).

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "alidns",                    // Current provider
    "id": "your_access_key_id",              // AccessKey ID
    "token": "your_access_key_secret",              // AccessKey Secret
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 domains
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 domains
    "endpoint": "https://alidns.aliyuncs.com",   // API endpoint
    "line": "default",                       // Resolution line
    "ttl": 600                                 // DNS record TTL (seconds)
}
```

### Parameter Description

| Parameter | Description | Type | Range/Options | Default | Parameter Type |
| :-------: | :---------- | :--- | :------------ | :------ | :------------- |
| dns | Provider identifier | String | `alidns` | None | Provider Parameter |
| id | Authentication ID | String | Alibaba Cloud AccessKey ID | None | Provider Parameter |
| token | Authentication key | String | Alibaba Cloud AccessKey Secret | None | Provider Parameter |
| index4 | IPv4 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| index6 | IPv6 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| ipv4 | IPv4 domains | Array | Domain list | None | Common Config |
| ipv6 | IPv6 domains | Array | Domain list | None | Common Config |
| endpoint | API endpoint | URL | [See below](#endpoint) | `https://alidns.aliyuncs.com` | Provider Parameter |
| line | Resolution line | String | [See below](#ttl) | `default` | Provider Parameter |
| ttl | TTL time | Integer (seconds) | [See below](#line)| None | Provider Parameter |
| proxy | Proxy settings | Array | [Reference](../config/json.en.md#proxy) | None | Common Network |
| ssl | SSL verification | Boolean/String | `auto`, `true`, `false` | `auto` | Common Network |
| cache | Cache settings | Boolean/String | `true`, `false`, `filepath` | `true` | Common Config |
| log | Log configuration | Object | [Reference](../config/json.en.md#log) | None | Common Config |

> **Parameter Type Description**:
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers  
> - **Provider Parameter**: Supported by current provider, values related to current provider
>
> **Note**: Different packages may support different values for `ttl` and `line`.

### endpoint

Alibaba Cloud DNS supports multiple regional endpoints, you can choose the optimal node based on region and network environment:

#### China Mainland Endpoints

- **Default (Recommended)**: `https://alidns.aliyuncs.com`
- **East China 1 (Hangzhou)**: `https://alidns.cn-hangzhou.aliyuncs.com`
- **East China 2 (Shanghai)**: `https://alidns.cn-shanghai.aliyuncs.com`
- **North China 1 (Qingdao)**: `https://alidns.cn-qingdao.aliyuncs.com`
- **North China 2 (Beijing)**: `https://alidns.cn-beijing.aliyuncs.com`
- **North China 3 (Zhangjiakou)**: `https://alidns.cn-zhangjiakou.aliyuncs.com`
- **South China 1 (Shenzhen)**: `https://alidns.cn-shenzhen.aliyuncs.com`
- **Southwest 1 (Chengdu)**: `https://alidns.cn-chengdu.aliyuncs.com`

#### International Endpoints

- **Asia Pacific Southeast 1 (Singapore)**: `https://alidns.ap-southeast-1.aliyuncs.com`
- **Asia Pacific Southeast 2 (Sydney)**: `https://alidns.ap-southeast-2.aliyuncs.com`
- **Asia Pacific Southeast 3 (Kuala Lumpur)**: `https://alidns.ap-southeast-3.aliyuncs.com`
- **Asia Pacific South 1 (Mumbai)**: `https://alidns.ap-south-1.aliyuncs.com`
- **Asia Pacific Northeast 1 (Tokyo)**: `https://alidns.ap-northeast-1.aliyuncs.com`
- **US East 1 (Virginia)**: `https://alidns.us-east-1.aliyuncs.com`
- **US West 1 (Silicon Valley)**: `https://alidns.us-west-1.aliyuncs.com`
- **Europe Central 1 (Frankfurt)**: `https://alidns.eu-central-1.aliyuncs.com`
- **Europe West 1 (London)**: `https://alidns.eu-west-1.aliyuncs.com`

> **Note**: It is recommended to use the default endpoint `https://alidns.aliyuncs.com`, Alibaba Cloud will automatically route to the optimal node. Only specify specific regional endpoints in special network environments.

### ttl

The `ttl` parameter specifies the Time To Live (TTL) for DNS records in seconds. Alibaba Cloud supports TTL ranges from 1 to 86400 seconds (1 day). If not set, the default value is used.

| Package Type | Supported TTL Range (seconds) |
| ------------ | :---------------------------: |
| Free | 600 - 86400 |
| Personal | 600 - 86400 |
| Enterprise Standard | 60 - 86400 |
| Enterprise Flagship | 1 - 86400 |

> Reference: [Alibaba Cloud DNS Documentation](https://www.alibabacloud.com/help/en/dns/pubz-how-to-modify-ttl-time)

### line

The `line` parameter specifies DNS resolution lines, supported by Alibaba Cloud:

| Line Identifier | Description |
| :-------------- | :---------- |
| default | Default |
| telecom | China Telecom |
| unicom | China Unicom |
| mobile | China Mobile |
| edu | China Education Network |
| aliyun | Alibaba Cloud |
| oversea | Overseas |
| internal | China Region |

> More lines reference: [Alibaba Cloud DNS Documentation](https://www.alibabacloud.com/help/en/dns/pubz-resolve-line-enumeration)

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **InvalidAccessKeyId.NotFound**: AccessKey does not exist
- **SignatureDoesNotMatch**: Signature error, check AccessKey Secret
- **DomainNotExists**: Domain not added to Alibaba Cloud DNS
- **Throttling.User**: Too frequent requests, reduce QPS (Personal: 20 QPS, Enterprise: 50 QPS)

## Support and Resources

- [Alibaba Cloud DNS Product Documentation](https://www.alibabacloud.com/help/en/dns)
- [Alibaba Cloud DNS Console](https://dns.console.aliyun.com/)
- [Alibaba Cloud Technical Support](https://www.alibabacloud.com/support)
- [GitHub Issues](https://github.com/NewFuture/DDNS/issues)

> **Recommendation**: Use RAM sub-accounts and regularly rotate AccessKeys to improve account security.
