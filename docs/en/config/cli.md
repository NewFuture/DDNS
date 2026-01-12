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
ddns --proxy SYSTEM --proxy DIRECT
```

#### Method 2: Space-Separated

```bash
ddns --ipv4 example.com www.example.com api.example.com
ddns --index4 public 0 "regex:192\\.168\\..*"
ddns --proxy SYSTEM DIRECT
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
| `-c, --config`  | String List | Specify configuration file path, supports multiple config files and remote HTTP(S) URLs                                                                                              | `--config config.json` or `--config config1.json --config config2.json` <br> `--config https://ddns.newfuture.cc/tests/config/debug.json`                                   |
| `--new-config`  | Flag/String | Generate a new config file (optional file path)                                                                                                                           | `--new-config` <br> `--new-config=config.json`           |
| `--debug`       |     Flag    | Enable debug mode                                                                                                                                                         | `--debug`                                                |
| `--dns`         |    Choice   | [DNS Providers](../providers/) include:<br>51dns, alidns, aliesa, callback, cloudflare,<br>debug, dnscom, dnspod\_com, dnspod, edgeone, he,<br>huaweidns, noip, tencentcloud | `--dns cloudflare`                                       |
| `--endpoint`    |    String   | Custom API endpoint URL (useful for self-hosted services)                                                                                                                 | `--endpoint https://api.private.com`                     |
| `--id`          |    String   | API Access ID, email, or Access Key                                                                                                                                       | `--id user@example.com`                                  |
| `--token`       |    String   | API token or secret key                                                                                                                                                   | `--token abcdef123456`                                   |
| `--ipv4`        | String List | List of domain names for IPv4, supports repeated parameters or space-separated                                                                                                     | `--ipv4 test.com 4.test.com` or `--ipv4 test.com --ipv4 4.test.com`                      |
| `--ipv6`        | String List | List of domain names for IPv6, supports repeated parameters or space-separated                                                                                                     | `--ipv6 test.com` or `--ipv6 test.com ipv6.test.com`                                        |
| `--index4`      |     List    | Methods to retrieve IPv4 address, supports: number, default, public,<br>url:, regex:, cmd:, shell:                                                                        | `--index4 public 0` or `--index4 public --index4 "regex:192\\.168\\..*"` |
| `--index6`      |     List    | Methods to retrieve IPv6 address, supports: number, default, public,<br>url:, regex:, cmd:, shell:                                                                        | `--index6 0 public` or `--index6 0 --index6 public`                      |
| `--ttl`         |   Integer   | DNS record TTL time in seconds                                                                                                                                            | `--ttl 600`                                              |
| `--line`        |    String   | DNS resolution line (e.g. ISP line)                                                                                                                                       | `--line 电信` <br> `--line telecom`                        |
| `--proxy`       | String List | HTTP proxy settings, supports: `http://host:port`, `DIRECT`(direct), `SYSTEM`(system proxy)                                | `--proxy SYSTEM DIRECT` or `--proxy http://127.0.0.1:1080 --proxy DIRECT`    |
| `--cache`       | Flag/String | Enable cache or specify custom cache path                                                                                                                                 | `--cache` <br> `--cache=/path/to/cache`                  |
| `--no-cache`    |     Flag    | Disable cache (equivalent to `--cache=false`)                                                                                                                             | `--no-cache`                                             |
| `--ssl`         |    String   | SSL certificate verification: true, false, auto, or file path                                                                                                             | `--ssl false` <br> `--ssl=/path/to/ca-certs.crt`         |
| `--no-ssl`      |     Flag    | Disable SSL verification (equivalent to `--ssl=false`)                                                                                                                    | `--no-ssl`                                               |
| `--log_file`    |    String   | Log file path. If not set, logs are output to the console                                                                                                                 | `--log_file=/var/log/ddns.log`                           |
| `--log_level`   |    String   | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL                                                                                                                      | `--log_level=ERROR`                                      |
| `--log_format`  |    String   | Log format string (compatible with Python `logging` module)                                                                                                               | `--log_format="%(asctime)s:%(message)s"`                 |
| `--log_datefmt` |    String   | Date/time format string for logs                                                                                                                                          | `--log_datefmt="%Y-%m-%d %H:%M:%S"`                      |

#### Task Subcommand Parameters

| Parameter          |     Type    | Description                                                                                                                                                               | Example                                                  |
| --------------- | :---------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `--install`, `-i` | Integer (Optional) | Install scheduled task with update interval in minutes (default: 5). **Automatically overwrites existing tasks** | `--install`, `--install 10` |
| `--uninstall`   |     Flag    | Uninstall the installed scheduled task                                                                                                                                    | `--uninstall`                                           |
| `--status`      |     Flag    | Show scheduled task installation status and running information                                                                                                           | `--status`                                               |
| `--enable`      |     Flag    | Enable the installed scheduled task                                                                                                                                       | `--enable`                                               |
| `--disable`     |     Flag    | Disable the installed scheduled task                                                                                                                                      | `--disable`                                              |
| `--scheduler`   |   Choice    | Specify scheduler type. Supports: auto (automatic), systemd, cron, launchd, schtasks                                                                                    | `--scheduler systemd`, `--scheduler auto`                |

