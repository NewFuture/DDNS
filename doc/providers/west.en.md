# West.cn Configuration Guide

## Overview

West.cn (西部数码) is a well-known domain registrar and DNS service provider in China, offering stable and reliable DNS resolution services. This DDNS project supports West.cn's dynamic DNS API for automatic domain IP address updates.

Official Links:

- Official Website: <https://www.west.cn/>
- Management Console: <https://www.west.cn/web/mi/>
- API Documentation: <https://www.west.cn/CustomerCenter/doc/domain_v2.html>

## Authentication

West.cn supports two authentication methods. Choose the one that fits your needs:

### 1. Domain-Level Authentication (Recommended for Single Domain)

Domain-level authentication is more secure and suitable for individual users or single domain DDNS updates.

#### Obtaining Authentication Credentials

1. Log in to [West.cn Management Console](https://www.west.cn/web/mi/)
2. Go to "Domain Management" and find your domain
3. Click on the domain to enter the details page
4. Find "API Key" or "Domain Key" option on the domain details page
5. Copy the domain key (apidomainkey)

#### Configuration Example

```json
{
    "dns": "west",
    "id": "example.com",           // Your main domain
    "token": "YOUR_API_DOMAIN_KEY" // Domain key
}
```

### 2. User-Level Authentication (For Resellers, Multi-Domain Support)

User-level authentication is suitable for resellers or users who need to manage multiple domains.

#### Obtaining Authentication Credentials

1. Log in to [West.cn Management Console](https://www.west.cn/web/mi/)
2. Go to "User Center" > "API Interface" or "API Configuration"
3. Get your username and API Key
4. Ensure your account has API permissions enabled (usually enabled by default for reseller accounts)

#### Configuration Example

```json
{
    "dns": "west",
    "id": "your_username",    // West.cn username
    "token": "YOUR_API_KEY"   // User-level API key
}
```

## Complete Configuration Examples

### Domain-Level Authentication

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "west",
    "id": "example.com",
    "token": "your_api_domain_key_here",
    "index4": ["url:http://api.ipify.cn", "public"],
    "index6": "public",
    "ipv4": ["ddns.example.com", "www.example.com"],
    "ipv6": ["ipv6.example.com"],
    "ttl": 600
}
```

### User-Level Authentication

```json
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "west",
    "id": "your_username",
    "token": "your_api_key_here",
    "index4": ["default"],
    "ipv4": ["ddns.example.com", "www.example.com"],
    "ttl": 600
}
```

## Parameter Description

| Parameter | Description | Type | Values/Options | Default | Type Category |
| :-------: | :---------- | :--- | :------------- | :------ | :------------ |
| dns       | Provider identifier | String | `west`, `west_cn`, `westcn` | None | Provider param |
| id        | Authentication ID | String | Domain or username | None | Provider param |
| token     | Authentication key | String | Domain key or user API key | None | Provider param |
| index4    | IPv4 source | Array | [Reference](../config/json.md#ipv4-ipv6) | `default` | Common config |
| index6    | IPv6 source | Array | [Reference](../config/json.md#ipv4-ipv6) | `default` | Common config |
| ipv4      | IPv4 domains | Array | Domain list | None | Common config |
| ipv6      | IPv6 domains | Array | Domain list | None | Common config |
| ttl       | TTL time | Integer (seconds) | Not supported via DDNS API | None | Provider param |
| proxy     | Proxy settings | Array | [Reference](../config/json.md#proxy) | None | Common network |
| ssl       | SSL verification | Boolean/String | `"auto"`, `true`, `false` | `auto` | Common network |
| cache     | Cache settings | Boolean/String | `true`, `false`, `filepath` | `true` | Common config |
| log       | Log configuration | Object | [Reference](../config/json.md#log) | None | Common config |

> **Parameter Type Categories**:
>
> - **Common config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common network**: Network settings applicable to all supported DNS providers
> - **Provider param**: Parameters specific to this provider

### Supported Record Types

West.cn DDNS API supports the following record types:

- **A Record**: IPv4 address resolution
- **AAAA Record**: IPv6 address resolution

> **Note**: West.cn DDNS API does not support CNAME, MX, or other record types. For managing other record types, please use the West.cn management console.

### TTL Configuration

West.cn DDNS API does not support setting TTL values through the API. To modify TTL, please log in to the West.cn management console and configure it manually.

## Usage Instructions

### Automatic Authentication Detection

The DDNS tool automatically detects the authentication method based on the `id` parameter:

- **Domain-level auth**: When `id` contains `.` (dot) or `@` symbol, it's recognized as domain-level authentication
- **User-level auth**: When `id` is a simple username (without `.` or `@`), it's recognized as user-level authentication

### API Behavior

West.cn DDNS API uses the `dnsrec.update` endpoint with the following characteristics:

1. **Auto-create or update**: If the record doesn't exist, it will be created automatically; if it exists, the record value will be updated
2. **Record replacement**: Updates delete the old record with the same name and create a new one
3. **Single operation**: Each API call updates only one record
4. **Encoding requirement**: API uses GB2312/GBK encoding

### Best Practices

1. **First-time use**: It's recommended to manually create a DNS record in the West.cn console first, then update it using the DDNS tool
2. **Update frequency**: Avoid frequent API calls; recommended update interval is no less than 5 minutes
3. **Domain-level auth**: For individual users and single domains, domain-level authentication is recommended for better security
4. **User-level auth**: For resellers managing multiple domains, user-level authentication is more convenient

## Troubleshooting

### Common Issues

#### 1. API Error: "Insufficient Permissions" or "Authentication Failed"

**Possible Causes**:
- Incorrect domain key or API key
- API permissions not enabled (user-level auth)
- Domain not under current account

**Solutions**:
- Check if `id` and `token` configurations are correct
- Confirm the domain is managed under the current account
- Reseller users need to confirm API permissions are enabled

#### 2. API Error: "Invalid Domain Format"

**Possible Causes**:
- Incorrect domain format in `id` configuration
- Main domain doesn't match the actual domain

**Solutions**:
- For domain-level auth, `id` should be the main domain (e.g., `example.com`), not the full domain (e.g., `www.example.com`)
- Check domain spelling is correct

#### 3. Record Updated Successfully But Not Taking Effect

**Possible Causes**:
- DNS cache not refreshed
- DNS server synchronization delay

**Solutions**:
- Wait for DNS cache to expire (usually a few minutes to hours)
- Use `nslookup` or `dig` command to check DNS resolution results
- Try clearing local DNS cache

#### 4. Unsupported Record Type

**Possible Causes**:
- DDNS API only supports A and AAAA records

**Solutions**:
- Ensure `record_type` parameter is `A` or `AAAA`
- Other record types need to be configured manually in the console

### Debugging Tips

1. **View logs**: Run with `--log-level DEBUG` parameter to see detailed logs
2. **Test API**: Use curl command to test if the API is working properly
3. **Contact support**: If you encounter unsolvable problems, contact West.cn technical support

## Technical Support

For more help, please visit:

- West.cn Help Center: <https://www.west.cn/docs/>
- West.cn API Documentation: <https://www.west.cn/CustomerCenter/doc/domain_v2.html>
- Technical Support Email: 58851879@west.cn

## Related Links

- [DDNS JSON Configuration Documentation](../config/json.md)
- [DDNS CLI Configuration Documentation](../config/cli.md)
- [Environment Variable Configuration Documentation](../config/env.md)
- [Provider List](README.en.md)
