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
  - [Command Line Arguments](/doc/cli.en.md)
  - [JSON Configuration File](/doc/json.en.md)
  - [Environment Variables](/doc/env.en.md)
  - [Provider Configuration Guide](/doc/providers/)

- **Domain Support:**
  - Multiple domain support
  - Multi-level domain resolution
  - Automatic DNS record creation
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
  - [Tencent Cloud](https://cloud.tencent.com/) ([Configuration Guide](doc/providers/tencentcloud.en.md)) ⚡
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

Choose one of the following methods: `binary` version, `pip` version, `source code` execution, or `Docker`.

Docker version is recommended for best compatibility, small size, and optimized performance.

- #### Docker (Requires Docker Installation)

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

- #### pip Installation (Requires pip or easy_install)

  1. Install ddns: `pip install ddns` or `easy_install ddns`
  2. Run: `ddns -h` or `python -m ddns`

- #### Binary Version (Single file, no Python required)

  Go to [releases to download the corresponding version](https://github.com/NewFuture/DDNS/releases/latest)

- #### Source Code Execution (No dependencies, requires Python environment)

  1. Clone or [download this repository](https://github.com/NewFuture/DDNS/archive/master.zip) and extract
  2. Run `python run.py` or `python -m ddns`

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
   - **Tencent Cloud DNS**: [Detailed Configuration](doc/providers/tencentcloud.en.md)
   - **No-IP**: [Username and Password](https://www.noip.com/) (Use No-IP account username and password) | [Detailed Configuration](doc/providers/noip.en.md)
   - **Custom Callback**: For parameter configuration, please refer to the custom callback configuration instructions below

2. Modify the configuration file, `ipv4` and `ipv6` fields for domains to be updated, refer to configuration instructions for details

## Detailed Configuration

All fields can be configured through three methods, with priority: **Command Line Parameters > JSON Configuration File > Environment Variables**

1. [Command Line Parameters](doc/cli.en.md) `ddns --key=value` (use `ddns -h` for details), highest priority
2. [JSON Configuration File](doc/json.en.md) (null values are considered valid and will override environment variable settings; if no corresponding key exists, environment variables will be used)
3. Environment Variables with DDNS_ prefix plus key in uppercase or lowercase, dots converted to underscores (`${ddns_id}` or `${DDNS_ID}`, `${DDNS_LOG_LEVEL}`)

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
<summary markdown="span">Set up scheduled tasks to run automatically</summary>

This tool itself does not include loop and scheduled execution functions (to reduce code complexity). You can use system scheduled tasks to run regularly.

#### Windows

- [Recommended] Run as system identity, right-click "Run as administrator" on `task.bat` (or run in administrator command line)
- Run scheduled task as current user, double-click or run `task.bat` (a black window will flash during execution)

#### Linux

- Using init.d and crontab:

  ```bash
  sudo ./task.sh
  ```

- Using systemd:

  ```bash
  Install:
  sudo ./systemd.sh install
  Uninstall:
  sudo ./systemd.sh uninstall
  ```

  Files installed by this script comply with [Filesystem Hierarchy Standard (FHS)](https://en.wikipedia.org/wiki/Filesystem_Hierarchy_Standard):
  Executable files are located in `/usr/share/DDNS`
  Configuration files are located in `/etc/DDNS`

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
