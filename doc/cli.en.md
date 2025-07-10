# DDNS Command Line Arguments Reference

This document provides detailed usage instructions for DDNS command line arguments. Command line arguments can override settings from configuration files and environment variables, having the **highest priority**.

## Basic Usage

Use `-h` to view the parameter list:

```bash
# ddns [options]
ddns -h
```

Or using Python source code:

```bash
# python run.py [options]
python -m ddns -h
```

## Parameter List

| Long Parameter  | Short | Type            | Description                                      |
| --------------- | ----- | --------------- | ------------------------------------------------ |
| `--help`        | `-h`  | Flag            | Show help message and exit                       |
| `--version`     | `-v`  | Flag            | Show version information and exit                |
| `--config`      | `-c`  | String          | Specify configuration file path                  |
| `--new-config`  |       | Flag/String     | Generate new configuration file                  |
| `--dns`         |       | Choice          | DNS service provider                             |
| `--endpoint`    |       | String          | API endpoint URL for custom or private API      |
| `--id`          |       | String          | API access ID or authorization account          |
| `--token`       |       | String          | API authorization token or key                  |
| `--ipv4`        |       | String List     | IPv4 domain list, repeat parameter for multiple |
| `--ipv6`        |       | String List     | IPv6 domain list, repeat parameter for multiple |
| `--index4`      |       | String/Number List | IPv4 address detection methods               |
| `--index6`      |       | String/Number List | IPv6 address detection methods               |
| `--ttl`         |       | Integer         | DNS record TTL time (seconds)                   |
| `--line`        |       | String          | DNS resolution line, ISP line selection         |
| `--proxy`       |       | String List     | HTTP proxy settings, repeat for multiple        |
| `--cache`       |       | Boolean/String  | Enable cache or custom cache path               |
| `--no-cache`    |       | Flag            | Disable cache (equivalent to --cache=false)     |
| `--ssl`         |       | String          | SSL certificate verification method              |
| `--no-ssl`      |       | Flag            | Disable SSL verification (equivalent to --ssl=false) |
| `--debug`       |       | Flag            | Enable debug mode (same as --log_level=DEBUG)   |
| `--log_file`    |       | String          | Log file path, outputs to console if not specified |
| `--log_level`   |       | String          | Log level                                        |
| `--log_format`  |       | String          | Log format string                                |
| `--log_datefmt` |       | String          | Date time format string                          |

Where `--debug`, `--new-config`, `--no-cache`, `--no-ssl`, `--help`, `--version` are command line only parameters.

### Parameter Value Examples

| Parameter    | Possible Values                              | Example                                   |
|--------------|----------------------------------------------|-------------------------------------------|
| `--dns`      | 51dns, alidns, aliesa, callback, cloudflare, debug, dnscom, dnspod_com, dnspod, he, huaweidns, noip, tencentcloud | `--dns cloudflare`                       |
| `--endpoint` | URL address                                  | `--endpoint https://api.private.com`     |
| `--id`       | API ID, email, Access Key                   | `--id user@example.com`                  |
| `--token`    | API Token, Secret Key                       | `--token abcdef123456`                   |
| `--new-config`| true, false, file path                     | `--new-config`, `--new-config=config.json` |
| `--ipv4`     | Domain names                                 | `--ipv4 example.com --ipv4 sub.example.com` |
| `--ipv6`     | Domain names                                 | `--ipv6 example.com`                     |
| `--index4`   | number, default, public, url:, regex:, cmd:, shell: | `--index4 public`, `--index4 "regex:192\\.168\\..*"` |
| `--index6`   | number, default, public, url:, regex:, cmd:, shell: | `--index6 0`, `--index6 public`           |
| `--ttl`      | Seconds                                      | `--ttl 600`                              |
| `--line`     | Line name                                    | `--line telecom`, `--line unicom`        |
| `--proxy`    | IP:port, DIRECT                              | `--proxy 127.0.0.1:1080 --proxy DIRECT` |
| `--cache`    | true, false, file path                      | `--cache=true`, `--cache=/path/to/cache.json` |
| `--ssl`      | true, false, auto, file path                | `--ssl false`, `--ssl /path/to/cert.pem` |
| `--debug`    | (no value)                                   | `--debug`                                |
| `--log_file` | File path                                    | `--log_file=/var/log/ddns.log`          |
| `--log_level`| DEBUG, INFO, WARNING, ERROR, CRITICAL       | `--log_level=DEBUG`                      |

## DNS Provider Values

DDNS supports the following DNS providers:

- **51dns** (alias for dnscom): DNS.COM service
- **alidns**: Alibaba Cloud DNS
- **aliesa**: Alibaba Cloud ESA (Edge Security Acceleration)
- **callback**: Custom callback/webhook
- **cloudflare**: Cloudflare DNS
- **debug**: Debug provider (prints IP without updating DNS)
- **dnscom**: DNS.COM service (same as 51dns)
- **dnspod**: DNSPod (China)
- **dnspod_com**: DNSPod International
- **he**: Hurricane Electric DNS
- **huaweidns**: Huawei Cloud DNS
- **noip**: No-IP Dynamic DNS
- **tencentcloud**: Tencent Cloud DNS

## IP Detection Methods

### IPv4/IPv6 Detection (`--index4`, `--index6`)

- **number** (0, 1, 2...): Use IP of the Nth network interface
- **default**: System's default external IP
- **public**: Get public IP from external services
- **url:ADDRESS**: Get IP from specific URL
- **regex:PATTERN**: Extract IP using regex pattern
- **cmd:COMMAND**: Get IP from command output
- **shell:COMMAND**: Get IP from shell command

