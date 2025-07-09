# DDNS JSON Configuration File Reference

This document provides detailed information about the DDNS JSON configuration file format and parameters. JSON configuration files have priority between command line arguments and environment variables.

## Basic Usage

By default, DDNS looks for a `config.json` file in the current directory. You can also specify a configuration file path using the `-c` parameter:

* Current directory `config.json` (note that Docker working directory is `/ddns/`)
* Current user directory `~/.ddns/config.json`
* Linux system directory `/etc/ddns/config.json`

> Note: When using configuration files in Docker, you need to mount the configuration file to the container's `/ddns/` directory through volume mapping. For details, please refer to the [Docker Usage Documentation](docker.en.md).

```bash
# Use default configuration file
# Will auto-generate configuration file if none exists
ddns

# Use specified configuration file
ddns -c /path/to/config.json

# Or using Python source code
python run.py -c /path/to/config.json
```

## JSON Schema

DDNS configuration files follow JSON Schema, and it's recommended to add the `$schema` field to your configuration file for editor auto-completion and validation:

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json"
}
```

## Configuration Parameters Table

| Key      | Type               | Required | Default Value | Description          | Notes                                                                                                                          |
| :------: | :----------------: | :------: | :-----------: | :------------------: | ------------------------------------------------------------------------------------------------------------------------------ |
| id       | string             | Yes      | None          | API Access ID        | Cloudflare uses email (leave empty when using Token)<br>HE.net can be empty<br>Huawei Cloud uses Access Key ID (AK)         |
| token    | string             | Yes      | None          | API Authorization Token | Some platforms call it secret key                                                                                           |
| endpoint | string             | No       | None          | API Endpoint URL     | For custom or private API deployments, uses default endpoint when empty                                                       |
| dns      | string             | No       | `"dnspod"`    | DNS Provider         | Available values: 51dns, alidns, aliesa, callback, cloudflare, debug, dnscom, dnspod_com, dnspod, he, huaweidns, noip, tencentcloud |
| ipv4     | array              | No       | `[]`          | IPv4 Domain List     | When `[]`, IPv4 address will not be retrieved and updated                                                                     |
| ipv6     | array              | No       | `[]`          | IPv6 Domain List     | When `[]`, IPv6 address will not be retrieved and updated                                                                     |
| index4   | string\|int\|array | No       | `["default"]` | IPv4 Detection Method | See detailed explanation below                                                                                                |
| index6   | string\|int\|array | No       | `["default"]` | IPv6 Detection Method | See detailed explanation below                                                                                                |
| ttl      | number             | No       | `null`        | DNS Resolution TTL    | In seconds, uses DNS default policy when not set                                                                             |
| line     | string             | No       | `null`        | DNS Resolution Line   | ISP line selection, supported values depend on DNS provider, e.g., `"default"`, `"telecom"`, `"unicom"`, `"mobile"`, etc.   |
| proxy    | string\|array      | No       | None          | HTTP Proxy           | Multiple proxies are tried one by one until success, `DIRECT` means direct connection                                        |
| ssl      | string\|boolean    | No       | `"auto"`      | SSL Certificate Verification | `true` (force verification), `false` (disable verification), `"auto"` (auto fallback), or custom CA certificate file path |
| debug    | boolean            | No       | `false`       | Enable Debug Mode    | Equivalent to setting log.level=DEBUG, setting this field in config file is ineffective, only `--debug` CLI parameter works |
| cache    | string\|bool       | No       | `true`        | Enable Record Caching | Normally enabled to avoid frequent updates, default location is `ddns.cache` in temp directory, can specify custom path     |
| log      | object             | No       | `null`        | Log Configuration (Optional) | Log configuration object, supports `level`, `file`, `format`, `datefmt` parameters                                      |

### log Object Parameters

| Key     | Type   | Required | Default Value                                   | Description            |
| :-----: | :----: | :------: | :-------------------------------------: | :--------------------: |
| level   | string | No       | `INFO`                                  | Log Level              |
| file    | string | No       | None                                    | Log File Path          |
| format  | string | No       | `%(asctime)s %(levelname)s [%(module)s]: %(message)s` | Log Format String |
| datefmt | string | No       | `%Y-%m-%dT%H:%M:%S`                     | Date Time Format       |

### index4 and index6 Parameters

The `index4` and `index6` parameters specify IP address detection methods and can use the following values:

* **Number** (e.g., `0`, `1`, `2`...): Use IP address of the Nth network interface
* **String**:
  * `"default"`: System's default external IP
  * **Comma or semicolon-separated strings**: Support using comma `,` or semicolon `;` to separate multiple detection methods, e.g., `"public,regex:192\\.168\\..*"`
* **Boolean**: `false` means disable updating corresponding IP type DNS records
* **Array**: Try different detection methods in order, use the first successful result

## DNS Provider Values

DDNS supports the following DNS providers:

* **51dns**: DNS.COM service (alias for dnscom)
* **alidns**: Alibaba Cloud DNS
* **aliesa**: Alibaba Cloud ESA (Edge Security Acceleration)
* **callback**: Custom callback/webhook
* **cloudflare**: Cloudflare DNS
* **debug**: Debug provider (prints IP without updating DNS)
* **dnscom**: DNS.COM service (same as 51dns)
* **dnspod**: DNSPod (China)
* **dnspod_com**: DNSPod International
* **he**: Hurricane Electric DNS
* **huaweidns**: Huawei Cloud DNS
* **noip**: No-IP Dynamic DNS
* **tencentcloud**: Tencent Cloud DNS

## Custom Callback Configuration

When `dns` is set to `callback`, you can configure custom callbacks as follows:

* `id` field: Fill in the callback URL starting with HTTP or HTTPS, supports variable substitution
* `token` field: POST request parameters (JSON object or JSON string), uses GET method when empty

For detailed configuration, please refer to: [Callback Provider Configuration Documentation](providers/callback.en.md)

Supported variable substitutions:

| Variable Name | Content | Description |
|---------------|---------|-------------|
| `__DOMAIN__` | Full domain name | e.g., `www.example.com` |
| `__IP__` | IP address | IPv4 or IPv6 address |
| `__RECORDTYPE__` | DNS record type | e.g., `A`, `AAAA`, `CNAME` |
| `__TTL__` | Time to live | TTL value in seconds |
| `__LINE__` | Resolution line | ISP line identifier |
| `__TIMESTAMP__` | Current timestamp | Unix timestamp |

## Configuration Examples

### Basic Configuration

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "dns": "cloudflare",
  "id": "user@example.com",
  "token": "your_cloudflare_token",
  "ipv4": ["example.com"]
}
```

