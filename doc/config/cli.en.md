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

### List Parameter Usage

For list-type parameters that support multiple values (such as `--ipv4`, `--ipv6`, `--index4`, `--index6`, `--proxy`, etc.), you can specify multiple values using the following two methods:

#### Method 1: Repeat Parameter Names (Recommended)

```bash
ddns --ipv4 example.com --ipv4 www.example.com --ipv4 api.example.com
ddns --index4 public --index4 0 --index4 "regex:192\\.168\\..*"
ddns --proxy 127.0.0.1:1080 --proxy DIRECT
```

#### Method 2: Space-Separated

```bash
ddns --ipv4 example.com www.example.com api.example.com
ddns --index4 public 0 "regex:192\\.168\\..*"
ddns --proxy 127.0.0.1:1080 DIRECT
```

#### Parameters with Spaces

If parameter values contain spaces, use quotes:

```bash
ddns --line "China Telecom" "China Unicom" "China Mobile"
ddns --index4 "url:http://ip.example.com/api?type=ipv4" public
```

#### Unsupported Usage

```bash
# ❌ Comma-separated not supported
ddns --ipv4 "example.com,www.example.com"
ddns --ipv4=example.com,www.example.com
```

### Parameter Details

| Parameter          |     Type    | Description                                                                                                                                                               | Example                                                  |
| --------------- | :---------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `-h, --help`    |     Flag    | Show help message and exit                                                                                                                                                | `--help`                                                 |
| `-v, --version` |     Flag    | Show version information and exit                                                                                                                                         | `--version`                                              |
| `-c, --config`  | String List | Specify configuration file path, supports multiple config files                                                                                              | `--config config.json` or `--config config1.json --config config2.json`                                   |
| `--new-config`  | Flag/String | Generate a new config file (optional file path)                                                                                                                           | `--new-config` <br> `--new-config=config.json`           |
| `--debug`       |     Flag    | Enable debug mode                                                                                                                                                         | `--debug`                                                |
| `--dns`         |    Choice   | [DNS Providers](../providers/README.en.md) include:<br>51dns, alidns, aliesa, callback, cloudflare,<br>debug, dnscom, dnspod\_com, dnspod, edgeone, he,<br>huaweidns, noip, tencentcloud | `--dns cloudflare`                                       |
| `--endpoint`    |    String   | Custom API endpoint URL (useful for self-hosted services)                                                                                                                 | `--endpoint https://api.private.com`                     |
| `--id`          |    String   | API Access ID, email, or Access Key                                                                                                                                       | `--id user@example.com`                                  |
| `--token`       |    String   | API token or secret key                                                                                                                                                   | `--token abcdef123456`                                   |
| `--ipv4`        | String List | List of domain names for IPv4, supports repeated parameters or space-separated                                                                                                     | `--ipv4 test.com 4.test.com` or `--ipv4 test.com --ipv4 4.test.com`                      |
| `--ipv6`        | String List | List of domain names for IPv6, supports repeated parameters or space-separated                                                                                                     | `--ipv6 test.com` or `--ipv6 test.com ipv6.test.com`                                        |
| `--index4`      |     List    | Methods to retrieve IPv4 address, supports: number, default, public,<br>url:, regex:, cmd:, shell:                                                                        | `--index4 public 0` or `--index4 public --index4 "regex:192\\.168\\..*"` |
| `--index6`      |     List    | Methods to retrieve IPv6 address, supports: number, default, public,<br>url:, regex:, cmd:, shell:                                                                        | `--index6 0 public` or `--index6 0 --index6 public`                      |
| `--ttl`         |   Integer   | DNS record TTL time in seconds                                                                                                                                            | `--ttl 600`                                              |
| `--line`        |    String   | DNS resolution line (e.g. ISP line)                                                                                                                                       | `--line 电信` <br> `--line telecom`                        |
| `--proxy`       | String List | HTTP proxy settings, format: IP\:Port or `DIRECT`                                                                                                                         | `--proxy 127.0.0.1:1080 DIRECT` or `--proxy 127.0.0.1:1080 --proxy DIRECT`                  |
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

### Basic Configuration File Usage

```bash
# Use default configuration file
ddns

# Use specified configuration file
ddns -c /path/to/config.json

# Use multiple configuration files
ddns -c cloudflare.json -c dnspod.json

# Generate new configuration file
ddns --new-config config.json
```

### Command Line Configuration

