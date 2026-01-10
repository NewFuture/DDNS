# HE.net (Hurricane Electric) Configuration Guide

## Overview

Hurricane Electric (HE.net) is a well-known network service provider offering free DNS hosting services with dynamic DNS record update support. This DDNS project authenticates through HE.net's dynamic DNS password.

> ⚠️ **Important Note**: HE.net Provider is currently in **verification pending** status, lacking sufficient real-world testing. Please provide feedback through [GitHub Issues](https://github.com/NewFuture/DDNS/issues).

**Important Limitation**: HE.net **does not support automatic record creation** - you must manually create DNS records in the HE.net control panel first.

Official Links:

- Official Website: <https://he.net/>
- Provider Console: <https://dns.he.net/>

## Authentication Information

### Dynamic DNS Password Authentication

HE.net uses a dedicated dynamic DNS password for authentication, not your account login password.

DNS records and DNS must be created in advance

1. Select the domain you want to manage in [HE.net DNS Management Panel](https://dns.he.net)
2. **Create DNS Record**: Manually create A (IPv4) or AAAA (IPv6) records
3. **Enable DDNS**: Enable dynamic DNS functionality for the record
4. **Get Password**: Click `Generate a DDNS key` or `Enable entry for DDNS` next to the record

```jsonc
{
    "dns": "he",
    "token": "your_ddns_key" // HE.net dynamic DNS password, no ID required
}
```

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "he",                        // Current provider
    "token": "your_ddns_key",      // HE.net dynamic DNS password
    "index4": ["public", 0],       // IPv4 address source, corresponds to A record value
    "ipv4": "ddns.newfuture.cc"    // IPv4 domain, corresponds to A record
}
```

### Parameter Description

| Parameter | Description      | Type           | Value Range/Options                     | Default   | Parameter Type |
| :-------: | :--------------- | :------------- | :------------------------------------- | :-------- | :------------- |
| dns       | Provider ID      | String         | `he`                                   | None      | Provider Param |
| token     | Authentication   | String         | HE.net DDNS password                   | None      | Provider Param |
| index4    | IPv4 Source      | Array          | [Reference](../json.en.md#ipv4-ipv6)  | `default` | Common Config  |
| index6    | IPv6 Source      | Array          | [Reference](../json.en.md#ipv4-ipv6)  | `default` | Common Config  |
| ipv4      | IPv4 Domain      | Array          | Domain list                            | None      | Common Config  |
| ipv6      | IPv6 Domain      | Array          | Domain list                            | None      | Common Config  |
| proxy     | Proxy Settings   | Array          | [Reference](../json.en.md#proxy)      | None      | Common Network |
| ssl       | SSL Verification | Boolean/String | `"auto"`, `true`, `false`              | `auto`    | Common Network |
| cache     | Cache Settings   | Boolean/String | `true`, `false`, `filepath`            | `true`    | Common Config  |
| log       | Log Config       | Object         | [Reference](../json.en.md#log)        | None      | Common Config  |

> **Parameter Type Description**:
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers
> - **Provider Param**: Supported by current provider, values related to current provider
>
> **Note**: HE.net does not support `id` parameter, only uses `token` (DDNS Key) for authentication; TTL is fixed at 300s.

## Usage Limitations

- ❌ **Does not support automatic record creation**: Must manually create DNS records in HE.net control panel first
- ⚠️ **Update only**: Can only update IP addresses of existing records, cannot create new records
- 🔑 **Dedicated password**: Each record has an independent DDNS password

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Authentication Failed**: Check if dynamic DNS password is correct, confirm record has DDNS functionality enabled
- **Domain Not Found**: Ensure record has been manually created in HE.net control panel, check domain spelling
- **Record Update Failed**: Check if record has dynamic DNS enabled, confirm password corresponds to correct record
- **Request Rate Limiting**: HE.net recommends update intervals of no less than 5 minutes, avoid frequent updates

### HE.net Response Codes

| Response Code   | Description           | Solution                    |
| :-------------- | :-------------------- | :-------------------------- |
| `good <ip>`     | Update successful     | Operation successful        |
| `nochg <ip>`    | IP address unchanged  | Operation successful        |
| `nohost`        | Hostname doesn't exist| Check record and DDNS setup |
| `badauth`       | Authentication failed | Check dynamic DNS password  |
| `badagent`      | Client disabled       | Contact HE.net support     |
| `abuse`         | Updates too frequent  | Increase update interval    |

## Support and Resources

- [HE.net Official Website](https://he.net/)
- [HE.net DNS Management](https://dns.he.net/)
- [HE.net DDNS Documentation](https://dns.he.net/docs.html)
- [HE.net Technical Support](https://he.net/contact.html)

> ⚠️ **Verification Pending Status**: HE.net Provider lacks sufficient real-world testing. It is recommended to conduct thorough testing before using in production environments. If you encounter issues, please provide feedback through [GitHub Issues](https://github.com/NewFuture/DDNS/issues).
