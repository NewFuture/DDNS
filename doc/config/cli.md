---
title: DDNS 命令行参数参考
description: 详细说明 DDNS 工具的命令行参数用法，包括基本用法、参数列表、配置文件等
---

本文档详细说明DDNS工具的命令行参数用法。命令行参数可用于覆盖配置文件和环境变量中的设置，具有**最高优先级**。

## 基本用法

可通过`-h` 查看参数列表

```bash
# ddns [选项]
ddns -h
```

或者使用Python：

```bash
# python3 -m ddns [选项]
python3 -m ddns -h
```

## 参数列表

### 列表参数说明

对于支持多个值的列表类型参数（如 `--ipv4`、`--ipv6`、`--index4`、`--index6`、`--proxy` 等），在命令行中支持以下两种方式指定多个值：

#### 方式一：重复参数名（推荐）

```bash
ddns --ipv4 example.com --ipv4 www.example.com --ipv4 api.example.com
ddns --index4 public --index4 0 --index4 "regex:192\\.168\\..*"
ddns --proxy 127.0.0.1:1080 --proxy DIRECT
```

#### 方式二：空格分隔

```bash
ddns --ipv4 example.com www.example.com api.example.com
ddns --index4 public 0 "regex:192\\.168\\..*"
ddns --proxy 127.0.0.1:1080 DIRECT
```

#### 包含空格的参数值

如果参数值本身包含空格，请使用引号包围：

```bash
ddns --line "中国电信" "中国联通" "中国移动"
ddns --index4 "url:http://ip.example.com/api?type=ipv4" public
```

#### 不支持的用法

```bash
# ❌ 不支持逗号分隔
ddns --ipv4 "example.com,www.example.com"
ddns --ipv4=example.com,www.example.com
```

### 参数详表

| 参数              | 类型       | 描述                                                                                                                                       | 示例                                                       |
| --------------- | :-----: | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `-h, --help`    | 标志       | 显示帮助信息并退出                                                                                                                                | `--help`                                                 |
| `-v, --version` | 标志       | 显示版本信息并退出                                                                                                                                | `--version`                                              |
| `-c, --config`  | 字符串列表      | 指定配置文件路径，支持多个配置文件                                                                                                                                 | `--config config.json` <br> `--config config1.json --config config2.json`                                   |
| `--new-config`  | 标志/字符串   | 生成新的配置文件（可指定路径）                                                                                                                          | `--new-config` <br> `--new-config=config.json`           |
| `--debug`       | 标志       | 开启调试模式                                                                                                                                   | `--debug`                                                |
| `--dns`         | 选择项      | [DNS服务提供商](providers/README.md)包括：<br>51dns, alidns, aliesa, callback, cloudflare,<br>debug, dnscom, dnspod\_com, dnspod, edgeone, he,<br>huaweidns, noip, tencentcloud | `--dns cloudflare`                                       |
| `--endpoint`    | 字符串      | 自定义API 端点 URL(更换服务节点)                                                                                                            | `--endpoint https://api.private.com`                     |
| `--id`          | 字符串      | API 访问 ID、邮箱或 Access ID                                                                                                                 | `--id user@example.com`                                  |
| `--token`       | 字符串      | API 授权令牌或密钥（Secret Key）                                                                                                                  | `--token abcdef123456`                                   |
| `--ipv4`        | 字符串列表    | IPv4 域名列表，支持重复参数或空格分隔                                                                                                                     | `--ipv4 test.com 4.test.com` 或 `--ipv4 test.com --ipv4 4.test.com`              |
| `--ipv6`        | 字符串列表    | IPv6 域名列表，支持重复参数或空格分隔                                                                                                                     | `--ipv6 test.com` 或 `--ipv6 test.com ipv6.test.com`                                     |
| `--index4`      | 列表 | IPv4 地址获取方式，支持：数字, default, public,<br>url:, regex:, cmd:, shell:                                                                        | `--index4 public 0` 或 `--index4 public --index4 "regex:192\\.168\\..*"` |
| `--index6`      | 列表 | IPv6 地址获取方式，支持：数字, default, public,<br>url:, regex:, cmd:, shell:                                                                        | `--index6 0 public` 或 `--index6 0 --index6 public`                      |
| `--ttl`         | 整数       | DNS 解析记录的 TTL 时间（秒）                                                                                                                      | `--ttl 600`                                              |
| `--line`        | 字符串      | 解析线路(部分provider支持)，如 ISP线路                                                                                                                         | `--line 电信` <br> `--line telecom`                        |
| `--proxy`       | 字符串列表    | HTTP 代理设置，可用格式：IP:端口 或 `DIRECT`                                                                                                   | `--proxy 127.0.0.1:1080 DIRECT` 或 `--proxy 127.0.0.1:1080 --proxy DIRECT`                  |
| `--cache`       | 标志/字符串   | 是否启用缓存或自定义缓存路径                                                                                                                           | `--cache` <br> `--cache=/path/to/cache`        |
| `--no-cache`    | 标志       | 禁用缓存（等效于 `--cache=false`）                                                                                                                | `--no-cache`                                             |
| `--ssl`         | 字符串      | SSL 证书验证方式，支持：true, false, auto, 文件路径                                                                                                    | `--ssl false` <br> `--ssl=/path/to/ca-certs.crt`             |
| `--no-ssl`      | 标志       | 禁用 SSL 验证（等效于 `--ssl=false`）                                                                                                             | `--no-ssl`                                               |
| `--log_file`    | 字符串      | 日志文件路径，不指定则输出到控制台                                                                                                                        | `--log_file=/var/log/ddns.log`                           |
| `--log_level`   | 字符串      | 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL                                                                                               | `--log_level=ERROR`                                      |
| `--log_format`  | 字符串      | 日志格式字符串（`logging`模块格式）                                                                                                                   | `--log_format="%(asctime)s:%(message)s"`                |
| `--log_datefmt` | 字符串      | 日志日期时间格式                                                                                                                                 | `--log_datefmt="%Y-%m-%d %H:%M:%S"`                      |
| `--install-task` | 可选整数      | 安装定时任务并设置执行间隔（分钟），默认5分钟                                                                                                              | `--install-task` <br> `--install-task 10`             |
| `--uninstall-task` | 标志      | 卸载已安装的定时任务                                                                                                                            | `--uninstall-task`                 |
| `--task-status` | 标志      | 显示定时任务状态信息                                                                                                                            | `--task-status`                     |

