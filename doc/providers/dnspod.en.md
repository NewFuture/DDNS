# DNSPod China Configuration Guide

> For Global DNSPod, see [DNSPod Global Configuration Guide](dnspod_com.en.md).

## Overview

DNSPod China (dnspod.cn) is a DNS service provider, widely used in mainland China. This DDNS project supports two authentication methods to connect to DNSPod:

1. **API Token** (Recommended)
2. **Email + Password** (Legacy)
3. AccessKey (Tencent Cloud DNSPod) [Reference](tencentcloud.md)

## Authentication Methods

### 1. API Token (Recommended)

The API Token method is more secure and is the recommended integration method by DNSPod.

#### Obtaining API Token

1. Login to [DNSPod Console](https://console.dnspod.cn/)
2. Go to "User Center" > "API Key" or visit <https://console.dnspod.cn/account/token/token>
3. Click "Create Key", fill in description, select domain management permissions, and complete creation
4. Copy the **ID** (numeric) and **Token** (string). The key is only displayed once, please save it securely

```json
{
    "dns": "dnspod",
    "id": "123456",
    "token": "abcdef1234567890abcdef1234567890"
}
```

- `id`: API Token ID
- `token`: API Token secret
- `dns`: Must be `"dnspod"`

### 2. Email + Password (Legacy)

Uses DNSPod account email and password. Lower security, only recommended for special scenarios.

```json
{
    "id": "your-email@example.com",
    "token": "your-account-password",
    "dns": "dnspod"
}
```

- `id`: DNSPod account email
- `token`: DNSPod account password
- `dns`: Must be `"dnspod"`

## Complete Configuration Example

```json
{
  "id": "123456",
  "token": "abcdef1234567890abcdef1234567890abcdef12",
  "dns": "dnspod",
  "index4": ["public"],
  "index6": ["public"],
  "ipv4": ["home.example.com"],
  "ipv6": ["home.example.com", "nas.example.com"],
  "line": "默认",
  "ttl": 600
}
```

## Optional Parameters

| Parameter | Description               | Type    | Range/Options                             | Default |
|-----------|---------------------------|---------|-------------------------------------------|---------|
| `ttl`     | Time To Live (seconds)    | Integer | 1-604800                                | 600     |
| `line`    | DNS line/route            | String  | "默认"、"电信"、"联通"、"移动" etc. | "默认" |

> **Note**: Supported values for `ttl` and `line` may vary by service plan.

## Troubleshooting

### Common Issues

#### "Authentication Failed"

- Check if API Token or email/password are correct
- Confirm domain management permissions

#### "Domain Not Found"

- Domain has been added to DNSPod account
- Configuration spelling is correct
- Domain is in active state

#### "Record Creation Failed"

- Check if subdomain has conflicting records
- TTL is reasonable
- Has modification permissions

### Debug Mode

Enable debug logging:

```sh
ddns --debug
```

## Support and Resources

- [DNSPod Documentation](https://docs.dnspod.cn/)
- [API Reference](https://docs.dnspod.cn/api/)
- [Tencent Cloud DNSPod (AccessKey)](./tencentcloud.en.md) (DNSPod's AccessKey method)

> It is recommended to use the API Token method for improved security and management convenience.
