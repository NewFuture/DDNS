# NameSilo DNS Configuration Guide

## Overview

NameSilo is a well-known US-based domain registrar and DNS service provider that offers reliable domain management and DNS resolution services, supporting dynamic DNS record creation and updates. This DDNS project authenticates through API Key.

> ⚠️ **Important Note**: NameSilo Provider is currently in **verification pending** status, lacking sufficient real-world testing. Please provide feedback through [GitHub Issues](https://github.com/NewFuture/DDNS/issues).

Official Links:

- Official Website: <https://www.namesilo.com/>
- Provider Console: <https://www.namesilo.com/account_home.php>

## Authentication Information

### API Key Authentication

NameSilo uses API Key for authentication, which is the only authentication method.

#### Obtaining Authentication Information

1. Log in to [NameSilo Console](https://www.namesilo.com/account_home.php)
2. Go to "Account Options" → "API Manager" or visit <https://www.namesilo.com/account/api-manager>
3. Generate a new API Key

> **Note**: The API Key has full account permissions. Please keep it secure and do not share it with others.

```jsonc
{
    "dns": "namesilo",
    "token": "your_api_key_here" // NameSilo API Key, no ID required
}
```

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "namesilo",                  // Current provider
    "token": "c40031261ee449dda629d2df14e9cb63", // NameSilo API Key
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 domain
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 domain
    "ttl": 3600                             // DNS record TTL (seconds)
}
```

### Parameter Description

| Parameter | Description      | Type           | Value Range/Options                     | Default   | Parameter Type |
| :-------: | :--------------- | :------------- | :------------------------------------- | :-------- | :------------- |
| dns       | Provider ID      | String         | `namesilo`                             | None      | Provider Param |
| token     | Authentication Key| String        | NameSilo API Key                       | None      | Provider Param |
| index4    | IPv4 Source      | Array          | [Reference](../config/json.en.md#ipv4-ipv6)  | `default` | Common Config  |
| index6    | IPv6 Source      | Array          | [Reference](../config/json.en.md#ipv4-ipv6)  | `default` | Common Config  |
| ipv4      | IPv4 Domain      | Array          | Domain list                            | None      | Common Config  |
| ipv6      | IPv6 Domain      | Array          | Domain list                            | None      | Common Config  |
| ttl       | TTL Time         | Integer (seconds)| 300 ~ 2592000                       | `7200`    | Provider Param |
| proxy     | Proxy Settings   | Array          | [Reference](../config/json.en.md#proxy)      | None      | Common Network |
| ssl       | SSL Verification | Boolean/String | `"auto"`, `true`, `false`              | `auto`    | Common Network |
| cache     | Cache Settings   | Boolean/String | `true`, `false`, `filepath`            | `true`    | Common Config  |
| log       | Log Config       | Object         | [Reference](../config/json.en.md#log)        | None      | Common Config  |

> **Parameter Type Description**:
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers
> - **Provider Param**: Supported by current provider, values related to current provider
>
> **Note**: NameSilo does not support `id` parameter, only uses `token` for authentication.
> **Note**: NameSilo official API endpoint is `https://www.namesilo.com`, it's not recommended to modify unless using a proxy service.

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Authentication Failed**: Check if API Key is correct, confirm API Key is not disabled, verify account status is normal
- **Domain Not Found**: Ensure domain has been added to NameSilo account, check spelling accuracy, confirm domain is in active status
- **Record Creation Failed**: Check subdomain format is correct, TTL value is within allowed range (300-2592000 seconds), verify there are no conflicting records
- **Request Rate Limiting**: NameSilo has API call frequency limits (recommended maximum 60 per minute), reduce request frequency

### API Response Codes

| Response Code | Description        | Solution                |
| :------------ | :----------------- | :---------------------- |
| 300           | Success            | Operation successful    |
| 110           | Domain not found   | Check domain configuration |
| 280           | Invalid domain format | Check domain format   |
| 200           | Invalid API Key    | Check API key           |

## API Limitations

- **Request Rate**: Recommended maximum 60 requests per minute
- **Domain Count**: Limited based on account type
- **Record Count**: Maximum 100 DNS records per domain

## Support and Resources

- [NameSilo Official Website](https://www.namesilo.com/)
- [NameSilo API Documentation](https://www.namesilo.com/api-reference)
- [NameSilo Console](https://www.namesilo.com/account_home.php)
- [NameSilo API Manager](https://www.namesilo.com/account/api-manager)

> ⚠️ **Verification Pending Status**: NameSilo Provider lacks sufficient real-world testing. It is recommended to conduct thorough testing before using in production environments. If you encounter issues, please provide feedback through [GitHub Issues](https://github.com/NewFuture/DDNS/issues).