```bash
# Simplest configuration - DNSPod
ddns --dns dnspod --id 12345 --token mytokenkey --ipv4 example.com

# Cloudflare with API token
ddns --dns cloudflare --token your_api_token --ipv4 example.com

# Enable debug mode
ddns --dns cloudflare --token API_TOKEN --ipv4 example.com --debug

# Multiple domains (space-separated)
ddns --dns cloudflare --token API_TOKEN \
     --ipv4 example.com www.example.com --ipv6 example.com

# Multiple domains (repeated parameters)
ddns --dns cloudflare --token API_TOKEN \
     --ipv4 example.com --ipv4 www.example.com --ipv6 example.com
```

### Provider-Specific Examples

```bash
# Alibaba Cloud DNS
ddns --dns alidns --id your_access_key --token your_secret_key --ipv4 example.com

# Huawei Cloud DNS  
ddns --dns huaweidns --id your_access_key --token your_secret_key --ipv4 example.com

# No-IP
ddns --dns noip --id your_username --token your_password --ipv4 example.com

# Custom Callback (GET request)
ddns --dns callback --id "https://api.example.com/ddns?domain=__DOMAIN__&ip=__IP__" --ipv4 example.com
```

### Advanced Configuration

```bash
# Complete configuration with proxy, TTL, and custom IP detection (space-separated)
ddns --dns cloudflare --token API_TOKEN \
     --ipv4 example.com www.example.com \
     --index4 public "regex:2001:.*" \
     --ttl 300 --proxy 127.0.0.1:1080 DIRECT \
     --cache=/var/cache/ddns.cache \
     --log_level=INFO --log_file=/var/log/ddns.log

# Complete configuration (repeated parameters)
ddns --dns cloudflare --token API_TOKEN \
     --ipv4 example.com --ipv4 www.example.com \
     --index4 public --index6 "regex:2001:.*" \
     --ttl 300 --proxy 127.0.0.1:1080 --proxy DIRECT \
     --cache=/var/cache/ddns.cache \
     --log_level=INFO --log_file=/var/log/ddns.log

# ISP line configuration (for Chinese providers)
ddns --dns dnspod --id 12345 --token mytokenkey \
     --ipv4 telecom.example.com --line 电信

# Disable cache and SSL verification
ddns --dns alidns --id ACCESS_KEY --token SECRET_KEY \
     --ipv4 example.com --no-cache --no-ssl
```

## Important Notes

1. **Command Line Parameter Priority**: Command line arguments have the highest priority and will override settings in configuration files and environment variables.

2. **Quote Usage**: For parameter values that contain spaces or special characters, please use quotes, for example: `--log_format="%(asctime)s: %(message)s"`.

3. **List Parameter Configuration**: For multi-value parameters (such as `--ipv4`, `--ipv6`, `--index4`, `--index6`, `--proxy`, etc.), two specification methods are supported:

   ```bash
   # ✅ Method 1: Repeat parameter names (recommended)
   ddns --ipv4 example.com --ipv4 sub.example.com --ipv4 api.example.com
   ddns --index4 public --index4 0 --index4 "regex:192\\.168\\..*"
   ddns --proxy 127.0.0.1:1080 --proxy DIRECT
   
   # ✅ Method 2: Space-separated
   ddns --ipv4 example.com sub.example.com api.example.com
   ddns --index4 public 0 "regex:192\\.168\\..*"
   ddns --proxy 127.0.0.1:1080 DIRECT
   
   # ✅ Parameter values with spaces use quotes
   ddns --line "China Telecom" "China Unicom"
   
   # ❌ Incorrect usage - not supported
   ddns --ipv4 "example.com,sub.example.com"    # Comma-separated not supported
   ddns --ipv4=example.com,sub.example.com      # Equals + comma not supported
   ```

4. **Debug Mode**: The `--debug` parameter is only effective as a command line argument; debug settings in configuration files will be ignored.

5. **Regular Expressions**: When using regular expressions, special characters need to be properly escaped. It's recommended to use quotes, for example: `--index4 "regex:192\\.168\\..*"`.

## Configuration Priority

DDNS uses the following priority order (highest to lowest):

1. **Command line arguments** (highest priority)
2. **JSON configuration file**
3. **Environment variables** (lowest priority)

This means command line arguments will override any settings in configuration files or environment variables.

## See Also

- [Environment Variables Configuration](env.en.md)
- [JSON Configuration File](json.en.md)
- [Docker Usage](../docker.en.md)
- [Provider-specific Configuration](../providers/)
