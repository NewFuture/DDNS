# 一键安装脚本

DDNS 一键安装脚本，支持 Linux 和 macOS 系统自动下载安装。

## 快速安装

默认安装方式会安装稳定的 Python `ddns`。Rust 客户端使用独立命令
`ddns-rs`，不会覆盖 `ddns`：

```bash
# 在线安装最新稳定版
curl -fsSL https://ddns.newfuture.cc/install.sh | sh
# 如需 root 权限安装到系统目录，使用 sudo
curl -fsSL https://ddns.newfuture.cc/install.sh | sudo sh

# 或使用 wget
wget -qO- https://ddns.newfuture.cc/install.sh | sh
```

> **说明：** 默认安装到 `/usr/local/bin`，如果该目录需要管理员权限，脚本会自动提示使用 sudo，或者可以预先使用 sudo 运行。

### Rust V5 开发版本

Rust V5 在 `v5` 分支开发，当前 `5.0.0-alpha1` 尚未发布。请从源码构建，
或使用 Rust CI 的五平台二进制工件，不要把 Python 的 `latest` / `beta`
当作 V5 下载入口：

```bash
cargo build --manifest-path rust/Cargo.toml --release --locked
rust/target/release/ddns-rs --help
```

源码或 CI 二进制支持 Web 与 MCP：

```bash
rust/target/release/ddns-rs web -c config.json --interval 5
rust/target/release/ddns-rs mcp -c config.json
```

Web 内嵌控制台并提供 `/mcp`；独立 HTTP MCP 使用 `mcp --transport http`。
Web/MCP 仅管理单个本地配置，非回环 HTTP 监听必须设置 `--http-token`。
进程内调度不迁移或检测系统任务；必须手动停用旧 Python/主机任务，避免重复运行。
详细选项、安全边界及兼容限制见 [Rust V5 开发文档](dev/rust.md)。

保留的 Rust 安装脚本是未来发布工具，仅支持 Linux x64/arm64 和 macOS x64/arm64，下载独立的
`ddns-rs-linux-x64`、`ddns-rs-linux-arm64`、`ddns-rs-macos-x64` 或
`ddns-rs-macos-arm64` Release 资产及其 `.sha256` 校验文件。Windows x64
工件名为 `ddns-rs-windows-x64.exe`。
Linux 资产使用静态 musl 目标，可同时运行于 glibc 与 musl 发行版。
Rust 安装器默认写入 `~/.local/bin/ddns-rs`，无需管理员权限；如需系统级安装，
显式传入 `--install-dir /usr/local/bin` 并自行提供相应权限。
安装器仅适用于已包含 `ddns-rs-*` 资产的标签版本；V5 发布前还需隔离版本选择逻辑。
开发与发布准备边界见 [Rust V5 开发文档](dev/rust.md)。

安装器会在系统提供 `sha256sum` 或 `shasum` 时校验下载的发布校验和。可用
`--verify` 强制要求校验，或仅在已理解风险时使用 `--no-verify`。

## 版本选择

```bash
# 安装最新稳定版
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- latest

# 安装最新测试版
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- beta

# 安装指定版本
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- v4.0.2
```

## 命令行选项

| 选项 | 说明 |
| --- | --- |
| `latest` | 安装最新稳定版（默认） |
| `beta` | 安装最新测试版 |
| `v4.0.2` | 安装指定版本 |
| `--install-dir PATH` | 指定安装目录（默认：/usr/local/bin） |
| `--proxy URL` | 指定代理域名前缀（例如：`https://hub.gitmirror.com/`），覆盖自动探测 |
| `--force` | 强制重新安装 |
| `--uninstall` | 卸载已安装的 ddns |
| `--help` | 显示帮助信息 |

## 高级用法

```bash
# 自定义安装目录
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- beta --install-dir ~/.local/bin

# 强制重新安装
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- --force

# 卸载
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- --uninstall

# 指定代理域名（覆盖自动探测）
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- --proxy https://hub.gitmirror.com/
```

## 系统支持

**操作系统：** Linux（glibc/musl）、macOS  
**架构：** x86_64、ARM64、ARM v7、ARM v6、i386  
**依赖：** curl 或 wget

### 自动检测功能
- **系统检测：** 自动识别操作系统、架构和 libc 类型
- **工具检测：** 自动选择 curl 或 wget 下载工具
- **网络优化：** 自动测试并选择最佳下载镜像（github.com → 国内镜像站）
- **手动覆盖：** 通过 `--proxy` 指定代理域名/镜像前缀，优先于自动探测

## 验证安装

```bash
ddns --version    # 检查版本
which ddns        # 检查安装位置
```

## 更新与卸载

```bash
# 更新到最新版本
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- latest

# 卸载
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- --uninstall

# 手动卸载
sudo rm -f /usr/local/bin/ddns
```

## 故障排除

**权限问题：** 使用 `sudo` 或安装到用户目录  
**网络问题：** 脚本自动使用镜像站点（hub.gitmirror.com、proxy.gitwarp.com 等）  
**架构不支持：** 查看 [releases 页面](https://github.com/NewFuture/DDNS/releases) 确认支持的架构
**代理环境:** 脚本会尊重系统代理设置（`HTTP_PROXY/HTTPS_PROXY`）；也可以使用 `--proxy https://hub.gitmirror.com/` 指定 GitHub 镜像前缀（覆盖自动探测）