> **注意**: 其中`--debug`, `--new-config`, `--no-cache`, `--no-ssl`, `--help`, `--version`为命令行独有参数。

## 配置文件

### `-c FILE`

`-c`是`--config`的简写形式，用于指定配置文件路径。可以使用多个`-c`参数来加载多个配置文件。

```bash

ddns -c config.json 

# 多配置文件
ddns -c cloudflare.json -c dnspod.json 

```

## DNS服务配置参数

### `--dns DNS_PROVIDER`

[DNS服务提供商](providers/README.md)详细列表。

### `--id ID`

API访问ID或用户标识。

- **必需**: 是（部分DNS服务商可选）
- **说明**:
  - Cloudflare: 填写邮箱地址（使用Token时可留空）
  - HE.net: 可留空
  - 华为云: 填写Access Key ID (AK)
  - Callback: 填写回调URL地址（支持变量替换）
  - 其他服务商: 根据各自要求填写ID

### `--token TOKEN`

API授权令牌或密钥。

- **必需**: 是
- **说明**:
  - 大部分平台: API密钥或Secret Key
  - Callback: POST请求参数（JSON字符串），为空时使用GET请求
  - 请妥善保管敏感信息

**Callback配置示例**:

```bash
# GET方式回调
ddns --dns callback --id "https://api.example.com/ddns?domain=__DOMAIN__&ip=__IP__" --token ""

# POST方式回调
ddns --dns callback --id "https://api.example.com/ddns" --token '{"api_key": "your_key", "domain": "__DOMAIN__"}'
```

详细配置请参考：[Callback Provider 配置文档](providers/callback.md)

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

### `--index4 [Rule...]`

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

### `--index6 [Rule...]`

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

### `--cache {true|false|PATH}`

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

### `--ssl {true|false|auto|PATH}`

SSL证书验证方式，控制HTTPS连接的证书验证行为。

- **默认值**: `auto`
- **可选值**:
  - `true`: 强制验证SSL证书（最安全）
  - `false`: 禁用SSL证书验证（最不安全）
  - `auto`: 优先验证，SSL证书错误时自动降级（不安全）
  - 文件路径: 使用指定路径的自定义CA证书（最安全）
