# Tencent Cloud EdgeOne International Configuration Guide

## Overview

Tencent Cloud EdgeOne International is a global edge computing and security acceleration service platform provided by Tencent Cloud, which includes DNS resolution capabilities. This DDNS project supports dynamic DNS record updates through Tencent Cloud EdgeOne API.

**Website**: [https://edgeone.ai/zh](https://edgeone.ai/zh)

## Authentication

### API Key Authentication

Tencent Cloud EdgeOne uses `SecretId` and `SecretKey` for API authentication, which is the recommended authentication method.

#### Obtaining API Keys

1. Log in to [Tencent Cloud Console](https://console.cloud.tencent.com/)
2. Visit [API Key Management](https://console.cloud.tencent.com/cam/capi)
3. Click "Create Key" button
4. Copy the generated **SecretId** and **SecretKey**, store them securely
5. Ensure the account has EdgeOne related permissions

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

## Complete Configuration Examples

### Basic Configuration

```json
{
    "id": "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "dns": "edgeone",
    "ipv4": "test",
    "ipv6": "test6",
    "domains": "test.example.com"
}
```

### Advanced Configuration

```json
{
    "id": "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", 
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "dns": "edgeone",
    "domains": [
        {
            "domain": "test.example.com",
            "type": "A",
            "ttl": 600
        },
        {
            "domain": "test6.example.com", 
            "type": "AAAA",
            "ttl": 300
        },
        {
            "domain": "@~example.com",
            "type": "A"
        }
    ],
    "ipv4": {
        "interface": "eth0",
        "url": "https://api.ipify.org"
    },
    "ipv6": "auto"
}
```

## Supported Record Types

EdgeOne supports the following DNS record types:

- **A Record**: IPv4 address resolution
- **AAAA Record**: IPv6 address resolution
- **CNAME Record**: Canonical name record
- **MX Record**: Mail exchange record
- **TXT Record**: Text record
- **NS Record**: Name server record

## Domain Format Support

### Standard Format
```
test.example.com
```

### Custom Separator Format
Use `~` or `+` to separate subdomain and main domain:
```
test~example.com
sub+example.com
@~example.com  # Root domain record
```

## Required Permissions

Ensure the Tencent Cloud account used for DDNS has the following EdgeOne related permissions:

- `teo:DescribeZones` - Query zone information
- `teo:DescribeRecords` - Query DNS records
- `teo:CreateRecord` - Create DNS records
- `teo:ModifyRecord` - Modify DNS records

It is recommended to use a sub-account with minimal necessary permissions rather than using the main account key.

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

```json
{
    "debug": true,
    "dns": "edgeone",
    ...
}
```

## Related Links

- [EdgeOne Official Documentation](https://edgeone.ai/zh/document)
- [API Authentication & Signature](https://edgeone.ai/zh/document/50458)
- [DNS Record Management API](https://edgeone.ai/zh/document/50484)
- [Tencent Cloud Console](https://console.cloud.tencent.com/)
- [EdgeOne Console](https://console.tencentcloud.com/edgeone)