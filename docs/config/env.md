# DDNS 环境变量配置文档

## 概述

DDNS 支持通过环境变量进行配置，环境变量的优先级为：**[命令行参数](cli.md) > [配置文件](json.md) > 环境变量**

所有环境变量都以 `DDNS_` 为前缀，后跟参数名（推荐全大写）,对象和属性分隔符用`_`分割。

> export DDNS_XXX="xxx"  命令作用于当前主机
> docker run -e DDNS_XXX="xxx" 命令作用于容器内

## 环境变量完整参数列表

| 环境变量               | 参数格式                                                                                             | 描述                              | 示例                                                     |
|------------------------|------------------------------------------------------------------------------------------------------|-----------------------------------|----------------------------------------------------------|
| `DDNS_CONFIG`          | 文件路径，支持逗号或分号分隔多个路径，支持远程HTTP(S) URL                                                              | 指定配置文件路径，支持多个配置文件和远程配置 | `DDNS_CONFIG="config.json"` 或 `DDNS_CONFIG="cloudflare.json,dnspod.json"` <br> `DDNS_CONFIG="https://ddns.newfuture.cc/tests/config/debug.json"` |
| `DDNS_DNS`             | `51dns`、`alidns`、`aliesa`、`callback`、`cloudflare`、`debug`、`dnscom`、`dnspod_com`、`dnspod`、`edgeone`、`he`、`huaweidns`、`noip`、`tencentcloud` | [DNS 服务商](./providers/README.md) | `DDNS_DNS=cloudflare`                                    |
| `DDNS_ID`              | 依 DNS 服务商而定                                                                                   | API 账号 或 ID                    | `DDNS_ID="user@example.com"`                             |
| `DDNS_TOKEN`           | 依 DNS 服务商而定                                                                                   | API 授权令牌或 Secret             | `DDNS_TOKEN="abcdef123456"`                              |
| `DDNS_ENDPOINT`        | URL（http 或 https 协议）                                                                           | 自定义 API 地址                   | `DDNS_ENDPOINT=https://api.dns.cn`                       |
| `DDNS_IPV4`            | 域名，数组或逗号分隔字符串                                                                          | IPv4 域名列表                     | `DDNS_IPV4='["t.com","4.t.com"]'`                        |
| `DDNS_IPV6`            | 域名，数组或逗号分隔字符串                                                                          | IPv6 域名列表                     | `DDNS_IPV6=t.com,6.t.com`                                |
| `DDNS_INDEX4`          | 数字、default、public、url:、regex:、cmd:、shell:，可为数组                                        | IPv4 获取方式                     | `DDNS_INDEX4="[0,'regex:192.168.*']"`                    |
| `DDNS_INDEX6`          | 数字、default、public、url:、regex:、cmd:、shell:，可为数组                                        | IPv6 获取方式                     | `DDNS_INDEX6=public`                                     |
| `DDNS_TTL`             | 整数（单位：秒），依服务商而定                                                                     | 设置 DNS TTL                      | `DDNS_TTL=600`                                           |
| `DDNS_LINE`            | 依服务商而定，如：电信、移动                                                                        | DNS 解析线路                      | `DDNS_LINE=电信`                                         |
| `DDNS_PROXY`           | `http://host:port` 或 DIRECT，支持多代理数组或分号分隔                                              | HTTP 代理设置                     | `DDNS_PROXY="http://127.0.0.1:1080;DIRECT"`              |
| `DDNS_CACHE`           | true、false 或文件路径                                                                              | 启用缓存或指定缓存文件路径        | `DDNS_CACHE="/tmp/cache"`                                |
| `DDNS_SSL`             | true、false、auto 或文件路径                                                                         | 设置 SSL 验证方式或指定证书路径   | `DDNS_SSL=false`<br>`DDNS_SSL=/path/ca.crt`              |
| `DDNS_CRON`            | Cron 表达式格式字符串（仅 Docker 环境有效）                                                          | Docker 容器内定时任务周期         | `DDNS_CRON="*/10 * * * *"`                               |
| `DDNS_LOG_LEVEL`       | DEBUG、INFO、WARNING、ERROR、CRITICAL                                                               | 设置日志等级                      | `DDNS_LOG_LEVEL="DEBUG"`                                 |
| `DDNS_LOG_FILE`        | 文件路径                                                                                            | 设置日志输出文件（默认输出到终端）| `DDNS_LOG_FILE="/tmp/ddns.log"`                          |
| `DDNS_LOG_FORMAT`      | Python logging 格式模板                                                                             | 设置日志格式                      | `DDNS_LOG_FORMAT="%(message)s"`                          |
| `DDNS_LOG_DATEFMT`     | 日期时间格式字符串                                                                                  | 设置日志时间格式                  | `DDNS_LOG_DATEFMT="%m-%d %H:%M"`                         |

