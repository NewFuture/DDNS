# [<img src="docs/public/img/ddns.svg" width="40" height="40" alt="DDNS logo"/>](https://ddns.newfuture.cc) DDNS

> Keep DNS records synchronized with the current IPv4 or IPv6 address. A cross-platform dynamic DNS client with no third-party runtime dependencies.

<div class="ddns-home-proof" role="list" aria-label="Core compatibility">
  <p role="listitem"><strong>IPv4 + IPv6</strong><br><span>Private, public, and custom address sources</span></p>
  <p role="listitem"><strong>15+ DNS providers</strong><br><span>Regional, global, and custom integrations</span></p>
  <p role="listitem"><strong>4 ways to run</strong><br><span>Docker, binary, pip, or source</span></p>
  <p role="listitem"><strong>Standard library only</strong><br><span>No third-party runtime packages</span></p>
</div>

<div class="ddns-home-actions">
  <p class="is-primary"><a href="#choose-an-installation-method"><strong>Choose an installation method</strong><span>Compare Docker, binary, pip, and source</span></a></p>
  <p><a href="docs/en/config/studio.md"><strong>Open Config Studio</strong><span>Build and validate config.json in the browser</span></a></p>
</div>

<details class="ddns-home-status">
<summary>View build, version, and release status</summary>

