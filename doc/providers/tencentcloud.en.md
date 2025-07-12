# Tencent Cloud DNS Configuration Guide

## Overview

Tencent Cloud DNS (TencentCloud DNSPod) is a professional DNS resolution service provided by Tencent Cloud, suitable for users who need high availability and high-performance DNS resolution. This DDNS project supports authentication through Tencent Cloud API keys.

## Authentication Method

### API Key Authentication

Tencent Cloud DNS uses SecretId and SecretKey for API authentication, which is the most secure and recommended authentication method.

#### How to Obtain API Keys

##### From DNSPod

1. **Login to DNSPod Console**
    - Visit [DNSPod Console](https://console.dnspod.cn/)
    - Sign in with your DNSPod account

2. **Go to API Key Management**
    - Visit [API Key Management](https://console.dnspod.cn/account/token)

3. **Create a New Secret Key**
    - Click the "Create Key" button
    - Enter a descriptive name (e.g., "DDNS Host")
    - Select appropriate permissions (domain management permission required)
    - Click "Confirm" to create

##### From Tencent Cloud

1. **Login to Tencent Cloud Console**
    - Visit [Tencent Cloud Console](https://console.cloud.tencent.com/)
    - Sign in with your Tencent Cloud account

2. **Go to API Key Management**
    - Visit [API Key Management](https://console.cloud.tencent.com/cam/capi)
    - Click "Create Key" button

3. **Create New API Key**
    - Click the "Create Key" button
    - Copy the generated **SecretId** and **SecretKey**
    - **Important**: Save both values securely, as they provide full access to your account

4. **Verify Permissions**
    - Ensure your account has DNSPod related permissions
    - Check [Access Management Console](https://console.cloud.tencent.com/cam/policy) if needed

#### Configuration Using API Keys

```json
{
  "dns": "tencentcloud",
  "id": "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Parameters:**

- `id`: Your Tencent Cloud SecretId
- `token`: Your Tencent Cloud SecretKey
- `dns`: Must be set to `"tencentcloud"`

## Complete Configuration Examples

### Basic Configuration

```json
{
  "id": "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "dns": "tencentcloud",
  "ipv6": ["home.example.com", "server.example.com"],
  "index6": ["default"]
}
```

### Configuration with Optional Parameters

```json
{
  "id": "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "dns": "tencentcloud",
  "endpoint": "https://dnspod.ap-singapore.tencentcloudapi.com",
  "index4": ["default"],
  "index6": ["default"],
  "ipv4": ["example.com"],
  "ipv6": ["dynamic.mydomain.com"],
  "ttl": 600
}
```

## Optional Configuration Parameters

### TTL (Time To Live)

```json
{
  "ttl": 300
}
```

### Line Type (ISP Route)

```json
{
  "line": "默认"
}
```

- **Options**: "默认" (Default), "电信" (China Telecom), "联通" (China Unicom), "移动" (China Mobile), "教育网" (Education Network), etc.
- **Default**: "默认" (Default line)

### Custom API Endpoint

```json
{
  "endpoint": "https://dnspod.tencentcloudapi.com"
}
```

Tencent Cloud DNSPod API supports multiple regional endpoints for optimal network performance:

#### China Regions

- **South China (Guangzhou)**: `https://dnspod.ap-guangzhou.tencentcloudapi.com`
- **East China (Shanghai)**: `https://dnspod.ap-shanghai.tencentcloudapi.com`
- **North China (Beijing)**: `https://dnspod.ap-beijing.tencentcloudapi.com`
- **Southwest China (Chengdu)**: `https://dnspod.ap-chengdu.tencentcloudapi.com`
- **Hong Kong**: `https://dnspod.ap-hongkong.tencentcloudapi.com`

#### International Regions

- **Asia Pacific Southeast (Singapore)**: `https://dnspod.ap-singapore.tencentcloudapi.com`
- **Asia Pacific Southeast (Bangkok)**: `https://dnspod.ap-bangkok.tencentcloudapi.com`
- **Asia Pacific South (Mumbai)**: `https://dnspod.ap-mumbai.tencentcloudapi.com`
- **Asia Pacific Northeast (Seoul)**: `https://dnspod.ap-seoul.tencentcloudapi.com`
- **Asia Pacific Northeast (Tokyo)**: `https://dnspod.ap-tokyo.tencentcloudapi.com`
- **US East (Virginia)**: `https://dnspod.na-ashburn.tencentcloudapi.com`
- **US West (Silicon Valley)**: `https://dnspod.na-siliconvalley.tencentcloudapi.com`
- **Europe (Frankfurt)**: `https://dnspod.eu-frankfurt.tencentcloudapi.com`

> **Note**: It's recommended to use the default endpoint `https://dnspod.tencentcloudapi.com`, as Tencent Cloud automatically routes to the optimal node. Specify regional endpoints only in special network environments.

## Permission Requirements

Ensure the Tencent Cloud account has the following permissions:

- **DNSPod**: Domain resolution management permissions
- **QcloudDNSPodFullAccess**: Full DNSPod access permission (recommended)

You can view and configure permissions in the [Access Management Console](https://console.cloud.tencent.com/cam/policy).

## Troubleshooting

### Common Issues

#### "Signature Error" or "Authentication Failed"

- Check if SecretId and SecretKey are correct
- Verify the keys haven't expired
- Confirm account has sufficient permissions

#### "Domain Not Found" Error

- Verify the domain is added to Tencent Cloud DNSPod
- Check domain spelling in configuration
- Ensure domain status is normal

#### "Record Operation Failed"

- Check if subdomain has conflicting records
- Verify TTL value is within acceptable range
- Confirm line type setting is correct

#### "API Call Limit Exceeded"

- Tencent Cloud API has rate limiting
- Increase update intervals appropriately
- Check if other programs are calling the API simultaneously

### Debug Mode

Enable debug logging to see detailed information:

```sh
ddns --debug
```

### Common Error Codes

- **AuthFailure.SignatureExpire**: Signature expired
- **AuthFailure.SecretIdNotFound**: SecretId does not exist
- **ResourceNotFound.NoDataOfRecord**: Record does not exist
- **LimitExceeded.RequestLimitExceeded**: Request frequency exceeded

## API Limitations

- **Request Rate**: Default 20 requests per second
- **Single Query**: Maximum 3000 records returned
- **Domain Count**: Limited based on service plan

## Support and Resources

- **Tencent Cloud DNSPod Documentation**: <https://cloud.tencent.com/document/product/1427>
- **Tencent Cloud DNSPod API Reference**: <https://cloud.tencent.com/document/api/1427>
- **Tencent Cloud Console**: <https://console.cloud.tencent.com/dnspod>
- **Tencent Cloud Technical Support**: <https://cloud.tencent.com/document/product/282>

> It is recommended to use sub-account API keys and grant only the necessary DNSPod permissions to improve security.
