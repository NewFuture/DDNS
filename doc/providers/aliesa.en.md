# Alibaba Cloud Edge Security Acceleration (ESA) Configuration Guide

## Overview

Alibaba Cloud Edge Security Acceleration (ESA) is an edge security acceleration service provided by Alibaba Cloud, supporting CDN acceleration and edge security protection. This DDNS project supports ESA DNS record management through Alibaba Cloud AccessKey.

## Authentication

### AccessKey Authentication

ESA API uses the same AccessKey authentication as other Alibaba Cloud services, requiring AccessKey ID and AccessKey Secret.

```json
{
    "id": "your_access_key_id",
    "token": "your_access_key_secret",
    "dns": "aliesa"
}
```

## Complete Configuration Examples

### Basic Configuration

```json
{
    "id": "LTAI4xxx",
    "token": "xxx",
    "dns": "aliesa",
    "ipv4": ["www.example.com", "api.example.com"],
    "ipv6": ["ipv6.example.com"]
}
```

### Advanced Configuration

```json
{
    "id": "LTAI4xxx", 
    "token": "xxx",
    "dns": "aliesa",
    "ipv4": ["www.example.com", "api.example.com"],
    "ipv6": ["ipv6.example.com"],
    "ttl": 300
}
```

## Optional Parameters

| Parameter | Description | Type | Default | Example |
|-----------|-------------|------|---------|---------|
| `ttl` | DNS record TTL value | Integer | 600 | 300 |

## Use Cases

### Dynamic IP CDN Origin

When your NAS or other services act as ESA CDN origin, you can use this DDNS to automatically update origin IP:

```json
{
    "id": "LTAI4xxx",
    "token": "xxx", 
    "dns": "aliesa",
    "ipv4": ["origin.example.com"]
}
```

## Permission Requirements

Ensure the Alibaba Cloud account has the following ESA permissions:

- **ESA Site Query Permission**: Used to query site IDs (`esa:ListSites`)
- **ESA DNS Record Management Permission**: Used to query, create, and update DNS records (`esa:ListRecords`, `esa:CreateRecord`, `esa:UpdateRecord`)

It's recommended to create a dedicated RAM sub-account with only the necessary ESA permissions.

### How to Get Site ID

1. Log in to [Alibaba Cloud ESA Console](https://esa.console.aliyun.com/)
2. Select the corresponding site
3. The site ID can be seen in the URL of the site details page, or use API call `ListSites` to get it

## API Limitations

- **Site Count**: Varies by ESA package
- **DNS Record Count**: Varies by ESA package
- **API Call Frequency**: Follows Alibaba Cloud ESA API limits

## Troubleshooting

### Common Issues

#### "Site not found for domain"

- Check if the domain has been added to ESA service
- Confirm domain format is correct (no protocol prefix)
- Verify AccessKey permissions

#### "Failed to create/update record"

- Check if DNS record type is supported
- Confirm record value format is correct
- Verify TTL value is within allowed range

#### "API call failed"

- Check if AccessKey ID and Secret are correct
- Confirm network connection is normal
- View detailed error logs

### Debug Mode

Enable debug mode to view detailed API interaction information:

```json
{
    "id": "LTAI4xxx",
    "token": "xxx",
    "dns": "aliesa",
    "debug": true,
    "ipv4": ["www.example.com"]
}
```

## Support and Resources

- [Alibaba Cloud ESA Product Documentation](https://help.aliyun.com/product/122312.html)
- [Alibaba Cloud ESA API Documentation](https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-overview)
- [Alibaba Cloud ESA Console](https://esa.console.aliyun.com/)
- [Alibaba Cloud Technical Support](https://selfservice.console.aliyun.com/ticket)

> It's recommended to use RAM sub-accounts with only necessary ESA permissions to improve security. Regularly rotate AccessKeys to ensure account security.
