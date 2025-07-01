# Alibaba Cloud DNS Configuration Guide

## Overview

Alibaba Cloud DNS (AliDNS) is an authoritative DNS resolution service provided by Alibaba Cloud, supporting high concurrency and high availability domain name resolution. This DDNS project supports authentication through Alibaba Cloud AccessKey.

## Authentication Method

### AccessKey Authentication

Alibaba Cloud DNS uses AccessKey ID and AccessKey Secret for API authentication, which is the standard authentication method for Alibaba Cloud.

#### How to Obtain AccessKey

1. **Login to Alibaba Cloud Console**
    - Visit [Alibaba Cloud Console](https://ecs.console.aliyun.com/)
    - Sign in with your Alibaba Cloud account

2. **Go to AccessKey Management**
    - Visit [AccessKey Management](https://usercenter.console.aliyun.com/#/manage/ak)
    - Click "Create AccessKey" button

3. **Create New AccessKey**
    - Click the "Create AccessKey" button
    - Copy the generated **AccessKey ID** and **AccessKey Secret**
    - **Important**: Save both values securely

4. **Verify Permissions**
    - Ensure your account has Alibaba Cloud DNS operation permissions
    - Check [RAM Access Control](https://ram.console.aliyun.com/policies) if needed

#### Configuration Using AccessKey

```json
{
  "dns": "alidns",
  "id": "LTAI4xxxxxxxxxxxxxxx",
  "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Parameters:**

- `id`: Your Alibaba Cloud AccessKey ID
- `token`: Your Alibaba Cloud AccessKey Secret
- `dns`: Must be set to `"alidns"`

## Complete Configuration Examples

### Basic Configuration

```json
{
  "id": "LTAI4xxxxxxxxxxxxxxx",
  "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "dns": "alidns",
  "ipv6": ["home.example.com", "server.example.com"]
}
```

### Configuration with Optional Parameters

```json
{
  "id": "LTAI4xxxxxxxxxxxxxxx",
  "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "dns": "alidns",
  "ipv6": ["dynamic.mydomain.com"],
  "ttl": 600,
  "record_type": "A"
}
```

## Optional Configuration Parameters

### TTL (Time To Live)

```json
{
  "ttl": 600
}
```

- **Range**: 1-86400 seconds
- **Default**: 600 seconds (10 minutes)
- **Recommended**: 300-600 seconds for dynamic DNS

### Record Type

```json
{
  "record_type": "A"
}
```

- **Supported Types**: A, AAAA, CNAME, MX, TXT, SRV, etc.
- **Default**: A (IPv4)
- Use "AAAA" for IPv6 addresses

### Resolution Line

```json
{
  "line": "default"
}
```

- **Options**: "default", "telecom", "unicom", "mobile", "oversea", etc.
- **Default**: "default"
- Available line types vary by service plan

## Permission Requirements

Ensure the Alibaba Cloud account has the following permissions:

- **AliyunDNSFullAccess**: Full access to Alibaba Cloud DNS (recommended)
- **AliyunDNSReadOnlyAccess + Custom Write Permissions**: Fine-grained permission control

You can view and configure permissions in the [RAM Access Control](https://ram.console.aliyun.com/policies).

## Troubleshooting

### Common Issues

#### "Signature Error" or "Authentication Failed"

- Check if AccessKey ID and AccessKey Secret are correct
- Verify the keys haven't been deleted or disabled
- Confirm account has sufficient permissions

#### "Domain Does Not Exist"

- Verify the domain is added to Alibaba Cloud DNS
- Check domain spelling in configuration
- Ensure domain status is normal

#### "Record Operation Failed"

- Check if subdomain has conflicting records
- Verify TTL value is within acceptable range
- Confirm resolution line setting is correct
- Check if domain plan supports the feature

#### "API Call Limit Exceeded"

- Alibaba Cloud API has QPS limitations
- Personal Edition: 20 QPS, Enterprise Edition: 50 QPS
- Increase update intervals appropriately

### Debug Mode

Enable debug logging to see detailed information:

```sh
ddns --debug
```

### Common Error Codes

- **InvalidAccessKeyId.NotFound**: AccessKey does not exist
- **SignatureDoesNotMatch**: Signature error
- **DomainRecordDuplicate**: Duplicate record
- **DomainNotExists**: Domain does not exist
- **Throttling.User**: User requests too frequent

## API Limitations

- **Personal Edition QPS**: 20 requests/second
- **Enterprise Edition QPS**: 50 requests/second
- **Domain Count**: Varies by service plan
- **DNS Records**: Varies by service plan

## Support and Resources

- **Alibaba Cloud DNS Documentation**: <https://help.aliyun.com/product/29697.html>
- **Alibaba Cloud DNS API Reference**: <https://help.aliyun.com/document_detail/29739.html>
- **Alibaba Cloud DNS Console**: <https://dns.console.aliyun.com/>
- **Alibaba Cloud Technical Support**: <https://selfservice.console.aliyun.com/ticket>

> It is recommended to use RAM sub-accounts and grant only the necessary DNS permissions to improve security. Regularly rotate AccessKeys to ensure account security.
