# West.cn Configuration Guide

## Overview

West.cn is a well-known domain service provider in China, offering domain registration, DNS resolution and other services. This DDNS project supports dynamic DNS record management for West.cn.

Official Links:

- Official Website: <https://www.west.cn/>
- API Documentation: <https://console-docs.apipost.cn/preview/bf57a993975b67e0/7b363d9b8808faa2>

> **Note**: 35.cn (三五互联) uses the same API and can use `35` or `35cn` as the provider identifier.

## Authentication Information

West.cn supports two authentication methods:

### 1. Domain Authentication (Recommended)

Authenticate using the domain management password, only requires `token` (apidomainkey).

#### Obtaining Credentials

1. Login to [West.cn Member Center](https://www.west.cn/manager/)
2. Go to "Domain Management" > Select domain > "Management Password"
3. Copy the **APIkey** (32-character MD5 value), which is the MD5 hash of the domain management password

```json
{
    "dns": "west",
    "token": "ec4c66e34561428b2e9ad65048f9bsed"  // Domain APIkey
}
```

### 2. Account Authentication

Authenticate using member account and API password.

#### Obtaining Credentials

1. Login to [West.cn Member Center](https://www.west.cn/manager/)
2. Go to "Account Management" > "API Interface Settings"
3. Set the API password
4. `id` is your member account username
5. `token` is the 32-character MD5 of your API password

```json
{
    "dns": "west",
    "id": "your_username",                      // Member account
    "token": "md5_of_your_api_password"         // MD5 of API password
}
```

## Complete Configuration Examples

### Domain Authentication

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "west",
    "token": "ec4c66e34561428b2e9ad65048f9bsed",
    "index4": ["url:http://api.ipify.cn", "public"],
    "index6": "public",
    "ipv4": ["ddns.example.com"],
    "ipv6": ["ipv6.example.com"],
    "ttl": 900
}
```

### Account Authentication

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "west",
    "id": "your_username",
    "token": "md5_of_your_api_password",
    "index4": ["url:http://api.ipify.cn", "public"],
    "index6": "public",
    "ipv4": ["ddns.example.com"],
    "ipv6": ["ipv6.example.com"],
    "ttl": 900
}
```

### 35.cn Configuration

35.cn uses the same API, just change the `dns` parameter or use the `endpoint` parameter:

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "35",
    "token": "your_apidomainkey",
    "endpoint": "https://api.35.cn/API/v2/domain/dns/",
    "ipv4": ["ddns.example.com"]
}
```

### Parameter Description

| Parameter | Description | Type | Range/Options | Default | Parameter Type |
| :-------: | :---------- | :--- | :------------ | :------ | :------------- |
| dns | Provider identifier | String | `west`, `west_cn`, `35`, `35cn` | None | Provider Parameter |
| id | Member account | String | Required for account auth | None | Provider Parameter |
| token | Auth credential | String | apidomainkey or MD5(API password) | None | Provider Parameter |
| endpoint | API endpoint | String | Custom API endpoint | West.cn | Provider Parameter |
| index4 | IPv4 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| index6 | IPv6 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| ipv4 | IPv4 domains | Array | Domain list | None | Common Config |
| ipv6 | IPv6 domains | Array | Domain list | None | Common Config |
| line | Resolution line | String | [Reference below](#line) | Default | Provider Parameter |
| ttl | TTL time | Integer (seconds) | 60 - 86400 | `900` | Provider Parameter |
| proxy | Proxy settings | Array | [Reference](../config/json.en.md#proxy) | None | Common Network |
| ssl | SSL verification | Boolean/String | `"auto"`, `true`, `false` | `auto` | Common Network |
| cache | Cache settings | Boolean/String | `true`, `false`, `filepath` | `true` | Common Config |
| log | Log configuration | Object | [Reference](../config/json.en.md#log) | None | Common Config |

> **Parameter Type Description**:
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers
> - **Provider Parameter**: Supported by current provider, values related to current provider

### line

The `line` parameter specifies DNS resolution lines. West.cn supported lines:

| Line Name | Line Code | Description |
| :-------- | :-------- | :---------- |
| 默认 | (empty) | Default line |
| 电信 | LTEL | China Telecom |
| 联通 | LCNC | China Unicom |
| 移动 | LMOB | China Mobile |
| 教育网 | LEDU | China Education Network |
| 搜索引擎 | LSEO | Search Engine |
| 境外 | LFOR | Overseas |

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Authentication Failed**: Check if APIkey or account password is correct, confirm token is a 32-character MD5 value
- **Domain Not Found**: Ensure domain is under your West.cn account, check configuration spelling
- **Record Creation Failed**: Check if subdomain has conflicting records, verify TTL settings are reasonable
- **Request Rate Limit**: Reduce request frequency

## Support and Resources

- [West.cn Official Website](https://www.west.cn/)
- [West.cn Member Center](https://www.west.cn/manager/)
- [API Documentation](https://console-docs.apipost.cn/preview/bf57a993975b67e0/7b363d9b8808faa2)
- [35.cn Official Website](https://www.35.cn/)

> **Recommendation**: Use domain authentication (apidomainkey) for simpler and more secure configuration.
