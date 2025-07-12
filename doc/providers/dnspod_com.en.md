# DNSPod Global Configuration Guide

## Overview

DNSPod Global (dnspod.com) provides DNS services outside mainland China and uses the same API interface as DNSPod China.

This DDNS project supports the dnspod_com provider with configuration parameters identical to DNSPod, with the only difference being the names of supported DNS lines.

## Authentication Methods

### API Token (Recommended)

DNSPod Global uses the same API Token mechanism. Obtain your token as follows:

1. Login to [DNSPod Global Console](https://www.dnspod.com/)
2. Go to "User Center" → "API Token" or visit <https://www.dnspod.com/account/token/token>
3. Click "Create Token", enter a description, select domain management permissions, and create
4. Copy the **ID** and **Token** shown (token is shown only once; save it securely)

```json
{
  "dns": "dnspod_com",
  "id": "123456",
  "token": "abcdef1234567890abcdef1234567890"
}
```

- `id`: API Token ID
- `token`: API Token secret
- `dns`: Must be set to `"dnspod_com"`

## Configuration Parameters

Refer to the [DNSPod China Configuration Guide](./dnspod.en.md) for details on parameters `id`, `token`, `dns`, `index4`, `index6`, `ipv4`, `ipv6`, and `ttl`.

## Supported Line Names

The `line` parameter values for DNSPod International are English identifiers:

| Line Name | Description          |
|-----------|----------------------|
| default   | Default public line  |
| telecom   | China Telecom route  |
| unicom    | China Unicom route   |
| mobile    | China Mobile route   |
| oversea   | International route  |

Example:

```json
{
  "id": "123456",
  "token": "abcdef1234567890abcdef1234567890abcdef12",
  "dns": "dnspod_com",
  "index4": ["public"],
  "index6": ["public"],
  "ipv4": ["home.example.com"],
  "ipv6": ["home.example.com", "nas.example.com"],
  "line": "oversea",
  "ttl": 600
}
```

## Support and Resources

- [DNSPod International API Documentation](https://www.dnspod.com/docs/)
- [DNSPod China Configuration Guide](./dnspod.en.md)
