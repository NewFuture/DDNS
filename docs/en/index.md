# [<img src="/doc/img/ddns.svg" width="32px" height="32px"/>](https://ddns.newfuture.cc) [DDNS](https://github.com/NewFuture/DDNS)

> Automatically update DNS records to the current IP address, supporting IPv4 and IPv6, local (private) IP and public IP.
> Proxy mode supported, with automatic DNS record creation.

[![Github Release](https://img.shields.io/github/v/release/NewFuture/DDNS?&logo=github&style=flatten
)](https://github.com/NewFuture/DDNS/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/ddns.svg?label=ddns&logo=pypi&style=flatten)](https://pypi.org/project/ddns/)
[![Docker Image Version](https://img.shields.io/docker/v/newfuture/ddns?label=newfuture/ddns&logo=docker&&sort=semver&style=flatten)](https://hub.docker.com/r/newfuture/ddns)
[![Build Status](https://github.com/NewFuture/DDNS/actions/workflows/build.yml/badge.svg?event=push)](https://github.com/NewFuture/DDNS/actions/workflows/build.yml)
[![Publish](https://github.com/NewFuture/DDNS/actions/workflows/publish.yml/badge.svg)](https://github.com/NewFuture/DDNS/actions/workflows/publish.yml)

---

## Features

- **Compatibility and Cross-Platform:**
  - [Docker (@NN708)](https://hub.docker.com/r/newfuture/ddns) [![Docker Image Size](https://img.shields.io/docker/image-size/newfuture/ddns/latest?logo=docker&style=social)](https://hub.docker.com/r/newfuture/ddns)[![Docker Platforms](https://img.shields.io/badge/arch-amd64%20%7C%20arm64%20%7C%20arm%2Fv7%20%7C%20arm%2Fv6%20%7C%20ppc64le%20%7C%20s390x%20%7C%20386%20%7C%20riscv64-blue?style=social)](https://hub.docker.com/r/newfuture/ddns)
  - [Binary files](https://github.com/NewFuture/DDNS/releases/latest) ![cross platform](https://img.shields.io/badge/system-windows_%7C%20linux_%7C%20mac-success.svg?style=social)
  
- **Configuration Methods:**
  - [Command Line Arguments](/doc/config/cli.en.md)
  - [JSON Configuration File](/doc/config/json.en.md) (supports single-file multi-provider, multiple config files, and remote URL)
  - [Environment Variables](/doc/config/env.en.md)
  - [Provider Configuration Guide](/doc/providers/)

- **Domain Support:**
  - Multiple domain support
  - Multi-level domain resolution
  - Automatic DNS record creation
  - Multiple configuration files and multi-provider concurrent execution
- **IP Types:**
  - Private IPv4 / IPv6
  - Public IPv4 / IPv6 (supports custom API)
  - Custom commands (shell)
  - Regex selection support (@rufengsuixing)
- **Network Proxy:**
  - HTTP proxy support
  - Automatic multi-proxy switching
- **DNS Provider Support:**
  - [DNSPOD China](https://www.dnspod.cn/) ([Configuration Guide](doc/providers/dnspod.en.md))
  - [Alibaba Cloud DNS](http://www.alidns.com/) ([Configuration Guide](doc/providers/alidns.en.md)) ⚡
  - [Alibaba Cloud ESA](https://esa.console.aliyun.com/) ([Configuration Guide](doc/providers/aliesa.en.md)) ⚡
  - [DNS.COM](https://www.dns.com/) ([Configuration Guide](doc/providers/dnscom.en.md)) (@loftor-git)
  - [DNSPOD International](https://www.dnspod.com/) ([Configuration Guide](doc/providers/dnspod_com.en.md))
  - [CloudFlare](https://www.cloudflare.com/) ([Configuration Guide](doc/providers/cloudflare.en.md)) (@tongyifan)
  - [HE.net](https://dns.he.net/) ([Configuration Guide](doc/providers/he.en.md)) (@NN708) (Does not support auto-record creation)
  - [Huawei Cloud](https://huaweicloud.com/) ([Configuration Guide](doc/providers/huaweidns.en.md)) (@cybmp3) ⚡
  - [NameSilo](https://www.namesilo.com/) ([Configuration Guide](doc/providers/namesilo.en.md))
  - [Tencent Cloud DNS](https://cloud.tencent.com/) ([Configuration Guide](doc/providers/tencentcloud.en.md)) ⚡
  - [Tencent Cloud EdgeOne](https://cloud.tencent.com/product/teo) ([Configuration Guide](doc/providers/edgeone.en.md)) ⚡
  - [No-IP](https://www.noip.com/) ([Configuration Guide](doc/providers/noip.en.md))
  - Custom Callback API ([Configuration Guide](doc/providers/callback.en.md))
  
  > ⚡ Providers marked with lightning use advanced HMAC-SHA256 signature authentication for enterprise-level security
- **Other Features:**
  - Configurable scheduled tasks
  - TTL configuration support
  - DNS line (ISP) configuration support (for domestic providers)
  - Local file caching (reduces API requests)
  - Custom callback API trigger on IP change (mutually exclusive with DDNS functionality)

## Usage

### ① Installation

Choose one of the following methods: `Docker`, `binary` version, `pip` version, or `source code` execution.

Docker version is recommended for best compatibility, small size, and optimized performance.

- #### Docker (Recommended)

  For detailed instructions and advanced usage, see [Docker Usage Documentation](/doc/docker.en.md)

  <details>
  <summary markdown="span">Supports command line, configuration file, and environment variable parameters</summary>

  - Command line CLI

      ```sh
      docker run newfuture/ddns -h
      ```

  - Using configuration file (Docker working directory `/ddns/`, default config location `/ddns/config.json`):

      ```sh
      docker run -d -v /host/config/:/ddns/ --network host newfuture/ddns
      ```

  - Using environment variables:

      ```sh
      docker run -d \
        -e DDNS_DNS=dnspod \
        -e DDNS_ID=12345 \
        -e DDNS_TOKEN=mytokenkey \
        -e DDNS_IPV4=ddns.newfuture.cc \
        --network host \
        newfuture/ddns
      ```

  </details>

- #### Binary Version (Single file, no Python required)

  Go to [releases to download the corresponding version](https://github.com/NewFuture/DDNS/releases/latest)

  Or use the one‑click installation script to automatically download and install the binary for your platform:

  ```bash
  curl -#fSL https://ddns.newfuture.cc/install.sh | sh
  ```
  Note: Installing to system directories (e.g., /usr/local/bin) may require root or sudo; if permissions are insufficient, run as `sudo sh`.

  For detailed instructions, see [Installation Documentation](doc/install.en.md)

- #### pip Installation (Requires pip or easy_install)

  1. Install ddns: `pip install ddns` or `easy_install ddns`
  2. Run: `ddns -h` or `python -m ddns`

- #### Source Code Execution (No dependencies, requires Python environment)

  1. Clone or [download this repository](https://github.com/NewFuture/DDNS/archive/master.zip) and extract
  2. Run `python -m ddns`

### ② Quick Configuration

1. Apply for API `token`, fill in the corresponding `id` and `token` fields:

   - **DNSPOD (China)**: [Create token](https://support.dnspod.cn/Kb/showarticle/tsid/227/) | [Detailed Configuration](doc/providers/dnspod.en.md)
   - **Alibaba Cloud DNS**: [Apply for accesskey](https://help.aliyun.com/document_detail/87745.htm) | [Detailed Configuration](doc/providers/alidns.en.md)
   - **Alibaba Cloud ESA**: [Apply for accesskey](https://help.aliyun.com/document_detail/87745.htm) | [Detailed Configuration](doc/providers/aliesa.en.md)
   - **DNS.COM**: [API Key/Secret](https://www.dns.com/member/apiSet) | [Detailed Configuration](doc/providers/dnscom.en.md)
   - **DNSPOD (International)**: [Get token](https://www.dnspod.com/docs/info.html#get-the-user-token) | [Detailed Configuration](doc/providers/dnspod_com.en.md)
   - **CloudFlare**: [API Key](https://support.cloudflare.com/hc/en-us/articles/200167836-Where-do-I-find-my-Cloudflare-API-key-) (Besides `email + API KEY`, you can also use `Token`, **requires list Zone permission**) | [Detailed Configuration](doc/providers/cloudflare.en.md)
   - **HE.net**: [DDNS Documentation](https://dns.he.net/docs.html) (Only fill the set password in the `token` field, `id` field can be left empty) | [Detailed Configuration](doc/providers/he.en.md)
   - **Huawei Cloud DNS**: [APIKEY Application](https://console.huaweicloud.com/iam/) (Click Access Keys on the left, then click Create Access Key) | [Detailed Configuration](doc/providers/huaweidns.en.md)
   - **NameSilo**: [API Key](https://www.namesilo.com/account/api-manager) (Get API Key from API Manager) | [Detailed Configuration](doc/providers/namesilo.en.md)
   - **Tencent Cloud DNS**: [Detailed Configuration](doc/providers/tencentcloud.en.md)
   - **No-IP**: [Username and Password](https://www.noip.com/) (Use No-IP account username and password) | [Detailed Configuration](doc/providers/noip.en.md)
   - **Custom Callback**: For parameter configuration, please refer to the custom callback configuration instructions below

2. Modify the configuration file, `ipv4` and `ipv6` fields for domains to be updated, refer to configuration instructions for details

## Detailed Configuration

All fields can be configured through three methods, with priority: **Command Line Parameters > JSON Configuration File > Environment Variables**

1. [Command Line Parameters](doc/config/cli.en.md) `ddns --key=value` (use `ddns -h` for details), highest priority
2. [JSON Configuration File](doc/config/json.en.md) (null values are considered valid and will override environment variable settings; if no corresponding key exists, environment variables will be used)
3. [Environment Variables](doc/config/env.en.md) with DDNS_ prefix plus key in uppercase or lowercase, dots converted to underscores (`${ddns_id}` or `${DDNS_ID}`, `${DDNS_LOG_LEVEL}`)

> 📖 **Environment Variables Documentation**: See [Environment Variables Configuration](doc/config/env.en.md) for detailed usage and examples of all environment variables

<details open>
<summary markdown="span">config.json Configuration File</summary>

- A template configuration file will be automatically generated on first run
- Use `-c` to specify a configuration file (defaults to config.json in the current directory)
- Recommended to use editors that support JsonSchema like VSCode for editing configuration files
- See [JSON Configuration File Documentation](doc/config/json.en.md) for complete configuration options and examples

```bash
ddns -c path/to/config.json
# Or run with Python
python -m ddns -c /path/to/config.json
# Remote configuration file
ddns -c https://ddns.newfuture.cc/tests/config/debug.json
```

#### Configuration Parameters Table

|  key   |        type        | required |   default   |    description     | tips                                                                                                                                                                                     |
| :----: | :----------------: | :------: | :---------: | :----------------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|   id   |       string       |    √     |     N/A     |    API Access ID   | Cloudflare uses email (leave empty when using Token)<br>HE.net can be left empty<br>Huawei Cloud uses Access Key ID (AK)                                                              |
| token  |       string       |    √     |     N/A     |   API Auth Token   | Some platforms call it secret key, **remove when sharing feedback**                                                                                                                     |
|  dns   |       string       |    No    | `"dnspod"`  |     DNS Provider   | Alibaba DNS: `alidns`, Alibaba ESA: `aliesa`, Cloudflare: `cloudflare`, DNS.COM: `dnscom`, DNSPOD China: `dnspod`, DNSPOD International: `dnspod_com`, HE.net: `he`, Huawei Cloud: `huaweidns`, NameSilo: `namesilo`, Tencent Cloud: `tencentcloud`, Tencent EdgeOne: `edgeone`, No-IP: `noip`, Custom Callback: `callback`. Some providers have [detailed configuration docs](doc/providers/) |
|  ipv4  |       array        |    No    |    `[]`     |   IPv4 Domain List | When `[]`, IPv4 address will not be retrieved and updated                                                                                                                               |
|  ipv6  |       array        |    No    |    `[]`     |   IPv6 Domain List | When `[]`, IPv6 address will not be retrieved and updated                                                                                                                               |
| index4 | string\|int\|array |    No    | `"default"` |   IPv4 Get Method  | Can set `network interface`, `private`, `public`, `regex` etc.                                                                                                                          |
| index6 | string\|int\|array |    No    | `"default"` |   IPv6 Get Method  | Can set `network interface`, `private`, `public`, `regex` etc.                                                                                                                          |
|  ttl   |       number       |    No    |   `null`    | DNS Resolution TTL | Uses DNS default policy when not set                                                                                                                                                    |
| proxy  |   string\|array    |    No    |     N/A     | HTTP Proxy Format: `http://host:port` | Multiple proxies tried sequentially until success, `DIRECT` for direct connection                                                                                                      |
|  ssl   |  string\|boolean   |    No    |  `"auto"`   | SSL Certificate Verification | `true` (force verify), `false` (disable verify), `"auto"` (auto downgrade) or custom CA certificate file path                                                                         |
| debug  |        bool        |    No    |   `false`   |    Enable Debug    | Debug mode, only effective with command line parameter `--debug`                                                                                                                       |
| cache  |    string\|bool    |    No    |   `true`    |    Cache Records   | Keep enabled normally to avoid frequent updates, default location is `ddns.cache` in temp directory, can also specify a specific path                                                |
|  log   |       object       |    No    |   `null`    |  Log Config (Optional) | Log configuration object, supports `level`, `file`, `format`, `datefmt` parameters                                                                                                     |

#### index4 and index6 Parameter Description

- Numbers (`0`, `1`, `2`, `3`, etc.): The i-th network interface IP
- String `"default"` (or no this field): System default IP for external access
- String `"public"`: Use public IP (query via public API, simplified URL mode)
- String `"url:xxx"`: Open URL `xxx` (e.g., `"url:http://ip.sb"`), extract IP address from returned data
- String `"regex:xxx"` Regular expression (e.g., `"regex:192.*"`): Extract the first IP address matching from `ifconfig`/`ipconfig`, **note JSON escaping** (`\` should be written as `\\`)
  - `"192.*"` matches all IPs starting with 192 (note: `regex:` cannot be omitted)
  - To match `10.00.xxxx`, write as `"regex:10\\.00\\..*"` (`"\\"` JSON escapes to `\`)
- String `"cmd:xxxx"`: Execute command `xxxx` and use stdout output as target IP
- String `"shell:xxx"`: Use system shell to run `xxx`, and use stdout result as target IP
- `false`: Force disable IPv4 or IPv6 DNS resolution updates
- List: Execute index rules in the list sequentially, using the first successful result as target IP
  - For example, `["public", "regex:172\\..*"]` will first query public API, then look for local IPs starting with 172 if no IP is obtained

#### Custom Callback Configuration

- `id` field: Fill in callback URL starting with HTTP or HTTPS, HTTPS recommended, supports variable replacement
- `token` field: POST request parameters (JSON object or JSON string), use GET request if this field is empty or missing. When JSON parameter values contain constants from the table below, they will be automatically replaced with actual content

For detailed configuration guide, see: [Callback Provider Configuration](doc/providers/callback.en.md)

| Constant Name    | Constant Content             | Description |
| ---------------- | ---------------------------- | ----------- |
| `__DOMAIN__`     | DDNS Domain                  |             |
| `__IP__`         | Obtained corresponding type IP address |             |
| `__RECORDTYPE__` | DDNS Record Type             |             |
| `__TTL__`        | DDNS TTL                     |             |
| `__TIMESTAMP__`  | Request timestamp            | With decimal |

#### Configuration Example

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "id": "12345",
  "token": "mytokenkey",
  "dns": "dnspod or dnspod_com or alidns or aliesa or dnscom or cloudflare or he or huaweidns or namesilo or tencentcloud or noip or callback",
  "ipv4": ["ddns.newfuture.cc", "ipv4.ddns.newfuture.cc"],
  "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"],
  "index4": 0,
  "index6": "public",
  "ttl": 600,
  "proxy": ["http://127.0.0.1:1080", "DIRECT"],
  "log": {
    "level": "DEBUG",
    "file": "dns.log",
    "datefmt": "%Y-%m-%dT%H:%M:%S"
  }
}
```

</details>

### Configuration Priority and Field Override Relationship

If the same configuration item is set in multiple places, the following priority rules apply:

- **Command Line Parameters**: Highest priority, overrides all other settings
- **JSON Configuration File**: Between command line and environment variables, overrides environment variable settings
- **Environment Variables**: Lowest priority, used when not set by other methods

**Advanced Usage:**

- JSON configuration file can contain only partial fields, missing fields will use environment variables
- Environment variables support both uppercase and lowercase formats
- Support for nested configuration through dot notation converted to underscores

### Scheduled Tasks

<details>
<summary markdown="span">Use built-in task command to set up scheduled tasks (checks IP every 5 minutes by default for automatic updates)</summary>

DDNS provides a built-in `task` subcommand for managing scheduled tasks with cross-platform automated deployment:

#### Basic Usage

```bash
# Install scheduled task (default 5-minute interval)
ddns task --install --dns dnspod --id your_id --token your_token --ipv4 your.domain.com

# Check task status
ddns task --status

# Uninstall scheduled task
ddns task --uninstall
```

#### Supported Systems

- **Windows**: Uses Task Scheduler
- **Linux**: Automatically selects systemd or crontab
- **macOS**: Uses launchd

#### Advanced Management

```bash
# Install with custom interval (minutes)
ddns task --install 10 -c /etc/ddns/config.json

# Enable/disable tasks
ddns task --enable
ddns task --disable
```

> **New Feature Advantages**:
>
> - ✅ Cross-platform automatic system detection
> - ✅ Automatically overwrites existing tasks without manual uninstallation
> - ✅ Supports all DDNS configuration parameters
> - ✅ Unified command-line interface

For detailed configuration guide, see: [CLI Parameters Documentation](/doc/config/cli.en.md#task-management)

#### Docker

Docker images, without additional parameters, have a scheduled task enabled by default that runs every 5 minutes

</details>

## FAQ

<details>
<summary markdown="span">Windows Server [SSL: CERTIFICATE_VERIFY_FAILED]</summary>

> Windows Server default security policy will prohibit any untrusted SSL certificates. You can manually add the corresponding certificates [#56](https://github.com/NewFuture/DDNS/issues/56#issuecomment-487371078)

Use the system's built-in IE browser to visit the corresponding API once:

- alidns: <https://alidns.aliyuncs.com>
- aliesa: <https://esa.cn-hangzhou.aliyuncs.com>
- cloudflare: <https://api.cloudflare.com>
- dns.com: <https://www.dns.com>
- dnspod.cn: <https://dnsapi.cn>
- dnspod international: <https://api.dnspod.com>
- Huawei DNS: <https://dns.myhuaweicloud.com>

</details>

<details>
<summary markdown="span">Troubleshooting and Feedback</summary>

1. First confirm whether it's a system/network environment issue
2. Search for similar issues in [issues](https://github.com/NewFuture/DDNS/issues)
3. If neither of the above can solve the problem or you're sure it's a bug, [create a new issue here](https://github.com/NewFuture/DDNS/issues/new)
   - [ ] Enable `--debug`
   - [ ] Include these contents: **running version and method**, **system environment**, **error logs**, **configuration file with id/token removed**
   - [ ] For source code execution, specify the Python environment used

</details>

---

## Contributors

<a href="https://github.com/NewFuture/DDNS/graphs/contributors"><img src="https://contrib.rocks/image?repo=NewFuture/DDNS" /></a>

## License

[![MIT](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](https://github.com/NewFuture/DDNS/blob/master/LICENSE)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=NewFuture/DDNS&type=Date)](https://star-history.com/#NewFuture/DDNS&Date)
