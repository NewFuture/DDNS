# DDNS Release Information

[<img src="https://ddns.newfuture.cc/doc/img/ddns.svg" height="32px"/>](https://ddns.newfuture.cc)[![Github Release](https://img.shields.io/github/v/release/newfuture/ddns?style=for-the-badge&logo=github&label=DDNS)](https://github.com/NewFuture/DDNS/releases/latest)[![Docker Image Version](https://img.shields.io/docker/v/newfuture/ddns/latest?label=Docker&logo=docker&style=for-the-badge)](https://hub.docker.com/r/newfuture/ddns/tags?name=latest)[![PyPI version](https://img.shields.io/pypi/v/ddns?logo=python&style=for-the-badge)](https://pypi.org/project/ddns)

## 各版本一览表 | Download Methods Overview

| 系统环境 (System) | 架构支持 (Architecture) | 说明 (Description) |
| ---------: |:------------------- |:---------|
| Docker | x64, 386, arm64, armv7, armv6, s390x, ppc64le, riscv64<br>[Github Registry](https://ghcr.io/newfuture/ddns) <br> [Docker Hub](https://hub.docker.com/r/newfuture/ddns) | 支持8种架构 <br/>`docker pull ghcr.io/newfuture/ddns:latest` <br/> 🚀 `docker pull newfuture/ddns:latest` |
| Windows | x64: [x64.zip](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-windows-x64.zip) · [x64.exe](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-windows-x64.exe) <br> x86: [x86.zip](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-windows-x86.zip) · [x86.exe](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-windows-x86.exe) <br> arm64: [arm64.zip](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-windows-arm64.zip) · [arm64.exe](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-windows-arm64.exe) | 在最新 Windows 10 和 Windows 11 测试。 <br> ✅ Tested on Windows 10 and Windows 11 |
| GNU Linux | [64-bit (ddns-glibc-linux_amd64)](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-glibc-linux_amd64)<br> [32-bit (ddns-glibc-linux_386)](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-glibc-linux_386) <br> [ARM64 (ddns-glibc-linux_arm64)](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-glibc-linux_arm64)<br> [ARM/V7 (ddns-glibc-linux_arm_v7)](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-glibc-linux_arm_v7) | 常规Linux桌面或服务器，需GLIBC≥2.28。<br>（如 Debian 9+、Ubuntu 20.04+、CentOS 8+）<br> 🐧 For common Linux desktop/server with GLIBC ≥ 2.28 |
| Musl Linux | [64-bit (ddns-musl-linux_amd64)](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-musl-linux_amd64) <br> [32-bit (ddns-musl-linux_386)](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-musl-linux_386) <br> [ARM64 (ddns-musl-linux_arm64)](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-musl-linux_arm64)<br> [ARM/V7 (ddns-musl-linux_arm_v7)](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-musl-linux_arm_v7) <br> [ARM/V6 (ddns-musl-linux_arm_v6)](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-musl-linux_arm_v6) | 适用于OpenWRT及嵌入式系统（musl ≥ 1.1.24），如OpenWRT 19+；ARMv6未测试。<br> 🛠️ For OpenWRT and embedded systems with musl ≥ 1.1.24. ARMv6 not tested. |
| macOS | [ARM/M-chip (ddns-mac-arm64)](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-mac-arm64) <br> [Intel x86_64 (ddns-mac-x64)](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-mac-x64) | 仅虚拟环境测试，未在真机测试 <br> 🍎 Tested in virtual environments only |
| PIP | [`ddns` (全平台)](https://pypi.org/project/ddns) | 可通过 pip/pip2/pip3/easy_install 安装，部分环境自动添加至 PATH。<br> 📦 Installable via pip and easy_install. May auto-register in PATH |
| Pipx | [`pipx run ddns` (全平台)](https://pypi.org/project/ddns) | 🚀 直接运行无需安装，独立虚拟环境避免冲突。<br> 🚀 Run directly without installation, isolated virtual environment. |
| Python | 源码 Source code (全平台)<br> [zip](https://github.com/NewFuture/DDNS/archive/refs/tags/latest.zip) + [tar](https://github.com/NewFuture/DDNS/archive/refs/tags/latest.tar.gz) | 可在 Python 2.7 或 Python 3 上直接运行，无需依赖 <br> 🐍 Directly runnable with Python 2.7 or Python 3. No extra dependencies. |

---

## Docker (推荐 Recommended)  ![Docker Image Size](https://img.shields.io/docker/image-size/newfuture/ddns/latest?style=social)[![Docker Platforms](https://img.shields.io/badge/arch-amd64%20%7C%20arm64%20%7C%20arm%2Fv7%20%7C%20arm%2Fv6%20%7C%20ppc64le%20%7C%20s390x%20%7C%20386%20%7C%20riscv64-blue?logo=docker&style=social)](https://hub.docker.com/r/newfuture/ddns)

```bash
# 当前版本 (Current version)
docker run --name ddns -v $(pwd)/:/ddns/ newfuture/ddns:latest -h

# 最新版本 (Latest version, may use cache)
docker run --name ddns -v $(pwd)/:/ddns/ newfuture/ddns -h

# 后台运行 (Run in background)
docker run -d --name ddns -v $(pwd)/:/ddns/ newfuture/ddns:latest
```

📁 请将 `$(pwd)` 替换为你的配置文件夹
📖 Replace $(pwd) with your config folder

* 使用 `-h` 查看帮助信息 (Use `-h` for help)
* config.json 支持编辑器自动补全 (config.json supports autocompletion)
* 支持 `DDNS_XXX` 环境变量 (Supports `DDNS_XXX` environment variables)

支持源 (Supported registries):

* Docker官方源 (Docker Hub): [docker.io/newfuture/ddns](https://hub.docker.com/r/newfuture/ddns)
* Github官方源 (Github Registry): [ghcr.io/newfuture/ddns](https://github.com/NewFuture/DDNS/pkgs/container/ddns)

## 一键安装 | One-click Install

Linux/MacOS 使用安装脚本获取并安装最新版本(Use the installer to fetch and install the latest release):

* curl 安装
    ```sh
    curl -#fSL https://ddns.newfuture.cc/install.sh | sh -s -- latest
    ```
* wget 安装
    ```sh
    wget -O- https://ddns.newfuture.cc/install.sh | sh -s -- latest
    ```

> 需要 root 或 sudo 权限 (Requires curl and sudo).
> 更多说明与源码 More details and source: <https://ddns.newfuture.cc>

### 二进制文件 | Executable Binary ![cross platform](https://img.shields.io/badge/system-Windows_%7C%20Linux_%7C%20MacOS-success.svg?style=social)

手动下载各平台文件和使用方式 (Download and Usage per platform):

* #### Windows

1. (推荐) 下载 ZIP: [`x64.zip`](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-windows-x64.zip) · [`x86.zip`](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-windows-x86.zip) · [`arm64.zip`](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-windows-arm64.zip) 解压并运行 `ddns.exe`。
(Recommended) Download the ZIP for your arch, extract, then run `ddns.exe`.

2. 直接下载 EXE: [`x64.exe`](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-windows-x64.exe) · [`x86.exe`](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-windows-x86.exe) · [`arm64.exe`](https://github.com/NewFuture/DDNS/releases/latest/download/ddns-windows-arm64.exe)
(Alternatively) Download the EXE and run in cmd or PowerShell.

   > ⚠️ **注意**: 单文件版exe可能会被杀毒软件误报，建议使用ZIP版本或添加信任例外。
   > ⚠️ **Note**: Single-file EXE may be flagged by antivirus software as false positive. Consider using ZIP version or adding trust exception.

3. [可选] 定时任务: 使用内置命令 `ddns task --install` 创建定时任务。
(Optionally) Use the built-in command `ddns task --install` to create a scheduled task.

* #### Linux

```bash
# 常规Linux (glibc x64)
curl https://github.com/NewFuture/DDNS/releases/latest/download/ddns-glibc-linux_amd64 -#SLo ddns && chmod +x ddns

# OpenWRT/嵌入式 (musl arm64)
curl https://github.com/NewFuture/DDNS/releases/latest/download/ddns-musl-linux_arm64 -#SLo ddns && chmod +x ddns

# 其他架构请替换下载地址 Replace URL for other architectures

# 安装到PATH目录 (Install to PATH directory)
sudo mv ddns /usr/local/bin/

# 可选定时任务 Optional scheduled task
ddns task --install
```

* #### MacOS

```sh
# ARM 芯片 Apple Silicon (M-chip)
curl https://github.com/NewFuture/DDNS/releases/latest/download/ddns-mac-arm64 -#SLo ddns && chmod +x ddns

# Intel x86_64
curl https://github.com/NewFuture/DDNS/releases/latest/download/ddns-mac-x64 -#SLo ddns && chmod +x ddns

# 安装到PATH目录 (Install to PATH directory)
sudo mv ddns /usr/local/bin/

# 可选定时任务 Optional scheduled task
ddns task --install
```

---

## 使用pip安装 | Install via PIP ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ddns.svg?style=social) ![PyPI - Wheel](https://img.shields.io/pypi/wheel/ddns.svg?style=social)

Pypi 安装当前版本或者更新最新版本

```sh
# 安装最新版本 (Install latest version)
pip install ddns

# 或更新为最新版本 (Or upgrade to latest)
pip install -U ddns

# 或使用pipx直接运行（无需安装）Run directly with pipx (no installation needed)
pipx run ddns -h
```