> **注意**: 数组确认字符串引号，可打印出来查看

## 基础配置参数

### 配置文件路径

#### DDNS_CONFIG

- **类型**: 字符串
- **必需**: 否
- **默认值**: 按默认路径搜索（`config.json`、`~/.ddns/config.json`等）
- **格式**: 单个文件路径、多个文件路径（用逗号或分号分隔）、或远程HTTP(S) URL
- **说明**: 指定配置文件路径，支持多个配置文件同时使用和远程配置文件
- **示例**:

  ```bash
  # 单个配置文件
  export DDNS_CONFIG="config.json"
  export DDNS_CONFIG="/path/to/ddns.json"
  
  # 远程配置文件
  export DDNS_CONFIG="https://ddns.newfuture.cc/tests/config/debug.json"
  export DDNS_CONFIG="https://user:password@config.example.com/ddns.json"
  
  # 多个配置文件径
  export DDNS_CONFIG="/etc/ddns/cloudflare.json,./dnspod.json"
  
  # 混合本地和远程配置
  export DDNS_CONFIG="local.json,https://remote.example.com/config.json"
  ```

### DNS 服务商

#### DDNS_DNS

- **类型**: 字符串
- **必需**: 否
- **默认值**: `dnspod`
- **可选值**: `51dns`, `alidns`, `aliesa`, `callback`, `cloudflare`, `debug`, `dnscom`, `dnspod`, `dnspod_com`, `edgeone`, `he`, `huaweidns`, `noip`, `tencentcloud`
- **说明**: DNS 服务提供商
- **示例**:

  ```bash
  export DDNS_DNS="alidns"        # 阿里云 DNS
  export DDNS_DNS="aliesa"        # 阿里云企业版 DNS
  export DDNS_DNS="cloudflare"    # CloudFlare
  export DDNS_DNS="dnspod"        # DNSPod 国内版
  export DDNS_DNS="dnspod_com"    # DNSPod 国际版
  export DDNS_DNS="dnscom"        # DNS.COM
  export DDNS_DNS="51dns"         # 51DNS (DNS.COM别名)
  export DDNS_DNS="he"            # HE.net
  export DDNS_DNS="huaweidns"     # 华为云 DNS
  export DDNS_DNS="noip"          # NoIP
  export DDNS_DNS="tencentcloud"  # 腾讯云 DNS
  export DDNS_DNS="edgeone"       # 腾讯云 EdgeOne
  export DDNS_DNS="callback"      # 自定义回调
  export DDNS_DNS="debug"         # 调试模式
  ```

#### DDNS_ENDPOINT

- **类型**: 字符串
- **必需**: 否
- **默认值**: 无（使用各DNS服务商的默认API端点）
- **说明**: API端点URL，用于自定义或私有部署的API地址
- **示例**:

  ```bash
  export DDNS_ENDPOINT="https://api.example.com"     # 自定义API端点
  export DDNS_ENDPOINT="https://private.dns.com"     # 私有部署的DNS API
  export DDNS_ENDPOINT=""                             # 使用默认端点
  ```

## 域名配置

### IPv4 域名列表

#### DDNS_IPV4

- **类型**: 数组（支持 JSON/python 格式）
- **必需**: 否
- **默认值**: `[]`
- **说明**: 需要更新 IPv4 记录的域名列表
- **示例**:

  ```bash
  # JSON 数组格式（推荐）
  export DDNS_IPV4='["example.com", "sub.example.com"]'
  
  # 单个域名
  export DDNS_IPV4="example.com"
  
  # 禁用 IPv4 更新
  export DDNS_IPV4="[]"
  ```