> **Important Notes**:
>
> - The `--install` command **automatically overwrites** scheduled tasks without needing to check or uninstall existing tasks first.
> - This design simplifies the task management process and avoids manual uninstallation procedures.
> - The `task` subcommand supports all main DDNS configuration parameters (such as `--dns`, `--id`, `--token`, `--ipv4`, `--ipv6`, etc.), which will be saved and passed to the scheduled task for execution.
> - Command line only parameters: `--debug`, `--new-config`, `--no-cache`, `--no-ssl`, `--help`, `--version`.

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
- **public**: Get public IP from external services with automatic failover
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

# Use remote configuration file
ddns -c https://ddns.newfuture.cc/tests/config/debug.json

# Use remote configuration with proxy
ddns -c https://config.example.com/ddns.json --proxy http://proxy:8080

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
     --ttl 300 --proxy http://127.0.0.1:1080 DIRECT \
     --cache=/var/cache/ddns.cache \
     --log_level=INFO --log_file=/var/log/ddns.log

# Complete configuration (repeated parameters)
ddns --dns cloudflare --token API_TOKEN \
     --ipv4 example.com --ipv4 www.example.com \
     --index4 public --index6 "regex:2001:.*" \
     --ttl 300 --proxy http://127.0.0.1:1080 --proxy DIRECT \
     --cache=/var/cache/ddns.cache \
     --log_level=INFO --log_file=/var/log/ddns.log

# ISP line configuration (for Chinese providers)
ddns --dns dnspod --id 12345 --token mytokenkey \
     --ipv4 telecom.example.com --line 电信

# Use remote configuration file
ddns -c https://ddns.newfuture.cc/tests/config/debug.json --debug

# Remote configuration with proxy
ddns -c https://config.example.com/ddns.json \
     --proxy http://proxy.company.com:8080

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
   ddns --proxy http://127.0.0.1:1080 --proxy DIRECT
   
   # ✅ Method 2: Space-separated
   ddns --ipv4 example.com sub.example.com api.example.com
   ddns --index4 public 0 "regex:192\\.168\\..*"
   ddns --proxy http://127.0.0.1:1080 DIRECT
   
   # ✅ Parameter values with spaces use quotes
   ddns --line "China Telecom" "China Unicom"
   
   # ❌ Incorrect usage - not supported
   ddns --ipv4 "example.com,sub.example.com"    # Comma-separated not supported
   ddns --ipv4=example.com,sub.example.com      # Equals + comma not supported
   ```

4. **Debug Mode**: The `--debug` parameter is only effective as a command line argument; debug settings in configuration files will be ignored.

5. **Regular Expressions**: When using regular expressions, special characters need to be properly escaped. It's recommended to use quotes, for example: `--index4 "regex:192\\.168\\..*"`.

## Task Management

DDNS supports managing scheduled tasks through the `task` subcommand, which automatically detects the system and selects the appropriate scheduler to install scheduled update tasks.

### Key Features

- **Smart Installation**: The `--install` command automatically overwrites existing tasks, simplifying the installation process
- **Cross-Platform Support**: Automatically detects system and selects the best scheduler
- **Complete Configuration**: Supports all DDNS configuration parameters

### Task Subcommand Usage

```bash
# View help
ddns task --help

# Check task status
ddns task --status

# Install scheduled task (default 5-minute interval)
ddns task --install

# Install scheduled task with custom interval (minutes)
ddns task --install 10
ddns task -i 15

# Specify scheduler type for installation
ddns task --install 5 --scheduler systemd
ddns task --install 10 --scheduler cron
ddns task --install 15 --scheduler auto

# Enable installed scheduled task
ddns task --enable

# Disable installed scheduled task
ddns task --disable

# Uninstall installed scheduled task
ddns task --uninstall
```

### Supported Schedulers

DDNS automatically detects the system and chooses the most appropriate scheduler:

- **Linux**: systemd (preferred) or cron
- **macOS**: launchd (preferred) or cron  
- **Windows**: schtasks

### Scheduler Selection Guide

| Scheduler | Supported Systems | Description | Recommendation |
|-----------|-------------------|-------------|----------------|
| `auto` | All systems | Automatically detects system and selects the best scheduler | ⭐⭐⭐⭐⭐ |
| `systemd` | Linux | Modern Linux standard timer with complete functionality | ⭐⭐⭐⭐⭐ |
| `cron` | Unix-like | Traditional Unix scheduled tasks with good compatibility | ⭐⭐⭐⭐ |
| `launchd` | macOS | macOS native task scheduler | ⭐⭐⭐⭐⭐ |
| `schtasks` | Windows | Windows Task Scheduler | ⭐⭐⭐⭐⭐ |

### Parameter Description

| Parameter | Description |
|-----------|-------------|
| `--status` | Show scheduled task installation status and running information |
| `--install [minutes]`, `-i [minutes]` | Install scheduled task with update interval (default: 5 minutes). **Automatically overwrites existing tasks** |
| `--uninstall` | Uninstall installed scheduled task |
| `--enable` | Enable installed scheduled task |
| `--disable` | Disable installed scheduled task |
| `--scheduler` | Specify scheduler type. Supports: auto, systemd, cron, launchd, schtasks |

> **Installation Behavior**:
>
> - The `--install` command always executes installation directly, without prior checking or uninstalling.
> - Any existing DDNS scheduled task in the system will be automatically replaced with the new configuration.
> - This design simplifies task management and avoids the hassle of manual uninstallation, enabling one-click task updates.
>
> **Configuration Parameter Support**: The `task` subcommand supports all DDNS configuration parameters, which will be passed to the scheduled task for execution.

### Permission Requirements

Different schedulers require different permissions:

- **systemd**: Requires root privileges (`sudo`)
- **cron**: Regular user privileges
- **launchd**: Regular user privileges
- **schtasks**: Administrator privileges required

### Task Management Examples

```bash
# Check current status
ddns task --status

