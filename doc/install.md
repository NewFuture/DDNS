# 一键安装脚本 (One-Click Installation Script)

## 简介 (Introduction)

`install.sh` 是 DDNS 项目的一键安装脚本，支持在 Linux 和 macOS 系统上自动下载和安装 DDNS 二进制文件。

The `install.sh` script provides one-click installation for DDNS on Linux and macOS systems, automatically downloading and installing the appropriate binary for your platform.

## 特性 (Features)

### 🚀 跨平台支持 (Cross-Platform Support)
- ✅ Linux (glibc/musl)  
- ✅ macOS (Intel/Apple Silicon)
- ✅ 多架构支持 (Multiple architectures): x86_64, ARM64, ARM v7, ARM v6, i386

### 📦 版本管理 (Version Management)
- **latest**: 最新稳定版 (Latest stable release)
- **beta**: 最新测试版 (Latest beta release)  
- **v4.0.2**: 指定版本号 (Specific version)

### 🌍 网络优化 (Network Optimization)
- 自动检测网络连接 (Auto network connectivity check)
- 镜像站点回退 (Mirror fallback for China users):
  - `github.com` (主站 Primary)
  - `hub.gitmirror.com` (镜像 Mirror)
  - `proxy.gitwarp.com` (代理 Proxy)
  - `gh.200112.xyz` (备用 Backup)

### 🔧 智能检测 (Smart Detection)
- 自动检测操作系统和架构 (Auto OS and architecture detection)
- 自动选择下载工具 (curl/wget) (Auto download tool selection)
- 自动检测 Linux libc 类型 (glibc/musl) (Auto libc detection)

## 使用方法 (Usage)

### 基本安装 (Basic Installation)

```bash
# 在线安装最新稳定版 (Install latest stable version online)
curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash

# 使用 wget (Using wget)
wget -qO- https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash
```

### 版本选择 (Version Selection)

```bash
# 安装最新稳定版 (Install latest stable)
curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash -s -- latest

# 安装最新测试版 (Install latest beta)
curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash -s -- beta

# 安装指定版本 (Install specific version)
curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash -s -- v4.0.2
```

### 自定义安装 (Custom Installation)

```bash
# 下载脚本后执行 (Download script first)
curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh -o install.sh
chmod +x install.sh

# 自定义安装目录 (Custom installation directory)
./install.sh latest --install-dir /usr/local/bin

# 强制重新安装 (Force reinstallation)  
./install.sh latest --force

# 查看帮助 (Show help)
./install.sh --help
```

## 命令行选项 (Command Line Options)

| 选项 (Option) | 说明 (Description) |
|---------------|-------------------|
| `latest` | 安装最新稳定版 (Install latest stable version) |
| `beta` | 安装最新测试版 (Install latest beta version) |
| `v4.0.2` | 安装指定版本 (Install specific version) |
| `--install-dir PATH` | 指定安装目录 (Custom installation directory) |
| `--force` | 强制重新安装 (Force reinstallation) |
| `--help` | 显示帮助信息 (Show help message) |

## 系统要求 (System Requirements)

### Linux
- **GNU Linux**: glibc ≥ 2.28 (Debian 9+, Ubuntu 20.04+, CentOS 8+)
- **Musl Linux**: musl ≥ 1.1.24 (OpenWRT 19+)
- **架构 (Architecture)**: x86_64, i386, ARM64, ARM v7, ARM v6

### macOS  
- **版本 (Version)**: macOS 10.15+ 
- **架构 (Architecture)**: Intel x86_64, Apple Silicon (ARM64)

### 工具依赖 (Tool Dependencies)
- `curl` 或 `wget` (required)
- `bash` (required)
- `grep`, `cut` (usually pre-installed)

## 安装位置 (Installation Location)

默认安装到 `/usr/local/bin/ddns` (Default installation to `/usr/local/bin/ddns`)

如果该目录需要 root 权限，请使用 sudo 运行：
(If the directory requires root permissions, run with sudo:)

```bash
curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | sudo bash
```

## 验证安装 (Verify Installation)

```bash
# 检查版本 (Check version)
ddns --version

# 查看帮助 (Show help)  
ddns --help

# 检查安装位置 (Check installation location)
which ddns
```

## 卸载 (Uninstallation)

```bash
# 删除二进制文件 (Remove binary)
sudo rm -f /usr/local/bin/ddns

# 或从自定义目录删除 (Or remove from custom directory)
rm -f /path/to/your/ddns
```

## 故障排除 (Troubleshooting)

### 网络连接问题 (Network Connectivity Issues)
如果 GitHub 访问受限，脚本会自动尝试镜像站点。
(If GitHub access is restricted, the script will automatically try mirror sites.)

### 权限问题 (Permission Issues)  
```bash
# 使用 sudo 安装到系统目录 (Use sudo for system directory)
curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | sudo bash

# 或安装到用户目录 (Or install to user directory)
curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash -s -- latest --install-dir ~/.local/bin
```

### 架构不支持 (Unsupported Architecture)
脚本会自动检测并报告不支持的架构。请查看 [releases 页面](https://github.com/NewFuture/DDNS/releases) 确认是否有适合的版本。
(The script will automatically detect and report unsupported architectures. Check the [releases page](https://github.com/NewFuture/DDNS/releases) for available versions.)

## 更新 DDNS (Update DDNS)

```bash
# 更新到最新版本 (Update to latest version)
curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash -s -- latest --force

# 更新到指定版本 (Update to specific version)
curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash -s -- v4.0.2 --force
```

## 开发和测试 (Development and Testing)

### 测试脚本 (Test Script)
```bash
# 运行测试 (Run tests)
./test_install.sh
```

### 贡献 (Contributing)
欢迎提交 Pull Request 来改进安装脚本！
(Pull requests are welcome to improve the installation script!)

## 许可证 (License)

与 DDNS 项目相同的 MIT 许可证。
(Same MIT license as the DDNS project.)