## IP 获取方式

### IPv4 获取方式

#### DDNS_INDEX4

- **类型**: 字符串或数组
- **必需**: 否
- **默认值**: `["default"]` (使用系统默认外网IP)
- **说明**: IPv4 地址获取方式。支持逗号`,`或分号`;`分隔的字符串格式
- **特殊说明**: 当值包含 `regex:`、`cmd:` 或 `shell:` 前缀时，不支持分隔符分割，整个字符串作为单一配置项
- **示例**:

  ```bash
  # 默认方式（系统默认外网 IP）
  export DDNS_INDEX4="default"
  
  # 公网 IP
  export DDNS_INDEX4="public"
  
  # 指定网卡（第 0 个网卡）
  export DDNS_INDEX4="0"
  
  # 自定义 URL 获取
  export DDNS_INDEX4="url:http://ip.sb"
  
  # 正则匹配（注意转义）- 不支持分割
  export DDNS_INDEX4="regex:192\\.168\\..*"
  
  # 执行命令 - 不支持分割
  export DDNS_INDEX4="cmd:curl -s http://ipv4.icanhazip.com"
  
  # Shell 命令 - 不支持分割
  export DDNS_INDEX4="shell:ip route get 8.8.8.8 | awk '{print \$7}'"
  
  # 逗号分隔多种方式（仅限无特殊前缀时）
  export DDNS_INDEX4="public,default"
  
  # 包含逗号的正则表达式（整体作为单一配置）
  export DDNS_INDEX4="regex:192\\.168\\..*,10\\..*"
  
  # 多种方式组合（JSON 数组）
  export DDNS_INDEX4='["public", "regex:172\\..*"]'
  
  # 禁用 IPv4 获取
  export DDNS_INDEX4="false"
  ```

## 网络配置

### 代理设置

#### DDNS_PROXY

- **类型**: 数组（支持 JSON 格式或分号分隔）
- **必需**: 否
- **默认值**: 无
- **说明**: HTTP 代理设置，支持多代理轮换
- **示例**:

  ```bash
  # 单个代理
  export DDNS_PROXY="http://127.0.0.1:1080"
  
  # 多个代理（JSON 数组格式）
  export DDNS_PROXY='["http://proxy1:8080", "http://proxy2:8080", "DIRECT"]'
  
  # 分号分隔格式
  export DDNS_PROXY="http://proxy1:8080;http://proxy2:8080;DIRECT"
  
  # DIRECT 表示直连
  export DDNS_PROXY="DIRECT"
  ```

## 系统配置

### 缓存设置

#### DDNS_CACHE

- **类型**: 布尔值或字符串
- **必需**: 否
- **默认值**: `true`
- **说明**: 启用缓存以减少 API 请求
- **示例**:

  ```bash
  # 启用缓存（默认路径）
  export DDNS_CACHE="true"
  
  # 禁用缓存
  export DDNS_CACHE="false"
  
  # 自定义缓存文件路径
  export DDNS_CACHE="/path/to/ddns.cache"
  ```

### SSL证书验证

#### DDNS_SSL

- **类型**: 字符串或布尔值
- **必需**: 否
- **默认值**: `"auto"`
- **说明**: SSL证书验证方式，控制HTTPS连接的证书验证行为
- **可选值**:
  - `"true"`: 强制验证SSL证书（最安全）
  - `"false"`: 禁用SSL证书验证（最不安全）
  - `"auto"`: 优先验证，SSL证书错误时自动降级（不安全）
  - 文件路径: 使用指定路径的自定义CA证书（最安全）
- **示例**:

  ```bash
  export DDNS_SSL="true"     # 强制验证SSL证书
  export DDNS_SSL="false"    # 禁用SSL验证（不推荐）
  export DDNS_SSL="auto"     # 自动降级模式
  export DDNS_SSL="/etc/ssl/certs/ca-certificates.crt"  # 自定义CA证书
  ```

