# [<img src="docs/public/img/ddns.svg" width="40" height="40" alt="DDNS 标志"/>](https://ddns.newfuture.cc) DDNS

> 自动将 DNS 记录同步到当前 IPv4/IPv6 地址。一个无第三方运行依赖、可跨平台部署的动态 DNS 客户端。

<div class="ddns-home-proof" role="list" aria-label="核心兼容性">
  <p role="listitem"><strong>IPv4 + IPv6</strong><br><span>内网、公网与自定义地址来源</span></p>
  <p role="listitem"><strong>15+ DNS 服务商</strong><br><span>国内、国际与自定义回调</span></p>
  <p role="listitem"><strong>4 种运行方式</strong><br><span>Docker、二进制、pip、源码</span></p>
  <p role="listitem"><strong>仅 Python 标准库</strong><br><span>运行时无需安装第三方依赖</span></p>
</div>

<div class="ddns-home-actions">
  <p class="is-primary"><a href="#选择安装方式"><strong>选择安装方式</strong><span>比较 Docker、二进制、pip 与源码</span></a></p>
  <p><a href="docs/config/studio.md"><strong>打开配置工具</strong><span>在浏览器中生成并校验 config.json</span></a></p>
</div>

<details class="ddns-home-status">
<summary>查看构建、版本与发布状态</summary>

