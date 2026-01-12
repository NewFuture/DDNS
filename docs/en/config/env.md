# DDNS Environment Variables Configuration

## Overview

DDNS supports configuration through environment variables with the following priority order: **[Command Line Arguments](cli.md) > [Configuration File](json.md) > Environment Variables**

All environment variables use the `DDNS_` prefix followed by the parameter name (recommended uppercase).

> `export DDNS_xxx="xxx"` command applies to the current host
> `docker run -e DDNS_xxx="xxx"` command applies to the container

## Complete Environment Variables List

| Environment Variable     | Accepted Values                                                                                     | Description                              | Example                                                     |
|--------------------------|------------------------------------------------------------------------------------------------------|------------------------------------------|-------------------------------------------------------------|
| `DDNS_CONFIG`            | File path, supports comma or semicolon-separated multiple paths, supports remote HTTP(S) URLs                                    | Specify config file path, supports multiple files and remote configs | `DDNS_CONFIG="config.json"` or `DDNS_CONFIG="cloudflare.json,dnspod.json"` <br> `DDNS_CONFIG="https://ddns.newfuture.cc/tests/config/debug.json"` |
| `DDNS_DNS`               | `51dns`, `alidns`, `aliesa`, `callback`, `cloudflare`, `debug`, `dnscom`, `dnspod_com`, `dnspod`, `edgeone`, `he`, `huaweidns`, `noip`, `tencentcloud` | [DNS Provider](./providers/)    | `DDNS_DNS=cloudflare`                                       |
| `DDNS_ID`                | Depends on the provider                                                                              | API account or ID                        | `DDNS_ID="user@example.com"`                                |
| `DDNS_TOKEN`             | Depends on the provider                                                                              | API token or secret                      | `DDNS_TOKEN="abcdef123456"`                                 |
| `DDNS_ENDPOINT`          | URL (starting with http or https)                                                                   | Custom API endpoint                       | `DDNS_ENDPOINT=https://api.dns.cn`                          |
| `DDNS_IPV4`              | Domains as array or comma-separated string                                                           | List of IPv4 domains                      | `DDNS_IPV4='["t.com","4.t.com"]'`                           |
| `DDNS_IPV6`              | Domains as array or comma-separated string                                                           | List of IPv6 domains                      | `DDNS_IPV6=t.com,6.t.com`                                   |
| `DDNS_INDEX4`            | Number, `default`, `public`, `url:`, `regex:`, `cmd:`, `shell:`, or an array of them                | IPv4 address detection methods            | `DDNS_INDEX4="[0,'regex:192.168.*']"`                       |
| `DDNS_INDEX6`            | Number, `default`, `public`, `url:`, `regex:`, `cmd:`, `shell:`, or an array of them                | IPv6 address detection methods            | `DDNS_INDEX6=public`                                        |
| `DDNS_TTL`               | Integer (seconds), varies by provider                                                                | DNS record TTL                            | `DDNS_TTL=600`                                              |
| `DDNS_LINE`              | ISP line such as: 电信, 联通, 移动, or provider-specific values                                     | DNS resolution line                       | `DDNS_LINE=电信`                                            |
| `DDNS_PROXY`             | `http://host:port` or `DIRECT`, multiple values separated by semicolons                             | HTTP proxy settings                       | `DDNS_PROXY="http://127.0.0.1:1080;DIRECT"`                 |
| `DDNS_CACHE`             | `true`, `false`, or file path                                                                        | Enable or specify cache file              | `DDNS_CACHE="/tmp/cache"`                                   |
| `DDNS_SSL`               | `true`, `false`, `auto`, or file path                                                                | SSL verification mode or certificate path | `DDNS_SSL=false`<br>`DDNS_SSL=/path/ca.crt`                 |
| `DDNS_CRON`              | Cron expression format string (Docker only)                                                          | Cron schedule for Docker container        | `DDNS_CRON="*/10 * * * *"`                                  |
| `DDNS_LOG_LEVEL`         | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`                                                     | Logging level                             | `DDNS_LOG_LEVEL="DEBUG"`                                    |
| `DDNS_LOG_FILE`          | File path                                                                                            | Output log file (default: stdout)         | `DDNS_LOG_FILE="/tmp/ddns.log"`                             |
| `DDNS_LOG_FORMAT`        | Python logging format string                                                                         | Log format template                       | `DDNS_LOG_FORMAT="%(message)s"`                             |
| `DDNS_LOG_DATEFMT`       | Date-time format string                                                                              | Log timestamp format                      | `DDNS_LOG_DATEFMT="%m-%d %H:%M"`                            |

## Basic Configuration Parameters

### Configuration File Path

#### DDNS_CONFIG

- **Type**: String
- **Required**: No
- **Default**: Search in default paths (`config.json`, `~/.ddns/config.json`, etc.)
- **Format**: Single file path, multiple file paths (separated by commas or semicolons), or remote HTTP(S) URLs
- **Description**: Specify configuration file path, supports multiple configuration files and remote configuration files
- **Examples**:

  ```bash
  # Single configuration file
  export DDNS_CONFIG="config.json"
  export DDNS_CONFIG="/path/to/ddns.json"
  
  # Remote configuration file
  export DDNS_CONFIG="https://ddns.newfuture.cc/tests/config/debug.json"
  export DDNS_CONFIG="https://user:password@config.example.com/ddns.json"
  
  # Multiple configuration files
  export DDNS_CONFIG="/etc/ddns/cloudflare.json,./dnspod.json"
  
  # Mixed local and remote configurations
  export DDNS_CONFIG="local.json,https://remote.example.com/config.json"
  ```

### Authentication Information

#### DDNS_ID

- **Type**: String
- **Required**: Yes (optional for some DNS providers)
- **Description**: API access ID or user identifier
- **Examples**:

  ```bash
  # Cloudflare (email address)
  export DDNS_ID="user@example.com"
  
  # DNSPod (numeric ID)
  export DDNS_ID="12345"
  
  # Alibaba Cloud (Access Key ID)
  export DDNS_ID="LTAI4xxxxxxxxxxxxx"
  
  # HE.net (can be empty)
  export DDNS_ID=""
  ```

#### DDNS_TOKEN

- **Type**: String
- **Required**: Yes
- **Description**: API authorization token or key
- **Examples**:

  ```bash
  # General API token
  export DDNS_TOKEN="abcdef1234567890"
  
  # Cloudflare API token
  export DDNS_TOKEN="1234567890abcdef_example_token"
  
  # Alibaba Cloud Secret Key
  export DDNS_TOKEN="secretkey1234567890"
  ```

### DNS Provider

#### DDNS_DNS

- **Type**: String
- **Required**: No
- **Default**: `dnspod`
- **Available Values**: `51dns`, `alidns`, `aliesa`, `callback`, `cloudflare`, `debug`, `dnscom`, `dnspod`, `dnspod_com`, `edgeone`, `he`, `huaweidns`, `noip`, `tencentcloud`
- **Description**: DNS service provider
- **Examples**:

  ```bash
  export DDNS_DNS="cloudflare"
  export DDNS_DNS="alidns"
  export DDNS_DNS="dnspod"
  ```

#### DDNS_ENDPOINT

- **Type**: String
- **Required**: No
- **Default**: None (uses default API endpoint for each DNS provider)
- **Description**: API endpoint URL for custom or private deployments
- **Examples**:

  ```bash
  # Custom Cloudflare endpoint
  export DDNS_ENDPOINT="https://api.private-cloudflare.com"
  
  # Private DNSPod deployment
  export DDNS_ENDPOINT="https://internal-dns-api.company.com"
  
  # Local testing endpoint
  export DDNS_ENDPOINT="http://localhost:8080/api"
  ```

### Custom Callback Configuration

When using `DDNS_DNS="callback"`, configure custom callbacks with these environment variables:

- **DDNS_ID**: Callback URL address with variable substitution support
- **DDNS_TOKEN**: POST request parameters (JSON string), empty for GET requests

For detailed configuration, see: [Callback Provider Configuration Documentation](providers/callback.md)

**Examples**:

```bash
# GET method callback
export DDNS_DNS="callback"
export DDNS_ID="https://api.example.com/ddns?domain=__DOMAIN__&ip=__IP__"
export DDNS_TOKEN=""

