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
ddns --proxy SYSTEM --proxy DIRECT
```

#### 方式二：空格分隔

```bash
ddns --ipv4 example.com www.example.com api.example.com
ddns --index4 public 0 "regex:192\\.168\\..*"
ddns --proxy SYSTEM DIRECT
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
| `-c, --config`  | 字符串列表      | 指定配置文件路径，支持多个配置文件和远程HTTP(S) URL                                                                                                                         | `--config config.json` <br> `--config config1.json --config config2.json` <br> `--config https://ddns.newfuture.cc/tests/config/debug.json`                                   |
| `--new-config`  | 标志/字符串   | 生成新的配置文件（可指定路径）                                                                                                                          | `--new-config` <br> `--new-config=config.json`           |
| `--debug`       | 标志       | 开启调试模式                                                                                                                                   | `--debug`                                                |
| `--dns`         | 选择项      | [DNS服务提供商](providers/)包括：<br>51dns, alidns, aliesa, callback, cloudflare,<br>debug, dnscom, dnspod\_com, dnspod, edgeone, he,<br>huaweidns, noip, tencentcloud | `--dns cloudflare`                                       |
| `--endpoint`    | 字符串      | 自定义API 端点 URL(更换服务节点)                                                                                                            | `--endpoint https://api.private.com`                     |
| `--id`          | 字符串      | API 访问 ID、邮箱或 Access ID                                                                                                                 | `--id user@example.com`                                  |
| `--token`       | 字符串      | API 授权令牌或密钥（Secret Key）                                                                                                                  | `--token abcdef123456`                                   |
| `--ipv4`        | 字符串列表    | IPv4 域名列表，支持重复参数或空格分隔                                                                                                                     | `--ipv4 test.com 4.test.com` 或 `--ipv4 test.com --ipv4 4.test.com`              |
| `--ipv6`        | 字符串列表    | IPv6 域名列表，支持重复参数或空格分隔                                                                                                                     | `--ipv6 test.com` 或 `--ipv6 test.com ipv6.test.com`                                     |
| `--index4`      | 列表 | IPv4 地址获取方式，支持：数字, default, public,<br>url:, regex:, cmd:, shell:                                                                        | `--index4 public 0` 或 `--index4 public --index4 "regex:192\\.168\\..*"` |
| `--index6`      | 列表 | IPv6 地址获取方式，支持：数字, default, public,<br>url:, regex:, cmd:, shell:                                                                        | `--index6 0 public` 或 `--index6 0 --index6 public`                      |
| `--ttl`         | 整数       | DNS 解析记录的 TTL 时间（秒）                                                                                                                      | `--ttl 600`                                              |
| `--line`        | 字符串      | 解析线路(部分provider支持)，如 ISP线路                                                                                                                         | `--line 电信` <br> `--line telecom`                        |
| `--proxy`       | 字符串列表    | HTTP 代理设置，支持：`http://host:port`、`DIRECT`(直连)、`SYSTEM`(系统代理)                                                      | `--proxy SYSTEM DIRECT` 或 `--proxy http://127.0.0.1:1080 --proxy DIRECT`    |
| `--cache`       | 标志/字符串   | 是否启用缓存或自定义缓存路径                                                                                                                           | `--cache` <br> `--cache=/path/to/cache`        |
| `--no-cache`    | 标志       | 禁用缓存（等效于 `--cache=false`）                                                                                                                | `--no-cache`                                             |
| `--ssl`         | 字符串      | SSL 证书验证方式，支持：true, false, auto, 文件路径                                                                                                    | `--ssl false` <br> `--ssl=/path/to/ca-certs.crt`             |
| `--no-ssl`      | 标志       | 禁用 SSL 验证（等效于 `--ssl=false`）                                                                                                             | `--no-ssl`                                               |
| `--log_file`    | 字符串      | 日志文件路径，不指定则输出到控制台                                                                                                                        | `--log_file=/var/log/ddns.log`                           |
| `--log_level`   | 字符串      | 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL                                                                                               | `--log_level=ERROR`                                      |
| `--log_format`  | 字符串      | 日志格式字符串（`logging`模块格式）                                                                                                                   | `--log_format="%(asctime)s:%(message)s"`                |
| `--log_datefmt` | 字符串      | 日志日期时间格式                                                                                                                                 | `--log_datefmt="%Y-%m-%d %H:%M:%S"`                      |

