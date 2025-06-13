
---

[<img src="https://ddns.newfuture.cc/doc/img/ddns.svg" height="32px"/>](https://ddns.newfuture.cc)[![Github Release](https://img.shields.io/github/v/tag/newfuture/ddns?include_prereleases&filter=${BUILD_VERSION}&style=for-the-badge&logo=github&label=DDNS&color=success)](https://github.com/NewFuture/DDNS/releases/${BUILD_VERSION})[![Docker Image Version](https://img.shields.io/docker/v/newfuture/ddns/${BUILD_VERSION}?label=Docker&logo=docker&style=for-the-badge)](https://hub.docker.com/r/newfuture/ddns/tags?name=${BUILD_VERSION})[![PyPI version](https://img.shields.io/pypi/v/ddns/${BUILD_VERSION}?logo=python&style=for-the-badge)](https://pypi.org/project/ddns/${BUILD_VERSION})

## 各版本一览表 (Download Methods Overview)

| 系统环境 (System) | 架构支持 (Architecture) | 说明 (Description) |
| ---------: |:------------------- |:---------|
| Docker | 支持8种架构 (8 architectures) <br> [Github Registry](https://ghcr.io/newfuture/ddns) <br> [Docker Hub](https://hub.docker.com/r/newfuture/ddns) | 🚀 `docker pull newfuture/ddns:${BUILD_VERSION}` |
| Windows | [64-bit (ddns-windows-x64.exe)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-x64.exe) <br> [32-bit (ddns-windows-x86.exe)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-x86.exe) <br> [ARM (ddns-windows-arm64.exe)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-arm64.exe) | 在最新 Windows 10 和 Windows 11 测试。 <br> ✅ Tested on Windows 10 and Windows 11 |
| GLIBC Linux | [64-bit (ddns-glibc-linux_amd64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-glibc-linux_amd64)<br> [32-bit (ddns-glibc-linux_386)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-glibc-linux_386) <br> [ARM64 (ddns-glibc-linux_arm64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-glibc-linux_arm64)<br> [ARM/V7 (ddns-glibc-linux_arm_v7)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-glibc-linux_arm_v7) | 常规Linux桌面或服务器，需GLIBC≥2.28。<br>（如 Debian 9+、Ubuntu 20.04+、CentOS 8+）<br> 🐧 For common Linux desktop/server with GLIBC ≥ 2.28 |
| Musl Linux | [64-bit (ddns-musl-linux_amd64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-musl-linux_amd64) <br> [32-bit (ddns-musl-linux_386)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-musl-linux_386) <br> [ARM64 (ddns-musl-linux_arm64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-musl-linux_arm64)<br> [ARM/V7 (ddns-musl-linux_arm_v7)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-musl-linux_arm_v7) <br> [ARM/V6 (ddns-musl-linux_arm_v6)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-musl-linux_arm_v6) | 适用于OpenWRT及嵌入式系统（musl ≥ 1.1.24），如OpenWRT 19+；ARMv6未测试。<br> 🛠️ For OpenWRT and embedded systems with musl ≥ 1.1.24. ARMv6 not tested. |
| macOS | [ARM/M-chip (ddns-mac-arm64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-mac-arm64) <br> [Intel x86_64 (ddns-mac-x64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-mac-x64) | 仅虚拟环境测试，未在真机测试 <br> 🍎 Tested in virtual environments only |
| PIP | [`ddns=${BUILD_VERSION}` (全平台)](https://pypi.org/project/ddns/${BUILD_VERSION}) | 可通过 pip/pip2/pip3/easy_install 安装，部分环境自动添加至 PATH。<br> 📦 Installable via pip and easy_install. May auto-register in PATH |
| Python | 源码 Source code (全平台)<br> [zip](https://github.com/NewFuture/DDNS/archive/refs/tags/${BUILD_VERSION}.zip) + [tar](https://github.com/NewFuture/DDNS/archive/refs/tags/${BUILD_VERSION}.tar) | 可在 Python 2.7 或 Python 3 上直接运行，无需依赖 <br> 🐍 Directly runnable with Python 2.7 or Python 3. No extra dependencies. |

---

## Docker (推荐 Recommended)  ![Docker Image Size](https://img.shields.io/docker/image-size/newfuture/ddns/${BUILD_VERSION}?style=social)[![Docker Platforms](https://img.shields.io/badge/arch-amd64%20%7C%20arm64%20%7C%20arm%2Fv7%20%7C%20arm%2Fv6%20%7C%20ppc64le%20%7C%20s390x%20%7C%20386%20%7C%20mips64le-blue?logo=docker&style=social)](https://hub.docker.com/r/newfuture/ddns)

```bash
# 当前版本 (Current version)
docker run --name ddns -v $(pwd)/:/DDNS newfuture/ddns:${BUILD_VERSION} -h

# 最新版本 (Latest version, may use cache)
docker run --name ddns -v $(pwd)/:/DDNS newfuture/ddns -h

# 后台运行 (Run in background)
docker run -d --name ddns -v $(pwd)/:/DDNS newfuture/ddns:${BUILD_VERSION}
```
📁 请将 `$(pwd)` 替换为你的配置文件夹
📖 Replace $(pwd) with your config folder

* 使用 `-h` 查看帮助信息 (Use `-h` for help)
* config.json 支持编辑器自动补全 (config.json supports autocompletion)
* 支持 `DDNS_XXX` 环境变量 (Supports `DDNS_XXX` environment variables)

支持源 (Supported registries):

* Docker官方源 (Docker Hub): [docker.io/newfuture/ddns](https://hub.docker.com/r/newfuture/ddns)
* Github官方源 (Github Registry): [ghcr.io/newfuture/ddns](https://github.com/NewFuture/DDNS/pkgs/container/ddns)

## 二进制文件 (Executable Binary) ![cross platform](https://img.shields.io/badge/system-Windows_%7C%20Linux_%7C%20MacOS-success.svg?style=social)

各平台下载和使用方式 (Download and Usage per platform):

* ### Windows

1. 下载 [`ddns-windows-x64.exe`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-x64.exe) 或 [`ddns-windows-x86.exe`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-x86.exe) 或 [`ddns-windows-arm64.exe`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-arm64.exe) 保存为 `ddns.exe` 并在终端运行. 
(Download the binary, rename it as `ddns.exe`, then run in cmd or PowerShell.)
2. [可选] 定时任务: 下载 [`create-task.bat`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/create-task.bat) 于相同目录，以管理员权限运行.
(Optionally, download and run [`create-task.bat`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/create-task.bat) with administrator privileges to create a scheduled task.)

### Linux

```bash
# 常规Linux (glibc x64)
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-glibc-linux_amd64 -#SLo ddns && chmod +x ddns

# OpenWRT/嵌入式 (musl arm64)
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-musl-linux_arm64 -#SLo ddns && chmod +x ddns

# 其他架构请替换下载地址 Replace URL for other architectures

# 可选定时任务 (仅支持systemd系统)
# Optional scheduled task (systemd only)
curl -sSL https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/create-task.sh | bash
```

### MacOS

```sh
# ARM 芯片 Apple Silicon (M-chip)
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-mac-arm64 -#SLo ddns && chmod +x ddns

# Intel x86_64
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-mac-x64 -#SLo ddns && chmod +x ddns
```

## 使用pip安装 (Install via PIP) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ddns/${BUILD_VERSION}.svg?style=social) ![PyPI - Wheel](https://img.shields.io/pypi/wheel/ddns/${BUILD_VERSION}.svg?style=social)

Pypi 安装当前版本或者更新最新版本

```sh
# 安装当前版本 (Install current version)
pip install ddns==${BUILD_VERSION}

# 或更新为最新版本 (Or upgrade to latest)
pip install -U ddns
```
