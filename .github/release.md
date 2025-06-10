
---

[<img src="https://ddns.newfuture.cc/doc/img/ddns.svg" height="32px"/>](https://ddns.newfuture.cc)
[![Github Release](https://img.shields.io/github/v/tag/newfuture/ddns?include_prereleases&filter=${BUILD_VERSION}&style=for-the-badge&logo=github&label=DDNS&color=success)](https://github.com/NewFuture/DDNS/releases/${BUILD_VERSION})[![Docker Image Version](https://img.shields.io/docker/v/newfuture/ddns/${BUILD_VERSION}?label=Docker&logo=docker&style=for-the-badge)](https://hub.docker.com/r/newfuture/ddns/tags?name=${BUILD_VERSION})[![PyPI version](https://img.shields.io/pypi/v/ddns/${BUILD_VERSION}?logo=python&style=for-the-badge)](https://pypi.org/project/ddns/${BUILD_VERSION})

## 各版本下载方式一览表

| 平台/方式   |架构支持  |
| ----------- |---------------------- |
| Docker      | `newfuture/ddns:${BUILD_VERSION}` (8 Arch) <br> [Github源](https://ghcr.io/newfuture/ddns) + [Docker源](https://hub.docker.com/r/newfuture/ddns) |
| Windows     | [下载64位 (download x64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-x64.exe) <br> [下载32位 (download x86)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-x86.exe) <br> [下载arm (download arm64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-arm64.exe) |
| Linux |  [下载64位 (download x64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-linux-x64) <br> [下载arm (download arm64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-linux-arm64) |
| Mac OS    |  [下载ARM64 (Apple Silicon)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-mac-arm64) <br> [下载x86_64 (Intel x64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-mac-x64) |
| PIP  | [`ddns=${BUILD_VERSION}`](https://pypi.org/project/ddns/${BUILD_VERSION}) (Any Arch) |
|Python | [源码 (source code)](https://github.com/NewFuture/DDNS/archive/refs/tags/${BUILD_VERSION}.zip) (Any Arch) |

## Docker (推荐) ![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/newfuture/ddns/${BUILD_VERSION}?style=social)[![Docker Platforms](https://img.shields.io/badge/arch-amd64%20%7C%20arm64%20%7C%20arm%2Fv7%20%7C%20arm%2Fv6%20%7C%20ppc64le%20%7C%20s390x%20%7C%20386%20%7C%20mips64le-blue?logo=docker&style=social)](https://hub.docker.com/r/newfuture/ddns)

```bash
# 当前版本
docker --name ddns -v $(pwd)/:/DDNS newfuture/ddns:${BUILD_VERSION} -h
# 最新版本(可能有缓存)
docker --name ddns -v $(pwd)/:/DDNS newfuture/ddns -h
```

请将 `$(pwd)/` 替换为你的配置文件夹。

* 命令行参数使用 `-h`
* 配置文件config.json，使用vscode等编辑会有自动提示
* 环境变量`DDNS_XXX`

支持源:

* Docker官方源: [docker.io/newfuture/ddns](https://hub.docker.com/r/newfuture/ddns)
* Github官方源: [ghcr.io/newfuture/ddns](https://github.com/NewFuture/DDNS/pkgs/container/ddns)

## 使用二进制文件 ![cross platform](https://img.shields.io/badge/system-Windows_%7C%20Linux_%7C%20MacOS-success.svg?style=social)

各平台下载/使用方式

* ### Windows

1. 下载 [`ddns-windows-x64.exe`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-x64.exe) 或者 [`ddns-windows-x86.exe`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-x86.exe) 或者[`ddns-windows-arm64.exe`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-arm64.exe) 保存为`ddns.exe` 运行
2. [可选] 定时任务 下载 [`create-task.bat`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/create-task.bat) 于**相同目录**，以管理员权限运行

* ### Linux

```bash
# 1. 下载ddns 
# x64 版本
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-linux-x64 -#SLo ddns && chmod +x ddns

# arm64 版本
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-linux-arm64 -#SLo ddns && chmod +x ddns

# 2. [可选] 定时任务(当前目录): 
curl -sSL https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/create-task.sh | bash
```

* ### MacOS

```sh
# 命令行下载
# arm64
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-mac-arm64 -#SLo ddns && chmod +x ddns

# intel x64
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-mac-x64 -#SLo ddns && chmod +x ddns
```

## 使用PIP 安装 ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ddns/${BUILD_VERSION}.svg?style=social) ![PyPI - Wheel](https://img.shields.io/pypi/wheel/ddns.${BUILD_VERSION}.svg?style=social)

Pypi 安装当前版本或者更新最新版本

* 安装当前版本[current version]: `pip install ddns=${BUILD_VERSION}`
* 更新最新版[update latest version]: `pip install -U ddns`
