
* windows 下载 `ddns.exe`
* Ubuntu 下载 `ddns`
* Mac OSX下载 `ddns-osx`解压运行
* 其他下载 源码 python 运行


### Ubunutu

* ddns 运行
```sh
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns -#SLo ddns && chmod +x ddns
```
* linux 创建定时任务(当前文件夹)
```sh
curl -sSL https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/create-task.sh | bash
```

### windows

* 下载 `ddns.exe` 运行
* 定时任务 下载 `create-task.bat` 相同目录

### MacOSX
```sh
curl https://github.com/NewFuture/DDNS/releases/download/${BUILD_SOURCEBRANCHNAME}/ddns-osx -#SLo ddns && chmod +x ddns
```