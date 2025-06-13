# DDNS 命令行参数参考

本文档详细说明DDNS工具的命令行参数用法。命令行参数可用于覆盖配置文件和环境变量中的设置，具有**最高优先级**。

## 基本用法

可通过`-h` 查看参数列表

```bash
# ddns [选项]
ddns -h
```

或者使用Python源码：

```bash
# python run.py [选项]
python run.py -h
```

## 参数列表

| 长参数          | 短参数 | 类型            | 描述                                         |
| --------------- | ------ | --------------- | -------------------------------------------- |
| `--help`        | `-h`   | 标志            | 显示帮助信息并退出                           |
| `--version`     | `-v`   | 标志            | 显示版本信息并退出                           |
| `--config`      | `-c`   | 字符串          | 指定配置文件路径                             |
| `--dns`         |        | 选择项          | DNS服务提供商                                |
| `--id`          |        | 字符串          | API 访问 ID 或授权账户                       |
| `--token`       |        | 字符串          | API 授权令牌或密钥                           |
| `--ipv4`        |        | 字符串列表      | IPv4 域名列表，多个域名重复使用参数          |
| `--ipv6`        |        | 字符串列表      | IPv6 域名列表，多个域名重复使用参数          |
| `--index4`      |        | 字符串/数字列表 | IPv4 地址获取方式，支持多种获取方式          |
| `--index6`      |        | 字符串/数字列表 | IPv6 地址获取方式，支持多种获取方式          |
| `--ttl`         |        | 整数            | DNS 解析记录的 TTL 时间（秒）                |
| `--proxy`       |        | 字符串列表      | HTTP 代理设置，支持多代理重复使用参数        |
| `--cache`       |        | 布尔/字符串     | 是否启用缓存或自定义缓存路径                 |
| `--debug`       |        | 标志            | 开启调试模式（等同于 --log.level=DEBUG）     |
| `--log.file`    |        | 字符串          | 日志文件路径，不指定则输出到控制台           |
| `--log.level`   |        | 字符串          | 日志级别                                     |
| `--log.format`  |        | 字符串          | 日志格式字符串                               |
| `--log.datefmt` |        | 字符串          | 日期时间格式字符串                           |

其中`--debug`和`--help`,`--version`为命令行独有参数。

### 参数值示例

| 参数         | 可能的值                                     | 示例                                    |
|--------------|----------------------------------------------|----------------------------------------|
| `--dns`      | dnspod, alidns, cloudflare, 等               | `--dns cloudflare`                     |
| `--id`       | API ID, 邮箱, Access Key                     | `--id user@example.com`                |
| `--token`    | API Token, Secret Key                        | `--token abcdef123456`                 |
| `--ipv4`     | 域名                                         | `--ipv4 example.com --ipv4 sub.example.com` |
| `--ipv6`     | 域名                                         | `--ipv6 example.com`                   |
| `--index4`   | 数字, default, public, url:, regex:, cmd:, shell: | `--index4 public`, `--index4 "regex:192\\.168\\..*"` |
| `--index6`   | 数字, default, public, url:, regex:, cmd:, shell: | `--index6 0`, `--index6 public`         |
| `--ttl`      | 秒数                                         | `--ttl 600`                            |
| `--proxy`    | IP:端口, DIRECT                              | `--proxy 127.0.0.1:1080 --proxy DIRECT` |
| `--cache`    | true, 文件路径                         | `--cache=true`, `--cache=/path/to/cache.json` |
| `--debug`    | (无值)                                       | `--debug`                              |
| `--log.file` | 文件路径                                     | `--log.file=/var/log/ddns.log`         |
| `--log.level`| DEBUG, INFO, WARNING, ERROR, CRITICAL        | `--log.level=DEBUG`                    |
| `--log.format` | 格式字符串                                 | `--log.format="%(asctime)s: %(message)s"` |
| `--log.datefmt` | 日期格式字符串                            | `--log.datefmt="%Y-%m-%d %H:%M:%S"`    |

## DNS服务配置参数

### `--dns {alidns,cloudflare,dnscom,dnspod,dnspod_com,he,huaweidns,callback}`

DNS服务提供商。

- **默认值**: `dnspod`
- **可选值**:
  - `alidns`: 阿里云DNS
  - `cloudflare`: Cloudflare
  - `dnscom`: DNS.COM
  - `dnspod`: DNSPOD国内版
  - `dnspod_com`: DNSPOD国际版
  - `he`: HE.net
  - `huaweidns`: 华为云DNS
  - `callback`: 自定义回调

### `--id ID`

API访问ID或用户标识。

- **必需**: 是（部分DNS服务商可选）
- **说明**:
  - Cloudflare: 填写邮箱地址（使用Token时可留空）
  - HE.net: 可留空
  - 华为云: 填写Access Key ID (AK)
  - 其他服务商: 根据各自要求填写ID

### `--token TOKEN`

API授权令牌或密钥。

- **必需**: 是
- **说明**: 部分平台称为Secret Key，请妥善保管

## 域名配置参数

### `--ipv4 [DOMAIN...]`

需要更新IPv4记录的域名列表。

- **默认值**: `[]`（不更新IPv4地址）
- **示例**:
  - `--ipv4 example.com` (单个域名)
  - `--ipv4 example.com --ipv4 subdomain.example.com` (多个域名)

### `--ipv6 [DOMAIN...]`

需要更新IPv6记录的域名列表。

- **默认值**: `[]`（不更新IPv6地址）
- **示例**:
  - `--ipv6 example.com` (单个域名)
  - `--ipv6 example.com --ipv6 ipv6.example.com` (多个域名)

