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

| Parameter          |     Type    | Description                                                                                                                                                               | Example                                                  |
| --------------- | :---------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `-h, --help`    |     Flag    | Show help message and exit                                                                                                                                                | `--help`                                                 |
| `-v, --version` |     Flag    | Show version information and exit                                                                                                                                         | `--version`                                              |
| `-c, --config`  |    String   | Specify the path to the configuration file                                                                                                                                | `--config config.json`                                   |
| `--new-config`  | Flag/String | Generate a new config file (optional file path)                                                                                                                           | `--new-config` <br> `--new-config=config.json`           |
| `--debug`       |     Flag    | Enable debug mode                                                                                                                                                         | `--debug`                                                |
| `--dns`         |    Choice   | [DNS Providers](providers/README.en.md) include:<br>51dns, alidns, aliesa, callback, cloudflare,<br>debug, dnscom, dnspod\_com, dnspod, edgeone, he,<br>huaweidns, noip, tencentcloud | `--dns cloudflare`                                       |
| `--endpoint`    |    String   | Custom API endpoint URL (useful for self-hosted services)                                                                                                                 | `--endpoint https://api.private.com`                     |
| `--id`          |    String   | API Access ID, email, or Access Key                                                                                                                                       | `--id user@example.com`                                  |
| `--token`       |    String   | API token or secret key                                                                                                                                                   | `--token abcdef123456`                                   |
| `--ipv4`        | String List | List of domain names for IPv4, repeat the option for multiple domains                                                                                                     | `--ipv4 test.com --ipv4 4.test.com`                      |
| `--ipv6`        | String List | List of domain names for IPv6, repeat the option for multiple domains                                                                                                     | `--ipv6 test.com`                                        |
| `--index4`      |     List    | Methods to retrieve IPv4 address, supports: number, default, public,<br>url:, regex:, cmd:, shell:                                                                        | `--index4 public` <br> `--index4 "regex:192\\.168\\..*"` |
| `--index6`      |     List    | Methods to retrieve IPv6 address, supports: number, default, public,<br>url:, regex:, cmd:, shell:                                                                        | `--index6 0` <br> `--index6 public`                      |
| `--ttl`         |   Integer   | DNS record TTL time in seconds                                                                                                                                            | `--ttl 600`                                              |
| `--line`        |    String   | DNS resolution line (e.g. ISP line)                                                                                                                                       | `--line 电信` <br> `--line telecom`                        |
| `--proxy`       | String List | HTTP proxy settings, format: IP\:Port or `DIRECT`                                                                                                                         | `--proxy 127.0.0.1:1080 --proxy DIRECT`                  |
| `--cache`       | Flag/String | Enable cache or specify custom cache path                                                                                                                                 | `--cache` <br> `--cache=/path/to/cache`                  |
| `--no-cache`    |     Flag    | Disable cache (equivalent to `--cache=false`)                                                                                                                             | `--no-cache`                                             |
| `--ssl`         |    String   | SSL certificate verification: true, false, auto, or file path                                                                                                             | `--ssl false` <br> `--ssl=/path/to/ca-certs.crt`         |
| `--no-ssl`      |     Flag    | Disable SSL verification (equivalent to `--ssl=false`)                                                                                                                    | `--no-ssl`                                               |
| `--log_file`    |    String   | Log file path. If not set, logs are output to the console                                                                                                                 | `--log_file=/var/log/ddns.log`                           |
| `--log_level`   |    String   | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL                                                                                                                      | `--log_level=ERROR`                                      |
| `--log_format`  |    String   | Log format string (compatible with Python `logging` module)                                                                                                               | `--log_format="%(asctime)s:%(message)s"`                 |
| `--log_datefmt` |    String   | Date/time format string for logs                                                                                                                                          | `--log_datefmt="%Y-%m-%d %H:%M:%S"`                      |

> **Note**: Where `--debug`, `--new-config`, `--no-cache`, `--no-ssl`, `--help`, `--version` are command line only parameters.

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
- **edgeone**: Tencent Cloud EdgeOne

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
