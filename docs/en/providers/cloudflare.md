# Cloudflare DNS Configuration Guide

## Overview

Cloudflare is a leading global CDN and network security service provider, offering authoritative DNS resolution services that support dynamic DNS record creation and updates. This DDNS project performs automatic DNS record management through the Cloudflare API.

Official Links:

- Official Website: <https://www.cloudflare.com/>
- Service Console: <https://dash.cloudflare.com/>

## Authentication Information

### 1. API Token Authentication (Recommended)

API Token method is more secure and supports fine-grained permission control, which is Cloudflare's recommended integration method.

#### Obtaining Authentication Information

1. Login to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Go to "My Profile" > "API Tokens" or visit <https://dash.cloudflare.com/profile/api-tokens>
3. Click "Create Token" and select "Custom token" template
4. Configure permissions:
   - **Zone:Read** (Zone:Read)
   - **DNS:Edit** (Zone:DNS:Edit)
5. Select the domain zones to manage
6. Copy the generated **API Token**. The token is only displayed once, please save it securely

```jsonc
{
    "dns": "cloudflare",
    "token": "your_cloudflare_api_token"  // Cloudflare API Token, leave ID empty or omit
}
```

### 2. Global API Key Authentication (Not Recommended)

Uses Cloudflare account email and Global API Key, with excessive permissions and **lower security**, only recommended for special scenarios.

#### Obtaining Global API Key

1. Login to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Go to "My Profile" > "API Tokens"
3. View "Global API Key" and copy

```jsonc
{
    "dns": "cloudflare",
    "id": "your-email@example.com",    // Cloudflare account email
    "token": "your_global_api_key"     // Cloudflare Global API Key
}
```

## Permission Requirements

Ensure that the Cloudflare account being used has the following permissions:

### API Token Permissions

- **Zone:Read**: Zone read permission for listing and retrieving domain zone information
- **Zone:DNS:Edit**: DNS edit permission for creating, updating, and deleting DNS records

### Global API Key Permissions

- **Full Access**: Complete control over all resources under the account

You can view and configure permissions in [Cloudflare API Token Management](https://dash.cloudflare.com/profile/api-tokens).

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "cloudflare",                // Current provider
    "token": "your_cloudflare_api_token", // Cloudflare API Token
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 domains
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 domains
    "ttl": 300,                             // DNS record TTL (seconds)
    "proxied": false                        // Whether to enable Cloudflare proxy
}
```

### Parameter Description

| Parameter | Description | Type | Range/Options | Default | Parameter Type |
| :-------: | :---------- | :--- | :------------ | :------ | :------------- |
| dns | Provider identifier | String | `cloudflare` | None | Provider Parameter |
| id | Authentication email | String | Cloudflare account email (Global API Key only) | None | Provider Parameter |
| token | Authentication key | String | Cloudflare API Token or Global API Key | None | Provider Parameter |
| index4 | IPv4 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| index6 | IPv6 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| ipv4 | IPv4 domains | Array | Domain list | None | Common Config |
| ipv6 | IPv6 domains | Array | Domain list | None | Common Config |
| ttl | TTL time | Integer (seconds) | [Reference below](#ttl) | `300/auto` | Provider Parameter |
| proxied | Proxy status | Boolean | `true`, `false` | None | Provider Parameter |
| proxy | Proxy settings | Array | [Reference](../config/json.en.md#proxy) | None | Common Network |
| ssl | SSL verification | Boolean/String | `"auto"`, `true`, `false` | `auto` | Common Network |
| cache | Cache settings | Boolean/String | `true`, `false`, `filepath` | `true` | Common Config |
| log | Log configuration | Object | [Reference](../config/json.en.md#log) | None | Common Config |

> **Parameter Type Description**:
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers
> - **Provider Parameter**: Supported by current provider, values related to current provider

### proxied

The `proxied` parameter controls whether DNS records are proxied through Cloudflare. This is a Cloudflare-specific feature used to enable or disable its CDN and security protection features.

#### Record Query Matching Logic

When the `proxied` parameter is configured, DDNS queries existing DNS records with the following priority:

1. **Priority: Use `proxied` filter**: First attempt to query records matching the specified `proxied` status
2. **Fallback: Query without filter**: If the query with `proxied` filter finds no records, automatically retry the query without the `proxied` filter

This fallback mechanism ensures correct handling of the following scenarios:

- **Scenario 1**: Configuration changed from `"proxied": true` to `"proxied": false`
  - Even if the original record has `proxied=true`, the system can still find and update it
  
- **Scenario 2**: Configuration changed from `"proxied": false` to `"proxied": true`
  - Even if the original record has `proxied=false`, the system can still find and update it

- **Scenario 3**: Configuration newly adds `"proxied": true/false` parameter
  - Can find records created without `proxied` filter and update them

> **Note**: If a record is found with the `proxied` filter during the query, the fallback query will not be executed and the matched record will be used directly.

### ttl

The `ttl` parameter specifies the Time To Live (TTL) of DNS records in seconds. Cloudflare's TTL settings vary depending on whether the record has proxy enabled.

#### Proxied Records

All proxied records have TTL defaulted to **Auto**, fixed at **300 seconds** (5 minutes), and this value **cannot be edited**.

Since only records used for IP address resolution can be proxied, this setting ensures that potential changes to the assigned anycast IP address will take effect quickly, as recursive resolvers will not cache them for longer than 300 seconds.

> **Note**: It may take longer than 5 minutes for you to actually experience record changes, as your local DNS cache may take longer to update.

#### Unproxied Records

For DNS-only records, you can choose the following TTL ranges:

| Plan Type | Supported TTL Range (seconds) | Description |
| --------- | :---------------------------: | :---------- |
| Free/Pro/Business | 60 - 86400 | Minimum TTL is 1 minute |
| Enterprise | 30 - 86400 | Minimum TTL is 30 seconds |

TTL set to **Auto** is fixed at **300 seconds** (5 minutes).

> Reference: [Cloudflare TTL Documentation](https://developers.cloudflare.com/dns/manage-dns-records/reference/ttl/)

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Invalid API token**: Check if API Token is correct, confirm permission configuration
- **Zone not found**: Ensure domain has been added to Cloudflare account, domain is in active state
- **Record creation failed**: Check record format and TTL values, confirm permission settings
- **Rate limit exceeded**: API call frequency exceeded, reduce request frequency

## Support and Resources

- [Cloudflare Developer Documentation](https://developers.cloudflare.com/)
- [Cloudflare API Reference](https://developers.cloudflare.com/api/)
- [Cloudflare Dashboard](https://dash.cloudflare.com/)
- [Cloudflare Community Support](https://community.cloudflare.com/)

> **Recommendation**: Use API Token method for fine-grained permission control and improved account security, avoid using Global API Key.