- **示例**:
  - `--ssl true` (强制验证)
  - `--ssl false` (禁用验证)
  - `--ssl auto` (自动降级)
  - `--ssl /etc/ssl/certs/ca-certificates.crt` (自定义CA证书)

### `--debug`

启用调试模式（等同于设置`--log_level=DEBUG`）。

- **说明**: 此参数仅作为命令行参数有效，配置文件中的同名设置无效
- **示例**: `--debug`

## 日志配置参数

### `--log_level {CRITICAL|FATAL|ERROR|WARN|WARNING|INFO|DEBUG|NOTSET}`

设置日志级别。

- **默认值**: `INFO`
- **示例**:
  - `--log_level=DEBUG` (调试模式)
  - `--log_level=ERROR` (仅显示错误)

### `--log_file LOGFILE`

设置日志文件路径。

- **默认值**: 无（输出到控制台）
- **示例**:
  - `--log_file=/var/log/ddns.log`
  - `--log_file=./ddns.log`

### `--log_datefmt FORMAT`

设置日期时间格式字符串（参考Python time.strftime()格式）。

- **默认值**: `%Y-%m-%dT%H:%M:%S`
- **示例**:
  - `--log_datefmt="%Y-%m-%d %H:%M:%S"`
  - `--log_datefmt="%m-%d %H:%M:%S"`

## 定时任务管理

DDNS 提供了跨平台的定时任务管理功能，可以自动安装和配置系统定时任务，无需手动维护脚本。

### `--install-task [MINUTES]`

安装定时任务，支持设置执行间隔。

- **默认值**: `5`（分钟）
- **平台支持**:
  - **Windows**: 使用 Windows Task Scheduler (`schtasks`)
  - **Linux**: 优先使用 systemd，降级使用 cron
  - **macOS**: 使用 launchd
  - **其他 Unix**: 使用 cron
- **权限要求**:
  - **Windows**: 需要管理员权限
  - **Linux systemd**: 需要 root 权限 (`sudo`)
  - **Linux/Unix cron**: 普通用户权限
  - **macOS**: 普通用户权限
- **示例**:
  - `--install-task` (使用默认5分钟间隔)
  - `--install-task 10` (设置10分钟间隔)
  - `--install-task 60` (设置1小时间隔)

```bash
# 安装默认5分钟间隔的定时任务
ddns --dns cloudflare --id user@example.com --token API_TOKEN --ipv4 example.com --install-task

# 安装10分钟间隔的定时任务
ddns --dns dnspod --id 12345 --token mytokenkey --ipv4 example.com --install-task 10

# 使用配置文件安装定时任务
ddns -c /path/to/config.json --install-task 15
```

### `--uninstall-task`

卸载已安装的定时任务。

- **功能**: 移除系统中的DDNS定时任务
- **权限要求**: 与安装时相同
- **示例**: `--uninstall-task`

```bash
# 卸载定时任务
ddns --uninstall-task

# 也可以配合其他参数一起使用（但通常不需要）
ddns --dns debug --uninstall-task
```

### `--task-status`

显示定时任务的状态信息。

- **功能**: 查看当前定时任务的安装状态、配置信息等
- **无需权限**: 查看状态不需要特殊权限
- **示例**: `--task-status`

```bash
# 查看定时任务状态
ddns --task-status --dns debug
```

### 版本跟踪

定时任务会记录安装时的 DDNS 版本信息，便于后续维护和升级管理。

### 注意事项

1. **权限要求**: 
   - Windows 和 Linux systemd 需要管理员/root权限
   - 普通用户推荐使用 cron 方式（Linux）或用户级 launchd（macOS）

2. **配置文件**: 
   - 安装时会使用当前指定的配置文件
   - 建议先测试配置正确性再安装定时任务

3. **日志记录**: 
   - 各平台会自动配置日志输出
   - 可通过平台特定工具查看执行日志

4. **卸载清理**: 
   - 卸载时会完全清理相关文件和配置
   - 如有重要配置建议提前备份

## 常用命令示例

### 基本使用

