---
title: DDNS JSON配置文件参考
description: 了解DDNS工具的JSON配置文件格式和参数，如何使用配置文件以及配置文件的优先级
---

本文档详细说明DDNS工具的JSON配置文件格式和参数。JSON配置文件优先级介于命令行参数和环境变量之间。

## 基本用法

默认情况下，DDNS会在当前目录查找`config.json`文件。您也可以使用`-c`参数指定配置文件路径：

* 当前目录 `config.json` (注意Docker运行目录是 `/ddns/`)
* 当前用户目录 `~/.ddns/config.json`
* Linux当前系统 `/etc/ddns/config.json`

> 注意：在Docker中使用配置文件时，需要通过卷映射将配置文件挂载到容器的`/ddns/`目录。详情请参考[Docker使用文档](docker.md)。

```bash
# 生成配置文件
ddns --new-config
# 指定参数和配置文件
ddns --dns dnspod --ipv4 ddns.newfuture.cc --new-config config.json

# 使用指定配置文件
ddns -c /path/to/config.json
# 或者使用Python源码
python -m ddns -c /path/to/config.json

# 使用多个配置文件
ddns -c cloudflare.json -c dnspod.json
# 或通过环境变量
export DDNS_CONFIG="cloudflare.json,dnspod.json"
ddns
```

## JSON模式

DDNS配置文件遵循JSON模式(Schema)，推荐在配置文件中添加`$schema`字段以获得编辑器的自动补全和验证功能：

自v4.1.0版本开始，配置文件支持单行注释。

```jsonc
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json"
}
```

## Schema

配置参数表

