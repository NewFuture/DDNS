# DDNS Environment Variables Configuration

## Overview

DDNS supports configuration through environment variables with the following priority order: **[Command Line Arguments](cli.en.md) > [Configuration File](json.en.md) > Environment Variables**

All environment variables use the `DDNS_` prefix followed by the parameter name (recommended uppercase).

> `export DDNS_xxx="xxx"` command applies to the current host
> `docker run -e DDNS_xxx="xxx"` command applies to the container

### Environment Variable Naming Rules

| Config Parameter | Environment Variable | Example |
|------------------|---------------------|---------|
| `id` | `DDNS_ID` or `ddns_id` | `DDNS_ID=12345` |
| `token` | `DDNS_TOKEN` or `ddns_token` | `DDNS_TOKEN=mytokenkey` |
| `log_level` | `DDNS_LOG_LEVEL` or `ddns_log_level` | `DDNS_LOG_LEVEL=DEBUG` |
| `log_file` | `DDNS_LOG_FILE` or `ddns_log_file` | `DDNS_LOG_FILE=/var/log/ddns.log` |

## Complete Environment Variables List

The following table lists all supported DDNS environment variables:

| Environment Variable | Type | Default Value | Description |
|---------------------|------|---------------|-------------|
| `DDNS_ID` | String | None | API access ID or user identifier |
| `DDNS_TOKEN` | String | None | API authorization token or key |
| `DDNS_DNS` | String | `dnspod` | DNS service provider |
| `DDNS_ENDPOINT` | String | None | API endpoint URL for custom or private API |
| `DDNS_IPV4` | Array/String | None | IPv4 domain list |
| `DDNS_IPV6` | Array/String | None | IPv6 domain list |
| `DDNS_INDEX4` | Array/String/Number | `["default"]` | IPv4 address detection methods |
| `DDNS_INDEX6` | Array/String/Number | `["default"]` | IPv6 address detection methods |
| `DDNS_TTL` | Integer | None | DNS resolution TTL time (seconds) |
| `DDNS_LINE` | String | None | DNS resolution line, ISP line selection |
| `DDNS_PROXY` | Array/String | None | HTTP proxy settings |
| `DDNS_CACHE` | Boolean/String | `true` | Cache settings |
| `DDNS_LOG_LEVEL` | String | `INFO` | Log level |
| `DDNS_LOG_FILE` | String | None | Log file path |
| `DDNS_LOG_FORMAT` | String | `%(asctime)s %(levelname)s [%(module)s]: %(message)s` | Log format string |
| `DDNS_LOG_DATEFMT` | String | `%Y-%m-%dT%H:%M:%S` | Date time format string |

### Parameter Value Examples

| Environment Variable | Possible Values | Example |
|---------------------|-----------------|---------|
| `DDNS_DNS` | 51dns, alidns, aliesa, callback, cloudflare, debug, dnscom, dnspod_com, he, huaweidns, noip, tencentcloud | `export DDNS_DNS="cloudflare"` |
| `DDNS_IPV4` | JSON array, comma-separated string | `export DDNS_IPV4='["example.com", "www.example.com"]'` |
| `DDNS_IPV6` | JSON array, comma-separated string | `export DDNS_IPV6="example.com,ipv6.example.com"` |
| `DDNS_INDEX4` | number, default, public, url:, regex:, cmd:, shell: | `export DDNS_INDEX4='["public", "regex:192\\.168\\..*"]'` |
| `DDNS_INDEX6` | number, default, public, url:, regex:, cmd:, shell: | `export DDNS_INDEX6="public"` |
| `DDNS_LINE` | Line names like default, telecom, unicom, mobile, etc. | `export DDNS_LINE="telecom"` |
| `DDNS_PROXY` | IP:port, DIRECT, semicolon-separated list | `export DDNS_PROXY="127.0.0.1:1080;DIRECT"` |
| `DDNS_CACHE` | true/false, file path | `export DDNS_CACHE="/path/to/cache.json"` |
| `DDNS_LOG_LEVEL` | DEBUG, INFO, WARNING, ERROR, CRITICAL | `export DDNS_LOG_LEVEL="DEBUG"` |
| `DDNS_LOG_FORMAT` | Format string | `export DDNS_LOG_FORMAT="%(asctime)s: %(message)s"` |
| `DDNS_LOG_DATEFMT` | Date format string | `export DDNS_LOG_DATEFMT="%Y-%m-%d %H:%M:%S"` |

## Basic Configuration Parameters

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
- **Available Values**: `51dns`, `alidns`, `aliesa`, `callback`, `cloudflare`, `debug`, `dnscom`, `dnspod`, `dnspod_com`, `he`, `huaweidns`, `noip`, `tencentcloud`
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

For detailed configuration, see: [Callback Provider Configuration Documentation](providers/callback.en.md)

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
  export DDNS_PROXY="127.0.0.1:1080"
  
  # Multiple proxies with fallback
  export DDNS_PROXY="127.0.0.1:1080;127.0.0.1:8080;DIRECT"
  
  # JSON array format
  export DDNS_PROXY='["127.0.0.1:1080", "DIRECT"]'
  
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
export DDNS_PROXY="127.0.0.1:1080;DIRECT"
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

- [Command Line Arguments](cli.en.md)
- [JSON Configuration File](json.en.md)
- [Docker Usage](docker.en.md)
- [Provider-specific Configuration](providers/)