### Advanced Configuration

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "dns": "cloudflare",
  "id": "user@example.com",
  "token": "your_cloudflare_token",
  "ipv4": ["example.com", "www.example.com", "api.example.com"],
  "ipv6": ["ipv6.example.com"],
  "index4": ["public", "default"],
  "index6": "public",
  "ttl": 600,
  "proxy": ["127.0.0.1:1080", "DIRECT"],
  "cache": "/var/cache/ddns.json",
  "ssl": true,
  "log": {
    "level": "INFO",
    "file": "/var/log/ddns.log",
    "format": "%(asctime)s [%(levelname)s] %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S"
  }
}
```

### Provider-Specific Examples

#### Cloudflare (Email + API Key)

```json
{
  "dns": "cloudflare",
  "id": "user@example.com",
  "token": "your_api_key",
  "ipv4": ["example.com", "www.example.com"]
}
```

#### Cloudflare (API Token Only)

```json
{
  "dns": "cloudflare",
  "token": "your_api_token",
  "ipv4": ["example.com", "www.example.com"]
}
```

#### DNSPod

```json
{
  "dns": "dnspod",
  "id": "12345",
  "token": "your_dnspod_token",
  "ipv4": ["example.com"],
  "line": "默认"
}
```

#### Alibaba Cloud DNS

```json
{
  "dns": "alidns",
  "id": "LTAI4xxxxxxxxxxxxx",
  "token": "your_secret_key",
  "ipv4": ["example.com"],
  "line": "default"
}
```

#### Custom Callback (GET)

```json
{
  "dns": "callback",
  "id": "https://api.example.com/ddns?domain=__DOMAIN__&ip=__IP__",
  "token": "",
  "ipv4": ["example.com"]
}
```

#### Custom Callback (POST)

```json
{
  "dns": "callback",
  "id": "https://api.example.com/ddns",
  "token": {
    "api_key": "your_key",
    "domain": "__DOMAIN__",
    "ip": "__IP__",
    "timestamp": "__TIMESTAMP__"
  },
  "ipv4": ["example.com"]
}
```

#### Custom Endpoint

```json
{
  "dns": "cloudflare",
  "endpoint": "https://api.private-cloudflare.com",
  "token": "your_token",
  "ipv4": ["example.com"]
}
```

### IP Detection Configuration

#### Multiple Detection Methods

```json
{
  "dns": "cloudflare",
  "token": "your_token",
  "ipv4": ["example.com"],
  "index4": ["public", "default", "regex:192\\.168\\..*"],
  "index6": ["public", 0, 1]
}
```

#### Custom URL Detection

```json
{
  "dns": "cloudflare",
  "token": "your_token",
  "ipv4": ["example.com"],
  "index4": "url:https://api.ipify.org",
  "index6": "url:https://api6.ipify.org"
}
```

#### Command-based Detection

```json
{
  "dns": "cloudflare",
  "token": "your_token",
  "ipv4": ["example.com"],
  "index4": "cmd:hostname -I | awk '{print $1}'",
  "index6": "cmd:ip -6 addr show | grep global | awk '{print $2}' | cut -d/ -f1"
}
```

### Network Configuration

#### Proxy Configuration

```json
{
  "dns": "cloudflare",
  "token": "your_token",
  "ipv4": ["example.com"],
  "proxy": [
    "127.0.0.1:1080",
    "socks5://127.0.0.1:1081",
    "http://user:pass@proxy.example.com:8080",
    "DIRECT"
  ]
}
```

#### SSL Configuration

```json
{
  "dns": "cloudflare",
  "token": "your_token",
  "ipv4": ["example.com"],
  "ssl": "auto"
}
```

Or with custom CA certificate:

```json
{
  "dns": "cloudflare",
  "token": "your_token",
  "ipv4": ["example.com"],
  "ssl": "/path/to/custom-ca.pem"
}
```

### Logging Configuration

#### Basic Logging

```json
{
  "dns": "cloudflare",
  "token": "your_token",
  "ipv4": ["example.com"],
  "log": {
    "level": "DEBUG",
    "file": "/var/log/ddns.log"
  }
}
```

#### Advanced Logging

```json
{
  "dns": "cloudflare",
  "token": "your_token",
  "ipv4": ["example.com"],
  "log": {
    "level": "INFO",
    "file": "/var/log/ddns.log",
    "format": "[%(asctime)s] %(levelname)s: %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S"
  }
}
```

### Cache Configuration

#### Default Cache

```json
{
  "dns": "cloudflare",
  "token": "your_token",
  "ipv4": ["example.com"],
  "cache": true
}
```

#### Custom Cache Location

```json
{
  "dns": "cloudflare",
  "token": "your_token",
  "ipv4": ["example.com"],
  "cache": "/var/cache/ddns/custom.json"
}
```

#### Disable Cache

```json
{
  "dns": "cloudflare",
  "token": "your_token",
  "ipv4": ["example.com"],
  "cache": false
}
```

## Configuration File Locations

DDNS searches for configuration files in the following order:

1. **Command line specified**: `-c /path/to/config.json`
2. **Current directory**: `./config.json`
3. **User home directory**: `~/.ddns/config.json`
4. **System directory**: `/etc/ddns/config.json`

The first found configuration file will be used.

## Configuration Validation

DDNS validates the configuration file and provides helpful error messages for invalid configurations:

* **Required fields**: `id` and `token` are required for most providers
* **Domain format**: Domains must be valid DNS names
* **Array format**: Domain lists must be arrays of strings
* **Number format**: TTL must be a positive integer
* **URL format**: Endpoints must be valid URLs

## Configuration Generation

You can generate a template configuration file using the `--new-config` command line parameter:

```bash
# Generate default config.json
ddns --new-config

# Generate with custom filename
ddns --new-config=my-config.json

# Generate with pre-filled values
ddns --new-config --dns cloudflare --id user@example.com --token your_token
```

## Configuration Priority

DDNS uses the following priority order (highest to lowest):

1. **Command line arguments** (highest priority)
2. **JSON configuration file**
3. **Environment variables** (lowest priority)

This means command line arguments will override any settings in configuration files or environment variables.

## Best Practices

### Security

- Store sensitive tokens in separate files with restricted permissions
* Use environment variables for tokens in containerized environments
* Never commit configuration files with real tokens to version control

### Reliability

- Use multiple IP detection methods for fallback
* Configure appropriate TTL values for your use case
* Enable caching to avoid rate limiting
* Set up proper logging for troubleshooting

### Performance

- Use `"auto"` SSL mode for automatic fallback
* Configure multiple proxy servers for redundancy
* Set reasonable TTL values to balance speed and reliability

## See Also

* [Command Line Arguments](cli.en.md)
* [Environment Variables Configuration](env.en.md)
* [Docker Usage](docker.en.md)
* [Provider-specific Configuration](providers/)
