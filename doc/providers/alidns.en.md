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

## Permission Requirements

Ensure the Alibaba Cloud account has the following permissions:

- **AliyunDNSFullAccess**: Full access to Alibaba Cloud DNS (recommended)
- **AliyunDNSReadOnlyAccess + Custom Write Permissions**: Fine-grained permission control

You can view and configure permissions in the [RAM Access Control](https://ram.console.aliyun.com/policies).

## Complete Configuration Examples

```json
{
  "id": "LTAI4xxxxxxxxxxxxxxx",
  "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "dns": "alidns",
  "endpoint": "https://alidns.aliyuncs.com",
  "index4": ["public"],
  "index6": ["default"],
  "ipv4": ["example.com"],
  "ipv6": ["dynamic.mydomain.com"],
  "line": "telecom",
  "ttl": 600
}
```

## Optional Configuration Parameters

| Parameter | Description           | Type              | Range/Options                                 | Default |
|-----------|-----------------------|-------------------|-----------------------------------------------|---------|
| ttl       | Time To Live (TTL)    | Integer (seconds) | 1 - 86400                                     | 600     |
| line      | Resolution Line       | String            | default, telecom, unicom, mobile, oversea    | default |
| endpoint  | Custom API Endpoint   | String            | URL (see below)                              | `https://alidns.aliyuncs.com`|

> **Note**: Supported values for `ttl` and `line` may vary by service plan.

### Custom API Endpoint

Alibaba Cloud DNS supports multiple regional endpoints for optimal network performance:

#### China Regions

- **Default (Recommended)**: `https://alidns.aliyuncs.com`
- **East China 1 (Hangzhou)**: `https://alidns.cn-hangzhou.aliyuncs.com`
- **East China 2 (Shanghai)**: `https://alidns.cn-shanghai.aliyuncs.com`
- **North China 1 (Qingdao)**: `https://alidns.cn-qingdao.aliyuncs.com`
- **North China 2 (Beijing)**: `https://alidns.cn-beijing.aliyuncs.com`
- **North China 3 (Zhangjiakou)**: `https://alidns.cn-zhangjiakou.aliyuncs.com`
- **South China 1 (Shenzhen)**: `https://alidns.cn-shenzhen.aliyuncs.com`
- **Southwest 1 (Chengdu)**: `https://alidns.cn-chengdu.aliyuncs.com`

#### International Regions

- **Asia Pacific Southeast 1 (Singapore)**: `https://alidns.ap-southeast-1.aliyuncs.com`
- **Asia Pacific Southeast 2 (Sydney)**: `https://alidns.ap-southeast-2.aliyuncs.com`
- **Asia Pacific Southeast 3 (Kuala Lumpur)**: `https://alidns.ap-southeast-3.aliyuncs.com`
- **Asia Pacific South 1 (Mumbai)**: `https://alidns.ap-south-1.aliyuncs.com`
- **Asia Pacific Northeast 1 (Tokyo)**: `https://alidns.ap-northeast-1.aliyuncs.com`
- **US East 1 (Virginia)**: `https://alidns.us-east-1.aliyuncs.com`
- **US West 1 (Silicon Valley)**: `https://alidns.us-west-1.aliyuncs.com`
- **Europe Central 1 (Frankfurt)**: `https://alidns.eu-central-1.aliyuncs.com`
- **Europe West 1 (London)**: `https://alidns.eu-west-1.aliyuncs.com`

> **Note**: It's recommended to use the default endpoint `https://alidns.aliyuncs.com`, as Alibaba Cloud automatically routes to the optimal node. Specify regional endpoints only in special network environments.

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
