# West.cn DNS Configuration Guide

## Overview

West.cn is a standard DNS provider offering REST APIs for record management and DDNS. This project integrates with the official endpoint `https://api.west.cn/API/v2/domain/dns/` to list, create, and update DNS records for IPv4/IPv6.

- Website: <https://www.west.cn/>
- Console: <https://www.west.cn/manager/>
- API Docs: <https://www.west.cn/CustomerCenter/doc/apiV2.html>

## Authentication

Two authentication modes are supported (choose one):

1. **Domain-level ApiKey (apidomainkey)**
   - Parameter: `apidomainkey`
   - How to obtain: open the target domain detail page and copy the domain **ApiKey** under “API/动态解析”.
2. **User-level ApiKey (username + apikey)**
   - Parameters: `username` + `apikey`
   - How to obtain: Console → **API 接口配置** → generate user-level API key (available for reseller/multi-domain).

```json
{
  "dns": "west",
  "id": "your_username (optional when using domain key)",
  "token": "your_apikey_or_apidomainkey",
  "ipv4": ["ddns.example.com"],
  "ttl": 600
}
```

## Full Configuration Examples

### Domain-level ApiKey

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "dns": "west",
  "token": "apidomainkey-from-domain",
  "ipv4": ["ddns.example.com"],
  "ipv6": ["ddns6.example.com"],
  "ttl": 600
}
```

### User-level ApiKey

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "dns": "west",
  "id": "your_username",
  "token": "user_apikey",
  "ipv4": ["ddns.example.com"],
  "index4": ["public"],
  "ttl": 600
}
```

### Parameter Description

| Param  | Description            | Type   | Options/Range                                  | Default  | Scope      |
| :----: | :-------------------- | :----- | :--------------------------------------------- | :------- | :--------- |
| dns    | Provider name         | string | `west`                                         | required | Provider   |
| id     | Username              | string | Required for user-level auth; empty for domain key | empty    | Provider   |
| token  | API key               | string | `apikey` (user-level) or `apidomainkey` (domain-level) | required | Provider   |
| index4 | IPv4 source           | array  | [Reference](../config/json.en.md#ipv4-ipv6)    | `default` | Common     |
| index6 | IPv6 source           | array  | [Reference](../config/json.en.md#ipv4-ipv6)    | `default` | Common     |
| ipv4   | IPv4 domains          | array  | Domain list                                    | required | Common     |
| ipv6   | IPv6 domains          | array  | Domain list                                    | optional | Common     |
| ttl    | TTL (seconds)         | number | 300–86400 (subject to provider limits)         | provider default | Provider |
| proxy  | Proxy                 | array  | [Reference](../config/json.en.md#proxy)        | none     | Network    |
| ssl    | SSL verify            | bool/string | `"auto"`, `true`, `false`                     | `auto`   | Network    |
| cache  | Cache                 | bool/string | `true`, `false`, `filepath`                   | `true`   | Common     |
| log    | Log config            | object | [Reference](../config/json.en.md#log)          | none     | Common     |

> Notes  
> - Leave `id` empty when using a domain-level ApiKey.  
> - Both A and AAAA records can be created/updated. If `record_line` is omitted, the default route is used.  
> - Ensure the ApiKey grants access to the target domain.

## Troubleshooting

- **Authentication failed / code != 1**: verify the ApiKey, and confirm it is authorized for the target domain; user-level keys require API permission enabled.  
- **Domain not found**: make sure the domain is hosted in your West.cn account and matches the provided key.  
- **Record not updated**: verify the hostname format (e.g., `www.example.com`), and pre-create the record if needed.  
- **Encoding issues**: the API uses `application/x-www-form-urlencoded`; if garbled, try UTF-8/GBK form submission.

## Support & Resources

- [West.cn](https://www.west.cn/)
- [API Docs](https://www.west.cn/CustomerCenter/doc/apiV2.html)
- [Console](https://www.west.cn/manager/)
- For questions, open a [GitHub Issue](https://github.com/NewFuture/DDNS/issues)
