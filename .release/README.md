[![PyPI version](https://img.shields.io/badge/DDNS-${BUILD_SOURCEBRANCHNAME}-1abc9c.svg?style=social)](https://pypi.org/project/ddns/${BUILD_SOURCEBRANCHNAME}/) ![Deploy OK](https://img.shields.io/badge/release-success-brightgreen.svg?style=flat-square)

## 使用二进制文件 ![cross platform](https://img.shields.io/badge/platform-windows_%7C%20linux_%7C%20osx-success.svg?style=flat-square)

* Windows 下载 [ddns.exe](https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns.exe)
* Ubuntu 下载 [ddns](https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns)
* Mac OS X下载 [ddns-osx](https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns-osx)

各平台下载/使用方式

* ### Windows
    1. 下载 [`ddns.exe`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns.exe) 运行
    2. [可选] 定时任务 下载 [`create-task.bat`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/create-task.bat) 于**相同目录**，以管理员权限运行
* ### Ubuntu
```bash
# 1. 下载ddns 
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns -#SLo ddns && chmod +x ddns
# 2. [可选] 定时任务(当前目录): 
curl -sSL https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/create-task.sh | bash
```
* ### Mac OSX
```sh
# 命令行下载
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns-osx -#SLo ddns && chmod +x ddns
```

## 使用PIP 安装 ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ddns.svg?style=flat-square) ![PyPI - Wheel](https://img.shields.io/pypi/wheel/ddns.svg?style=flat-square)

Pypi 安装当前版本或者更新最新版本

* 安装当前版本[current version]: `pip install ddns=${BUILD_SOURCEBRANCHNAME}`
* 更新最新版[update latest version]: `pip install -U ddns`