[![GitHub](https://img.shields.io/github/license/NewFuture/DDNS?logo=github&style=flat)](https://github.com/NewFuture/DDNS)
[![Build](https://github.com/NewFuture/DDNS/actions/workflows/build.yml/badge.svg?event=push)](https://github.com/NewFuture/DDNS/actions/workflows/build.yml)
[![Publish](https://github.com/NewFuture/DDNS/actions/workflows/publish.yml/badge.svg)](https://github.com/NewFuture/DDNS/actions/workflows/publish.yml)
[![Release](https://img.shields.io/github/v/release/NewFuture/DDNS?logo=github&style=flat)](https://github.com/NewFuture/DDNS/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/ddns.svg?logo=pypi&style=flat)](https://pypi.org/project/ddns/)
[![Python Version](https://img.shields.io/pypi/pyversions/ddns.svg?logo=python&style=flat)](https://pypi.org/project/ddns/)
[![Docker](https://img.shields.io/docker/v/newfuture/ddns?logo=docker&sort=semver&style=flat)](https://hub.docker.com/r/newfuture/ddns)
[![Docker image size](https://img.shields.io/docker/image-size/newfuture/ddns/latest?logo=docker&style=flat)](https://hub.docker.com/r/newfuture/ddns)

</details>

## Complete the first update in three steps

<div class="ddns-home-steps" role="list" aria-label="First update workflow">
  <p role="listitem"><strong><span>1</span> Install</strong><br>Choose the runtime that fits the current device.</p>
  <p role="listitem"><strong><span>2</span> Configure</strong><br>Select a provider, credentials, and domains.</p>
  <p role="listitem"><strong><span>3</span> Run</strong><br>Verify the result, then schedule ongoing updates.</p>
</div>

After installation, verify the complete execution path with the Debug provider, which never changes real DNS records:

```bash
ddns --dns=debug --ipv4=home.example.com --debug
```

Once the output looks correct, select a real provider in [Config Studio](docs/en/config/studio.md) and export the configuration.

## Choose an installation method

- **[Docker (recommended)](docs/en/docker.md)**: Best for NAS devices, servers, and container platforms. Multi-architecture images run an update task every five minutes by default.
- **[Standalone binary](https://github.com/NewFuture/DDNS/releases/latest)**: Best when Python should not be installed. A single file runs on Windows, Linux, or macOS.
- **[pip](https://pypi.org/project/ddns/)**: Best for an existing Python environment. Install with `pip install ddns`.
- **[Source](https://github.com/NewFuture/DDNS/archive/master.zip)**: Best when the code needs to be reviewed or customized. Extract it and run `python -m ddns`.

Linux and macOS users can also install the matching binary with one command:

```bash
curl -fsSL https://ddns.newfuture.cc/install.sh | sh
```

## Why it works for long-running deployments

### DNS update capabilities

- Manage multiple domains, providers, and configuration files together.
- Resolve IPv4 or IPv6 from interfaces, default routes, public APIs, URLs, regular expressions, or custom commands.
- Find DNS records automatically and create missing records with most providers (except HE.net and No-IP); configure TTL and routing lines where supported.
- Reduce unchanged DNS API requests with a local cache.

### Deployment and operations

- Uses only the Python standard library and supports Python 2.7 and Python 3.x.
- Supports HTTP proxies, multi-proxy fallback, SSL verification policies, and custom certificate authorities.
- Includes cross-platform scheduling through systemd/cron on Linux, launchd on macOS, and Task Scheduler on Windows.
- Supports configurable log levels, files, formats, and timestamps.

## Configuration and credentials

[Config Studio](docs/en/config/studio.md) processes input in the browser and does not call DNS provider APIs. Validate the structure with the Debug provider before switching to a real provider.

Most runtime configuration fields can be supplied through these methods, in priority order:

1. **[Command-line arguments](docs/en/config/cli.md)**: `ddns --key=value`
2. **[JSON configuration](docs/en/config/json.md)**: Best for multiple domains, providers, or remote configurations
3. **[Environment variables](docs/en/config/env.md)**: Best for Docker and automated deployment

A small set of controls is command-line only; see the [CLI reference](docs/en/config/cli.md).

Credential names vary by provider, including API Token, Access Key, and Secret. Follow the matching [provider guide](docs/en/providers/) for least-privilege access, and remove real credentials from logs, issues, and examples.

## DNS providers

- **Regional and cloud platforms**: [AliDNS](docs/en/providers/alidns.md), [Alibaba Cloud ESA](docs/en/providers/aliesa.md), [DNSPod China](docs/en/providers/dnspod.md), [Tencent Cloud DNS](docs/en/providers/tencentcloud.md), [Tencent Cloud EdgeOne](docs/en/providers/edgeone.md), [EdgeOne DNS](docs/en/providers/edgeone_dns.md), [Huawei Cloud DNS](docs/en/providers/huaweidns.md), [DNS.COM / 51DNS](docs/en/providers/51dns.md), [West.cn](docs/en/providers/west.md)
- **Global providers**: [Cloudflare](docs/en/providers/cloudflare.md), [ClouDNS](docs/en/providers/cloudns.md), [DNSPod Global](docs/en/providers/dnspod_com.md), [HE.net](docs/en/providers/he.md), [NameSilo](docs/en/providers/namesilo.md), [No-IP](docs/en/providers/noip.md)
- **Integration and validation**: [Callback API](docs/en/providers/callback.md), [Debug](docs/en/providers/debug.md)

Cloud providers marked in their guides use HMAC-SHA256 request signing. See the [complete provider documentation](docs/en/providers/) for capabilities, credential formats, and limitations.

## Running and automation

Run with a configuration file:

```bash
ddns -c config.json
```

Install a system task that runs every five minutes:

```bash
ddns task --install 5 -c /etc/ddns/config.json
```

Inspect it with `ddns task --status`, then manage it with `--enable`, `--disable`, or `--uninstall`. See the [CLI documentation](docs/en/config/cli.md#task-management) for platform-specific behavior.

If a router or modem only supports a legacy DDNS protocol, use **[edge-ddns-proxy](https://github.com/NewFuture/edge-ddns-proxy)** to bridge it to a modern DNS provider API.

## Getting help

1. Reproduce the problem with `--debug`, then rule out network, permission, and operating-system issues.
2. Search [Issues](https://github.com/NewFuture/DDNS/issues) for the same error.
3. If it remains unresolved, [open an issue](https://github.com/NewFuture/DDNS/issues/new) with the version, installation method, system environment, and logs or configuration after removing credentials.

For development and extensions, see the [provider development guide](docs/en/dev/provider.md) and [configuration system design](docs/en/dev/config.md).

## Project

<a href="https://github.com/NewFuture/DDNS/graphs/contributors"><img src="https://contrib.rocks/image?repo=NewFuture/DDNS" alt="Contributors to DDNS"/></a>

DDNS is released under the [MIT License](https://github.com/NewFuture/DDNS/blob/master/LICENSE). Source, releases, and change history are available in the [GitHub repository](https://github.com/NewFuture/DDNS).