## IP获取方式参数

### `--index4 [METHOD...]`

IPv4地址获取方式。

- **默认值**: `default`
- **可选值**:
  - 数字（`0`，`1`，`2`...）: 第N个网卡IP
  - `default`: 系统访问外网默认IP
  - `public`: 使用公网IP（通过API查询）
  - `url:{URL}`: 从指定URL获取IP
  - `regex:{PATTERN}`: 使用正则表达式匹配本地网络配置中的IP
  - `cmd:{COMMAND}`: 执行指定命令并使用其输出作为IP
  - `shell:{COMMAND}`: 使用系统shell运行命令并使用其输出作为IP
- **示例**:
  - `--index4 0` (第一个网卡)
  - `--index4 public` (公网IP)
  - `--index4 "url:http://ip.sb"` (从URL获取)
  - `--index4 "regex:192\\.168\\.*"` (匹配192.168开头的IP)
  - `--index4 public --index4 0` (先尝试获取公网IP，失败则使用第一个网卡)

### `--index6 [METHOD...]`

IPv6地址获取方式，用法同`--index4`。

## 网络配置参数

### `--ttl TTL`

DNS解析TTL时间（秒）。

- **默认值**: `null`（使用DNS服务商默认设置）
- **示例**:
  - `--ttl 600` (10分钟)
  - `--ttl 3600` (1小时)

### `--proxy [PROXY...]`

HTTP代理设置，支持多代理轮换。

- **默认值**: 无（DIRECT 直连）
- **示例**:
  - `--proxy 127.0.0.1:1080` (单个代理)
  - `--proxy 127.0.0.1:1080 --proxy DIRECT` (多个代理，逐个尝试)

## 系统配置参数

### `--cache [BOOL|PATH]`

启用缓存以减少API请求。

- **默认值**: `true`
- **可选值**:
  - `true`: 启用缓存，使用默认路径
  - `false`: 禁用缓存
  - 文件路径: 自定义缓存文件位置
- **示例**:
  - `--cache` (启用默认缓存)
  - `--cache=false` (禁用缓存)
  - `--cache=/path/to/ddns.cache` (自定义缓存路径)

### `--debug`

启用调试模式（等同于设置`--log.level=DEBUG`）。

- **说明**: 此参数仅作为命令行参数有效，配置文件中的同名设置无效
- **示例**: `--debug`

## 日志配置参数

### `--log.level {CRITICAL|FATAL|ERROR|WARN|WARNING|INFO|DEBUG|NOTSET}`

设置日志级别。

- **默认值**: `INFO`
- **示例**:
  - `--log.level=DEBUG` (调试模式)
  - `--log.level=ERROR` (仅显示错误)

### `--log.file LOGFILE`

设置日志文件路径。

- **默认值**: 无（输出到控制台）
- **示例**:
  - `--log.file=/var/log/ddns.log`
  - `--log.file=./ddns.log`

### `--log.format FORMAT`

设置日志格式字符串（参考Python logging模块格式）。

- **默认值**: `%(asctime)s %(levelname)s [%(module)s]: %(message)s`
- **示例**:
  - `--log.format="%(asctime)s %(levelname)s: %(message)s"`
  - `--log.format="%(levelname)s [%(filename)s:%(lineno)d]: %(message)s"`

### `--log.datefmt FORMAT`

设置日期时间格式字符串（参考Python time.strftime()格式）。

- **默认值**: `%Y-%m-%dT%H:%M:%S`
- **示例**:
  - `--log.datefmt="%Y-%m-%d %H:%M:%S"`
  - `--log.datefmt="%m-%d %H:%M:%S"`

## 常用命令示例

### 使用配置文件

```bash
# 使用默认配置文件
ddns

# 使用指定配置文件
ddns -c /path/to/config.json
```

### 命令行临时修改配置

```bash
# 启用调试模式
ddns --debug

# 使用指定配置文件并启用调试模式
ddns -c /path/to/config.json --debug

# 更新特定域名的IPv4地址（多个域名）
ddns --ipv4 example.com --ipv4 www.example.com

# 设置为阿里云DNS并提供认证信息
ddns --dns alidns --id YOUR_ACCESS_KEY_ID --token YOUR_ACCESS_KEY_SECRET
```

### 高级用法示例

```bash
# 使用公网IP和特定的网络配置
ddns --ipv4 example.com --index4 public --ttl 600 --proxy 127.0.0.1:1080

# 自定义日志配置
ddns --log.level=DEBUG --log.file=./ddns.log --log.format="%(asctime)s - %(levelname)s: %(message)s"

# 完整配置示例
ddns --dns cloudflare --id user@example.com --token API_TOKEN \
     --ipv4 example.com --ipv4 www.example.com --ipv6 example.com \
     --index4 public --index6 "regex:2001:.*" \
     --ttl 300 --proxy 127.0.0.1:1080 --proxy DIRECT \
     --cache=/var/cache/ddns.cache \
     --log.level=INFO --log.file=/var/log/ddns.log
```

## 注意事项

1. 命令行参数具有最高优先级，会覆盖配置文件和环境变量中的设置。
2. 对于需要空格的参数值，请使用引号包围，例如：`--log.format="%(asctime)s: %(message)s"`。
3. 对于多值参数（如`--ipv4`、`--index4`、`--proxy`等），请重复使用参数标识，例如：`--ipv4 example.com --ipv4 sub.example.com`。
4. `--debug`参数仅在命令行中有效，配置文件中的debug设置将被忽略。