[![GitHub](https://img.shields.io/github/license/NewFuture/DDNS?logo=github&style=flat)](https://github.com/NewFuture/DDNS)
[![Build](https://github.com/NewFuture/DDNS/actions/workflows/build.yml/badge.svg?event=push)](https://github.com/NewFuture/DDNS/actions/workflows/build.yml)
[![Publish](https://github.com/NewFuture/DDNS/actions/workflows/publish.yml/badge.svg)](https://github.com/NewFuture/DDNS/actions/workflows/publish.yml)
[![Release](https://img.shields.io/github/v/release/NewFuture/DDNS?logo=github&style=flat)](https://github.com/NewFuture/DDNS/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/ddns.svg?logo=pypi&style=flat)](https://pypi.org/project/ddns/)
[![Python Version](https://img.shields.io/pypi/pyversions/ddns.svg?logo=python&style=flat)](https://pypi.org/project/ddns/)
[![Docker](https://img.shields.io/docker/v/newfuture/ddns?logo=docker&sort=semver&style=flat)](https://hub.docker.com/r/newfuture/ddns)
[![Docker image size](https://img.shields.io/docker/image-size/newfuture/ddns/latest?logo=docker&style=flat)](https://hub.docker.com/r/newfuture/ddns)

</details>

## 三步完成首次更新

<div class="ddns-home-steps" role="list" aria-label="首次更新流程">
  <p role="listitem"><strong><span>1</span> 安装</strong><br>选择适合当前设备的运行方式。</p>
  <p role="listitem"><strong><span>2</span> 配置</strong><br>选择服务商，填写凭据与待更新域名。</p>
  <p role="listitem"><strong><span>3</span> 运行</strong><br>验证结果，再由常驻 Web 或系统任务持续更新。</p>
</div>

安装后可以先使用不会修改真实 DNS 记录的 Debug 服务商验证运行链路：

```bash
ddns --dns=debug --ipv4=home.example.com --debug
```

确认输出符合预期后，再在[配置工具](docs/config/studio.md)中选择实际服务商并导出配置。

## 选择安装方式

- **[Docker（推荐）](docs/docker.md)**：适合 NAS、服务器与容器平台，支持多架构，镜像默认每 5 分钟运行一次更新任务。
- **[二进制文件](https://github.com/NewFuture/DDNS/releases/latest)**：适合不希望安装 Python 的 Windows、Linux 与 macOS 用户，单文件即可运行。
- **[pip](https://pypi.org/project/ddns/)**：适合已有 Python 环境的设备，运行 `pip install ddns` 即可安装。
- **[源码运行](https://github.com/NewFuture/DDNS/archive/master.zip)**：适合需要审阅或定制代码的用户，解压后运行 `python -m ddns`。

Linux 与 macOS 也可以使用一键安装脚本获取匹配当前平台的二进制：

```bash
curl -fsSL https://ddns.newfuture.cc/install.sh | sh
```

### 实验性 Rust 客户端

仓库内的 [`rust/`](https://github.com/NewFuture/DDNS/tree/master/rust) 提供并行开发的 `ddns-rs` MVP，当前支持单次运行、IPv4/IPv6、全部 IP 获取规则，以及 Cloudflare、AliDNS、DNSPod 和 Debug。它可复用现有 CLI、环境变量和配置文件，但尚未替换稳定的 Python `ddns`，也未接入正式安装与发布。

```bash
cargo build --manifest-path rust/Cargo.toml --release --locked
rust/target/release/ddns-rs -c config.json
```

架构、验证命令、支持矩阵和迁移路线见 [Rust 开发文档](docs/dev/rust.md)。

## 为什么适合长期运行

### DNS 更新能力

- 同时管理多个域名、多个服务商和多份配置文件。
- 支持 IPv4/IPv6、内网地址、公网地址、URL、正则表达式与自定义命令取值。
- 自动查找 DNS 记录；多数服务商可自动创建不存在的记录（HE.net 与 No-IP 除外）；服务商支持时可配置 TTL 与解析线路。
- 本地缓存减少无变化时的 DNS API 请求。

### 部署与维护

- 仅使用 Python 标准库，兼容 Python 2.7 与 Python 3.x。
- 支持 HTTP 代理、多代理回退、SSL 验证策略与自定义 CA。
- Web 控制台内置常驻调度；无 Web 场景仍可使用 systemd/cron、launchd 或 Windows 任务计划程序。
- 支持日志级别、日志文件、格式与时间格式配置。

## 配置与凭据

[配置生成与校验工具](docs/config/studio.md)会在浏览器中处理输入，不会调用 DNS 服务商 API。可以先用 Debug 服务商校验结构，再切换到真实服务商。

多数运行配置项都可通过以下方式提供，优先级为：

1. **[命令行参数](docs/config/cli.md)**：`ddns --key=value`
2. **[JSON 配置文件](docs/config/json.md)**：适合多域名、多服务商和远程配置
3. **[环境变量](docs/config/env.md)**：适合 Docker 与自动化部署

少数控制项仅支持命令行，详见[命令行参数文档](docs/config/cli.md)。

凭据名称会因服务商而异，例如 API Token、Access Key 或 Secret。请从对应的[服务商文档](docs/providers/)获取最小权限配置，并在日志、Issue 或配置示例中删除真实凭据。

## DNS 服务商

- **国内与云平台**：[阿里 DNS](docs/providers/alidns.md)、[阿里云 ESA](docs/providers/aliesa.md)、[DNSPod](docs/providers/dnspod.md)、[腾讯云 DNS](docs/providers/tencentcloud.md)、[腾讯云 EdgeOne](docs/providers/edgeone.md)、[EdgeOne DNS](docs/providers/edgeone_dns.md)、[华为云 DNS](docs/providers/huaweidns.md)、[DNS.COM / 51DNS](docs/providers/51dns.md)、[西部数码](docs/providers/west.md)
- **国际服务商**：[Cloudflare](docs/providers/cloudflare.md)、[ClouDNS](docs/providers/cloudns.md)、[DNSPod 国际版](docs/providers/dnspod_com.md)、[HE.net](docs/providers/he.md)、[NameSilo](docs/providers/namesilo.md)、[No-IP](docs/providers/noip.md)
- **集成与验证**：[回调 API](docs/providers/callback.md)、[Debug](docs/providers/debug.md)

标有相关说明的云服务商使用 HMAC-SHA256 签名认证。完整能力、凭据格式与限制以[所有服务商文档](docs/providers/)为准。

## 运行与自动化

使用配置文件运行：

```bash
ddns -c config.json
```

长期运行本机控制台，并由同一进程每 5 分钟自动同步：

```bash
ddns -c config.json --interval 5 --open
```

提供 `--interval` 会自动进入 Web 模式，无需额外写 `web`；也可在本地 JSON 顶层配置 `"interval": 5`。Web 同时在 `/mcp` 提供 MCP `2026-07-28` Streamable HTTP。默认回环监听未配置 token 时，Web API 与 `/mcp` 均免认证；非回环或通配监听必须配置共享 HTTP token，并应由 HTTPS 反向代理保护。页面保存的新间隔会写回配置；暂停和恢复只影响当前进程。

让 GitHub Copilot 等本机 MCP 客户端查询缓存状态，或在人工确认后触发一次完整同步：

```bash
ddns mcp -c /etc/ddns/config.json
```

该 stdio 服务只使用 Python 标准库，不监听网络，也不会向模型暴露配置凭据；支持 MCP `2026-07-28`，并兼容 GitHub Copilot CLI 使用的 `2025-11-25`。具体客户端配置、工具与限制见 [MCP 服务文档](docs/config/mcp.md)。

不能启动本机进程的 MCP 客户端也可连接独立 HTTP endpoint：

```bash
ddns mcp -c /etc/ddns/config.json --transport http
```

不需要 Web 控制台时，可以安装每 5 分钟执行一次的系统定时任务：

```bash
ddns task --install 5 -c /etc/ddns/config.json
```

任务可通过 `ddns task --status` 查看，并使用 `--enable`、`--disable` 或 `--uninstall` 管理。不要让系统任务与 Web 内置调度同时运行。参数与平台差异请查看[命令行文档](docs/config/cli.md#task-management-定时任务管理)。

路由器或光猫仅支持传统 DDNS 协议时，可以使用 **[edge-ddns-proxy](https://github.com/NewFuture/edge-ddns-proxy)** 转换到现代 DNS 服务商 API。

## 获取帮助

1. 使用 `--debug` 复现问题，并确认是否来自网络、权限或系统环境。
2. 在 [Issues](https://github.com/NewFuture/DDNS/issues) 中搜索相同错误。
3. 仍无法解决时，[提交 Issue](https://github.com/NewFuture/DDNS/issues/new)，附上运行版本、安装方式、系统环境和已删除凭据的日志与配置。

开发与扩展请查看 [Provider 开发指南](docs/dev/provider.md)和[配置系统设计](docs/dev/config.md)。

## 项目

<a href="https://github.com/NewFuture/DDNS/graphs/contributors"><img src="https://contrib.rocks/image?repo=NewFuture/DDNS" alt="DDNS 项目贡献者"/></a>

DDNS 采用 [MIT License](https://github.com/NewFuture/DDNS/blob/master/LICENSE) 发布。源码、版本与变更记录均可在 [GitHub 仓库](https://github.com/NewFuture/DDNS)查看。