> 这些参数仅支持命令行使用：`--debug`, `--no-cache`, `--no-ssl`, `--help`, `--version`。

#### Task 子命令参数

| 参数              | 类型       | 描述                                                                                                                                       | 示例                                                       |
| --------------- | :-----: | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `--install`, `-i` | 整数（可选） | 安装定时任务，可指定更新间隔分钟数（默认5分钟）。**自动覆盖已有任务**                                                                                 | `--install`、`-i 10`                         |
| `--uninstall`   | 标志       | 卸载已安装的定时任务                                                                                                                           | `--uninstall`                                           |
| `--status`      | 标志       | 显示定时任务安装状态和运行信息                                                                                                                      | `--status`                                               |
| `--enable`      | 标志       | 启用已安装的定时任务                                                                                                                           | `--enable`                                               |
| `--disable`     | 标志       | 禁用已安装的定时任务                                                                                                                           | `--disable`                                              |
| `--scheduler`   | 选择项      | 指定调度器类型，支持：auto（自动选择）、systemd、cron、launchd、schtasks                                                                         | `--scheduler systemd`、`--scheduler auto`                |

> **重要说明**:
>
> - `--install` 命令**自动覆盖安装**，无需检查是否已安装。如果系统中已有 DDNS 定时任务，会自动替换为新配置。
> - 这种设计简化了任务管理流程，避免手动卸载的繁琐操作。
> - `task` 子命令支持所有主要 DDNS 配置参数（如 `--dns`, `--id`, `--token`, `--ipv4`, `--ipv6` 等），这些参数将被保存并传递给定时任务执行时使用。

## 配置文件

### `-c FILE`

`-c`是`--config`的简写形式，用于指定配置文件路径。可以使用多个`-c`参数来加载多个配置文件。同时支持远程HTTP(S) URL。

```bash

ddns -c config.json 

# 多配置文件
ddns -c cloudflare.json -c dnspod.json 

# 远程配置文件
ddns -c https://ddns.newfuture.cc/tests/config/debug.json

# 带认证的远程配置
ddns -c https://user:password@config.example.com/ddns.json

# 混合本地和远程配置
ddns -c local-config.json -c https://remote.example.com/config.json

```

## DNS服务配置参数

### `--dns DNS_PROVIDER`

[DNS服务提供商](providers/)详细列表。

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
  - `public`: 使用公网IP（通过多个API自动查询，支持失败重试）
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

HTTP代理设置，支持多代理轮换。代理类型包括：

- **具体代理**: `http://host:port` - 使用指定代理服务器
- **直连**: `DIRECT` - 强制直连，忽略系统代理设置  
- **系统代理**: `SYSTEM` - 使用系统默认代理设置

- **默认值**: 无（使用系统默认代理设置）
- **示例**:
  - `--proxy http://127.0.0.1:1080` (单个代理)
  - `--proxy SYSTEM` (使用系统代理设置)
  - `--proxy DIRECT` (强制直连)
  - `--proxy http://127.0.0.1:1080 --proxy DIRECT` (先尝试代理，失败后直连)
  - `--proxy SYSTEM --proxy http://backup:8080 --proxy DIRECT` (系统代理→备用代理→直连)

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

## Task Management (定时任务管理)

DDNS 支持通过 `task` 子命令管理定时任务，可自动根据系统选择合适的调度器安装定时更新任务。

### 重要特性

- **智能安装**: `--install` 命令自动覆盖已有任务，简化安装流程
- **跨平台支持**: 自动检测系统并选择最佳调度器
- **完整配置**: 支持所有 DDNS 配置参数

### Task 子命令用法

```bash
# 查看帮助
ddns task --help

# 检查任务状态
ddns task --status

# 自动安装（如果未安装）或显示状态（如果已安装）
ddns task

# 安装定时任务（默认5分钟间隔）
ddns task --install

# 安装定时任务并指定间隔时间（分钟）
ddns task --install 10
ddns task -i 15

# 指定调度器类型安装任务
ddns task --install 5 --scheduler systemd
ddns task --install 10 --scheduler cron
ddns task --install 15 --scheduler auto

# 启用已安装的定时任务
ddns task --enable

# 禁用已安装的定时任务
ddns task --disable

# 卸载已安装的定时任务
ddns task --uninstall
```

