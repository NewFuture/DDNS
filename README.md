[DDNS](https://github.com/NewFuture/DDNS)
===================

>自动更新DNS解析 到本机IP地址,支持 ipv4和ipv6 以 本地(内网)IP 和 公网IP。
>代理模式,支持自动创建域名记录。

[![PyPI](https://img.shields.io/pypi/v/ddns.svg?label=DDNS&style=social)](https://pypi.org/project/ddns/)
[![Build Status](https://travis-ci.com/NewFuture/DDNS.svg?branch=master)](https://travis-ci.com/NewFuture/DDNS)
[![Build Status](https://dev.azure.com/NewFuture-CI/ddns-ci/_apis/build/status/NewFuture.DDNS?branchName=master)](https://dev.azure.com/NewFuture-CI/ddns-ci/_build/latest?definitionId=2&branchName=master)
[![latest deploy](https://vsrm.dev.azure.com/NewFuture-CI/_apis/public/Release/badge/2ab09aad-c4b4-4c57-ab1b-2fb92c485664/1/1)](https://github.com/NewFuture/DDNS/releases/latest)

<details>

<summary markdown="span">Build Details
</summary>

* Linux Python (2和3): [![Travis build](https://img.shields.io/travis/com/NewFuture/DDNS/master.svg?label=python2%2Cpython3&logo=ubuntu&logoColor=white)](https://travis-ci.com/NewFuture/DDNS)
* Windows Python3.7: [![Build Status](https://dev.azure.com/NewFuture-CI/ddns-ci/_apis/build/status/NewFuture.DDNS?branchName=master&jobName=Windows&configuration=Python37)](https://dev.azure.com/NewFuture-CI/ddns-ci/_build/latest?definitionId=2&branchName=master)
* Windows Python2.7: [![Build Status](https://dev.azure.com/NewFuture-CI/ddns-ci/_apis/build/status/NewFuture.DDNS?branchName=master&jobName=Windows&configuration=Python27)](https://dev.azure.com/NewFuture-CI/ddns-ci/_build/latest?definitionId=2&branchName=master)
* Mac OSX Python3.7: [![Build Status](https://dev.azure.com/NewFuture-CI/ddns-ci/_apis/build/status/NewFuture.DDNS?branchName=master&jobName=MacOS&configuration=Python37)](https://dev.azure.com/NewFuture-CI/ddns-ci/_build/latest?definitionId=2&branchName=master) 
*  Mac OSX Python2.7: [![Build Status](https://dev.azure.com/NewFuture-CI/ddns-ci/_apis/build/status/NewFuture.DDNS?branchName=master&jobName=MacOS&configuration=Python27)](https://dev.azure.com/NewFuture-CI/ddns-ci/_build/latest?definitionId=2&branchName=master)

</details>

------------

## Features

* 兼容和跨平台:
    * [x] 可执行文件(无需python环境)
    * [x] 多系统兼容 ![cross platform](https://img.shields.io/badge/platform-windows_%7C%20linux_%7C%20osx-success.svg?style=social)
    * [x] python2和python3支持 ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ddns.svg?style=social) 
    * [x] PIP安装 ![PyPI - Wheel](https://img.shields.io/pypi/wheel/ddns.svg?style=social)
* 域名支持:
    * [x] 多个域名支持
    * [x] 多级域名解析
    * [x] 自动创建新记录
* IP类型:
    * [x] 内网IP
    * [x] 公网IP
    * [x] ipv6支持
    * [x] 正则选取支持(@rufengsuixing)
* 网络代理:
    * [x] http代理支持
    * [x] 多代理自动切换
* 服务商支持:
    * [x] [DNSPOD](https://www.dnspod.cn/)
    * [x] [阿里DNS](http://www.alidns.com/)
    * [x] [DNS.COM](https://www.dns.com/)(@loftor-git)
    * [x] [DNSPOD国际版](https://www.dnspod.com/)
    * [x] [CloudFlare](https://www.cloudflare.com/)(@tongyifan)
* 其他: 
	* [x] 可设置定时任务
	* [x] 本地文件缓存(减少API请求)

## 使用

### ① 安装

根据需要选择一种方式: `二进制`版,`pip`版,或者`源码`运行

* #### pip安装(需要pip或easy_install) _beta_
	1. 安装ddns: `pip install ddns` 或 `easy_install ddns`
	2. 运行: `ddns`
* #### 二进制版(单文件,无需python)
	* Windows [ddns.exe](https://github.com/NewFuture/DDNS/releases/latest)
	* Linux (仅Ubuntu测试) [ddns](https://github.com/NewFuture/DDNS/releases/latest)
	* Mac OSX [ddns-oxs](https://github.com/NewFuture/DDNS/releases/latest)
* #### 源码运行(无任何依赖, 需python环境)
	1. clone 或者[下载此仓库](https://github.com/NewFuture/DDNS/archive/master.zip)并解压
	2. 运行./run.py (widnows 双击`run.bat`或者运行`python run.py`)

### ② 快速配置

1. 申请 api `token`,填写到对应的`id`和`token`字段:
	* [DNSPOD(国内版)创建token](https://support.dnspod.cn/Kb/showarticle/tsid/227/)
	* [阿里云accesskey](https://help.aliyun.com/knowledge_detail/38738.html)
	* [DNS.COM API Key/Secret](https://www.dns.com/member/apiSet)
	* [DNSPOD(国际版)](https://www.dnspod.com/docs/info.html#get-the-user-token)
	* [CloudFlare API Key](https://support.cloudflare.com/hc/en-us/articles/200167836-Where-do-I-find-my-Cloudflare-API-key-)

2. 修改配置文件,`ipv4`和`ipv6`字段，为待更新的域名,详细参照配置说明


## 详细配置

<details open>

<summary markdown="span">config.json 配置文件
</summary>

* 首次运行会自动生成一个模板配置文件
* 可以使用 `-c`使用指定的配置文件 (默认读取当前目录的 config.json)
* 推荐使用vscode等支持JsonSchema的编辑器编辑配置文件

```bash
ddns -c path/to/config.json
# 或者源码运行
python run.py -c /path/to/config.json 
```

#### 配置参数表

| key   | type   | required | default | description | tips | 
| :---: | :----: | :------: | :-----: | :---------: | ------- |
| id    | string | √        | 无      | api访问ID | cloudflare为邮箱 |
| token | string | √        | 无      | api授权token | 也叫secret key, **反馈粘贴时删除** |
| dns   | string | No       |`"dnspod"`| dns 服务商 | 阿里`alidns`,<br>dns.com为`dnscom`,<br>DNSPOD国际版`dnspod_com`|
| ipv4  | array  | No       | `[]`     | ipv4 域名列表 | 为`[]`时,不会获取和更新IPv4地址 |
| ipv6  | array  | No       | `[]`     | ipv6 域名列表 | 为`[]`时,不会获取和更新IPv6地址 |
| index4|string\|int|No     |`"default"`| ipv4 获取方式 | 可设置`网卡`,`内网`,`公网`,`正则`等方式 |
| index6|string\|int|No     |`"default"`| ipv6 获取方式 | 可设置`网卡`,`内网`,`公网`,`正则`等方式 |
| proxy | string | No       | 无      | http代理`;`分割 | 多代理逐个尝试直到成功,`DIRECT`为直连|
| debug | bool   | No       | `false` | 是否开启调试 | 运行异常时,打开调试输出,方便诊断错误 |
| cache | bool   | No       | `true`  | 是否缓存记录 | 正常情况打开避免频繁更新 |


#### index4和index6参数说明

* 数字(`0`,`1`,`2`,`3`等): 第i个网卡ip
* 正则表达(如`"192.*"`): 提取`ifconfig`/`ipconfig`中与之匹配的首个IP地址,**注意json转义**(`\`要写成`\\`)
	* `"192.*"`表示192开头的所有ip
	* 如果想匹配`10.00.xxxx`应该写成`"10\\.00\\..*"`(`"\\"`json转义成`\`)
* 字符串`"default"`(或者无此项): 系统访问外网默认IP
* 字符串`"public"`: 使用公网ip(使用公网API查询)
* `false`: 强制禁止更新ipv4或ipv6的DNS解析

#### 配置示例

```json
{
	"$schema": "https://ddns.newfuture.cc/schema/v2.json",
	"id": "12345",
	"token": "mytokenkey",
	"dns": "dnspod 或 dnspod_com 或 alidns 或 dnscom 或 cloudflare",
	"ipv4": [
		"ddns.newfuture.cc",
		"ipv4.ddns.newfuture.cc"
	],
	"ipv6": [
		"ddns.newfuture.cc",
		"ipv6.ddns.newfuture.cc"
	],
	"index4": 0,
	"index6": "public",
	"proxy": "127.0.0.1:1080;DIRECT",
	"debug": false
}
```

</details>


## 定时任务

<details>

<summary markdown="span">可以通过脚本设置定时任务(默认每5分钟检查一次ip,自动更新)
</summary>

#### windows

* [推荐]以系统身份运行,右键"以管理员身份运行"`task.bat`(或者在管理员命令行中运行)
* 以当前用户身份运行定时任务,双击或者运行`task.bat` (执行时会闪黑框)

#### linux

运行 `sudo ./task.sh`

</details>

## FAQ

<details>

<summary markdown="span"> Windows Server [SSL: CERTIFICATE_VERIFY_FAILED]
</summary>


> Windows Server 默认安全策略会禁止任何未添加的信任ssl证书,可手动添加一下对应的证书 [#56](https://github.com/NewFuture/DDNS/issues/56#issuecomment-487371078)

使用系统自带的IE浏览器访问一次对应的API即可
* alidns打开: <https://alidns.aliyuncs.com>
* cloudflare打开: <https://api.cloudflare.com>
* dns.com打开: <https://www.dns.com>
* dnspod.cn打开: <https://dnsapi.cn>
* dnspod国际版:  <https://api.dnspod.com>

</details>

<details>

<summary markdown="span"> 问题排查反馈
</summary>

1. 先确认排查是否是系统/网络环境问题
2. 在[issues](https://github.com/NewFuture/DDNS/issues)中搜索是否有类似问题
3. 前两者均无法解决或者确定是bug,[在此新建issue](https://github.com/NewFuture/DDNS/issues/new)
    * [ ] 开启debug配置
    * [ ] 附上这些内容 **运行版本和方式**,**系统环境**, **出错日志**,**去掉id/token**的配置文件
    * [ ] 源码运行注明使用的python环境

</details>
