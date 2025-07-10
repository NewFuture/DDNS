# Huawei Cloud DNS Configuration Guide

> ⚠️ **Important Notice: This provider is awaiting verification**
>
> Huawei Cloud DNS lacks sufficient real-world testing. Please test carefully before use. If you encounter any issues, please report them in [GitHub Issues](https://github.com/NewFuture/DDNS/issues).

## Overview

Huawei Cloud DNS is an authoritative DNS resolution service provided by Huawei Cloud, featuring high availability, high scalability, and high security. This DDNS project supports authentication through Huawei Cloud Access Key.

## Authentication Method

### Access Key Authentication

Huawei Cloud DNS uses Access Key ID and Secret Access Key for API authentication, which is the standard authentication method for Huawei Cloud.

#### Getting Access Keys

1. Log in to the [Huawei Cloud Console](https://www.huaweicloud.com/)
2. Go to **My Credentials** > **Access Keys**
3. Click the "Create Access Key" button
4. Copy the generated **Access Key ID** and **Secret Access Key**, and store them securely
5. Ensure the account has the necessary DNS resolution permissions

#### Configuration Example

```json
{
    "dns": "huaweidns",
    "id": "your_access_key_id",
    "token": "your_secret_access_key"
}
```

- `id`: Huawei Cloud Access Key ID
- `token`: Huawei Cloud Secret Access Key
- `dns`: Fixed as `"huaweidns"`

## Complete Configuration Examples

### Basic Configuration

```json
{
    "id": "your_access_key_id",
    "token": "your_secret_access_key",
    "dns": "huaweidns",
    "ipv6": ["home.example.com", "server.example.com"],
    "index6": ["default"]
}
```

### Configuration with Optional Parameters

```json
{
    "id": "your_access_key_id",
    "token": "your_secret_access_key",
    "dns": "huaweidns",
    "endpoint": "https://dns.myhuaweicloud.com",
    "index4": ["default"],
    "index6": ["default"],
    "ipv4": ["example.com"],
    "ipv6": ["dynamic.mydomain.com"],
    "ttl": 600
}
```

## Optional Parameters

### TTL (Time To Live)

```json
{
    "ttl": 600
}
```

- **Range**: 1-86400 seconds
- **Default**: 300 seconds
- **Recommended**: 300-600 seconds for dynamic DNS

### Resolution Line

```json
{
    "line": "default"
}
```

- **Options**: "default", "unicom", "telecom", "mobile", "overseas", "edu", etc.
- **Default**: "default"
- Different service plans support different line types

## Endpoint Configuration

Huawei Cloud DNS supports multiple regional service endpoints, allowing users to choose the optimal node based on their location:

### Recommended Endpoint

```json
{
    "endpoint": "https://dns.myhuaweicloud.com"
}
```

### Available Endpoints

#### China Mainland

- **Global Service**: `https://dns.myhuaweicloud.com` (Default, Recommended)
- **North China-Beijing4**: `https://dns.cn-north-4.myhuaweicloud.com`
- **East China-Shanghai1**: `https://dns.cn-east-3.myhuaweicloud.com`
- **South China-Guangzhou**: `https://dns.cn-south-1.myhuaweicloud.com`
- **North China-Ulanqab1**: `https://dns.cn-north-9.myhuaweicloud.com`
- **Southwest China-Guiyang1**: `https://dns.cn-southwest-2.myhuaweicloud.com`

#### International Regions

- **Asia Pacific-Singapore**: `https://dns.ap-southeast-3.myhuaweicloud.com`
- **Asia Pacific-Hong Kong**: `https://dns.ap-southeast-1.myhuaweicloud.com`
- **Asia Pacific-Bangkok**: `https://dns.ap-southeast-2.myhuaweicloud.com`
- **Africa-Johannesburg**: `https://dns.af-south-1.myhuaweicloud.com`
- **Latin America-Santiago**: `https://dns.la-south-2.myhuaweicloud.com`
- **Latin America-Mexico City1**: `https://dns.la-north-2.myhuaweicloud.com`
- **Latin America-Sao Paulo1**: `https://dns.sa-brazil-1.myhuaweicloud.com`

### Endpoint Selection Recommendations

```json
{
    "dns": "huaweidns",
    "id": "your_access_key_id",
    "token": "your_secret_access_key",
    "endpoint": "https://dns.myhuaweicloud.com",
    "ipv4": ["example.com"],
    "ttl": 600
}
```

**Recommended Usage Scenarios:**

- **Default Choice**: Use the global service endpoint `https://dns.myhuaweicloud.com`
- **Network Optimization**: Choose nearby regional endpoints if experiencing high latency in specific regions
- **Compliance Requirements**: Select appropriate regional endpoints for data sovereignty requirements

> **Note**: Huawei Cloud DNS automatically selects the optimal node based on the user's network location. It's recommended to use the default global service endpoint. Only specify regional endpoints in special network environments or when there are specific compliance requirements.

## Permission Requirements

Ensure the Huawei Cloud account has the following permissions:

- **DNS Administrator**: Full DNS management permissions (Recommended)
- **DNS ReadOnlyAccess + Custom Write Permissions**: Fine-grained permission control

You can view and configure permissions in the [Identity and Access Management](https://console.huaweicloud.com/iam/) console.

## Troubleshooting

### Common Issues

#### "Signature Error" or "Authentication Failed"

- Check if Access Key ID and Secret Access Key are correct
- Verify the keys haven't been deleted or disabled
- Confirm account has sufficient permissions

#### "Domain Does Not Exist"

- Verify the domain is added to Huawei Cloud DNS
- Check domain spelling in configuration
- Ensure domain status is normal

#### "Record Operation Failed"

- Check if subdomain has conflicting records
- Verify TTL value is within acceptable range
- Confirm resolution line setting is correct
- Check if domain plan supports the feature

#### "API Call Limit Exceeded"

- Huawei Cloud API has rate limiting
- Increase update intervals appropriately
- Check if other programs are calling the API simultaneously

### Debug Mode

Enable debug logging to see detailed information:

```sh
ddns --debug
```

### Common Error Codes

- **APIGW.0301**: Authentication failed
- **DNS.0101**: Domain does not exist
- **DNS.0102**: Record set does not exist
- **DNS.0103**: Record set already exists
- **DNS.0203**: Request rate too high

## API Limitations

- **Request Rate**: Varies by service plan
- **Single Query**: Maximum 500 records returned
- **Domain Count**: Limited based on service plan

## Support and Resources

- **Huawei Cloud DNS Documentation**: <https://support.huaweicloud.com/intl/en-us/dns/>
- **Huawei Cloud DNS API Reference**: <https://support.huaweicloud.com/intl/en-us/api-dns/>
- **Huawei Cloud Console**: <https://console.huaweicloud.com/dns/>
- **Huawei Cloud Technical Support**: <https://support.huaweicloud.com/intl/en-us/>

> It is recommended to use sub-users and grant only the necessary DNS permissions to improve security. Regularly rotate access keys to ensure account security.