### 支持的调度器

DDNS 会自动检测系统并选择最合适的调度器：

- **Linux**: systemd (优先) 或 cron
- **macOS**: launchd (优先) 或 cron  
- **Windows**: schtasks

### 调度器选择说明

| 调度器 | 适用系统 | 描述 | 推荐度 |
|--------|----------|------|--------|
| `auto` | 所有系统 | 自动检测系统并选择最佳调度器 | ⭐⭐⭐⭐⭐ |
| `systemd` | Linux | 现代 Linux 系统的标准定时器，功能完整 | ⭐⭐⭐⭐⭐ |
| `cron` | Unix-like | 传统 Unix 定时任务，兼容性好 | ⭐⭐⭐⭐ |
| `launchd` | macOS | macOS 系统原生任务调度器 | ⭐⭐⭐⭐⭐ |
| `schtasks` | Windows | Windows 任务计划程序 | ⭐⭐⭐⭐⭐ |

### 参数说明

| 参数 | 描述 |
|------|------|
| `--status` | 显示定时任务安装状态和运行信息 |
| `--install [分钟]`, `-i [分钟]` | 安装定时任务，可指定更新间隔（默认5分钟）。**自动覆盖已有任务** |
| `--uninstall` | 卸载已安装的定时任务 |
| `--enable` | 启用已安装的定时任务 |
| `--disable` | 禁用已安装的定时任务 |
| `--scheduler` | 指定调度器类型，支持：auto、systemd、cron、launchd、schtasks |

> **安装行为说明**:
>
> - `--install` 命令直接执行安装，无需事先检查或卸载
> - 自动替换系统中已有的 DDNS 定时任务
> - 简化任务管理流程，一键完成任务更新

> **配置参数支持**: `task` 子命令支持所有 DDNS 配置参数，这些参数将被传递给定时任务执行时使用。

### 权限要求

不同调度器需要不同的权限：

- **systemd**: 需要 root 权限 (`sudo`)
- **cron**: 普通用户权限即可
- **launchd**: 普通用户权限即可
- **schtasks**: 需要管理员权限

### 使用示例

```bash
# 检查当前状态
ddns task --status

# 安装 10 分钟间隔的定时任务，使用指定配置文件
ddns task --install 10 -c /etc/ddns/config.json

# 安装定时任务并直接指定 DDNS 参数（无需配置文件）
ddns task --install 5 --dns cloudflare --id user@example.com --token API_TOKEN --ipv4 example.com

# 安装定时任务，包含高级配置参数
ddns task --install 10 --dns dnspod --id 12345 --token secret \
          --ipv4 example.com --ttl 600 --proxy http://proxy:8080 \
          --log_file /var/log/ddns.log --log_level INFO

# 指定调度器类型安装任务
ddns task --install 5 --scheduler systemd --dns cloudflare --id user@example.com --token API_TOKEN --ipv4 example.com

# 强制使用 cron 调度器（适用于没有 systemd 的 Linux 系统）
ddns task --install 10 --scheduler cron -c config.json

# 在 macOS 上强制使用 launchd
ddns task --install 15 --scheduler launchd --dns dnspod --id 12345 --token secret --ipv4 example.com

# 在 Windows 上使用 schtasks
ddns task --install 5 --scheduler schtasks --dns cloudflare --id user@example.com --token API_TOKEN --ipv4 example.com

# 在 Linux 上使用 sudo 安装 systemd 定时器
sudo ddns task --install 5 -c /etc/ddns/config.json

# 更新任务配置（自动覆盖）
ddns task --install 15 --dns cloudflare --id user@example.com --token NEW_TOKEN --ipv4 example.com

# 启用已安装的任务
ddns task --enable

# 禁用任务（不删除，仅停止执行）
ddns task --disable

# 完全卸载定时任务
ddns task --uninstall
```

### 与配置文件结合使用

`task` 子命令可以与配置文件完美结合，支持多种配置方式：

