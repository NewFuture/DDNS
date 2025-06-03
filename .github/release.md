[![PyPI version](https://img.shields.io/badge/DDNS-${BUILD_VERSION}-1abc9c.svg?style=social)](https://pypi.org/project/ddns/${BUILD_VERSION}/) ![Deploy OK](https://img.shields.io/badge/release-success-brightgreen.svg?style=flat-square)

## 版本下载方式一览表

| 平台/方式   |架构支持  |
| ----------- |---------------------- |
| Docker      | `newfuture/ddns:${BUILD_VERSION}` 8种架构|
| Windows     | [64位(x64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-x64.exe) / [32位(x86)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-x86.exe) / [arm64](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-arm64.exe) |
| Linux |  [64位(x64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-linux-x64) / [arm64](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-linux-arm64) |
| Mac OS X    |  [Apple Silicon (ARM64)](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-mac-arm64) / [Intel x64](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-mac-x64) |
| Python/PIP  | any |

## Docker (推荐) ![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/newfuture/ddns/${BUILD_VERSION}?style=flat-square)[![Docker Platforms](https://img.shields.io/badge/arch-amd64%20%7C%20arm64%20%7C%20arm%2Fv7%20%7C%20arm%2Fv6%20%7C%20ppc64le%20%7C%20s390x%20%7C%20386%20%7C%20mips64le-blue?logo=docker&style=flat-square)](https://hub.docker.com/r/newfuture/ddns)

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
* Github镜像源: [ghcr.io/newfuture/ddns](https://github.com/NewFuture/DDNS/pkgs/container/ddns/426721813?tag=${BUILD_VERSION})

---

## 使用二进制文件 ![cross platform](https://img.shields.io/badge/system-windows_%7C%20linux_%7C%20osx-success.svg?style=flat-square)

各平台下载/使用方式

* ### Windows

1. 下载 [`ddns-windows-x64.exe`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-x64.exe) 或者 [`ddns-windows-x32.exe`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-x32.exe) 或者[`ddns-windows-arm64.exe`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-windows-arm64.exe) 保存为`ddns.exe` 运行
2. [可选] 定时任务 下载 [`create-task.bat`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/create-task.bat) 于**相同目录**，以管理员权限运行

* ### Linux 系统

```bash
# 1. 下载ddns 
# x64 版本
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-linux-x64 -#SLo ddns && chmod +x ddns

# arm64 版本
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-linux-arm64 -#SLo ddns && chmod +x ddns

# 2. [可选] 定时任务(当前目录): 
curl -sSL https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/create-task.sh | bash
```

* ### Mac OSX

```sh
# 命令行下载
# arm64
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-mac-arm64 -#SLo ddns && chmod +x ddns

# intel x64
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_VERSION}/ddns-mac-x64 -#SLo ddns && chmod +x ddns
```

## 使用PIP 安装 ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ddns/${BUILD_VERSION}.svg?style=flat-square) ![PyPI - Wheel](https://img.shields.io/pypi/wheel/ddns.svg?style=flat-square)

Pypi 安装当前版本或者更新最新版本

* 安装当前版本[current version]: `pip install ddns=${BUILD_VERSION}`
* 更新最新版[update latest version]: `pip install -U ddns`