### Docker 定时任务配置

#### DDNS_CRON

- **类型**: 字符串
- **必需**: 否
- **默认值**: `*/5 * * * *` （每 5 分钟）
- **说明**: Docker 容器中定时任务的执行周期，仅在 Docker 环境中有效。使用标准的 cron 表达式格式
- **格式**: `分钟 小时 日 月 星期`
- **示例**:

  ```bash
  # 每 10 分钟执行一次
  export DDNS_CRON="*/10 * * * *"
  
  # 每小时执行一次
  export DDNS_CRON="0 * * * *"
  
  # 每天凌晨 2 点执行一次
  export DDNS_CRON="0 2 * * *"
  
  # 每 15 分钟执行一次
  export DDNS_CRON="*/15 * * * *"
  
  # 每 2 小时执行一次
  export DDNS_CRON="0 */2 * * *"
  ```

**Cron 表达式说明**:

| 字段 | 允许值 | 允许的特殊字符 |
|------|--------|----------------|
| 分钟 | 0-59   | * , - /        |
| 小时 | 0-23   | * , - /        |
| 日   | 1-31   | * , - /        |
| 月   | 1-12   | * , - /        |
| 星期 | 0-7    | * , - /        |

**常用表达式**:
- `*/5 * * * *` - 每 5 分钟（默认）
- `*/10 * * * *` - 每 10 分钟
- `*/15 * * * *` - 每 15 分钟
- `0 * * * *` - 每小时
- `0 */2 * * *` - 每 2 小时
- `0 0 * * *` - 每天午夜
- `0 2 * * *` - 每天凌晨 2 点
- `0 0 * * 0` - 每周日午夜

**注意**: 此环境变量仅在 Docker 容器中生效，不影响通过其他方式运行的 DDNS 程序。

### 日志配置

#### DDNS_LOG_LEVEL

- **类型**: 字符串
- **必需**: 否
- **默认值**: `INFO`
- **可选值**: `CRITICAL`, `FATAL`, `ERROR`, `WARN`, `WARNING`, `INFO`, `DEBUG`, `NOTSET`
- **说明**: 日志级别
- **示例**:

  ```bash
  export DDNS_LOG_LEVEL="DEBUG"    # 调试模式
  export DDNS_LOG_LEVEL="INFO"     # 信息模式
  export DDNS_LOG_LEVEL="ERROR"    # 仅错误
  ```

#### DDNS_LOG_FILE

- **类型**: 字符串
- **必需**: 否
- **默认值**: 无（输出到控制台）
- **说明**: 日志文件路径
- **示例**:

  ```bash
  export DDNS_LOG_FILE="/var/log/ddns.log"
  export DDNS_LOG_FILE="./ddns.log"
  ```

#### DDNS_LOG_FORMAT

- **类型**: 字符串
- **必需**: 否
- **默认值**: `%(asctime)s %(levelname)s [%(module)s]: %(message)s`
- **说明**: 日志格式字符串，参考Python logging模块的格式化语法
- **示例**:

  ```bash
  # 默认格式（含模块名）
  export DDNS_LOG_FORMAT="%(asctime)s %(levelname)s [%(module)s]: %(message)s"
  
  # 包含文件名和行号（debug模式下默认格式）
  export DDNS_LOG_FORMAT="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d]: %(message)s"
  
  # 简单格式
  export DDNS_LOG_FORMAT="%(levelname)s: %(message)s"
  ```

#### DDNS_LOG_DATEFMT

- **类型**: 字符串
- **必需**: 否
- **默认值**: `%Y-%m-%dT%H:%M:%S`
- **说明**: 日期时间格式字符串，参考Python time.strftime()的格式化语法
- **示例**:

  ```bash
  # ISO 格式（默认）
  export DDNS_LOG_DATEFMT="%Y-%m-%dT%H:%M:%S"
  
  # 简短格式
  export DDNS_LOG_DATEFMT="%m-%d %H:%M:%S"
  
  # 标准格式
  export DDNS_LOG_DATEFMT="%Y-%m-%d %H:%M:%S"
  ```

## 使用示例