# Quick install (automatically overwrites existing tasks)
ddns task --install

# Install 10-minute interval scheduled task with specified config file
ddns task --install 10 -c /etc/ddns/config.json

# Install scheduled task with direct DDNS parameters (no config file needed)
ddns task --install 5 --dns cloudflare --id user@example.com --token API_TOKEN --ipv4 example.com

# Install scheduled task with advanced configuration parameters
ddns task --install 10 --dns dnspod --id 12345 --token secret \
          --ipv4 example.com --ttl 600 --proxy http://proxy:8080 \
          --log_file /var/log/ddns.log --log_level INFO

# Specify scheduler type for installation
ddns task --install 5 --scheduler systemd --dns cloudflare --id user@example.com --token API_TOKEN --ipv4 example.com

# Force use cron scheduler (for Linux systems without systemd)
ddns task --install 10 --scheduler cron -c config.json

# Force use launchd on macOS
ddns task --install 15 --scheduler launchd --dns dnspod --id 12345 --token secret --ipv4 example.com

# Use schtasks on Windows
ddns task --install 5 --scheduler schtasks --dns cloudflare --id user@example.com --token API_TOKEN --ipv4 example.com

# Install systemd timer on Linux with sudo
sudo ddns task --install 5 -c /etc/ddns/config.json

# Update task configuration (automatic overwrite)
ddns task --install 15 --dns cloudflare --id user@example.com --token NEW_TOKEN --ipv4 example.com

# Enable installed task
ddns task --enable

# Disable task (doesn't delete, just stops execution)
ddns task --disable

# Completely uninstall scheduled task
ddns task --uninstall
```

### Using with Configuration Files

The `task` subcommand works perfectly with configuration files, supporting multiple configuration methods:

```bash
# Use local configuration file
ddns task --install 10 -c config.json

# Use multiple configuration files
ddns task --install 5 -c cloudflare.json -c dnspod.json

# Use remote configuration file
ddns task --install 15 -c https://config.example.com/ddns.json

# Configuration file + command line parameter override
ddns task --install 10 -c config.json --debug --ttl 300

# Specify scheduler type + configuration file
ddns task --install 5 --scheduler cron -c config.json

# Use remote configuration file + specify scheduler
ddns task --install 10 --scheduler systemd -c https://config.example.com/ddns.json
```

### Scheduler Usage Examples

Choose the appropriate scheduler based on different systems and requirements:

```bash
# Automatic selection (recommended, let system choose the best scheduler)
ddns task --install 5 --scheduler auto

# Linux system choices
ddns task --install 5 --scheduler systemd  # Preferred choice, full functionality
ddns task --install 5 --scheduler cron     # Backup choice, good compatibility

# macOS system choices
ddns task --install 5 --scheduler launchd  # Preferred choice, system native
ddns task --install 5 --scheduler cron     # Backup choice, good compatibility

# Windows system choices
ddns task --install 5 --scheduler schtasks # Only choice, Windows Task Scheduler
```

### Debugging Installation Issues

```bash
# Enable debug mode to view detailed installation process
ddns task --install 5 --debug

# View task status and configuration
ddns task --status --debug

# View status of specified scheduler
ddns task --status --scheduler systemd --debug
```

# Configuration file + command line parameter override

ddns task --install 10 -c config.json --debug --ttl 300

```

### Debugging Installation Issues

```bash
# Enable debug mode to see detailed installation process
ddns task --install 5 --debug

# View task status and configuration
ddns task --status --debug
```

## Configuration Priority

DDNS uses the following priority order (highest to lowest):

1. **Command line arguments** (highest priority)
2. **JSON configuration file**
3. **Environment variables** (lowest priority)

This means command line arguments will override any settings in configuration files or environment variables.

## See Also

- [Environment Variables Configuration](env.md)
- [JSON Configuration File](json.md)
- [Docker Usage](../docker.md)
- [Provider-specific Configuration](../providers/)
