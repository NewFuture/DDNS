---
title: DDNS JSON Configuration
post_tile: JSON File Configuration
header_pages:
  - /README.en.md
  - /doc/config/
  - /docs/proivders/README.en.md
---
# DDNS JSON Configuration File Reference

This document provides detailed information about the JSON configuration file format and parameters for the DDNS tool. JSON configuration files have priority between command line arguments and environment variables.

## Basic Usage

By default, DDNS looks for a `config.json` file in the current directory. You can also use the `-c` parameter to specify a configuration file path:

* Current directory `config.json` (note that Docker runtime directory is `/ddns/`)
* Current user directory `~/.ddns/config.json`
* Linux system directory `/etc/ddns/config.json`

> Note: When using configuration files in Docker, you need to mount the configuration file to the container's `/ddns/` directory through volume mapping. For details, please refer to the [Docker documentation](docker.en.md).

```bash
# Generate configuration file
ddns --new-config
# Specify parameters and configuration file
ddns --dns dnspod --ipv4 ddns.newfuture.cc --new-config config.json

# Use specified configuration file
ddns -c /path/to/config.json
# Or use Python source code
python -m ddns -c /path/to/config.json

# Use multiple configuration files
ddns -c cloudflare.json -c dnspod.json
# Or via environment variables
export DDNS_CONFIG="cloudflare.json,dnspod.json"
ddns
```

## JSON Schema

DDNS configuration files follow JSON Schema standards. It's recommended to add the `$schema` field to your configuration file for editor auto-completion and validation features:

Since v4.1, configuration files support single-line comments.

```jsonc
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.1.json"
}
```

## Schema

Configuration Parameters Table

