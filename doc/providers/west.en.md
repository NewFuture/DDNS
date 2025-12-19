# West.cn DNS Configuration Guide

## Overview

West.cn provides standard DNS hosting and supports dynamic DNS updates via the `dnsrec.update` API. Both IPv4 and IPv6 are supported.

- Website: <https://www.west.cn/>
- Console: <https://www.west.cn/CustomerCenter/index.asp>
- API Docs: <https://www.west.cn/CustomerCenter/doc/apiV2.html>

## Authentication

Two authentication methods are available:

1. **Domain Key (`apidomainkey`)**
   - Obtain the key on the domain detail page.
   - Best for a single domain with API enabled.
   - Leave `id` empty; set `token` to the `apidomainkey`.

2. **Account Key (`username` + `apikey`)**
   - Generate the 32‑character API key in the account/agent console.
   - Suitable for managing multiple domains.
   - Set `id` to the account username and `token` to the `apikey`.

> Create the DNS record in the console first, then enable DDNS to avoid missing records.

## Configuration Examples

### Domain key (recommended)

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "dns": "west",
  "token": "your_apidomainkey",
  "ipv4": ["ddns.example.com"],
  "ipv6": ["ddns.example.com"]
}
```

### Account key

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "dns": "west",
  "id": "your_username",
  "token": "your_apikey_md5",
  "ipv4": ["ddns.example.com"]
}
```

## Parameters

| Parameter | Description | Type | Options | Default | Scope |
| :------: | :---------- | :--- | :------ | :------ | :---- |
| dns | Provider name | string | `west` | – | Provider |
| id | Account username (for account key) | string | account name | `""` | Provider |
| token | `apidomainkey` or `apikey` | string | console key | – | Provider |
| index4 | IPv4 source | array/string | [Reference](../config/json.md#ipv4-ipv6) | `default` | Common |
| index6 | IPv6 source | array/string | [Reference](../config/json.md#ipv4-ipv6) | `default` | Common |
| ipv4 | IPv4 domains | array | domain list | – | Common |
| ipv6 | IPv6 domains | array | domain list | – | Common |
| proxy | Proxy | array/string | [Reference](../config/json.md#proxy) | – | Network |
| ssl | SSL verify | bool/string | `"auto"`, `true`, `false` | `auto` | Network |
| cache | Cache | bool/string | `true`, `false`, file path | `true` | Common |
| log | Log config | object | [Reference](../config/json.md#log) | – | Common |

> The `dnsrec.update` endpoint does not expose TTL/line options; console defaults are used.

## Troubleshooting

- **Authentication failed**: Ensure the credential type matches the configuration; domain keys only work for the corresponding domain.
- **Record not updated**: Confirm the record exists in the console and that the IP changed.
- **Rate limit**: Avoid excessive requests; keep an interval of 5 minutes or more.

Enable debug logging:

```sh
ddns -c config.json --debug
```

## Support & Resources

- Official docs: <https://www.west.cn/CustomerCenter/doc/apiV2.html>
- Help Center: <https://api.west.cn/faq/list.asp?Unid=2522>
- Reference: [Reference](../config/json.md)