Examples:

```bash
# Use public IP detection
ddns --dns cloudflare --index4 public

# Use multiple detection methods (fallback)
ddns --dns cloudflare --index4 public --index4 "regex:192\\.168\\..*"

# Use custom URL for IP detection
ddns --dns cloudflare --index4 "url:https://api.ipify.org"

# Use command output for IP
ddns --dns cloudflare --index4 "cmd:hostname -I | awk '{print $1}'"
```

## Usage Examples

### Basic Usage

```bash
# Update IPv4 record for a single domain
ddns --dns cloudflare --id user@example.com --token your_token --ipv4 example.com

# Update both IPv4 and IPv6 records
ddns --dns cloudflare --id user@example.com --token your_token \
     --ipv4 example.com --ipv6 example.com

# Use debug mode to see detailed output
ddns --debug --dns cloudflare --id user@example.com --token your_token --ipv4 example.com
```

### Multiple Domains

```bash
# Update multiple domains
ddns --dns cloudflare --id user@example.com --token your_token \
     --ipv4 example.com --ipv4 www.example.com --ipv4 api.example.com

# Mix IPv4 and IPv6 domains
ddns --dns cloudflare --id user@example.com --token your_token \
     --ipv4 example.com --ipv4 www.example.com \
     --ipv6 ipv6.example.com
```

### Provider-Specific Examples

#### Cloudflare

```bash
# Using email + API key
ddns --dns cloudflare --id user@example.com --token your_api_key --ipv4 example.com

# Using API token only (recommended)
ddns --dns cloudflare --token your_api_token --ipv4 example.com
```

#### DNSPod

```bash
ddns --dns dnspod --id 12345 --token your_token --ipv4 example.com
```

#### Alibaba Cloud DNS

```bash
ddns --dns alidns --id your_access_key --token your_secret_key --ipv4 example.com
```

#### Alibaba Cloud ESA

```bash
ddns --dns aliesa --id your_access_key --token your_secret_key --ipv4 example.com
```

#### No-IP

```bash
ddns --dns noip --id your_username --token your_password --ipv4 example.com
```

#### Custom Callback

```bash
# GET request callback
ddns --dns callback --id "https://api.example.com/ddns?domain=__DOMAIN__&ip=__IP__" --ipv4 example.com

# POST request callback
ddns --dns callback \
     --id "https://api.example.com/ddns" \
     --token '{"api_key": "your_key", "domain": "__DOMAIN__", "ip": "__IP__"}' \
     --ipv4 example.com
```

### Advanced Configuration

#### Custom TTL and Line

```bash
# Set custom TTL (10 minutes)
ddns --dns dnspod --id 12345 --token your_token --ipv4 example.com --ttl 600

# Specify ISP line
ddns --dns dnspod --id 12345 --token your_token --ipv4 example.com --line "电信"
```

#### Proxy Configuration

```bash
# Use HTTP proxy
ddns --dns cloudflare --token your_token --ipv4 example.com --proxy 127.0.0.1:1080

# Use multiple proxies with fallback
ddns --dns cloudflare --token your_token --ipv4 example.com \
     --proxy 127.0.0.1:1080 --proxy DIRECT
```

#### Custom Endpoint

```bash
# Use custom API endpoint
ddns --dns cloudflare --token your_token --ipv4 example.com \
     --endpoint https://api.private-cloudflare.com

# Alibaba Cloud ESA with custom region
ddns --dns aliesa --id your_access_key --token your_secret_key --ipv4 example.com \
     --endpoint https://esa.ap-southeast-1.aliyuncs.com

# No-IP compatible service
ddns --dns noip --id your_username --token your_password --ipv4 example.com \
     --endpoint https://your-ddns-server.com
```

#### Cache and SSL Settings

```bash
# Disable cache
ddns --dns cloudflare --token your_token --ipv4 example.com --no-cache

# Custom cache file
ddns --dns cloudflare --token your_token --ipv4 example.com --cache /tmp/ddns.cache

# Disable SSL verification
ddns --dns cloudflare --token your_token --ipv4 example.com --no-ssl

# Use custom CA certificate
ddns --dns cloudflare --token your_token --ipv4 example.com --ssl /path/to/ca.pem
```

### Configuration File Generation

```bash
# Generate default config file
ddns --new-config

# Generate config with specific filename
ddns --new-config=my-config.json

# Generate config with initial values
ddns --new-config --dns cloudflare --id user@example.com --token your_token
```

### Logging Configuration

```bash
# Set log level
ddns --dns cloudflare --token your_token --ipv4 example.com --log_level DEBUG

# Save logs to file
ddns --dns cloudflare --token your_token --ipv4 example.com --log_file /var/log/ddns.log

# Custom log format
ddns --dns cloudflare --token your_token --ipv4 example.com \
     --log_format "%(asctime)s: %(message)s" \
     --log_datefmt "%Y-%m-%d %H:%M:%S"
```

## Configuration Priority

DDNS uses the following priority order (highest to lowest):

1. **Command line arguments** (highest priority)
2. **JSON configuration file**
3. **Environment variables** (lowest priority)

This means command line arguments will override any settings in configuration files or environment variables.

## See Also

- [Environment Variables Configuration](env.en.md)
- [JSON Configuration File](json.en.md)
- [Docker Usage](docker.en.md)
- [Provider-specific Configuration](providers/)
