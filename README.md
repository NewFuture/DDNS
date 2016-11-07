DNSPOD
===================
自动更新DNS解析 到本机地址,地址解析支持 ipv4和ipv6, 支持本地(内网)和代理模式。
支持自动创建域名记录

* [x] 多个域名支持
* [x] 多级域名解析
* [x] 内网IP
* [x] 公网IP
* [x] ipv6支持
* [x] 代理模式(http代理)
* [x] 定时任务
* [x] 自动创建记录
* [x] 多系统(Widnows, Linux, MacOS)
* [x] DNSPOD
* [ ] 阿里DNS
* [ ] socks代理


## 使用
1. 复制 `example.config.json`到`config.json`
2. [申请api token](https://support.dnspod.cn/Kb/showarticle/tsid/227/)修改配置 `token` ,`ipv4`和`ipv6`字段，没有则设为`[]`
3. 运行run.py (widnows 双击`run.bat`或者运行`python run.py`, *nix `./run.py`)

## 配置
`-c`使用指定的配置文件 (默认读取当前目录的 config.json)
```bash
python run.py -c /path/to/config.json 
```

### 配置说明

| key  | type |  required |default |  comment|
| ------| ------- | --------- | ---- | ----------- | 
| id | string |  Yes | 无 | api授权id |
| token | string | Yes | 无 | api授权token | 
| ipv4 | array | No | [] | ipv4 域名列表 |
| ipv6 | array | No | [] | ipv6 域名列表 |
| index4 | string/int | No | 'default'| ipv4获取方式 |
| index6 | string/int | No | 'default'| ipv6获取方式 |
| proxy | string | No | 无 | 设置请求代理 |
| debug | boolean | No | false | 是否开启调试(输出调试信息) |

### index4和index6参数说明
* `default` 系统访问外网默认IP
* 数字(`0`,`1`,`2`,`3`等)第i个网卡ip
* `public`使用公网ip(使用公网API查询)
* `nku` NKU网关ip(只支持ipv4)

### 配置example

```json
{
	"id": "12345",
	"token": "mythokenkey",
	"ipv4": [
		"dns.newfuture.xyz",
		"ipv4.dns.newfuture.xyz"
	],
	"ipv6": [
		"dns.newfuture.xyz",
		"ipv6.dns.newfuture.xyz"
	],
	"index4": "0",
	"index6": "public",
	"proxy": "127.0.0.1:1111",
	"debug": false
}
```

## 定时任务
默认没5分钟检查一次ip变化,自动更新

### windows
**需要已经安装python**
* 以当前用户身份运行定时任务,双击或者运行`task.bat` (执行时会闪黑框)
* 以系统身份运行定时任务,右键"以管理员身份运行"`task.bat`(或者在管理员命令行中运行)

### linux
运行 `sudo ./task.sh`
