# Name.com DNS Configuration Guide

## Overview

Name.com is a well-known domain registrar and DNS service provider, offering a complete DNS management API (Core API) that supports dynamic DNS record creation and updates. This DDNS project performs automatic DNS record management through the Name.com Core API.

Official Links:

- Official Website: <https://www.name.com/>
- Service Console: <https://www.name.com/account>
- API Documentation: <https://docs.name.com/>

## Authentication Information

The Name.com API uses HTTP Basic authentication, requiring a username and API Token.

### Obtaining API Token

1. Login to your [Name.com account](https://www.name.com/account)
2. Click on your username in the top right corner, go to "Account Settings"
3. Find "API Token" in the left menu or visit <https://www.name.com/account/settings/api>
4. Click "Generate Token" to create a new API Token
5. Copy and save the generated **API Token**. The token is only displayed once, please save it securely

> **Note**: If your account has two-factor authentication (2FA) enabled, you need to enable API access in your account settings first.

```json
{
    "dns": "namecom",
    "id": "your_username",           // Name.com account username
    "token": "your_api_token"        // Name.com API Token
}
```

## Permission Requirements

Ensure that the Name.com account being used has the following permissions:

- **Domain Management Permission**: Full management permission for the target domain is required
- **API Access Permission**: The account must have API access enabled

You can view and configure permissions in [Name.com Account Settings](https://www.name.com/account/settings).

## Complete Configuration Example

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "namecom",                   // Current provider
    "id": "your_username",              // Name.com account username
    "token": "your_api_token",          // Name.com API Token
    "index4": ["url:http://api.ipify.cn", "public"],  // IPv4 address source
    "index6": "public",                 // IPv6 address source
    "ipv4": ["ddns.example.com"],       // IPv4 domains
    "ipv6": ["ddns.example.com", "ipv6.example.com"],  // IPv6 domains
    "ttl": 300                          // DNS record TTL (seconds)
}
```

### Parameter Description

| Parameter | Description | Type | Range/Options | Default | Parameter Type |
| :-------: | :---------- | :--- | :------------ | :------ | :------------- |
| dns | Provider identifier | String | `namecom`, `name.com`, `name_com` | None | Provider Parameter |
| id | Account username | String | Name.com account username | None | Provider Parameter |
| token | API Token | String | Name.com API Token | None | Provider Parameter |
| index4 | IPv4 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| index6 | IPv6 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| ipv4 | IPv4 domains | Array | Domain list | None | Common Config |
| ipv6 | IPv6 domains | Array | Domain list | None | Common Config |
| ttl | TTL time | Integer (seconds) | Minimum 300 seconds | 300 | Provider Parameter |
| proxy | Proxy settings | Array | [Reference](../config/json.en.md#proxy) | None | Common Network |
| ssl | SSL verification | Boolean/String | `"auto"`, `true`, `false` | `auto` | Common Network |
| cache | Cache settings | Boolean/String | `true`, `false`, `filepath` | `true` | Common Config |
| log | Log configuration | Object | [Reference](../config/json.en.md#log) | None | Common Config |

> **Parameter Type Description**:
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers
> - **Provider Parameter**: Supported by current provider, values related to current provider

### TTL Notes

The Name.com API requires a minimum TTL of **300 seconds** (5 minutes). If the configured TTL is less than 300 seconds, it will be automatically adjusted to 300 seconds.

### Test Environment

Name.com provides a sandbox testing environment for API development and testing:

- **Sandbox API URL**: `https://api.dev.name.com`
- **Sandbox Username**: Append `-test` to your normal username (e.g., `username-test`)
- **Sandbox Token**: Use a sandbox environment-specific API Token

You can configure the sandbox environment using the `endpoint` parameter:

```json
{
    "dns": "namecom",
    "id": "username-test",
    "token": "sandbox_api_token",
    "endpoint": "https://api.dev.name.com",
    "ipv4": ["test.example.com"]
}
```

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Invalid credentials**: Check if username and API Token are correct
- **Domain not found**: Ensure domain has been added to Name.com account and you have management permissions
- **Record creation failed**: Check record format and TTL values, confirm permission settings
- **2FA required**: If two-factor authentication is enabled, you need to enable API access in account settings
- **Rate limit exceeded**: API call frequency exceeded (max 20 requests/sec, 3000 requests/hour), reduce request frequency

## Support and Resources

- [Name.com Official Website](https://www.name.com/)
- [Name.com Core API Documentation](https://docs.name.com/)
- [Name.com Account Management](https://www.name.com/account)
- [Name.com Support Center](https://www.name.com/support)

> **Tip**: Please keep your API Token secure and avoid disclosure. If you suspect your Token has been compromised, regenerate it immediately in your account settings.