# POST method callback (JSON string)
export DDNS_DNS="callback"
export DDNS_ID="https://api.example.com/ddns"
export DDNS_TOKEN='{"api_key": "your_key", "domain": "__DOMAIN__", "ip": "__IP__"}'
```

**Supported Variable Substitutions**:

- `__DOMAIN__`: Full domain name
- `__IP__`: IP address (IPv4 or IPv6)
- `__RECORDTYPE__`: DNS record type
- `__TTL__`: Time to live (seconds)
- `__LINE__`: Resolution line
- `__TIMESTAMP__`: Current timestamp

## Domain Configuration

### IPv4 Domain List

#### DDNS_IPV4

- **Type**: Array (supports JSON/Python format)
- **Required**: No
- **Default**: `[]`
- **Description**: List of domains requiring IPv4 record updates
- **Examples**:

  ```bash
  # JSON array format (recommended)
  export DDNS_IPV4='["example.com", "www.example.com", "api.example.com"]'
  
  # Python list format
  export DDNS_IPV4="['example.com', 'www.example.com']"
  
  # Comma-separated string
  export DDNS_IPV4="example.com,www.example.com"
  
  # Single domain
  export DDNS_IPV4="example.com"
  ```

### IPv6 Domain List

#### DDNS_IPV6

- **Type**: Array (supports JSON/Python format)
- **Required**: No
- **Default**: `[]`
- **Description**: List of domains requiring IPv6 record updates
- **Examples**:

  ```bash
  # JSON array format
  export DDNS_IPV6='["example.com", "ipv6.example.com"]'
  
  # Comma-separated string
  export DDNS_IPV6="example.com,ipv6.example.com"
  
  # Single domain
  export DDNS_IPV6="ipv6.example.com"
  ```

## IP Detection Methods

### IPv4 Detection Method

#### DDNS_INDEX4

- **Type**: String or Array
- **Required**: No
- **Default**: `["default"]` (uses system's default external IP)
- **Description**: IPv4 address detection methods. Supports comma `,` or semicolon `;` separated string format
- **Special Note**: When value contains `regex:`, `cmd:`, or `shell:` prefix, separator splitting is not supported; the entire string is treated as a single configuration item
- **Examples**:

  ```bash
  # Use public IP detection
  export DDNS_INDEX4="public"
  
  # Multiple methods with fallback
  export DDNS_INDEX4='["public", "default"]'
  
  # Network interface index
  export DDNS_INDEX4="0"  # First network interface
  export DDNS_INDEX4="1"  # Second network interface
  
  # Custom URL
  export DDNS_INDEX4="url:https://api.ipify.org"
  
  # Regex pattern (no splitting)
  export DDNS_INDEX4="regex:192\\.168\\..*"
  
  # Command execution (no splitting)
  export DDNS_INDEX4="cmd:hostname -I | awk '{print \$1}'"
  
  # Shell command (no splitting)
  export DDNS_INDEX4="shell:ip route get 8.8.8.8 | awk '{print \$7}'"
  ```

### IPv6 Detection Method

#### DDNS_INDEX6

- **Type**: String or Array
- **Required**: No
- **Default**: `["default"]` (uses system's default external IPv6)
- **Description**: IPv6 address detection methods
- **Examples**:

  ```bash
  # Use public IPv6 detection
  export DDNS_INDEX6="public"
  
  # Network interface index
  export DDNS_INDEX6="0"
  
  # Custom IPv6 detection URL
  export DDNS_INDEX6="url:https://api6.ipify.org"
  
  # Multiple methods
  export DDNS_INDEX6='["public", "default"]'
  ```

## DNS Configuration

### TTL Setting

#### DDNS_TTL

- **Type**: Integer
- **Required**: No
- **Default**: None (uses DNS provider's default)
- **Description**: DNS record TTL (Time To Live) in seconds
- **Examples**:

  ```bash
  # 5 minutes
  export DDNS_TTL="300"
  
  # 10 minutes (commonly used)
  export DDNS_TTL="600"
  
  # 1 hour
  export DDNS_TTL="3600"
  ```

### Resolution Line

#### DDNS_LINE

- **Type**: String
- **Required**: No
- **Default**: None (uses default line)
- **Description**: DNS resolution line, ISP line selection
- **Examples**:

  ```bash
  # Default line
  export DDNS_LINE="default"
  
  # China Telecom
  export DDNS_LINE="telecom"
  
  # China Unicom
  export DDNS_LINE="unicom"
  
  # China Mobile
  export DDNS_LINE="mobile"
  
  # Overseas
  export DDNS_LINE="overseas"
  ```

## Network Configuration

### Proxy Settings

#### DDNS_PROXY

- **Type**: Array or String
- **Required**: No
- **Default**: None (no proxy)
- **Description**: HTTP proxy settings, tries multiple proxies until success
- **Examples**:

  ```bash
  # Single proxy
  export DDNS_PROXY="http://127.0.0.1:1080"
  
  # Multiple proxies with fallback
  export DDNS_PROXY="http://127.0.0.1:1080;http://127.0.0.1:8080;DIRECT"
  
  # JSON array format
  export DDNS_PROXY='["http://127.0.0.1:1080", "DIRECT"]'
  
  # SOCKS proxy
  export DDNS_PROXY="socks5://127.0.0.1:1080"
  
  # HTTP proxy with authentication
  export DDNS_PROXY="http://user:pass@proxy.example.com:8080"
  ```

### Cache Configuration

#### DDNS_CACHE

- **Type**: Boolean or String
- **Required**: No
- **Default**: `true`
- **Description**: Cache settings to avoid frequent updates
- **Examples**:

  ```bash
  # Enable cache (default location)
  export DDNS_CACHE="true"
  
  # Disable cache
  export DDNS_CACHE="false"
  
  # Custom cache file path
  export DDNS_CACHE="/var/cache/ddns/cache.json"
  
  # Use temporary directory
  export DDNS_CACHE="/tmp/ddns.cache"
  ```

### Docker Cron Schedule Configuration

#### DDNS_CRON

- **Type**: String
- **Required**: No
- **Default**: `*/5 * * * *` (every 5 minutes)
- **Description**: Cron schedule for scheduled tasks in Docker containers. Only effective in Docker environments. Uses standard cron expression format
- **Format**: `minute hour day month weekday`
- **Examples**:

  ```bash
  # Run every 10 minutes
  export DDNS_CRON="*/10 * * * *"
  
  # Run every hour
  export DDNS_CRON="0 * * * *"
  
  # Run once daily at 2 AM
  export DDNS_CRON="0 2 * * *"
  
  # Run every 15 minutes
  export DDNS_CRON="*/15 * * * *"
  
  # Run every 2 hours
  export DDNS_CRON="0 */2 * * *"
  ```

**Cron Expression Reference**:

| Field    | Allowed Values | Allowed Special Characters |
|----------|----------------|----------------------------|
| Minute   | 0-59           | * , - /                    |
| Hour     | 0-23           | * , - /                    |
| Day      | 1-31           | * , - /                    |
| Month    | 1-12           | * , - /                    |
| Weekday  | 0-7            | * , - /                    |

**Common Expressions**:
- `*/5 * * * *` - Every 5 minutes (default)
- `*/10 * * * *` - Every 10 minutes
- `*/15 * * * *` - Every 15 minutes
- `0 * * * *` - Every hour
- `0 */2 * * *` - Every 2 hours
- `0 0 * * *` - Daily at midnight
- `0 2 * * *` - Daily at 2 AM
- `0 0 * * 0` - Weekly on Sunday at midnight

**Note**: This environment variable only works in Docker containers and does not affect DDNS programs running through other methods.

## Logging Configuration

### Log Level

#### DDNS_LOG_LEVEL

- **Type**: String
- **Required**: No
- **Default**: `INFO`
- **Available Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Log level
- **Examples**:

  ```bash
  # Debug mode (most verbose)
  export DDNS_LOG_LEVEL="DEBUG"
  
  # Normal operation
  export DDNS_LOG_LEVEL="INFO"
  
  # Warnings only
  export DDNS_LOG_LEVEL="WARNING"
  
  # Errors only
  export DDNS_LOG_LEVEL="ERROR"
  ```

### Log File

#### DDNS_LOG_FILE

- **Type**: String
- **Required**: No
- **Default**: None (outputs to console)
- **Description**: Log file path
- **Examples**:

  ```bash
  # System log directory
  export DDNS_LOG_FILE="/var/log/ddns.log"
  
  # User home directory
  export DDNS_LOG_FILE="$HOME/ddns.log"
  
  # Temporary directory
  export DDNS_LOG_FILE="/tmp/ddns.log"
  ```

### Log Format

#### DDNS_LOG_FORMAT

- **Type**: String
- **Required**: No
- **Default**: `%(asctime)s %(levelname)s [%(module)s]: %(message)s`
- **Description**: Log format string
- **Examples**:

  ```bash
  # Simple format
  export DDNS_LOG_FORMAT="%(asctime)s: %(message)s"
  
  # Detailed format
  export DDNS_LOG_FORMAT="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  
  # JSON format
  export DDNS_LOG_FORMAT='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
  ```

#### DDNS_LOG_DATEFMT

- **Type**: String
- **Required**: No
- **Default**: `%Y-%m-%dT%H:%M:%S`
- **Description**: Date time format string
- **Examples**:

  ```bash
  # ISO format (default)
  export DDNS_LOG_DATEFMT="%Y-%m-%dT%H:%M:%S"
  
  # Standard format
  export DDNS_LOG_DATEFMT="%Y-%m-%d %H:%M:%S"
  
  # Short format
  export DDNS_LOG_DATEFMT="%m/%d %H:%M:%S"
  ```

## Complete Configuration Examples

### Basic Configuration

```bash
# Basic Cloudflare configuration
export DDNS_DNS="cloudflare"
export DDNS_ID="user@example.com"
export DDNS_TOKEN="your_cloudflare_token"
export DDNS_IPV4="example.com"
```

### Advanced Configuration

```bash
# Advanced configuration with multiple domains and custom settings
export DDNS_DNS="cloudflare"
export DDNS_TOKEN="your_api_token"
export DDNS_IPV4='["example.com", "www.example.com", "api.example.com"]'
export DDNS_IPV6='["ipv6.example.com"]'
export DDNS_INDEX4="public"
export DDNS_INDEX6="public"
export DDNS_TTL="600"
export DDNS_PROXY="http://127.0.0.1:1080;DIRECT"
export DDNS_CACHE="/var/cache/ddns.json"
export DDNS_LOG_LEVEL="DEBUG"
export DDNS_LOG_FILE="/var/log/ddns.log"
```

### Provider-Specific Examples

#### DNSPod Configuration

```bash
export DDNS_DNS="dnspod"
export DDNS_ID="12345"
export DDNS_TOKEN="your_dnspod_token"
export DDNS_IPV4="example.com"
export DDNS_LINE="默认"
```

#### Alibaba Cloud DNS Configuration

```bash
export DDNS_DNS="alidns"
export DDNS_ID="LTAI4xxxxxxxxxxxxx"
export DDNS_TOKEN="your_secret_key"
export DDNS_IPV4="example.com"
export DDNS_LINE="default"
```

#### Custom Callback Configuration

```bash
export DDNS_DNS="callback"
export DDNS_ID="https://api.example.com/webhook?domain=__DOMAIN__&ip=__IP__"
export DDNS_TOKEN=""
export DDNS_IPV4="example.com"
```

## Standard Environment Variables Support

DDNS also supports some standard environment variables commonly used in system environments:

| Standard Variable | DDNS Equivalent | Description |
|------------------|-----------------|-------------|
| `HTTP_PROXY` | `DDNS_PROXY` | HTTP proxy server |
| `HTTPS_PROXY` | `DDNS_PROXY` | HTTPS proxy server |
| `NO_PROXY` | - | Bypass proxy for these hosts |
| `PYTHONHTTPSVERIFY` | `DDNS_SSL` | Python HTTPS verification |

**Note**: DDNS-specific variables take priority over standard environment variables.

## Configuration Validation

When using environment variables, DDNS will validate the configuration and provide error messages for invalid values:

- **DNS Provider**: Must be one of the supported providers
- **Domains**: Must be valid domain names
- **TTL**: Must be a positive integer
- **Log Level**: Must be a valid log level
- **File Paths**: Must be accessible file paths

## See Also

- [Command Line Arguments](cli.md)
- [JSON Configuration File](json.md)
- [Docker Usage](docker.md)
- [Provider-specific Configuration](providers/)