### Docker 环境变量示例

```bash
docker run -d \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=your_token_here \
  -e DDNS_IPV4=example.com \
  -e DDNS_IPV6='["ipv6.example.com","example.com"]' \
  -e DDNS_INDEX4=["public", 0] \
  -e DDNS_INDEX6=public \
  -e DDNS_TTL=600 \
  -e DDNS_LOG_LEVEL=INFO \
  -e DDNS_LOG_FORMAT="%(asctime)s %(levelname)s [%(module)s]: %(message)s" \
  -e DDNS_LOG_DATEFMT="%Y-%m-%dT%H:%M:%S" \
  --network host \
  newfuture/ddns
```

### 复杂配置示例

```bash
#!/bin/bash
# 阿里云 DNS 高级配置
export DDNS_DNS="alidns"
export DDNS_ID="your_access_key_id"
export DDNS_TOKEN="your_access_key_secret"

# 多域名配置
export DDNS_IPV4='["ddns.example.com", "home.example.com", "server.example.com"]'
export DDNS_IPV6='["ipv6.example.com"]'

# 多种 IP 获取方式
export DDNS_INDEX4='["public", "regex:192\\.168\\.1\\..*", "cmd:curl -s ipv4.icanhazip.com"]'
export DDNS_INDEX6="public"

# 代理和缓存配置
export DDNS_PROXY='["http://proxy.example.com:8080", "DIRECT"]'
export DDNS_CACHE="/home/user/.ddns_cache"

# 日志配置
export DDNS_LOG_LEVEL="DEBUG"
export DDNS_LOG_FILE="/var/log/ddns.log"
export DDNS_LOG_FORMAT="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d]: %(message)s"
export DDNS_LOG_DATEFMT="%Y-%m-%d %H:%M:%S"

# TTL 设置
export DDNS_TTL="300"

# 运行
ddns
```

## 注意事项

1. **数组参数格式**: `index4`, `index6`, `ipv4`, `ipv6`, `proxy` 等数组参数支持两种格式：
   - JSON 数组格式：`'["item1", "item2"]'`（推荐）
   - 逗号分隔格式：`"item1,item2"`

2. **特殊前缀规则**: 对于 `index4` 和 `index6` 参数：
   - 当值包含 `regex:`、`cmd:` 或 `shell:` 前缀时，整个字符串将作为单一配置项，不会按分隔符分割
   - 例如：`"regex:192\\.168\\..*,10\\..*"` 会被视为一个完整的正则表达式，而不是两个配置项
   - 这是因为这些前缀的值内部可能包含逗号或分号，分割会破坏配置的完整性

3. **配置优先级和字段覆盖关系**:

   DDNS工具中的配置优先级顺序为：**命令行参数 > JSON配置文件 > 环境变量**

   - **命令行参数**: 优先级最高，会覆盖JSON配置文件和环境变量中的相同设置
   - **JSON配置文件**: 优先级中等，会覆盖环境变量中的设置，但会被命令行参数覆盖
   - **环境变量**: 优先级最低，当命令行参数和JSON配置文件中都没有相应设置时使用

   举例说明：

   ```
   # 环境变量设置
   export DDNS_TTL="600"
   
   # JSON配置文件内容
   {
     "ttl": 300
   }
   
   # 命令行参数
   ddns --ttl 900
   ```

   在上述例子中：
   - 最终生效的是命令行参数值：`ttl=900`
   - 如果不提供命令行参数，则使用JSON配置文件值：`ttl=300`
   - 如果JSON配置和命令行参数都不提供，则使用环境变量值：`ttl=600`

   另外，JSON配置文件中明确设置为`null`的值会覆盖环境变量设置，相当于未设置该值。

4. **大小写兼容**: 环境变量名支持大写、小写或混合大小写

5. **安全提醒**:
   - 请妥善保管 `DDNS_TOKEN` 等敏感信息
   - 在脚本中使用时避免明文存储
   - 考虑使用 `.env` 文件或密钥管理系统

6. **调试建议**: 出现问题时，可设置 `DDNS_LOG_LEVEL=DEBUG` 获取详细日志信息