```bash
# 使用本地配置文件
ddns task --install 10 -c config.json

# 使用多个配置文件
ddns task --install 5 -c cloudflare.json -c dnspod.json

# 使用远程配置文件
ddns task --install 15 -c https://config.example.com/ddns.json

# 配置文件 + 命令行参数覆盖
ddns task --install 10 -c config.json --debug --ttl 300

# 指定调度器类型 + 配置文件
ddns task --install 5 --scheduler cron -c config.json

# 使用远程配置文件 + 指定调度器
ddns task --install 10 --scheduler systemd -c https://config.example.com/ddns.json
```

### 调度器选择指南

根据不同系统和需求选择合适的调度器：

```bash
# 自动选择（推荐，让系统选择最佳调度器）
ddns task --install 5 --scheduler auto

# Linux 系统选择
ddns task --install 5 --scheduler systemd  # 优先选择，功能完整
ddns task --install 5 --scheduler cron     # 备用选择，兼容性好

# macOS 系统选择
ddns task --install 5 --scheduler launchd  # 优先选择，系统原生
ddns task --install 5 --scheduler cron     # 备用选择，兼容性好

# Windows 系统选择
ddns task --install 5 --scheduler schtasks # 唯一选择，Windows 任务计划
```

### 调试安装问题

```bash
# 启用调试模式查看详细安装过程
ddns task --install 5 --debug

# 查看任务状态和配置
ddns task --status --debug

# 查看指定调度器的状态
ddns task --status --scheduler systemd --debug
```

## 常用命令示例

### 基本使用

```bash
# 使用默认配置文件
ddns

# 使用指定配置文件
ddns -c /path/to/config.json

# 使用多个配置文件
ddns -c cloudflare.json -c dnspod.json

# 使用远程配置文件
ddns -c https://ddns.newfuture.cc/tests/config/debug.json

# 使用带代理的远程配置
ddns -c https://config.example.com/ddns.json --proxy http://proxy:8080
```

### 计划任务管理

```bash
# 安装计划任务，每5分钟执行一次（自动选择调度器）
ddns task --install 5

# 指定调度器类型安装任务
ddns task --install 5 --scheduler systemd
ddns task --install 10 --scheduler cron
ddns task --install 15 --scheduler launchd

# 查看任务状态
ddns task --status

# 查看指定调度器的状态
ddns task --status --scheduler systemd

# 启用/禁用任务
ddns task --enable
ddns task --disable

# 卸载任务
ddns task --uninstall

# 使用自定义配置文件创建任务
ddns task --install 10 -c /path/to/custom.json

# 指定调度器 + 配置文件
ddns task --install 10 --scheduler cron -c /path/to/custom.json

# 更新任务配置（自动覆盖）
ddns task --install 15 --dns cloudflare --id new@example.com --token NEW_TOKEN --ipv4 example.com

# 更新任务配置并更改调度器
ddns task --install 15 --scheduler systemd --dns cloudflare --id new@example.com --token NEW_TOKEN --ipv4 example.com

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
     --ttl 300 --proxy http://127.0.0.1:1080 DIRECT \
     --cache=/var/cache/ddns.cache \
     --log_level=INFO --log_file=/var/log/ddns.log

# 完整配置示例 - 使用重复参数
ddns --dns cloudflare --id user@example.com --token API_TOKEN \
     --ipv4 example.com --ipv4 www.example.com \
     --index4 public --index6 "regex:2001:.*" \
     --ttl 300 --proxy http://127.0.0.1:1080 --proxy DIRECT \
     --cache=/var/cache/ddns.cache \
     --log_level=INFO --log_file=/var/log/ddns.log

# 使用线路解析
ddns --dns dnspod --id 12345 --token mytokenkey \
     --ipv4 telecom.example.com --line 电信

# 使用远程配置文件
ddns -c https://ddns.newfuture.cc/tests/config/debug.json --debug

# 远程配置文件带代理
ddns -c https://config.example.com/ddns.json \
     --proxy http://proxy.company.com:8080

# 禁用缓存和SSL验证
ddns --dns alidns --id ACCESS_KEY --token SECRET_KEY \
     --ipv4 example.com --no-cache --no-ssl
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
