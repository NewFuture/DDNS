# No-IP Configuration Guide

## Overview

No-IP is a popular dynamic DNS service provider that supports the standard DDNS dynamic update protocol with Basic Auth authentication, supporting dynamic DNS record creation and updates. This DDNS project supports authentication through username and password or DDNS KEY.

Official Links:

- Official Website: <https://www.noip.com/>
- Provider Console: <https://www.noip.com/members/>

## Authentication Information

### 1. DDNS KEY + ID Authentication (Recommended)

Use DDNS ID and DDNS KEY for authentication, which is more secure.

#### Getting DDNS KEY

1. Log in to [No-IP website](https://www.noip.com/)
2. Go to **Dynamic DNS** > **No-IP Hostnames**
3. Create or edit dynamic DNS hostname
4. Generate DDNS KEY for API authentication

```jsonc
{
    "dns": "noip",
    "id": "your_ddns_id",    // DDNS ID
    "token": "your_ddns_key" // DDNS KEY
}
```

### 2. Username and Password Authentication

Use No-IP account username and password for authentication, which is the simplest authentication method.

#### Account Password

1. Register or log in to [No-IP website](https://www.noip.com/)
2. Use your registered username and password
3. Create hostnames in the control panel

```jsonc
{
    "dns": "noip",
    "id": "your_username",    // No-IP username
    "token": "your_password"  // No-IP password
}
```

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "noip",                      // Current provider
    "id": "myusername",                 // No-IP username or DDNS ID
    "token": "mypassword",              // No-IP password or DDNS KEY
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["all.ddnskey.com"],           // IPv4 domain
    "ipv6": ["all.ddnskey.com"],           // IPv6 domain
    "endpoint": "https://dynupdate.no-ip.com" // API endpoint
}
```

### Parameter Description

| Parameter | Description      | Type           | Value Range/Options                     | Default                       | Parameter Type |
| :-------: | :--------------- | :------------- | :------------------------------------- | :---------------------------- | :------------- |
| dns       | Provider ID      | String         | `noip`                                 | None                          | Provider Param |
| id        | Authentication ID| String         | No-IP username or DDNS ID              | None                          | Provider Param |
| token     | Authentication Key| String        | No-IP password or DDNS KEY             | None                          | Provider Param |
| index4    | IPv4 Source      | Array          | [Reference](../config/json.en.md#ipv4-ipv6)  | `default`                     | Common Config  |
| index6    | IPv6 Source      | Array          | [Reference](../config/json.en.md#ipv4-ipv6)  | `default`                     | Common Config  |
| ipv4      | IPv4 Domain      | Array          | Domain list                            | `all.ddnskey.com`             | Common Config  |
| ipv6      | IPv6 Domain      | Array          | Domain list                            | `all.ddnskey.com`             | Common Config  |
| proxy     | Proxy Settings   | Array          | [Reference](../config/json.en.md#proxy)      | None                          | Common Network |
| ssl       | SSL Verification | Boolean/String | `"auto"`, `true`, `false`              | `auto`                        | Common Network |
| cache     | Cache Settings   | Boolean/String | `true`, `false`, `filepath`            | `true`                        | Common Config  |
| log       | Log Config       | Object         | [Reference](../config/json.en.md#log)        | None                          | Common Config  |

> **Parameter Type Description**:
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers
> - **Provider Param**: Supported by current provider, values related to current provider

## Troubleshooting

### Debug Mode

Enable debug logging to view detailed information:

```sh
ddns -c config.json --debug
```

### Common Issues

- **Authentication Failed**: Check if username and password are correct, confirm account has not been disabled
- **Hostname Not Found**: Ensure hostname has been created in No-IP control panel, check spelling accuracy
- **Update Failed**: Check hostname status is normal, confirm account has sufficient permissions
- **Request Rate Limiting**: No-IP recommends update intervals of no less than 5 minutes, avoid frequent updates

### No-IP Response Codes

| Response Code   | Description              | Solution                |
| :-------------- | :----------------------- | :---------------------- |
| `good <ip>`     | Update successful        | Operation successful    |
| `nochg <ip>`    | IP address unchanged     | Operation successful    |
| `nohost`        | Hostname does not exist  | Check hostname settings |
| `badauth`       | Authentication failed    | Check username password |
| `badagent`      | Client disabled          | Contact No-IP support   |
| `!donator`      | Paid account feature required | Upgrade account type |
| `abuse`         | Account banned or abused | Contact No-IP support   |

## API Limitations

- **Update Frequency**: Recommended interval of at least 5 minutes
- **Free Accounts**: Must login at least once within 30 days for confirmation
- **Hostname Count**: Free accounts limited to 3 hostnames

## Support and Resources

- [No-IP Official Website](https://www.noip.com/)
- [No-IP API Documentation](https://www.noip.com/integrate/request)
- [No-IP Control Panel](https://www.noip.com/members/)
- [No-IP Technical Support](https://www.noip.com/support)

> **Recommendation**: It's recommended to use DDNS KEY authentication for improved security. Regularly check hostname status to ensure proper service operation.
