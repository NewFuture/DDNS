# No-IP Configuration Guide

## Overview

No-IP is a popular dynamic DNS service that supports the standard DDNS dynamic update protocol with Basic Auth authentication. This DDNS project supports authentication through No-IP username and password or DDNS KEY.

## Authentication Methods

### Username and Password Authentication

Uses No-IP account username and password for authentication, which is the simplest authentication method.

#### Getting Authentication Information

1. Register or log in to [No-IP website](https://www.noip.com/)
2. Use your registered username and password
3. Create hostnames in the control panel

#### Configuration Example

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

### DDNS KEY Authentication (Recommended)

Uses DDNS ID and DDNS KEY for authentication, which is more secure.

#### Getting DDNS KEY

1. Log in to [No-IP website](https://www.noip.com/)
2. Go to **Dynamic DNS** > **No-IP Hostnames**
3. Create or edit dynamic DNS hostname
4. Generate DDNS KEY for API authentication

#### Configuration Example

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

## Complete Configuration Examples

### Basic Configuration

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
    "ipv4": ["home.example.com"],
    "ipv6": ["home-v6.example.com"],
    "index4": ["public"],
    "index6": ["public"],
    "ttl": 300
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

### TTL (Time To Live)

```json
{
    "ttl": 300
}
```

- **Range**: 60-86400 seconds
- **Default**: 300 seconds
- **Recommended**: 300-600 seconds for dynamic DNS

### Record Type

```json
{
    "record_type": "A"
}
```

- **Supported Types**: A, AAAA
- **Default**: A (IPv4)
- Use "AAAA" for IPv6 addresses

## Permission Requirements

Ensure the No-IP account has the following permissions:

- **Hostname Management**: Ability to create and manage dynamic DNS hostnames
- **DDNS Updates**: Dynamic DNS update permissions

You can view and manage hostnames in the [No-IP Control Panel](https://www.noip.com/members/).

## Response Codes

| Response | Meaning | Status |
|----------|---------|--------|
| `good <ip>` | Update successful | ✅ |
| `nochg <ip>` | IP unchanged | ✅ |
| `nohost` | Hostname not found | ❌ |
| `badauth` | Authentication failed | ❌ |
| `badagent` | Client disabled | ❌ |
| `!donator` | Paid account required | ❌ |
| `abuse` | Account banned | ❌ |

## Troubleshooting

- **Authentication failed (badauth)**: Check username and password
- **Hostname not found (nohost)**: Check domain spelling
- **Paid feature required (!donator)**: Upgrade account
- **Account banned (abuse)**: Contact support

## Related Links

- [No-IP Website](https://www.noip.com/)
- [API Documentation](https://www.noip.com/integrate/request)
