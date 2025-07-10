# DNS.COM Configuration Guide

## Overview

DNS.COM (formerly dns.com, now 51dns.com) is a Chinese domain name resolution service provider. This document describes how to configure DDNS to use DNS.COM's API for dynamic DNS updates.

> ⚠️ **Notice**: DNS.COM Provider is currently in **pending verification** status, lacking sufficient real-world testing. It is recommended to thoroughly test before using in production environments.

## Authentication Method

### API Key + Secret Key

DNS.COM uses API Key and Secret Key for API authentication, which is the official recommended authentication method.

#### Obtaining API Credentials

1. Log into [DNS.COM Console](https://www.51dns.com/)
2. Navigate to "API Management" page
3. Create new API key
4. Record the **API Key** and **Secret Key**, please keep them safe

```json
{
    "dns": "dnscom",
    "id": "your-api-key",
    "token": "your-secret-key"
}
```

- `id`: DNS.COM API Key
- `token`: DNS.COM Secret Key
- `dns`: Fixed as `"dnscom"`

## Complete Configuration Example

```json
{
    "id": "your-api-key",
    "token": "your-secret-key",
    "dns": "dnscom",
    "index4": ["public"],
    "index6": ["public"],
    "ipv4": ["home.example.com"],
    "ipv6": ["home.example.com", "nas.example.com"],
    "line": "1",
    "ttl": 600
}
```

## Optional Parameters

| Parameter | Description | Type | Range/Examples | Default |
|-----------|-------------|------|----------------|---------|
| ttl | TTL (Time to Live) | int | 60-86400 (seconds) | auto |
| line | Resolution line ID | str | "1", "2", "3", "4", "5", "6" | auto |

> **Note**: Values supported for `ttl` and `line` may vary depending on your service plan.

DNS.COM supports multiple resolution lines. You can choose the optimal line based on your network environment:

| Line ID | Line Name | Description |
|---------|-----------|-------------|
| `1` | Default | Global default line |
| `2` | China Telecom | Telecom network optimization |
| `3` | China Unicom | Unicom network optimization |
| `4` | China Mobile | Mobile network optimization |
| `5` | Overseas | Overseas access optimization |
| `6` | Education Network | Education network optimization |

## API Limits

- **Request Rate**: Maximum 100 API calls per minute
- **Domain Count**: Free version supports up to 10 domains
- **Record Count**: Maximum 100 records per domain
- **TTL Range**: 60-86400 seconds

## Troubleshooting

| Error Code | Description | Solution |
|------------|-------------|----------|
| `0` | Success | Operation successful |
| `1` | Parameter error | Check request parameters |
| `2` | Authentication failed | Check API credentials |
| `3` | Insufficient permissions | Check API permissions |
| `4` | Record not found | Check domain and record |
| `5` | Domain not found | Check domain configuration |

### Common Issues

#### "Authentication Failed"

- Check if API Key and Secret Key are correct
- Ensure API key status is enabled
- Verify account permissions are sufficient

#### "Domain Not Found"

- Confirm domain is added to DNS.COM
- Check domain spelling is correct
- Verify domain status is normal

#### "Record Operation Failed"

- Check if subdomain has conflicting records
- Ensure TTL value is within reasonable range
- Verify resolution line settings are correct

#### "API Call Limit Exceeded"

- DNS.COM API has QPS limits
- Appropriately increase update intervals

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns --debug
```

## Support & Resources

- [DNS.COM Official Website](https://www.51dns.com/)
- [DNS.COM API Documentation](https://www.51dns.com/document/api/index.html)
- [Configuration File Format](../json.en.md)
- [Command Line Usage](../cli.en.md)
- [Environment Variables](../env.en.md)

> ⚠️ **Pending Verification**: DNS.COM Provider lacks sufficient real-world testing. It is recommended to thoroughly test before using in production environments. Please report any issues via [GitHub Issues](https://github.com/NewFuture/DDNS/issues).
