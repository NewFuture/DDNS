# DDNS JSON配置文件参考

本文档详细说明DDNS工具的JSON配置文件格式和参数。JSON配置文件优先级介于命令行参数和环境变量之间。

## 基本用法

默认情况下，DDNS会在当前目录查找`config.json`文件。您也可以使用`-c`参数指定配置文件路径：

* 当前目录 `config.json` (注意Docker运行目录是 `/ddns/`)
* 当前用户目录 `~/.ddns/config.json`
* Linux当前系统 `/etc/ddns/config.json`

> 注意：在Docker中使用配置文件时，需要通过卷映射将配置文件挂载到容器的`/ddns/`目录。详情请参考[Docker使用文档](docker.md)。

```bash
# 使用默认配置文件
# 无配置时会自动生成配置文件
ddns

# 使用指定配置文件
ddns -c /path/to/config.json

# 或者使用Python源码
python run.py -c /path/to/config.json
```

## JSON模式

DDNS配置文件遵循JSON模式(Schema)，推荐在配置文件中添加`$schema`字段以获得编辑器的自动补全和验证功能：

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json"
}
```

## 配置参数表

|  键名    |        类型        | 必需 |   默认值    |    说明          | 备注                                                                                                         |
| :------: | :----------------: | :--: | :---------: | :---------------: | ------------------------------------------------------------------------------------------------------------ |
|   id     |       string       |  是  |     无      |    API 访问 ID    | Cloudflare为邮箱（使用Token时留空）<br>HE.net可留空<br>华为云为Access Key ID (AK)                         |
|  token   |       string       |  是  |     无      |  API 授权令牌     | 部分平台叫secret key                                                                                    |
|  dns     |       string       |  否  | `"dnspod"`  |    DNS服务商      | 可选值: dnspod, alidns, cloudflare, dnscom, dnspod_com, he, huaweidns, callback                              |
|  ipv4    |       array        |  否  |    `[]`     |   IPv4域名列表    | 为`[]`时，不会获取和更新IPv4地址                                                                            |
|  ipv6    |       array        |  否  |    `[]`     |   IPv6域名列表    | 为`[]`时，不会获取和更新IPv6地址                                                                            |
| index4   | string\|int\|array |  否  | `"default"` |   IPv4获取方式    | 详见下方说明                                                                                               |
| index6   | string\|int\|array |  否  | `"default"` |   IPv6获取方式    | 详见下方说明                                                                                               |
|  ttl     |       number       |  否  |   `null`    | DNS解析TTL时间     | 单位为秒，不设置则采用DNS默认策略                                                                          |
|  proxy   | string\|array      |  否  |     无      | HTTP代理          | 多代理逐个尝试直到成功，`DIRECT`为直连                                                                      |
|  debug   |       boolean      |  否  |   `false`   | 是否开启调试       | 等同于设置log.level=DEBUG，配置文件中设置此字段无效，仅命令行参数`--debug`有效                             |
|  cache   |    string\|bool    |  否  |   `true`    | 是否缓存记录       | 正常情况打开避免频繁更新，默认位置为临时目录下`ddns.cache`，也可以指定具体路径                              |
|  log     |       object       |  否  |   `null`    | 日志配置（可选）   | 日志配置对象，支持`level`、`file`、`format`、`datefmt`参数                                                |

### log对象参数说明

|  键名   |   类型   | 必需 |               默认值                |    说明    |
| :-----: | :------: | :--: | :---------------------------------: | :--------: |
|  level  |  string  |  否  |               `INFO`                | 日志级别   |
|  file   |  string  |  否  |                 无                  | 日志文件路径 |
| format  |  string  |  否  | `%(asctime)s %(levelname)s [%(module)s]: %(message)s` | 日志格式字符串 |
| datefmt |  string  |  否  |         `%Y-%m-%dT%H:%M:%S`         | 日期时间格式 |

### index4和index6参数说明

`index4`和`index6`参数用于指定获取IP地址的方式，可以使用以下值：

* **数字**（如`0`、`1`、`2`...）：表示使用第N个网卡的IP地址
* **字符串**：
  * `"default"`：系统访问外网的默认IP
  * `"public"`：使用公网IP（通过API查询）
  * `"url:xxx"`：通过指定URL获取IP，例如`"url:http://ip.sb"`
  * `"regex:xxx"`：使用正则表达式匹配本地网络配置中的IP，例如`"regex:192\\.168\\..*"`
    * 注意：JSON中反斜杠需要转义，如`"regex:10\\.00\\..*"`表示匹配`10.00.`开头的IP
  * `"cmd:xxx"`：执行指定命令并使用其输出作为IP
  * `"shell:xxx"`：使用系统shell运行命令并使用其输出作为IP
* **布尔值**：`false`表示禁止更新相应IP类型的DNS记录
* **数组**：按顺序尝试不同的获取方式，使用第一个成功获取的结果

## 自定义回调配置

当`dns`设置为`callback`时，可通过以下方式配置自定义回调：

* `id`字段：填写回调地址，以HTTP或HTTPS开头，支持变量替换
* `token`字段：POST请求参数（JSON对象或JSON字符串），为空则使用GET方式发起回调

详细配置请参考：[Callback Provider 配置文档](providers/callback.md)

支持的变量替换：

| 常量名称 | 常量内容 | 说明 |
|---------|---------|------|
| `__DOMAIN__` | DDNS域名 | 完整域名 |
| `__IP__` | 获取的IP地址 | IPv4或IPv6地址 |
| `__RECORDTYPE__` | DDNS记录类型 | A、AAAA、CNAME等 |
| `__TTL__` | DDNS TTL | 生存时间（秒） |
| `__LINE__` | 解析线路 | default、unicom等 |
| `__TIMESTAMP__` | 请求发起时间戳 | 包含小数 |

## 配置示例

### 基本配置示例

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "id": "12345",
  "token": "mytokenkey",
  "dns": "dnspod",
  "ipv4": ["example.com", "www.example.com"],
  "ipv6": ["example.com", "ipv6.example.com"],
  "ttl": 600
}
```

### 高级配置示例

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "id": "12345",
  "token": "mytokenkey",
  "dns": "cloudflare",
  "ipv4": ["example.com", "www.example.com"],
  "ipv6": ["example.com", "ipv6.example.com"],
  "index4": ["public", "regex:192\\.168\\.1\\..*"],
  "index6": "public",
  "ttl": 300,
  "proxy": "127.0.0.1:1080;DIRECT",
  "cache": "/var/cache/ddns.cache",
  "log": {
    "level": "DEBUG",
    "file": "/var/log/ddns.log",
    "format": "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d]: %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S"
  }
}
```

### 使用多种IP获取方式的配置

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "id": "12345",
  "token": "mytokenkey",
  "dns": "dnspod",
  "ipv4": ["example.com"],
  "ipv6": ["example.com"],
  "index4": ["public", 0, "regex:192\\.168\\..*"],
  "index6": ["public", "url:http://ipv6.icanhazip.com"],
  "ttl": 600
}
```

### 自定义回调配置示例

```json
{
  "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
  "id": "https://api.example.com/ddns/update?domain=__DOMAIN__&type=__RECORDTYPE__&ip=__IP__",
  "token": "{\"domain\": \"__DOMAIN__\", \"ip\": \"__IP__\", \"timestamp\": \"__TIMESTAMP__\"}",
  "dns": "callback",
  "ipv4": ["example.com"],
  "ipv6": ["example.com"],
  "ttl": 600
}
```

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
