# DDNS Provider English Documentation

## Overview

DNSPod is a DNS service provider under Tencent Cloud, widely used in mainland China. This DDNS project supports connecting to DNSPod via two authentication methods:

1. **API Token** (Recommended)
2. **Email + Password** (Legacy)

## Authentication Methods

### Method 1: API Token (Recommended)

The API Token method is more secure and is the recommended way to integrate with DNSPod.

#### How to Obtain an API Token

1. **Login to DNSPod Console**
    - Visit [DNSPod Console](https://console.dnspod.cn/)
    - Sign in with your DNSPod account

2. **Go to API Key Management**
    - Click "User Center"
    - Select the "API Key" menu
    - Or directly visit: <https://console.dnspod.cn/account/token/token>

3. **Create a New API Key**
    - Click the "Create Key" button
    - Enter a descriptive name (e.g., "DDNS Host")
    - Select appropriate permissions (domain management permission required)
    - Click "Confirm" to create

4. **Copy Key Information**
    - **ID**: The key ID (numeric value)
    - **Token**: The actual key string (long alphanumeric string)
    - **Important**: Save both values immediately, as the key will only be shown once

#### Configuration Using API Token

```json
{
  "dns": "dnspod",
  "id": "123456",
  "token": "abcdef1234567890abcdef1234567890"
}
```

**Parameters:**

- `id`: Your API Token ID (numeric string)
- `token`: Your API Token secret
- `dns`: Must be set to `"dnspod"`

### Method 2: Email + Password (Legacy)

This method uses your DNSPod account email and password. It is still supported but less secure than API Token.

#### How to Use Email Authentication

1. **Ensure Account Availability**
    - Make sure you can log in to DNSPod with your email and password
    - Verify your account has domain management permissions

2. **Email and Password Configuration**

```json
{
  "id": "your-email@example.com",
  "token": "your-account-password",
  "dns": "dnspod"
}
```

**Parameters:**

- `id`: Your DNSPod account email address
- `token`: Your DNSPod account password
- `dns`: Must be set to `"dnspod"`

## Complete Configuration Examples

### Example 1: API Token Configuration (Recommended)

```json
{
  "id": "123456",
  "token": "abcdef1234567890abcdef1234567890abcdef12",
  "dns": "dnspod",
  "ipv6": ["home.example.com", "nas.example.com"]
}
```

### Example 2: Email Authentication Configuration

```json
{
  "id": "myemail@gmail.com",
  "token": "mypassword123",
  "dns": "dnspod",
  "ipv6": ["dynamic.mydomain.com"]
}
```

## Optional Configuration Parameters

### TTL (Time To Live)

```json
{
  "ttl": 600
}
```

- **Range**: 1-604800 seconds
- **Default**: 600 seconds (10 minutes)
- **Recommended**: 120-600 seconds for dynamic DNS

### Record Type

```json
{
  "record_type": "A"
}
```

- **Supported Types**: A, AAAA, CNAME
- **Default**: A (IPv4)
- Use "AAAA" for IPv6 addresses

### Line (ISP Route)

```json
{
  "line": "默认"
}
```

- **Options**: "默认" (Default), "电信" (China Telecom), "联通" (China Unicom), "移动" (China Mobile), etc.
- **Default**: "默认" (Default line)

## Troubleshooting

### Common Issues

#### "Authentication Failed" Error

- **API Token**: Check if ID and Token are correct
- **Email**: Check email and password for typos
- **Permissions**: Ensure the token/account has domain management permissions

#### "Domain Not Found" Error

- Verify the domain is added to your DNSPod account
- Check the domain spelling in your configuration
- Ensure the domain is active and not suspended

#### "Record Creation Failed"

- Check if the subdomain already exists with a different record type
- Verify TTL value is within the acceptable range
- Ensure you have permission to modify the specific domain

### Debug Mode

Enable debug logging to troubleshoot issues:

```sh
ddns --debug
```

This will display detailed logs for troubleshooting.

## Support and Resources

- **DNSPod Documentation**: <https://docs.dnspod.cn/>
- **API Reference**: <https://docs.dnspod.cn/api/>
- **Support**: DNSPod customer service or community forums

It is recommended to use the API Token method for better security and easier DDNS configuration management.
