# No-IP Configuration Guide

## Overview

No-IP is a popular dynamic DNS service that supports the standard DDNS dynamic update protocol with Basic Auth authentication. This DDNS project supports authentication through No-IP username and password or DDNS KEY.

## Authentication Methods

1. Register or log in to [No-IP website](https://www.noip.com/)
2. Use your registered username and password
3. Create hostnames in the control panel

### Username and Password Authentication

Uses No-IP account username and password for authentication, which is the simplest authentication method.

```json
{
    "dns": "noip",
    "id": "your_username",
    "token": "your_password"
}
```

- `id`: No-IP username
- `token`: No-IP password
- `dns`: Fixed as `"noip"`

### DDNS KEY + ID Authentication (Recommended)

Uses DDNS ID and DDNS KEY for authentication, which is more secure.

#### Getting DDNS KEY

1. Log in to [No-IP website](https://www.noip.com/)
2. Go to **Dynamic DNS** > **No-IP Hostnames**
3. Create or edit dynamic DNS hostname
4. Generate DDNS KEY for API authentication

```json
{
    "dns": "noip",
    "id": "your_ddns_id",
    "token": "your_ddns_key"
}
```

- `id`: DDNS ID
- `token`: DDNS KEY
- `dns`: Fixed as `"noip"`

## Complete Configuration Example

```json
{
    "id": "myusername",
    "token": "mypassword",
    "dns": "noip",
    "ipv4": ["home.example.com", "office.example.com"],
    "index4": ["public"]
}
```

### Configuration with Optional Parameters

```json
{
    "id": "your_username",
    "token": "your_password",
    "dns": "noip",
    "endpoint": "https://dynupdate.no-ip.com",
    "index4": ["public"],
    "index6": ["public"],
    "ipv4": ["home.example.com"],
    "ipv6": ["home-v6.example.com"]
}
```

## Optional Parameters

### Custom API Endpoint

```json
{
    "endpoint": "https://dynupdate.no-ip.com"
}
```

No-IP supports custom API endpoints, suitable for:

#### Official Endpoints

- **Default Endpoint**: `https://dynupdate.no-ip.com` (Recommended)
- **Backup Endpoint**: `https://dynupdate2.no-ip.com`

#### Compatible Services

```json
{
    "dns": "noip",
    "id": "your_username",
    "token": "your_password",
    "endpoint": "https://your-ddns-server.com",
    "ipv4": ["home.example.com"]
}
```

For other No-IP compatible DDNS services or custom deployments, you can specify different API endpoints.

## Troubleshooting

### Debug Mode

Enable debug logging to see detailed information:

```sh
ddns --debug
```

### No-IP Response Codes

| Response | Meaning | Status |
|----------|---------|--------|
| `good <ip>` | Update successful | ✅ |
| `nochg <ip>` | IP address unchanged | ✅ |
| `nohost` | Hostname does not exist | ❌ |
| `badauth` | Authentication failed | ❌ |
| `badagent` | Client disabled | ❌ |
| `!donator` | Paid account feature required | ❌ |
| `abuse` | Account banned or abused | ❌ |

## API Limitations

- **Update Frequency**: Recommended interval of at least 5 minutes
- **Free Accounts**: Must login at least once within 30 days for confirmation
- **Hostname Count**: Free accounts limited to 3 hostnames

## Support and Resources

- [No-IP Website](https://www.noip.com/)
- [No-IP API Documentation](https://www.noip.com/integrate/request)
- [No-IP Control Panel](https://www.noip.com/members/)
- [No-IP Technical Support](https://www.noip.com/support)

> It's recommended to use DDNS KEY authentication for improved security. Regularly check hostname status to ensure proper service operation.
