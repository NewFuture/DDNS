# TencentCloud DNS (TencentCloud DNSPod) Configuration Guide

## Overview

TencentCloud DNS (TencentCloud DNSPod) is a professional DNS resolution service provided by Tencent Cloud, featuring high availability and high performance, supporting dynamic DNS record creation and updates. This DDNS project uses SecretId and SecretKey for API authentication.

Official links:

- Official website: <https://cloud.tencent.com/product/dns>
- Service console: <https://console.cloud.tencent.com/dnspod>

## Authentication

### API Key Authentication

TencentCloud DNS uses `SecretId` and `SecretKey` for API authentication, which is the most secure and recommended authentication method.

#### Obtaining API Keys

```jsonc
{
    "dns": "tencentcloud",
    "id": "Your_Secret_Id",     // TencentCloud SecretId
    "token": "Your_Secret_Key"  // TencentCloud SecretKey
}
```

There are two ways to obtain API keys:

##### From DNSPod

The simplest and quickest way to obtain keys

1. Log in to [DNSPod Console](https://console.dnspod.cn/)
2. Navigate to "User Center" > "API Keys" or visit <https://console.dnspod.cn/account/token>
3. Click "Create Key", fill in the description, select domain management permissions, and complete creation

##### From TencentCloud

1. Log in to [TencentCloud Console](https://console.cloud.tencent.com/)
2. Visit [API Key Management](https://console.cloud.tencent.com/cam/capi)
3. Click "Create Key" button
4. Copy the generated **SecretId** and **SecretKey**, please keep them safe
5. Ensure the account has DNSPod-related permissions

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "tencentcloud",              // Current provider
    "id": "Your_Secret_Id",     // TencentCloud SecretId
    "token": "Your_Secret_Key", // TencentCloud SecretKey
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 domains
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 domains
    "endpoint": "https://dnspod.tencentcloudapi.com", // API endpoint
    "line": "默认",                          // Resolution line
    "ttl": 600                              // DNS record TTL (seconds)
}
```

### Parameter Description

| Parameter | Description | Type | Value Range/Options | Default | Parameter Type |
| :-------: | :---------- | :--- | :------------------ | :------ | :------------- |
| dns | Provider identifier | String | `tencentcloud` | None | Provider Parameter |
| id | Authentication ID | String | TencentCloud SecretId | None | Provider Parameter |
| token | Authentication key | String | TencentCloud SecretKey | None | Provider Parameter |
| index4 | IPv4 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Configuration |
| index6 | IPv6 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Configuration |
| ipv4 | IPv4 domains | Array | Domain list | None | Common Configuration |
| ipv6 | IPv6 domains | Array | Domain list | None | Common Configuration |
| endpoint | API endpoint | URL | [See below](#endpoint) | `https://dnspod.tencentcloudapi.com` | Provider Parameter |
| line | Resolution line | String | [See below](#line) | `默认` | Provider Parameter |
| ttl | TTL time | Integer (seconds) | [See below](#ttl) | `600` | Provider Parameter |
| proxy | Proxy settings | Array | [Reference](../config/json.en.md#proxy) | None | Common Network |
| ssl | SSL verification | Boolean/String | `"auto"`, `true`, `false` | `auto` | Common Network |
| cache | Cache settings | Boolean/String | `true`, `false`, `filepath` | `true` | Common Configuration |
| log | Log configuration | Object | [Reference](../config/json.en.md#log) | None | Common Configuration |

> **Parameter Type Description**:  
>
> - **Common Configuration**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers
> - **Provider Parameter**: Supported by current provider, values related to current provider
>
> ### endpoint

TencentCloud DNSPod API supports multiple regional endpoints, allowing you to choose the optimal node based on your network environment:

#### Domestic Nodes

- **Default (Recommended)**: `https://dnspod.tencentcloudapi.com`
- **South China (Guangzhou)**: `https://dnspod.ap-guangzhou.tencentcloudapi.com`
- **East China (Shanghai)**: `https://dnspod.ap-shanghai.tencentcloudapi.com`
- **North China (Beijing)**: `https://dnspod.ap-beijing.tencentcloudapi.com`
- **Southwest (Chengdu)**: `https://dnspod.ap-chengdu.tencentcloudapi.com`
- **Hong Kong, Macao and Taiwan (Hong Kong)**: `https://dnspod.ap-hongkong.tencentcloudapi.com`

#### Overseas Nodes

- **Asia Pacific Southeast (Singapore)**: `https://dnspod.ap-singapore.tencentcloudapi.com`
- **Asia Pacific Southeast (Bangkok)**: `https://dnspod.ap-bangkok.tencentcloudapi.com`
- **Asia Pacific South (Mumbai)**: `https://dnspod.ap-mumbai.tencentcloudapi.com`
- **Asia Pacific Northeast (Seoul)**: `https://dnspod.ap-seoul.tencentcloudapi.com`
- **Asia Pacific Northeast (Tokyo)**: `https://dnspod.ap-tokyo.tencentcloudapi.com`
- **US East (Virginia)**: `https://dnspod.na-ashburn.tencentcloudapi.com`
- **US West (Silicon Valley)**: `https://dnspod.na-siliconvalley.tencentcloudapi.com`
- **Europe (Frankfurt)**: `https://dnspod.eu-frankfurt.tencentcloudapi.com`

> **Note**: It is recommended to use the default endpoint `https://dnspod.tencentcloudapi.com`, as TencentCloud will automatically route to the optimal node. Only specify specific regional endpoints under special network conditions.

### ttl

The `ttl` parameter specifies the Time To Live (TTL) of DNS records in seconds. TencentCloud DNSPod supports a TTL range from 1 to 604800 seconds (7 days). If not set, the default value is used.

| Plan Type | Supported TTL Range (seconds) |
| :-------- | :---------------------------- |
| Free | 600 ~ 604800 |
| Professional | 60 ~ 604800 |
| Enterprise | 1 ~ 604800 |
| Premium | 1 ~ 604800 |

> Reference: TencentCloud [DNS TTL Documentation](https://cloud.tencent.com/document/product/302/9072)

### line

The `line` parameter specifies DNS resolution lines. TencentCloud DNSPod supported lines:

| Line Identifier | Description |
| :-------------- | :---------- |
| 默认 | Default |
| 电信 | China Telecom |
| 联通 | China Unicom |
| 移动 | China Mobile |
| 教育网 | China Education Network |
| 境外 | Overseas |

> More lines reference: TencentCloud [DNS Resolution Lines Documentation](https://cloud.tencent.com/document/product/302/8643)

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Signature Error**: Check if SecretId and SecretKey are correct, confirm the keys haven't expired
- **Domain Not Found**: Ensure the domain has been added to TencentCloud DNSPod, configuration spelling is correct, domain is active
- **Record Creation Failed**: Check if subdomain has conflicting records, TTL settings are reasonable, confirm modification permissions
- **API Call Limit Exceeded**: TencentCloud API has call frequency limits, reduce request frequency

### Common Error Codes

| Error Code | Description | Solution |
| :--------- | :---------- | :------- |
| AuthFailure.SignatureExpire | Signature expired | Check system time |
| AuthFailure.SecretIdNotFound | SecretId not found | Check key configuration |
| ResourceNotFound.NoDataOfRecord | Record does not exist | Check record settings |
| LimitExceeded.RequestLimitExceeded | Request frequency exceeded | Reduce request frequency |

## API Limitations

- **Request Frequency**: Default 20 requests per second
- **Single Query**: Maximum 3000 records returned
- **Domain Count**: Limited by plan type

## Support and Resources

- [TencentCloud DNSPod Product Documentation](https://cloud.tencent.com/document/product/1427)
- [TencentCloud DNSPod V3 API Documentation](https://cloud.tencent.com/document/api/1427)
- [TencentCloud DNSPod Console](https://console.cloud.tencent.com/dnspod)
- [TencentCloud Technical Support](https://cloud.tencent.com/online-service)

> **Recommendation**: It is recommended to use sub-account API keys and grant only necessary DNSPod permissions to improve security. Regularly rotate API keys to ensure account security.
