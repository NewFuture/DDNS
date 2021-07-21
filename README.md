# [DDNS](https://github.com/NewFuture/DDNS)

> 自动更新 DNS 解析 到本机 IP 地址,支持 ipv4 和 ipv6 以 本地(内网)IP 和 公网 IP。
> 代理模式,支持自动创建域名记录。

[![PyPI](https://img.shields.io/pypi/v/ddns.svg?label=DDNS&style=social)](https://pypi.org/project/ddns/)
[![Build Status](https://travis-ci.com/NewFuture/DDNS.svg?branch=master)](https://travis-ci.com/NewFuture/DDNS)
[![Build Status](https://dev.azure.com/NewFuture-CI/ddns-ci/_apis/build/status/NewFuture.DDNS?branchName=master)](https://dev.azure.com/NewFuture-CI/ddns-ci/_build/latest?definitionId=2&branchName=master)
[![latest deploy](https://vsrm.dev.azure.com/NewFuture-CI/_apis/public/Release/badge/2ab09aad-c4b4-4c57-ab1b-2fb92c485664/1/1)](https://github.com/NewFuture/DDNS/releases/latest)

<details>

<summary markdown="span">Build Details
</summary>

- Linux Python (2 和 3): [![Travis build](https://img.shields.io/travis/com/NewFuture/DDNS/master.svg?label=python2%2Cpython3&logo=ubuntu&logoColor=white)](https://travis-ci.com/NewFuture/DDNS)
- Windows Python3.7: [![Build Status](https://dev.azure.com/NewFuture-CI/ddns-ci/_apis/build/status/NewFuture.DDNS?branchName=master&jobName=Windows&configuration=Windows%20Python37)](https://dev.azure.com/NewFuture-CI/ddns-ci/_build/latest?definitionId=2&branchName=master)
- Windows Python2.7: [![Build Status](https://dev.azure.com/NewFuture-CI/ddns-ci/_apis/build/status/NewFuture.DDNS?branchName=master&jobName=Windows&configuration=Windows%20Python27)](https://dev.azure.com/NewFuture-CI/ddns-ci/_build/latest?definitionId=2&branchName=master)
- Mac OSX Python3.7: [![Build Status](https://dev.azure.com/NewFuture-CI/ddns-ci/_apis/build/status/NewFuture.DDNS?branchName=master&jobName=MacOS&configuration=MacOS%20Python37)](https://dev.azure.com/NewFuture-CI/ddns-ci/_build/latest?definitionId=2&branchName=master)
- Mac OSX Python2.7: [![Build Status](https://dev.azure.com/NewFuture-CI/ddns-ci/_apis/build/status/NewFuture.DDNS?branchName=master&jobName=MacOS&configuration=MacOS%20Python27)](https://dev.azure.com/NewFuture-CI/ddns-ci/_build/latest?definitionId=2&branchName=master)

</details>

---

## Features

- 兼容和跨平台:
  - [x] 可执行文件(无需 python 环境)
  - [x] 多系统兼容 ![cross platform](https://img.shields.io/badge/platform-windows_%7C%20linux_%7C%20osx-success.svg?style=social)
  - [x] python2 和 python3 支持 ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ddns.svg?style=social)
  - [x] PIP 安装 ![PyPI - Wheel](https://img.shields.io/pypi/wheel/ddns.svg?style=social)
  - [x] Docker 支持(@NN708)
- 域名支持:
  - [x] 多个域名支持
  - [x] 多级域名解析
  - [x] 自动创建新记录
- IP 类型:
  - [x] 内网 IPv4 / IPv6
  - [x] 公网 IPv4 / IPv6 (支持自定义 API)
  - [x] 自定义命令(shell)
  - [x] 正则选取支持(@rufengsuixing)
- 网络代理:
  - [x] http 代理支持
  - [x] 多代理自动切换
- 服务商支持:
  - [x] [DNSPOD](https://www.dnspod.cn/)
  - [x] [阿里 DNS](http://www.alidns.com/)
  - [x] [DNS.COM](https://www.dns.com/)(@loftor-git)
  - [x] [DNSPOD 国际版](https://www.dnspod.com/)
  - [x] [CloudFlare](https://www.cloudflare.com/)(@tongyifan)
  - [x] [HE.net](https://dns.he.net/)(@NN708) (不支持自动创建记录)
  - [x] [华为云](https://huaweicloud.com/)(@cybmp3)
- 其他:
  - [x] 可设置定时任务
  - [x] TTL 配置支持
  - [x] 本地文件缓存(减少 API 请求)
  - [x] 地址变更时触发自定义回调API(与 DDNS 功能互斥)

## 使用

### ① 安装

根据需要选择一种方式: `二进制`版,`pip`版,`源码`运行,或者`Docker`

- #### pip 安装(需要 pip 或 easy_install)
  1. 安装 ddns: `pip install ddns` 或 `easy_install ddns`
  2. 运行: `ddns`
- #### 二进制版(单文件,无需 python)
  - Windows [ddns.exe](https://github.com/NewFuture/DDNS/releases/latest)
  - Linux (仅 Ubuntu 测试) [ddns](https://github.com/NewFuture/DDNS/releases/latest)
  - Mac OSX [ddns-osx](https://github.com/NewFuture/DDNS/releases/latest)
- #### 源码运行(无任何依赖, 需 python 环境)
  1. clone 或者[下载此仓库](https://github.com/NewFuture/DDNS/archive/master.zip)并解压
  2. 运行./run.py (widnows 双击`run.bat`或者运行`python run.py`)
- #### Docker(需要安装 Docker)
  `docker run -d -v /path/to/config.json:/config.json --network host newfuture/ddns`

### ② 快速配置

1. 申请 api `token`,填写到对应的`id`和`token`字段:

   - [DNSPOD(国内版)创建 token](https://support.dnspod.cn/Kb/showarticle/tsid/227/)
   - [阿里云 accesskey](https://help.aliyun.com/document_detail/87745.htm)
   - [DNS.COM API Key/Secret](https://www.dns.com/member/apiSet)
   - [DNSPOD(国际版)](https://www.dnspod.com/docs/info.html#get-the-user-token)
   - [CloudFlare API Key](https://support.cloudflare.com/hc/en-us/articles/200167836-Where-do-I-find-my-Cloudflare-API-key-) (除了`email + API KEY`,也可使用`Token`需要列出 Zone 权限)
   - [HE.net DDNS 文档](https://dns.he.net/docs.html)（仅需将设置的密码填入`token`字段，`id`字段可留空）
   - [华为 APIKEY 申请](https://console.huaweicloud.com/iam/)（点左边访问密钥，然后点新增访问密钥）
   - 自定义回调的参数填写方式请查看下方的自定义回调配置说明

2. 修改配置文件,`ipv4`和`ipv6`字段，为待更新的域名,详细参照配置说明

## 详细配置

所有字段可通过三种方式进行配置

1. 命令行参数 `ddns --key=value` (`ddns -h` 查看详情)，优先级最高
2. JSON配置文件(值为null认为是有效值，会覆盖环境变量的设置，如果没有对应的key则会尝试试用环境变量)
3. 环境变量DDNS_前缀加上key 全大写或者全小写 (`${ddns_key}` 或 `${DDNS_KEY}`)

<details open>

<summary markdown="span">config.json 配置文件
</summary>

- 首次运行会自动生成一个模板配置文件
- 可以使用 `-c`使用指定的配置文件 (默认读取当前目录的 config.json)
- 推荐使用 vscode 等支持 JsonSchema 的编辑器编辑配置文件

```bash
ddns -c path/to/config.json
# 或者源码运行
python run.py -c /path/to/config.json
```

#### 配置参数表

|  key   |        type        | required |   default   |    description    | tips                                                                                                        |
| :----: | :----------------: | :------: | :---------: | :---------------: | ----------------------------------------------------------------------------------------------------------- |
|   id   |       string       |    √     |     无      |    api 访问 ID    | Cloudflare 为邮箱(使用 Token 时留空)<br>HE.net 可留空                                                       |
| token  |       string       |    √     |     无      |  api 授权 token   | 部分平台叫 secret key , **反馈粘贴时删除**                                                                  |
|  dns   |       string       |    No    | `"dnspod"`  |    dns 服务商     | 阿里 DNS 为`alidns`,<br>Cloudflare 为 `cloudflare`,<br>dns.com 为 `dnscom`,<br>DNSPOD 国内为 `dnspod`,<br>DNSPOD 国际版为 `dnspod_com`,<br>HE.net 为`he`,<br>华为 DNS 为`huaweidns`,<br>自定义回调为`callback` |
|  ipv4  |       array        |    No    |    `[]`     |   ipv4 域名列表   | 为`[]`时,不会获取和更新 IPv4 地址                                                                           |
|  ipv6  |       array        |    No    |    `[]`     |   ipv6 域名列表   | 为`[]`时,不会获取和更新 IPv6 地址                                                                           |
| index4 | string\|int\|array |    No    | `"default"` |   ipv4 获取方式   | 可设置`网卡`,`内网`,`公网`,`正则`等方式                                                                     |
| index6 | string\|int\|array |    No    | `"default"` |   ipv6 获取方式   | 可设置`网卡`,`内网`,`公网`,`正则`等方式                                                                     |
|  ttl   |       number       |    No    |   `null`    | DNS 解析 TTL 时间 | 不设置采用 DNS 默认策略                                                                                     |
| proxy  |       string       |    No    |     无      | http 代理`;`分割  | 多代理逐个尝试直到成功,`DIRECT`为直连                                                                       |
| debug  |        bool        |    No    |   `false`   |   是否开启调试    | 运行异常时,打开调试输出,方便诊断错误                                                                        |
| cache  |        bool        |    No    |   `true`    |   是否缓存记录    | 正常情况打开避免频繁更新                                                                                    |

#### index4 和 index6 参数说明

- 数字(`0`,`1`,`2`,`3`等): 第 i 个网卡 ip
- 字符串`"default"`(或者无此项): 系统访问外网默认 IP
- 字符串`"public"`: 使用公网 ip(使用公网 API 查询,url 的简化模式)
- 字符串`"interface"`: 使用指定网卡 ip(如:`"interface:eno1"`)
- 字符串`"url:xxx"`: 打开 URL `xxx`(如:`"url:http://ip.sb"`),从返回的数据提取 IP 地址
- 字符串`"regex:xxx"` 正则表达(如`"regex:192.*"`): 提取`ifconfig`/`ipconfig`中与之匹配的首个 IP 地址,**注意 json 转义**(`\`要写成`\\`)
  - `"192.*"`表示 192 开头的所有 ip
  - 如果想匹配`10.00.xxxx`应该写成`"regex:10\\.00\\..\*"`(`"\\"`json 转义成`\`)
- 字符串`"cmd:xxxx"`: 执行命令`xxxx`的 stdout 输出结果作为目标 IP
- 字符串`"shell:xxx"`: 使用系统 shell 运行`xxx`,并把结果 stdout 作为目标 IP
- `false`: 强制禁止更新 ipv4 或 ipv6 的 DNS 解析
- 列表：依次执行列表中的index规则，并将最先获得的结果作为目标 IP
  - 例如`["public", "172.*"]`将先查询公网API，未获取到IP后再从本地寻找172开头的IP

#### 自定义回调配置说明

- `id` 字段填写回调地址，以 HTTP 或 HTTPS 开头，推荐采用 HTTPS 方式的回调 API ，当 `token` 字段非空且 URL 参数包含下表所示的常量字符串时，常量会被程序替换为实际值
- `token` 字段为 POST 参数，本字段为空或不存在则使用 GET 方式发起回调，回调参数采用 JSON 格式编码，当 JSON 的首层参数值包含下表所示的常量字符串时，常量会被程序替换为实际值

| 常量名称          | 常量内容               | 说明      |
| ---------------- | ---------------------- | -------- |
| `__DOMAIN__`     | DDNS 域名              |          |
| `__RECORDTYPE__` | DDNS 记录类型           |          |
| `__TTL__`        | DDNS TTL               |          |
| `__TIMESTAMP__`  | 请求发起时间戳          | 包含小数 |
| `__IP__`         | 获取的对应类型的IP地址   |          |

#### 配置示例

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v2.8.json",
  "id": "12345",
  "token": "mytokenkey",
  "dns": "dnspod 或 dnspod_com 或 alidns 或 dnscom 或 cloudflare 或 he 或 huaweidns 或 callback",
  "ipv4": ["ddns.newfuture.cc", "ipv4.ddns.newfuture.cc"],
  "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"],
  "index4": 0,
  "index6": "public",
  "ttl": 600,
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

- [推荐]以系统身份运行,右键"以管理员身份运行"`task.bat`(或者在管理员命令行中运行)
- 以当前用户身份运行定时任务,双击或者运行`task.bat` (执行时会闪黑框)

#### linux

- 使用init.d和crontab:
`sudo ./task.sh`
- 使用systemd:
    ```bash
    安装:
    sudo ./systemd.sh install
    卸载:
    sudo ./systemd.sh uninstall
    ```
  该脚本安装的文件符合 [Filesystem Hierarchy Standard (FHS)](https://en.wikipedia.org/wiki/Filesystem_Hierarchy_Standard)：
  可执行文件所在目录为 `/usr/share/DDNS`
  配置文件所在目录为 `/etc/DDNS`
</details>

## FAQ

<details>

<summary markdown="span"> Windows Server [SSL: CERTIFICATE_VERIFY_FAILED]
</summary>

> Windows Server 默认安全策略会禁止任何未添加的信任 ssl 证书,可手动添加一下对应的证书 [#56](https://github.com/NewFuture/DDNS/issues/56#issuecomment-487371078)

使用系统自带的 IE 浏览器访问一次对应的 API 即可

- alidns 打开: <https://alidns.aliyuncs.com>
- cloudflare 打开: <https://api.cloudflare.com>
- dns.com 打开: <https://www.dns.com>
- dnspod.cn 打开: <https://dnsapi.cn>
- dnspod 国际版: <https://api.dnspod.com>
- 华为 DNS <https://dns.myhuaweicloud.com>
  </details>

<details>

<summary markdown="span"> 问题排查反馈
</summary>

1. 先确认排查是否是系统/网络环境问题
2. 在[issues](https://github.com/NewFuture/DDNS/issues)中搜索是否有类似问题
3. 前两者均无法解决或者确定是 bug,[在此新建 issue](https://github.com/NewFuture/DDNS/issues/new)
   - [ ] 开启 debug 配置
   - [ ] 附上这些内容 **运行版本和方式**,**系统环境**, **出错日志**,**去掉 id/token**的配置文件
   - [ ] 源码运行注明使用的 python 环境

</details>
