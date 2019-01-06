DDNS
===================
自动更新DNS解析 到本机IP地址,支持 ipv4和ipv6 以 本地(内网)IP 和 公网IP。
代理模式,支持自动创建域名记录。

### Features
* 域名
    * [x] 多个域名支持
    * [x] 多级域名解析
    * [x] 自动创建记录
* IP支持 
    * [x] 内网IP
    * [x] 公网IP
    * [x] ipv6支持
    * [x] 正则选取支持(@rufengsuixing)
* 兼容和跨平台
    * [x] 多系统(Widnows, Linux, MacOS)
    * [x] python2 
    * [x] python3
    * [x] 无Python可执行文件
* [x] 定时任务
* [x] 文件缓存(减少服务器IP请求)
* 网络代理
    * [x] http代理支持
    * [x] 多代理自动切换
* 多厂商兼容支持:
    * [x] [DNSPOD](https://www.dnspod.cn/)
    * [x] [阿里DNS](http://www.alidns.com/)
    * [x] [DNS.COM](https://www.dns.com/)(@loftor-git)
    * [x] [DNSPOD国际版](https://www.dnspod.com/)
    * [x] [CloudFlare](https://www.cloudflare.com/)(@tongyifan)

### TODO:
* [ ] 腾讯云
* [ ] 同线路多记录支持
* [ ] socks代理
* [ ] TTL自定义(更多配置) 

## 使用

### 1.下载

* 单文件版(二进制编译,无需python环境,preview)
	* Windows [ddns.exe](https://github.com/NewFuture/DDNS/releases/latest)
	* Linux （仅Ubuntu测试) [ddns](https://github.com/NewFuture/DDNS/releases/latest)
* 源码运行(需要python环境)
	1. clone 或者[下载此仓库](https://github.com/NewFuture/DDNS/archive/master.zip)并解压
	2. 运行./run.py (widnows 双击`run.bat`或者运行`python run.py`)
* [历史版本](https://github.com/NewFuture/DDNS/releases)

### 2.快速配置

1. 复制 `example.config.json`到`config.json`
2. 申请 api `token`:
	* [DNSPOD(国内版)创建token](https://support.dnspod.cn/Kb/showarticle/tsid/227/)
	* [阿里云accesskey](https://help.aliyun.com/knowledge_detail/38738.html)
	* [DNS.COM API Key/Secret](https://www.dns.com/member/apiSet)
	* [DNSPOD(国际版)](https://www.dnspod.com/docs/info.html#get-the-user-token)
	* [CloudFlare](https://support.cloudflare.com/hc/en-us/articles/200167836-Where-do-I-find-my-Cloudflare-API-key-)

3. 修改配置,`ipv4`和`ipv6`字段，无则设为`[]`(此时不会解析和更新对应IP),详细参照配置说明


## 配置

<details open>

<summary>config.json
</summary>

* 首次运行会自动生成一个模板配置文件
* 可以使用 `-c`使用指定的配置文件 (默认读取当前目录的 config.json)

```bash
python run.py -c /path/to/config.json 
```

#### 配置说明

| key  | type |  required |default |  comment|
| ------| ------- | --------- | ---- | ----------- | 
| id | string |  Yes | 无 | api授权id |
| token | string | Yes | 无 | api授权token | 
| dns | string | No | `dnspod` | dns服务商,阿里为`alidns`,DNS.COM为`dnscom`,DNSPOD国际版为(`dnspod_com`)，`cloudflare`| 
| ipv4 | array | No | [] | ipv4 域名列表 |
| ipv6 | array | No | [] | ipv6 域名列表 |
| index4 | string/int | No | 'default'| ipv4获取方式 |
| index4_url | string | No | 'http://v4.ipv6-test.com/api/myip.php' | ipv4获取 |
| index6 | string/int | No | 'default'| ipv6获取方式 |
| index6_url | string | No | 'http://v6.ipv6-test.com/api/myip.php' | ipv6获取 |
| proxy | string | No | 无 | 多个代理`;`分割，`DIRECT`表示直连，从第一个代理尝试|
| debug | boolean | No | false | 是否开启调试(输出调试信息) |

#### index4和index6参数说明

* 数字(`0`,`1`,`2`,`3`等)第i个网卡ip
* 正则表达(如`"192.*"`) 提取`ifconfig`/`ipconfig`中与之匹配的首个IP地址,**注意json转义**(`\`要写成`\\`)
	* `"192.*"`表示192开头的所有ip
	* 如果想匹配`10.00.xxxx`应该写成`"10\\.00\\..*"`(`"\\"`json转义成`\`)
* 字符串`"default"`(或者无此项) 系统访问外网默认IP
* 字符串`"public"`使用公网ip(使用公网API查询)
* `false` 强制禁止更新ipv4或ipv6的DNS解析

#### 配置示例

```json
{
	"id": "12345",
	"token": "mythokenkey",
	"dns": "dnspod 或 dnspod_com 或 alidns 或 dnscom 或 cloudflare",
	"ipv4": [
		"ddns.newfuture.xyz",
		"ipv4.ddns.newfuture.xyz"
	],
	"ipv6": [
		"ddns.newfuture.xyz",
		"ipv6.ddns.newfuture.xyz"
	],
	"index4": 0,
	"index6": "public",
	"proxy": "127.0.0.1:1111",
	"debug": false
}
```

</details>


## 定时任务

<details>

<summary>可以通过脚本设置定时任务(默认每5分钟检查一次ip,自动更新)
</summary>

#### windows

* 以当前用户身份运行定时任务,双击或者运行`task.bat` (执行时会闪黑框)
* 以系统身份运行,右键"以管理员身份运行"`task.bat`(或者在管理员命令行中运行)

#### linux

运行 `sudo ./task.sh`

</details>
