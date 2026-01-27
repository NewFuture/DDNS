# ClouDNS Configuration Guide

## Overview

ClouDNS is a global DNS hosting service provider that offers free and premium DNS resolution services, supporting dynamic DNS record creation and updates. This DDNS project performs automatic DNS record management through the ClouDNS API.

Official Links:

- Official Website: <https://www.cloudns.net/>
- Control Panel: <https://www.cloudns.net/dns-zones/>
- API Documentation: <https://www.cloudns.net/wiki/>

## Authentication Information

ClouDNS uses **Auth-ID** and **Auth-Password** for API authentication.

### Obtaining Authentication Information

1. Login to [ClouDNS Control Panel](https://www.cloudns.net/login/)
2. Go to "API" settings page or visit <https://www.cloudns.net/api-settings/>
3. If API access is not yet enabled, click "Enable API"
4. Copy your **Auth-ID** (usually a numeric ID)
5. Create or view your **Auth-Password** (API password)

> **Security Tip**: For enhanced security, it is recommended to create a sub-account specifically for DDNS API access and grant only necessary DNS management permissions.

```jsonc
{
    "dns": "cloudns",
    "id": "12345",                    // ClouDNS Auth-ID
    "token": "your_auth_password"     // ClouDNS Auth-Password
}
```

## Permission Requirements

Ensure that the ClouDNS account being used has the following permissions:

- **DNS Zone Management**: Ability to list and access DNS zones
- **DNS Record Management**: Ability to create, read, and update DNS records

If using a sub-account, assign the appropriate permissions to the sub-account from the main account.

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.1.json", // Format validation
    "dns": "cloudns",                       // Current provider
    "id": "12345",                          // ClouDNS Auth-ID
    "token": "your_auth_password",          // ClouDNS Auth-Password
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.example.com"],           // IPv4 domains
    "ipv6": ["ddns.example.com", "ipv6.example.com"], // IPv6 domains
    "ttl": 60                               // DNS record TTL (seconds)
}
```

### Parameter Description

| Parameter | Description | Type | Range/Options | Default | Parameter Type |
| :-------: | :---------- | :--- | :------------ | :------ | :------------- |
| dns | Provider identifier | String | `cloudns` | None | Provider Parameter |
| id | Auth-ID | String/Number | ClouDNS Auth-ID | None | Provider Parameter |
| token | Auth-Password | String | ClouDNS Auth-Password | None | Provider Parameter |
| index4 | IPv4 source | Array | [Reference](../config/json.md#ipv4-ipv6) | `default` | Common Config |
| index6 | IPv6 source | Array | [Reference](../config/json.md#ipv4-ipv6) | `default` | Common Config |
| ipv4 | IPv4 domains | Array | Domain list | None | Common Config |
| ipv6 | IPv6 domains | Array | Domain list | None | Common Config |
| ttl | TTL time | Integer (seconds) | 60 - 2592000 (30 days) | 60 | Provider Parameter |
| proxy | Proxy settings | Array | [Reference](../config/json.md#proxy) | None | Common Network |
| ssl | SSL verification | Boolean/String | `"auto"`, `true`, `false` | `auto` | Common Network |
| cache | Cache settings | Boolean/String | `true`, `false`, `filepath` | `true` | Common Config |
| log | Log configuration | Object | [Reference](../config/json.md#log) | None | Common Config |

> **Parameter Type Description**:
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers
> - **Provider Parameter**: Supported by current provider, values related to current provider

### TTL

The `ttl` parameter specifies the Time To Live (TTL) of DNS records in seconds.

ClouDNS supported TTL ranges:

| Plan Type | Supported TTL Range (seconds) | Description |
| --------- | :---------------------------: | :---------- |
| Free | 60 - 86400 | Minimum 60 seconds, maximum 1 day |
| Premium | 60 - 2592000 | Minimum 60 seconds, maximum 30 days |

Default TTL is **60 seconds** (minimum value), suitable for fast DDNS record updates.

> Reference: [ClouDNS TTL Documentation](https://www.cloudns.net/wiki/article/12/)

### Root Domain Records

ClouDNS uses empty string `""` or `"@"` to represent root domain records. DDNS automatically handles both representations.

- To update records for `example.com`, simply use the domain `example.com`
- To update records for `www.example.com`, use the domain `www.example.com`

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Invalid authentication**: Check if Auth-ID and Auth-Password are correct
- **Zone not found**: Ensure domain has been added to ClouDNS account, domain is in active state
- **Record creation failed**: Check record format and TTL values, confirm account permissions
- **API limit exceeded**: API call frequency exceeded, reduce request frequency or upgrade plan

### Free Plan Limitations

ClouDNS free plan has the following limitations:

- Maximum 4 DNS zones per account
- Maximum 50 records per zone
- API request frequency limits (refer to official documentation for specific limits)

For more resources, consider upgrading to a premium plan.

## Support and Resources

- [ClouDNS Official Website](https://www.cloudns.net/)
- [ClouDNS API Documentation](https://www.cloudns.net/wiki/)
- [ClouDNS Control Panel](https://www.cloudns.net/dns-zones/)
- [ClouDNS Support Center](https://www.cloudns.net/support/)

> **Recommendation**: Use a sub-account for API access to enhance account security. Regularly check API access logs to monitor for unusual activity.
