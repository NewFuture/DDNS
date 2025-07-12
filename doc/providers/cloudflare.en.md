# Cloudflare DNS Configuration Guide

## Overview

Cloudflare is a leading global CDN and network security service provider. This DDNS project supports automatic DNS record management through the Cloudflare API.

## Authentication Methods

### API Token Authentication (Recommended)

```json
{
    "dns": "cloudflare",
    "token": "your_api_token_here"
}
```

### API Key Authentication

```json
{
    "id": "your_email@example.com",
    "token": "your_global_api_key",
    "dns": "cloudflare",
}
```

## Getting Authentication Credentials

### API Token

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Go to "My Profile" → "API Tokens"
3. Create custom token with permissions:
   - **Zone.Zone Read**, **Zone.DNS Read**, **Zone.DNS Edit**
4. Select domains to manage

### Global API Key

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Go to "My Profile" → "API Tokens"
3. View "Global API Key"

## Permission Requirements

- **API Token**: Grant the following minimum permissions for secure operation:
  - `Zone.Zone Read` – list and retrieve zone information
  - `Zone.DNS Read` – list existing DNS records
  - `Zone.DNS Edit` – create and update DNS records
- **Global API Key**: Has full permissions; use only when API Token is not supported and store securely

## Configuration Examples

```json
{
    "dns": "cloudflare",
    "token": "your_api_token_here",
    "ipv4": ["ddns.example.com", "www.example.com"],
    "ipv6": ["ddns.example.com"],
    "index4": ["default"],
    "index6": ["default"],  
    "ttl": 600
}
```

## Optional Parameters

| Parameter | Description         | Type   | Default               |
|-----------|------------------------|--------|-----------------------|
| `ttl`     | DNS record TTL value   | int    | auto (automatic TTL)  |

Cloudflare uses a single global API endpoint, but custom endpoints may be needed in special cases:

- **Enterprise/Private Cloud Deployments**: Configure according to specific deployment environment
- **Proxy/Mirror Services**: Third-party API proxy service addresses

> **Note**: Cloudflare officially recommends using the default global endpoint `https://api.cloudflare.com`, which is automatically optimized through Cloudflare's global network. Custom endpoints are only needed when using enterprise private deployments or third-party proxy services.

## Troubleshooting

### Common Errors

- **"Invalid API token"** - Check token validity and permissions
- **"Zone not found"** - Ensure domain is added to Cloudflare
- **"Record creation failed"** - Check record format and TTL value (60-86400 seconds)

### Debug Mode

```sh
ddns -c config.json --debug
```

## Related Links

- [Cloudflare API Documentation](https://developers.cloudflare.com/api/)
- [Cloudflare Dashboard](https://dash.cloudflare.com/)

> It's recommended to use API Token instead of Global API Key for better security with finer-grained permissions.