|  键名    |        类型        | 必需 |   默认值    |    参数说明          | 备注                                                                                                         |
| :------: | :----------------: | :--: | :---------: | :---------------: | ------------------------------------------------------------------------------------------------------------ |
|  dns     |       string       |  否  |     无      |    DNS服务商      | 可选值: 51dns, alidns, aliesa, callback, cloudflare, debug, dnscom, dnspod_com, dnspod, edgeone, he, huaweidns, namesilo, noip, tencentcloud |
|   id     |       string       |  是  |     无      |   API 访问 ID    | 请根据服务商说明配置(如 AccessKeyID)  |
|  token   |       string       |  是  |     无      |  API 授权令牌     | 请根据服务商说明配置(如 AccessSecret)  |
| endpoint |       string       |  否  |     无      |   API端点URL      | 用于自定义或私有部署的API地址，为空时使用默认端点                                                           |
|  ipv4    |       array        |  否  |    `[]`     |   IPv4域名列表    |  |
|  ipv6    |       array        |  否  |    `[]`     |   IPv6域名列表    | |
| index4   | string\|int\|array |  否  | `["default"]` |   IPv4获取方式    | [详见下方说明](#index4-index6)|
| index6   | string\|int\|array |  否  | `["default"]` |   IPv6获取方式    | [详见下方说明](#index4-index6)|
|  ttl     |       number       |  否  |   `null`    | DNS TTL时间     | 单位为秒，不设置则采用DNS默认策略|
|  line    |       string       |  否  |   `null`    | DNS解析线路       | ISP线路选择，支持的值视DNS服务商而定 |
|  proxy   | string\|array      |  否  |     无      | HTTP代理          | 多代理逐个尝试直到成功，支持`DIRECT`(直连)、`SYSTEM`(系统代理)                                              |
|   ssl    | string\|boolean    |  否  |  `"auto"`   | SSL验证方式    | `true`（强制验证）、`false`（禁用验证）、`"auto"`（自动降级）或自定义CA证书文件路径                          |
|  cache   |    string\|bool    |  否  |   `true`    | 是否缓存记录       | 正常情况打开避免频繁更新，默认位置为临时目录下`ddns.{hash}.cache`，也可以指定具体路径                              |
|  log     |       object       |  否  |   `null`    | 日志配置  | 日志配置对象，支持`level`、`file`、`format`、`datefmt`参数                                                |

### dns

`dns`参数指定使用的DNS服务商标识，支持以下值, 请参考 [服务商列表](providers/README.md):

> 当 debug 模式，且未配置dns参数时,使用 debug provider。

### id-token

`id`和`token`参数用于API认证，具体含义和格式取决于所选的DNS服务商。

### endpoint

`endpoint`参数用于指定自定义API端点，大多数服务商都有默认端点，除非有特殊需求，否则不需要修改。

特殊情况包括：

* 不同区域部署的服务商（如腾讯云、阿里云等）需要指定对应区域的API端点。
* **私有云部署**：如果您使用的是私有部署的DNS服务，需要指定相应的私有API端点地址。
* **代理转发**：如果您使用第三方API代理服务，需要指定代理的URL。

### ipv4-ipv6

`ipv4`和`ipv6`参数指定需要更新的DNS记录名称，可以是域名或子域名列表。可以使用数组形式指定多个记录。

支持格式

* 无值时，表示不更新对应类型的DNS记录。
* **单个域名**：`"ddns.newfuture.cc"`
* **多个域名**：`["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"]`

### index4-index6

`index4`和`index6`参数用于指定获取IP地址的方式，可以使用以下值：

支持类型:

* `false`表示禁止更新相应IP类型的DNS记录
* **数字**（如`0`、`1`、`2`...）：表示使用第N个网卡的IP地址
* `"default"`：系统访问外网的默认IP
* `"public"`：使用公网IP（通过API查询）
* `"url:http..."`：通过指定URL获取IP，例如`"url:http://ip.sb"`
* `"regex:xxx"`：使用正则表达式匹配本地网络配置中的IP，例如`"regex:192\\.168\\..*"`
  * 注意：JSON中反斜杠需要转义，如`"regex:10\\.00\\..*"`表示匹配`10.00.`开头的IP
* `"cmd:xxx"`：执行指定命令并使用其输出作为IP
* `"shell:xxx"`：使用系统shell运行命令并使用其输出作为IP

配置示例：

```jsonc
{
    "index4": ["public", "url:http://ipv4.icanhazip.com"], // 优先使用公网IP，失败后使用指定URL获取
    "index6": ["shell:ip route", "regex:2003:.*"], // 使用shell命令,失败换成正则匹配IPv6地址
    "index4": [0, "public"], // 使用第一个网卡IP,失败换成公网IP
    "index6": "public", // 使用公网IPv6地址
    "index4": false // 禁止更新IPv4记录
}
```

### ttl

`ttl`参数指定DNS记录的生存时间（TTL），单位为秒。默认值为`null`，表示使用DNS服务商的默认TTL策略。
具体取值范围和默认值取决于所选的DNS服务商。

### line

`line`参数用于指定DNS解析线路，支持的值取决于所选的DNS服务商。

### proxy

`proxy`参数用于设置HTTP代理，可以是单个代理地址或多个代理地址的数组。支持以下格式：

代理类型:

* **具体代理**: `"http://<proxy_host>:<proxy_port>"` 或 `"https://<proxy_host>:<proxy_port>"`
* **直连**: `"DIRECT"` - 强制不使用代理，忽略系统代理设置
* **系统代理**: `"SYSTEM"` - 使用系统默认代理设置（如IE代理、环境变量等）
* **自动**: `null` 或不设置 - 使用系统默认代理设置

配置示例

```jsonc
{
    "proxy": "http://127.0.0.1:1080",                    // 单个代理地址
    "proxy": "SYSTEM",                                   // 使用系统代理设置
    "proxy": "DIRECT",                                   // 强制直连，不使用代理
    "proxy": ["http://127.0.0.1:1080", "DIRECT"],       // 先尝试代理，失败后直连
    "proxy": ["SYSTEM", "http://backup:8080", "DIRECT"], // 系统代理→备用代理→直连
    "proxy": null                                        // 使用系统默认代理设置
}
```

> 注意：如果配置了`proxy`，代理只对provider请求有效，获取IP的API不会使用proxy参数。

### ssl

`ssl`参数用于配置SSL验证方式，支持以下值：

* `"auto"`：自动降级到不验证SSL证书（不太安全）
* `true`：强制验证SSL证书
* `false`：禁用SSL验证 (不安全)
* `"/path/to/ca.crt"`，用于指定自定义的CA证书文件

> 注意：如果配置了`ssl`，则所有API请求，包括 provider 和 IP 获取 API 都会使用该配置。

### cache

`cache`参数用于配置DNS记录的缓存方式，支持以下值：

* `true`：启用缓存，默认位置为临时目录下的`ddns.{hash}.cache`
* `false`：禁用缓存
* `"/path/to/cache.file"`：指定自定义缓存文件路径

### log

`log`参数用于配置日志记录，是一个对象，支持以下字段：

|  键名   |   类型   | 必需 |     默认值            |    说明    |
| :-----: | :------: | :--: | :-----------------: | :--------: |
|  level  |  string  |  否  |       `INFO`        | 日志级别   |
|  file   |  string  |  否  |         无          | 日志文件路径 |
| format  |  string  |  否  |    自动调整          | 日志格式字符串 |
| datefmt |  string  |  否  | `%Y-%m-%dT%H:%M:%S` | 日期时间格式 |

## 配置示例

### 单Provider格式

```jsonc
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "id": "12345",
  "token": "mytokenkey",
  "dns": "cloudflare",
  "ipv4": ["ddns.newfuture.cc"],
  "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"],
  "index4": ["public", "regex:192\\.168\\.1\\..*"],
  "index6": "public",
  "ttl": 300,
  "proxy": ["http://127.0.0.1:1080", "DIRECT"],
  "ssl": "auto",
  "cache": "/var/cache/ddns.cache",
  "log": {
    "level": "DEBUG",
    "file": "/var/log/ddns.log",
    "datefmt": "%Y-%m-%d %H:%M:%S"
  }
}
```

### 多Provider格式

从v4.1.0版本开始，支持在单个配置文件中定义多个DNS Provider，使用新的 `providers` 数组格式：

```jsonc
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
  "ssl": "auto",
  "cache": true,
  "log": {"level": "INFO", "file": "/var/log/ddns.log"},
  "providers": [
    {
      "provider": "cloudflare",
      "id": "user1@example.com",
      "token": "cloudflare-token",
      "ipv4": ["test1.example.com"],
      "ttl": 300
    },
    {
      "provider": "dnspod",
      "id": "user2@example.com",
      "token": "dnspod-token",
      "ipv4": ["test2.example.com"],
      "ttl": 600
    }
  ]
}
```

#### v4.1格式特性

* **全局配置继承**: `providers` 外的所有配置项（如 `ssl`, `cache`, `log` 等）作为全局设置，会被所有provider继承
* **provider覆盖**: 每个provider内的配置可以覆盖相应的全局设置
* **provider字段**: 必须字段，指定DNS服务商类型（等同于传统格式中的 `dns` 字段）
* **完整兼容**: 支持所有传统格式中的配置参数
* **嵌套对象扁平化**: provider内的嵌套对象会被自动扁平化处理

#### 冲突检查

* `providers` 和 `dns` 字段不能同时存在
* 多providers时，不能在全局配置中使用 `ipv4` 或 `ipv6` 字段
  * 每个provider必须包含 `provider` 字段
  * 外层(global)不得包含 `ipv4`或者 `ipv6` 字段

## 配置优先级和字段覆盖关系

DDNS工具中的配置优先级顺序为：**命令行参数 > JSON配置文件 > 环境变量**。

* **命令行参数**：优先级最高，会覆盖JSON配置文件和环境变量中的相同设置
* **JSON配置文件**：介于命令行参数和环境变量之间，会覆盖环境变量中的设置
* **环境变量**：优先级最低，当命令行参数和JSON配置文件中都没有相应设置时使用

### 配置覆盖示例

假设有以下配置：

1. **环境变量**：`DDNS_TTL=600`
2. **JSON配置文件**：`"ttl": 300`
3. **命令行参数**：`--ttl 900`

最终生效的是命令行参数的值：`ttl=900`

如果没有提供命令行参数，则使用JSON配置值：`ttl=300`

### 特殊情况

* 当JSON配置文件中某个值明确设为`null`时，将覆盖环境变量设置，相当于未设置该值
* 当JSON配置文件中缺少某个键时，会尝试使用对应的环境变量
* 某些参数（如`debug`）仅在特定配置方式下有效：`debug`参数只在命令行中有效，JSON配置中的设置会被忽略

## 注意事项

1. 配置文件使用UTF-8编码，不包含BOM标记
2. JSON中所有键名区分大小写
3. 在配置文件中，对于需要使用反斜杠的字符串（如正则表达式），需要进行双重转义
4. `debug`参数在配置文件中设置无效，仅支持命令行参数`--debug`
5. 首次运行时会在当前目录自动生成一个模板配置文件
6. 推荐使用支持JSONSchema的编辑器（如VSCode）编辑配置文件，可获得自动补全和验证功能
