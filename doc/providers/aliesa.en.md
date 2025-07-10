# Alibaba Cloud Edge Security Acceleration (ESA) Configuration Guide

## Overview

Alibaba Cloud Edge Security Acceleration (ESA) is an edge security acceleration service provided by Alibaba Cloud, supporting CDN acceleration and edge security protection. This DDNS project supports ESA DNS record management through Alibaba Cloud AccessKey.

## Authentication

### AccessKey Authentication

ESA API uses the same AccessKey authentication as other [Alibaba Cloud services](alidns.en.md), requiring AccessKey ID and AccessKey Secret.

```json
{
    "id": "your_access_key_id",
    "token": "your_access_key_secret",
    "dns": "aliesa"
}
```

## Permission Requirements

Ensure the Alibaba Cloud account has the following ESA permissions:

Recommended `AliyunESAFullAccess` includes all the permissions below:

- **ESA Site Query Permission**: Used to query site IDs (`esa:ListSites`)
- **ESA DNS Record Management Permission**: Used to query, create, and update DNS records (`esa:ListRecords`, `esa:CreateRecord`, `esa:UpdateRecord`)

It's recommended to create a dedicated RAM sub-account with only the necessary ESA permissions.

## Complete Configuration Example

```json
{
    "id": "LTAI4xxx",
    "token": "xxx",
    "dns": "aliesa",
    "ipv4": ["www.example.com", "api.example.com"],
    "ipv6": ["www6.example.com"],
    "index4": ["public"],
    "index6": ["public"]
}
```

## Optional Parameters

| Parameter   | Description                   | Type          | Default                            | Example                                 |
|-------------|-------------------------------|---------------|------------------------------------|-----------------------------------------|
| `ttl`       | DNS record TTL value          | Integer       | 1 (auto)                           | 600                                     |
| `endpoint`  | Custom API endpoint URL       | String        | `https://esa.cn-hangzhou.aliyuncs.com` | `https://esa.ap-southeast-1.aliyuncs.com` |

### Custom Regional Endpoint

When you need to access ESA services in specific regions, you can configure a custom endpoint address:

#### China Regions

- **East China 1 (Hangzhou)**: `https://esa.cn-hangzhou.aliyuncs.com` (Default, Recommended)

#### International Regions

- **Asia Pacific Southeast 1 (Singapore)**: `https://esa.ap-southeast-1.aliyuncs.com`

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

```sh
ddns -c config.json --debug
```

## Support and Resources

- [Alibaba Cloud ESA Product Documentation](https://help.aliyun.com/product/122312.html)
- [Alibaba Cloud ESA API Documentation](https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-overview)
- [Alibaba Cloud ESA Console](https://esa.console.aliyun.com/)
- [Alibaba Cloud Technical Support](https://selfservice.console.aliyun.com/ticket)

> It's recommended to use RAM sub-accounts with only necessary ESA permissions to improve security. Regularly rotate AccessKeys to ensure account security.
