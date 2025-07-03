# No-IP Provider Configuration Guide

No-IP is a popular dynamic DNS service that provides simple HTTP-based API for updating DNS records. This DDNS project supports the standard No-IP Dynamic Update Protocol.

## Basic Configuration

### Configuration Parameters

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `id` | Your No-IP username | ✅ | `"your_username"` |
| `token` | Your No-IP password | ✅ | `"your_password"` |
| `dns` | Provider name | ✅ | `"noip"` |

### Minimal Configuration Example

```json
{
    "id": "your_username",
    "token": "your_password", 
    "dns": "noip",
    "ipv4": ["subdomain.example.com"],
    "ipv6": ["ipv6.example.com"]
}
```

## Authentication Methods

### Username and Password

No-IP uses your account username and password for authentication. This is sent via HTTP Basic Authentication.

#### How to Obtain Credentials

1. **Sign up for No-IP Account**
   - Visit [No-IP website](https://www.noip.com/)
   - Create a free account or upgrade to paid service

2. **Create Dynamic DNS Hostname**
   - Log in to your No-IP account
   - Go to "Dynamic DNS" > "No-IP Hostnames"
   - Create a new hostname or use existing ones

3. **Use Account Credentials**
   - **Username**: Your No-IP account username or email
   - **Password**: Your No-IP account password

#### Configuration Example

```json
{
    "dns": "noip",
    "id": "your_username",
    "token": "your_password"
}
```

**Parameters:**

- `id`: Your No-IP account username
- `token`: Your No-IP account password
- `dns`: Must be set to `"noip"`, `"no-ip"`, or `"noip_com"`

## Response Codes

The No-IP API returns plain text responses with the following meanings:

| Response | Meaning | Action |
|----------|---------|--------|
| `good <ip>` | Update successful | ✅ Success |
| `nochg <ip>` | IP address is current, no update performed | ✅ Success (no change needed) |
| `nohost` | Hostname supplied does not exist | ❌ Check hostname spelling |
| `badauth` | Invalid username/password combination | ❌ Check credentials |
| `badagent` | Client disabled | ❌ Contact No-IP support |
| `!donator` | Feature not available (requires upgraded account) | ❌ Upgrade account |
| `abuse` | Username is blocked due to abuse | ❌ Contact No-IP support |

## Complete Configuration Examples

### IPv4 Only

```json
{
    "dns": "noip",
    "id": "myusername",
    "token": "mypassword",
    "ipv4": ["home.example.com", "server.example.com"],
    "ttl": 300
}
```

### IPv4 and IPv6

```json
{
    "dns": "noip", 
    "id": "myusername",
    "token": "mypassword",
    "ipv4": ["home.example.com"],
    "ipv6": ["ipv6.example.com"],
    "ttl": 600
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
        "server.example.com", 
        "nas.example.com"
    ],
    "debug": true
}
```

## Provider Aliases

The following provider names are supported and equivalent:

- `"noip"` (primary)
- `"no-ip"` (alias)
- `"noip_com"` (alias)

## API Details

- **API Endpoint**: `https://dynupdate.no-ip.com/nic/update`
- **Method**: GET
- **Authentication**: HTTP Basic Auth
- **Parameters**: `hostname` (domain name), `myip` (IP address)

## Troubleshooting

### Common Issues

1. **"badauth" Response**
   - Verify your No-IP username and password are correct
   - Ensure you can log in to the No-IP website with the same credentials

2. **"nohost" Response**
   - Check that the hostname exists in your No-IP account
   - Verify hostname spelling in configuration

3. **"!donator" Response**
   - Feature requires a paid No-IP account
   - Upgrade your account or use basic features only

4. **"abuse" Response**
   - Your account has been flagged for abuse
   - Contact No-IP customer support

### Debug Mode

Enable debug mode to see detailed API responses:

```json
{
    "dns": "noip",
    "id": "myusername",
    "token": "mypassword", 
    "ipv4": ["test.example.com"],
    "debug": true
}
```

## Supported Features

- ✅ IPv4 address updates
- ✅ IPv6 address updates  
- ✅ Multiple hostname support
- ✅ Custom TTL (if supported by account type)
- ✅ Comprehensive error handling
- ✅ HTTP Basic Authentication

## Limitations

- No-IP free accounts have limited features
- Some advanced features require paid accounts
- Rate limiting may apply (refer to No-IP documentation)

## Related Links

- [No-IP Official Website](https://www.noip.com/)
- [No-IP Dynamic Update API Documentation](https://www.noip.com/integrate/request)
- [No-IP Support](https://www.noip.com/support)

## Examples

### Basic Setup

```bash
# Configuration file: config.json
{
    "dns": "noip",
    "id": "your_username",
    "token": "your_password",
    "ipv4": ["home.your-domain.com"]
}

# Run DDNS
python run.py -c config.json
```

### Advanced Setup with Multiple Domains

```json
{
    "dns": "noip",
    "id": "your_username", 
    "token": "your_password",
    "ipv4": [
        "home.your-domain.com",
        "server.your-domain.com"
    ],
    "ipv6": ["ipv6.your-domain.com"],
    "ttl": 300,
    "proxy": "",
    "debug": false
}
```