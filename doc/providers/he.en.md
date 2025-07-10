# HE.net (Hurricane Electric) Configuration Guide English Documentation

> ⚠️ **Important Note: This provider is awaiting verification**
>
> HE.net lacks sufficient real-world testing. Please test carefully before use. If you encounter issues, please report them in [GitHub Issues](https://github.com/NewFuture/DDNS/issues).

## Overview

Hurricane Electric (HE.net) is a well-known network service provider offering free DNS hosting services with dynamic DNS update support. This DDNS project supports authentication through HE.net's dynamic DNS password.

**Important Limitation**: HE.net **does not support automatic record creation** - you must manually create DNS records in the HE.net control panel first.

## Authentication Methods

### Dynamic DNS Password Authentication

HE.net uses a dedicated dynamic DNS password for authentication, not your account login password.

#### Obtaining Dynamic DNS Password

1. Log in to [HE.net DNS Management](https://dns.he.net/)
2. Select the domain you want to manage
3. Find the record you need to update dynamically
4. Click **Generate a DDNS key** or **Enable entry for DDNS** next to the record
5. Record the generated DDNS password

#### Configuration Example

```json
{
    "dns": "he",
    "token": "your_ddns_password"
}
```

- `token`: HE.net dynamic DNS password
- `dns`: Fixed as `"he"`
- `id`: **Not required** (HE.net doesn't use user ID)

## Complete Configuration Example

```json
{
  "token": "your_ddns_password",
  "dns": "he",
  "index4": ["public"],
  "index6": ["public"],
  "ipv4": ["home.example.com", "server.example.com"],
  "ipv6": ["home-v6.example.com"],
  "ttl": 300
}
```

## Optional Parameters

| Parameter | Description              | Range        | Default | Notes                                      |
|-----------|--------------------------|--------------|---------|--------------------------------------------|
| `ttl`     | DNS record TTL (seconds) | 300 - 86400  | auto    | Actual TTL determined by HE.net record settings |

## Usage Limitations

### Important Limitations

- ❌ **Does not support automatic record creation**: You must manually create DNS records in the HE.net control panel first
- ⚠️ **Update only**: Can only update the IP address of existing records, cannot create new records
- 🔑 **Dedicated password**: Each record has an independent DDNS password

### Usage Steps

1. **Create DNS record**: Manually create A or AAAA records in the HE.net control panel
2. **Enable DDNS**: Enable dynamic DNS functionality for the record
3. **Get password**: Record the DDNS password for each record
4. **Configure DDNS**: Use the corresponding password to configure the dynamic DNS client

## Troubleshooting

### Common Issues

#### "Authentication Failed" or No Response

- Check if the DDNS password is correct
- Confirm that dynamic DNS functionality is enabled for the record
- Verify that the domain and subdomain spelling is correct

#### "Record Not Found"

- Confirm that the corresponding DNS record has been created in the HE.net control panel
- Check if the record type matches (A record for IPv4, AAAA record for IPv6)
- Verify that the domain status in HE.net is normal

#### "Update Failed"

- Check if network connection is normal
- Confirm that the IP address format is correct
- Verify that the target record has DDNS functionality enabled

#### "Rate Limiting"

- HE.net has limits on update frequency, recommend at least 5-minute intervals
- Avoid frequent unnecessary updates
- Check if other programs are simultaneously updating the same record

### Debug Mode

Enable debug logging to see detailed information:

```sh
ddns --debug
```

### HE.net Response Codes

| Response | Meaning | Status |
|----------|---------|---------|
| `good <ip>` | Update successful | ✅ |
| `nochg <ip>` | IP address unchanged | ✅ |
| `nohost` | Hostname doesn't exist or DDNS not enabled | ❌ |
| `badauth` | Authentication failed | ❌ |
| `badagent` | Client disabled | ❌ |
| `abuse` | Updates too frequent | ❌ |

## API Limitations

- **Update frequency**: Recommend intervals of no less than 5 minutes
- **Record count**: Free accounts support multiple domains and records
- **Response format**: Plain text response, not JSON format

## Support and Resources

- [HE.net Official Website](https://he.net/)
- [HE.net DNS Management](https://dns.he.net/)
- [HE.net DDNS Documentation](https://dns.he.net/docs.html)
- [HE.net Technical Support](https://he.net/contact.html)

> HE.net is a professional network service provider offering stable DNS hosting services. Please ensure you have correctly configured DNS records in the control panel and enabled DDNS functionality before use.