| Key Name | Type | Required | Default Value | Parameter Description | Notes |
| :------: | :--: | :------: | :-----------: | :------------------: | ----- |
| dns | string | No | None | DNS Provider | Available values: 51dns, alidns, aliesa, callback, cloudflare, debug, dnscom, dnspod_com, dnspod, edgeone, he, huaweidns, namesilo, noip, tencentcloud |
| id | string | Yes | None | API Access ID | Configure according to provider documentation (e.g., AccessKeyID) |
| token | string | Yes | None | API Authorization Token | Configure according to provider documentation (e.g., AccessSecret) |
| endpoint | string | No | None | API Endpoint URL | For custom or private deployment API addresses, uses default endpoint when empty |
| ipv4 | array | No | `[]` | IPv4 Domain List | |
| ipv6 | array | No | `[]` | IPv6 Domain List | |
| index4 | string\|int\|array | No | `["default"]` | IPv4 Retrieval Method | [See details below](#index4-index6) |
| index6 | string\|int\|array | No | `["default"]` | IPv6 Retrieval Method | [See details below](#index4-index6) |
| ttl | number | No | `null` | DNS TTL Time | In seconds, uses DNS default policy when not set |
| line | string | No | `null` | DNS Resolution Line | ISP line selection, supported values depend on DNS provider |
| proxy | string\|array | No | None | HTTP Proxy | Try multiple proxies sequentially until success, supports `DIRECT`(direct), `SYSTEM`(system proxy) |
| ssl | string\|boolean | No | `"auto"` | SSL Verification Method | `true` (force verification), `false` (disable verification), `"auto"` (auto downgrade) or custom CA certificate file path |
| cache | string\|bool | No | `true` | Enable Record Caching | Enable to avoid frequent updates, default location is `ddns.{hash}.cache` in temp directory, or specify custom path |
| log | object | No | `null` | Log Configuration | Log configuration object, supports `level`, `file`, `format`, `datefmt` parameters |

### dns

The `dns` parameter specifies the DNS provider identifier. For supported values, please refer to the [Provider List](providers/README.en.md):

> When in debug mode and no dns parameter is configured, the debug provider is used.

### id and token

The `id` and `token` parameters are used for API authentication. Their specific meaning and format depend on the selected DNS provider.

### endpoint

The `endpoint` parameter is used to specify a custom API endpoint. Most providers have default endpoints, so modification is not needed unless there are special requirements.

Special cases include:

* Providers with regional deployment (such as Tencent Cloud, Alibaba Cloud, etc.) need to specify the corresponding regional API endpoint.
* **Private Cloud Deployment**: If you're using a privately deployed DNS service, you need to specify the corresponding private API endpoint address.
* **Proxy Forwarding**: If you're using a third-party API proxy service, you need to specify the proxy URL.

### ipv4-ipv6

The `ipv4` and `ipv6` parameters specify the DNS record names to be updated, which can be domain or subdomain lists. You can use array format to specify multiple records.

Supported formats:

* When empty, the corresponding IP type DNS records will not be updated.
* **Single domain**: `"ddns.newfuture.cc"`
* **Multiple domains**: `["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"]`

### index4-index6

The `index4` and `index6` parameters are used to specify the method for obtaining IP addresses. The following values can be used:

Supported types:

* `false` indicates prohibition of updating the corresponding IP type DNS records
* **Numbers** (such as `0`, `1`, `2`...): Use the IP address of the Nth network interface
* `"default"`: System's default IP for external network access
* `"public"`: Use public IP (queried through API)
* `"url:http..."`: Get IP through specified URL, e.g., `"url:http://ip.sb"`
* `"regex:xxx"`: Use regular expression to match IP in local network configuration, e.g., `"regex:192\\.168\\..*"`
  * Note: Backslashes need to be escaped in JSON, e.g., `"regex:10\\.00\\..*"` matches IPs starting with `10.00.`
* `"cmd:xxx"`: Execute specified command and use its output as IP
* `"shell:xxx"`: Use system shell to run command and use its output as IP

Configuration examples:

```jsonc
{
    "index4": ["public", "url:http://ipv4.icanhazip.com"], // Prefer public IP, fallback to specified URL
    "index6": ["shell:ip route", "regex:2003:.*"], // Use shell command, fallback to regex matching IPv6 addresses
    "index4": [0, "public"], // Use first network interface IP, fallback to public IP
    "index6": "public", // Use public IPv6 address
    "index4": false // Disable IPv4 record updates
}
```

### ttl

The `ttl` parameter specifies the Time To Live (TTL) for DNS records in seconds. The default value is `null`, which means using the DNS provider's default TTL policy.
The specific value range and default value depend on the selected DNS provider.

### line

The `line` parameter is used to specify DNS resolution lines. Supported values depend on the selected DNS provider.

### proxy

The `proxy` parameter is used to set HTTP proxy, which can be a single proxy address or an array of multiple proxy addresses. The following formats are supported:

Proxy types:

* **Specific proxy**: `"http://<proxy_host>:<proxy_port>"` or `"https://<proxy_host>:<proxy_port>"`
* **Direct connection**: `"DIRECT"` - Force direct connection, ignore system proxy settings
* **System proxy**: `"SYSTEM"` - Use system default proxy settings (IE proxy, environment variables, etc.)
* **Auto**: `null` or not set - Use system default proxy settings

Configuration examples:

```jsonc
{
    "proxy": "http://127.0.0.1:1080",                    // Single proxy address
    "proxy": "SYSTEM",                                   // Use system proxy settings
    "proxy": "DIRECT",                                   // Force direct connection
    "proxy": ["http://127.0.0.1:1080", "DIRECT"],       // Try proxy first, fallback to direct
    "proxy": ["SYSTEM", "http://backup:8080", "DIRECT"], // System proxy → backup proxy → direct
    "proxy": null                                        // Use system default proxy settings
}
```

> Note: If `proxy` is configured, the proxy only applies to provider requests; IP retrieval APIs will not use the proxy parameter.

### ssl

The `ssl` parameter is used to configure SSL verification method. The following values are supported:

* `"auto"`: Auto downgrade to not verify SSL certificates (less secure)
* `true`: Force SSL certificate verification
* `false`: Disable SSL verification (insecure)
* `"/path/to/ca.crt"`: Specify custom CA certificate file

> Note: If `ssl` is configured, all API requests, including provider and IP retrieval APIs, will use this configuration.

### cache

The `cache` parameter is used to configure DNS record caching method. The following values are supported:

* `true`: Enable caching, default location is `ddns.{hash}.cache` in the temporary directory
* `false`: Disable caching
* `"/path/to/cache.file"`: Specify custom cache file path

### log

The `log` parameter is used to configure logging. It's an object that supports the following fields:

| Key Name | Type | Required | Default Value | Description |
| :------: | :--: | :------: | :-----------: | :---------: |
| level | string | No | `INFO` | Log level |
| file | string | No | None | Log file path |
| format | string | No | Auto-adjusted | Log format string |
| datefmt | string | No | `%Y-%m-%dT%H:%M:%S` | Date time format |

## Configuration Examples

### Single-Provider Format

```jsonc
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "id": "12345",
  "token": "mytokenkey",
  "dns": "cloudflare",
  "ipv4": ["ddns.newfuture.cc"],
  "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"],
  "index4": ["public", "regex:192\\.168\\.1\\..*"],
  "index6": "public",
  "ttl": 300,
  "proxy": ["http://127.0.0.1:1080", "DIRECT"],
  "ssl": "auto",
  "cache": "/var/cache/ddns.cache",
  "log": {
    "level": "DEBUG",
    "file": "/var/log/ddns.log",
    "datefmt": "%Y-%m-%d %H:%M:%S"
  }
}
```

### Multi-Provider Format

Starting from v4.1.0, you can define multiple DNS providers in a single configuration file using the new `providers` array format:

```jsonc
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
  "ssl": "auto",
  "cache": true,
  "log": {"level": "INFO", "file": "/var/log/ddns.log"},
  "providers": [
    {
      "provider": "cloudflare",
      "id": "user1@example.com",
      "token": "cloudflare-token",
      "ipv4": ["test1.example.com"],
      "ttl": 300
    },
    {
      "provider": "dnspod",
      "id": "user2@example.com",
      "token": "dnspod-token",
      "ipv4": ["test2.example.com"],
      "ttl": 600
    }
  ]
}
```

#### v4.1 Format Features

* **Global Configuration Inheritance**: All configuration items outside `providers` (such as `ssl`, `cache`, `log`, etc.) serve as global settings and are inherited by all providers
* **Provider Override**: Configuration within each provider can override corresponding global settings
* **provider Field**: Required field that specifies the DNS provider type (equivalent to the `dns` field in traditional format)
* **Full Compatibility**: Supports all configuration parameters from traditional format
* **Nested Object Flattening**: Nested objects within providers are automatically flattened during processing

#### Conflict Check

* `providers` and `dns` fields cannot coexist
* When using multiple providers, `ipv4` or `ipv6` fields cannot be used in global configuration
  * Each provider must contain a `name` field
  * Global (outer) level must not contain `ipv4` or `ipv6` fields

## Configuration Priority and Field Override Relationships

The configuration priority order in the DDNS tool is: **Command Line Arguments > JSON Configuration File > Environment Variables**.

* **Command Line Arguments**: Highest priority, will override the same settings in JSON configuration files and environment variables
* **JSON Configuration File**: Between command line arguments and environment variables, will override settings in environment variables
* **Environment Variables**: Lowest priority, used when there are no corresponding settings in command line arguments and JSON configuration files

### Configuration Override Example

Assuming the following configuration:

1. **Environment Variable**: `DDNS_TTL=600`
2. **JSON Configuration File**: `"ttl": 300`
3. **Command Line Argument**: `--ttl 900`

The final effective value is from the command line argument: `ttl=900`

If no command line argument is provided, the JSON configuration value is used: `ttl=300`

### Special Cases

* When a value in the JSON configuration file is explicitly set to `null`, it will override environment variable settings, equivalent to not setting that value
* When a key is missing from the JSON configuration file, the corresponding environment variable will be attempted
* Some parameters (such as `debug`) are only effective under specific configuration methods: the `debug` parameter is only effective in command line, settings in JSON configuration will be ignored

## Notes

1. Configuration files use UTF-8 encoding without BOM
2. All key names in JSON are case-sensitive
3. For strings that need to use backslashes (such as regular expressions) in configuration files, double escaping is required
4. The `debug` parameter is ineffective when set in configuration files, only supports command line parameter `--debug`
5. A template configuration file will be automatically generated in the current directory on first run
6. It's recommended to use editors that support JSON Schema (such as VSCode) to edit configuration files for auto-completion and validation features
