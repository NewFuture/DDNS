# NameSilo DNS Configuration Guide

## Overview

NameSilo is a US-based domain registrar and DNS service provider that offers reliable domain management and DNS resolution services. This DDNS project supports automatic DNS record management through the NameSilo API.

## Authentication Method

### API Key Authentication

NameSilo uses API Key for authentication, which is the only available authentication method.

```json
{
    "dns": "namesilo",
    "token": "your_api_key_here"
}
```

## Getting Authentication Information

### API Key

1. Log in to [NameSilo Console](https://www.namesilo.com/account_home.php)
2. Go to "Account Options" → "API Manager" or visit <https://www.namesilo.com/account/api-manager>
3. Generate a new API Key
4. Record the generated API Key and keep it secure

> **Note**: The API Key has full account permissions. Please keep it secure and do not share it with others.

## Permission Requirements

NameSilo API Key has the following permissions:
- **Domain Management**: View and manage all domains in your account
- **DNS Record Management**: Create, read, update, and delete DNS records
- **Domain Information Query**: Get domain registration information and status

## Configuration Examples

### Basic Configuration

```json
{
    "dns": "namesilo",
    "token": "c40031261ee449dda629d2df14e9cb63",
    "ipv4": ["ddns.example.com", "www.example.com"],
    "index4": ["default"]
}
```

### Complete Configuration Example

```json
{
    "dns": "namesilo",
    "token": "c40031261ee449dda629d2df14e9cb63",
    "index4": ["default"],
    "index6": ["default"],
    "ipv4": ["ddns.example.com", "www.example.com"],
    "ipv6": ["ddns.example.com"],
    "ttl": 3600
}
```

## Optional Parameters

| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| `ttl` | TTL value for DNS records (seconds) | int | 7207 |

> **Note**: NameSilo TTL minimum value is 300 seconds (5 minutes), maximum value is 2592000 seconds (30 days).

### Custom API Endpoint

In special circumstances, you may need to customize the endpoint:

```json
{
    "endpoint": "https://www.namesilo.com"
}
```

> **Note**: The official NameSilo API endpoint is `https://www.namesilo.com`. It's not recommended to modify this unless using a proxy service.

## Supported Record Types

NameSilo API supports the following DNS record types:
- **A Record**: IPv4 address resolution
- **AAAA Record**: IPv6 address resolution
- **CNAME Record**: Domain alias
- **MX Record**: Mail exchange record
- **TXT Record**: Text record
- **NS Record**: Name server record
- **SRV Record**: Service record

## Troubleshooting

### Common Errors

#### "Invalid API key"
- Check if the API Key is correct
- Ensure the API Key is not disabled
- Verify account status is normal

#### "Domain not found"
- Confirm the domain is added to your NameSilo account
- Check if the domain spelling is correct
- Verify the domain status is Active

#### "Record creation failed"
- Check if the subdomain format is correct
- Ensure TTL value is within allowed range (300-2592000 seconds)
- Verify there are no conflicting records

#### "API request limit exceeded"
- NameSilo has API call rate limits
- Increase update intervals appropriately
- Avoid concurrent API calls

### Debug Mode

Enable debug logging to see detailed information:

```sh
ddns -c config.json --debug
```

### API Response Codes

- **300**: Success
- **110**: Domain does not exist
- **280**: Invalid domain format
- **200**: Invalid API Key

## API Limitations

- **Request Rate**: Recommended maximum 60 requests per minute
- **Domain Count**: Limited based on account type
- **Record Count**: Maximum 100 DNS records per domain

## Related Links

- [NameSilo API Documentation](https://www.namesilo.com/api-reference)
- [NameSilo Console](https://www.namesilo.com/account_home.php)
- [NameSilo API Manager](https://www.namesilo.com/account/api-manager)

> **Security Tip**: It's recommended to regularly rotate API Keys and monitor account activity logs to ensure secure API usage.

> **Important Note**: The NameSilo provider implementation is pending verification. Please test thoroughly before using in production environments.