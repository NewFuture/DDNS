# Cloudflare DNS Configuration Guide

## Overview

Cloudflare is a leading global CDN and network security service provider. This DDNS project supports automatic DNS record management through the Cloudflare API.

## Authentication Methods

### API Token Authentication (Recommended)

```json
{
    "dns": "cloudflare",
    "token": "your_api_token_here",
    "ipv4": ["ddns.example.com"]
}
```

### API Key Authentication

```json
{
    "id": "your_email@example.com",
    "token": "your_global_api_key",
    "dns": "cloudflare",
    "ipv4": ["ddns.example.com"]
}
```

## Getting Authentication Credentials

### API Token

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Go to "My Profile" → "API Tokens"
3. Create custom token with permissions:
   - **Zone:Read** and **DNS:Edit**
4. Select domains to manage

### Global API Key

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Go to "My Profile" → "API Tokens"
3. View "Global API Key"

## Configuration Examples

### Basic Configuration

```json
{
    "dns": "cloudflare",
    "token": "your_api_token_here",
    "ipv4": ["ddns.example.com", "www.example.com"],
    "ipv6": ["ddns.example.com"]
}
```

### Advanced Configuration

```json
{
    "dns": "cloudflare",
    "token": "your_api_token_here",
    "ipv4": ["ddns.example.com"],
    "ttl": 300,
    "comment": "Dynamic DNS update"
}
```

## Optional Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ttl` | DNS record TTL value | 300 |
| `comment` | DNS record comment | "DDNS" |

## Troubleshooting

### Common Errors

- **"Invalid API token"** - Check token validity and permissions
- **"Zone not found"** - Ensure domain is added to Cloudflare
- **"Record creation failed"** - Check record format and TTL value (60-86400 seconds)

### Debug Mode

```json
{
    "dns": "cloudflare",
    "token": "your_api_token_here",
    "debug": true,
    "ipv4": ["ddns.example.com"]
}
```

## Resources

- [Cloudflare API Documentation](https://developers.cloudflare.com/api/)
- [Cloudflare Dashboard](https://dash.cloudflare.com/)

> It's recommended to use API Token instead of Global API Key for better security with finer-grained permissions.
