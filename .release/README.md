
![latest deploy](https://vsrm.dev.azure.com/NewFuture-CI/_apis/public/Release/badge/2ab09aad-c4b4-4c57-ab1b-2fb92c485664/1/1)


* Windows 下载 [ddns.exe](https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns.exe)
* Ubuntu 下载 [ddns](https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns)
* Mac OS X下载 [ddns-osx](https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns-osx)
* 其他平台可下载源码(需`python` 运行环境)

### Windows

* 下载 [`ddns.exe`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns.exe) 运行
* 定时任务 下载 [`create-task.bat`](https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/create-task.bat) 于**相同目录**，以管理员权限运行

### Ubunutu

* ddns 运行
```sh
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns -#SLo ddns && chmod +x ddns
```
* 创建定时任务(当前文件夹)
```sh
curl -sSL https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/create-task.sh | bash
```

### Mac OSX
```sh
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns-osx -#SLo ddns && chmod +x ddns
```