```bash
# 使用默认配置文件
ddns

# 使用指定配置文件
ddns -c /path/to/config.json

# 使用多个配置文件
ddns -c cloudflare.json -c dnspod.json

# 生成新的配置文件
ddns --new-config config.json
```

### 直接命令行配置

```bash
# 最简单的配置
ddns --dns dnspod --id 12345 --token mytokenkey --ipv4 example.com

# 启用调试模式
ddns --dns cloudflare --id user@example.com --token API_TOKEN --ipv4 example.com --debug

# 多域名配置（空格分隔）
ddns --dns cloudflare --id user@example.com --token API_TOKEN \
     --ipv4 example.com www.example.com --ipv6 example.com

# 多域名配置（重复参数）
ddns --dns cloudflare --id user@example.com --token API_TOKEN \
     --ipv4 example.com --ipv4 www.example.com --ipv6 example.com
```

### 高级配置示例

```bash
# 完整配置示例（包含代理、TTL、IP获取方式等） - 使用空格分隔
ddns --dns cloudflare --id user@example.com --token API_TOKEN \
     --ipv4 example.com www.example.com \
     --index4 public "regex:2001:.*" \
     --ttl 300 --proxy 127.0.0.1:1080 DIRECT \
     --cache=/var/cache/ddns.cache \
     --log_level=INFO --log_file=/var/log/ddns.log

# 完整配置示例 - 使用重复参数
ddns --dns cloudflare --id user@example.com --token API_TOKEN \
     --ipv4 example.com --ipv4 www.example.com \
     --index4 public --index6 "regex:2001:.*" \
     --ttl 300 --proxy 127.0.0.1:1080 --proxy DIRECT \
     --cache=/var/cache/ddns.cache \
     --log_level=INFO --log_file=/var/log/ddns.log

# 使用线路解析
ddns --dns dnspod --id 12345 --token mytokenkey \
     --ipv4 telecom.example.com --line 电信

# 禁用缓存和SSL验证
ddns --dns alidns --id ACCESS_KEY --token SECRET_KEY \
     --ipv4 example.com --no-cache --no-ssl
```

### 定时任务管理示例

```bash
# 安装定时任务（默认5分钟间隔）
ddns --dns cloudflare --id user@example.com --token API_TOKEN \
     --ipv4 example.com --install-task

# 安装定时任务（自定义间隔）
ddns --dns dnspod --id 12345 --token mytokenkey \
     --ipv4 example.com --install-task 10

# 使用配置文件安装定时任务
ddns -c /etc/ddns/config.json --install-task 15

# 查看定时任务状态
ddns --task-status

# 卸载定时任务
ddns --uninstall-task

# Linux: 使用 sudo 安装系统级定时任务
sudo ddns --dns cloudflare --id user@example.com --token API_TOKEN \
          --ipv4 example.com --install-task 5

# Windows: 以管理员身份运行安装任务
# 右键点击命令提示符 -> "以管理员身份运行"
ddns --dns cloudflare --id user@example.com --token API_TOKEN \
     --ipv4 example.com --install-task 5
```

## 注意事项

### 优先级

**命令行参数优先级**: 命令行参数具有最高优先级，会覆盖配置文件和环境变量中的设置。

### 引号

**引号使用**: 对于需要空格或特殊字符的参数值，请使用引号包围，例如：`--log_format="%(asctime)s: %(message)s"`。

### 列表参数

**列表参数配置**: 对于多值参数（如`--ipv4`、`--ipv6`、`--index4`、`--index6`、`--proxy`等），支持两种指定方式：

   ```bash
   # ✅ 方式一：重复参数名（推荐）
   ddns --ipv4 example.com --ipv4 sub.example.com --ipv4 api.example.com
   ddns --index4=public --index4=0 --index4="regex:192\\.168\\..*"

   # ✅ 方式二：空格分隔
   ddns --ipv4 example.com sub.example.com api.example.com
   ddns --index4 public 0 "regex:192\\.168\\..*"
   
   ddns --ipv4=example.com,sub.example.com      # 不支持等号加逗号
   ```

### 调试模式

**调试模式**: `--debug`参数仅在命令行中有效，配置文件中的debug设置将被忽略。

### 正则表达式

**正则表达式**: 使用正则表达式时需要适当转义特殊字符，建议使用引号包围，例如：`--index4 "regex:192\\.168\\..*"`。
