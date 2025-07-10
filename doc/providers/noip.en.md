# No-IP Provider Configuration Guide

No-IP is a popular dynamic DNS service that supports the standard No-IP Dynamic Update Protocol.

## Configuration Parameters

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `dns` | Provider name | ✅ | `"noip"` |
| `id` | No-IP username or DDNS ID | ✅ | `"your_username"` |
| `token` | No-IP password or DDNS KEY | ✅ | `"your_password"` |
| `endpoint` | Custom API endpoint URL | 🔘 | `"https://dynupdate.no-ip.com"` |

## Configuration Examples

### Basic Configuration

```json
{
    "dns": "noip",
    "id": "your_username",
    "token": "your_password",
    "ipv4": ["home.example.com"],
    "index4": ["default"]
}
```

### Multiple Domains

```json
{
    "dns": "noip",
    "id": "myusername", 
    "token": "mypassword",
    "ipv4": [
        "home.example.com",
        "office.example.com"
    ],
    "ipv6": ["ipv6.example.com"]
}
```

### Custom Service Endpoint

For other No-IP compatible DDNS services or custom deployments, you can specify different API endpoints:

```json
{
    "dns": "noip",
    "id": "your_username",
    "token": "your_password", 
    "endpoint": "https://your-ddns-server.com",
    "ipv4": ["home.example.com"]
}
```

## Authentication Methods

### Username and Password

Uses No-IP account username and password for authentication.

### DDNS KEY Authentication (Recommended)

Uses DDNS ID and DDNS KEY for authentication, which is more secure.

How to obtain: Login to [No-IP website](https://www.noip.com/) → Create Dynamic DNS hostname → Generate DDNS KEY

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
