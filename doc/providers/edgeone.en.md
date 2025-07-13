# Tencent Cloud EdgeOne Configuration Guide

## Overview

Tencent Cloud EdgeOne is a global edge computing and security acceleration service platform provided by Tencent Cloud, which includes DNS resolution capabilities. This DDNS project supports dynamic DNS record updates through Tencent Cloud EdgeOne API.

**Website**: 
- International: [https://edgeone.ai/zh](https://edgeone.ai/zh)
- Domestic: [https://cloud.tencent.com/product/teo](https://cloud.tencent.com/product/teo)

## Authentication

### API Key Authentication

Tencent Cloud EdgeOne uses `SecretId` and `SecretKey` for API authentication, which is the recommended authentication method.

#### Obtaining API Keys

1. Log in to [Tencent Cloud Console](https://console.cloud.tencent.com/)
2. Visit [API Key Management](https://console.cloud.tencent.com/cam/capi)
3. Click "Create Key" button
4. Copy the generated **SecretId** and **SecretKey**, store them securely
5. Ensure the account has EdgeOne related permissions

## Permission Requirements

Ensure the Tencent Cloud account used for DDNS has the following EdgeOne related permissions:

- `teo:DescribeZones` - Query site information
- `teo:DescribeRecords` - Query DNS records
- `teo:CreateRecord` - Create DNS records  
- `teo:ModifyRecord` - Modify DNS records

It is recommended to use a sub-account with minimal necessary permissions instead of using the main account credentials.

#### Configuration Example

```json
{
    "dns": "edgeone",
    "id": "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

- `id`: Tencent Cloud SecretId
- `token`: Tencent Cloud SecretKey
- `dns`: Can use `"edgeone"`, `"tencent_edgeone"`, or `"teo"`

## Complete Configuration Example

```json
{
    "id": "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "dns": "edgeone",
    "domains": "test.example.com"
}
```

- `id`: Tencent Cloud SecretId
- `token`: Tencent Cloud SecretKey
- `dns`: Can use `"edgeone"`, `"tencent_edgeone"`, or `"teo"`

## Service Endpoints

EdgeOne supports both international and domestic versions with different API endpoints:

- **International**: `https://teo.tencentcloudapi.com` (default)
- **Domestic**: `https://teo.tencentcloudapi.com`

Both versions have the same API logic but different server node distributions.

## Important Notes

1. **Service Differences**: EdgeOne is different from traditional DNSPod service, ensure domains are properly configured in EdgeOne console
2. **API Limits**: EdgeOne API has rate limits, set reasonable update intervals
3. **Permission Management**: Create dedicated sub-accounts for DDNS with minimal necessary permissions
4. **Key Security**: SecretKey is sensitive information, store securely and avoid exposure
5. **Record Conflicts**: Ensure DNS records to be updated don't conflict with other EdgeOne features (acceleration, security rules)

## Troubleshooting

### Common Errors

1. **Authentication Failed**
   - Check if SecretId and SecretKey are correct
   - Confirm account has EdgeOne permissions
   - Verify time synchronization, API signature is time-sensitive

2. **Domain Not Found**
   - Confirm domain is added in EdgeOne console
   - Check domain status is normal
   - Verify DNS configuration is correct

3. **Record Operation Failed**
   - Check if record type is supported
   - Confirm TTL value is within allowed range
   - Verify record value format is correct

### Log Analysis

Enable debug mode to view detailed API requests and responses:

```bash
ddns --debug
```

## Related Links

- [EdgeOne Official Documentation](https://edgeone.ai/zh/document)
- [API Authentication & Signature](https://edgeone.ai/zh/document/50458)
- [DNS Record Management API](https://edgeone.ai/zh/document/50484)
- [Tencent Cloud Console](https://console.cloud.tencent.com/)
- [EdgeOne Console](https://console.tencentcloud.com/edgeone)