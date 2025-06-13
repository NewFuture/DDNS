# DDNS 环境变量配置文档

## 概述

DDNS 支持通过环境变量进行配置，环境变量的优先级为：**[命令行参数](cli.md) > 配置文件 > 环境变量**

所有环境变量都以 `DDNS_` 为前缀，后跟参数名（推荐全大写），点号(`.`)替换为下划线(`_`)。

### 环境变量命名规则

| 配置参数 | 环境变量名称 | 示例 |
|---------|-------------|------|
| `id` | `DDNS_ID` 或 `ddns_id` | `DDNS_ID=12345` |
| `token` | `DDNS_TOKEN` 或 `ddns_token` | `DDNS_TOKEN=mytokenkey` |
| `log.level` | `DDNS_LOG_LEVEL` 或 `ddns_log_level` | `DDNS_LOG_LEVEL=DEBUG` |
| `log.file` | `DDNS_LOG_FILE` 或 `ddns_log_file` | `DDNS_LOG_FILE=/var/log/ddns.log` |

## 环境变量完整参数列表

以下是DDNS支持的所有环境变量参数列表：

| 环境变量 | 类型 | 默认值 | 描述 |
|---------|------|--------|------|
| `DDNS_ID` | 字符串 | 无 | API访问ID或用户标识 |
| `DDNS_TOKEN` | 字符串 | 无 | API授权令牌或密钥 |
| `DDNS_DNS` | 字符串 | `dnspod` | DNS服务提供商 |
| `DDNS_IPV4` | 数组/字符串 | 无 | IPv4域名列表 |
| `DDNS_IPV6` | 数组/字符串 | 无 | IPv6域名列表 |
| `DDNS_INDEX4` | 数组/字符串/数字 | `default` | IPv4地址获取方式 |
| `DDNS_INDEX6` | 数组/字符串/数字 | `default` | IPv6地址获取方式 |
| `DDNS_TTL` | 整数 | 无 | DNS解析TTL时间（秒） |
| `DDNS_PROXY` | 数组/字符串 | 无 | HTTP代理设置 |
| `DDNS_CACHE` | 布尔值/字符串 | `true` | 缓存设置 |
| `DDNS_LOG_LEVEL` | 字符串 | `INFO` | 日志级别 |
| `DDNS_LOG_FILE` | 字符串 | 无 | 日志文件路径 |
| `DDNS_LOG_FORMAT` | 字符串 | `%(asctime)s %(levelname)s [%(module)s]: %(message)s` | 日志格式字符串 |
| `DDNS_LOG_DATEFMT` | 字符串 | `%Y-%m-%dT%H:%M:%S` | 日期时间格式字符串 |

### 参数值示例

| 环境变量 | 可能的值 | 示例 |
|---------|---------|------|
| `DDNS_DNS` | dnspod, alidns, cloudflare, dnscom, dnspod_com, he, huaweidns, callback | `export DDNS_DNS="cloudflare"` |
| `DDNS_IPV4` | JSON数组, 逗号分隔的字符串 | `export DDNS_IPV4='["example.com", "www.example.com"]'` |
| `DDNS_IPV6` | JSON数组, 逗号分隔的字符串 | `export DDNS_IPV6="example.com,ipv6.example.com"` |
| `DDNS_INDEX4` | 数字、default、public、url:、regex:、cmd:、shell: | `export DDNS_INDEX4='["public", "regex:192\\.168\\..*"]'` |
| `DDNS_INDEX6` | 数字、default、public、url:、regex:、cmd:、shell: | `export DDNS_INDEX6="public"` |
| `DDNS_PROXY` | IP:端口, DIRECT, 分号分隔的列表 | `export DDNS_PROXY="127.0.0.1:1080;DIRECT"` |
| `DDNS_CACHE` | true/false, 文件路径 | `export DDNS_CACHE="/path/to/cache.json"` |
| `DDNS_LOG_LEVEL` | DEBUG, INFO, WARNING, ERROR, CRITICAL | `export DDNS_LOG_LEVEL="DEBUG"` |
| `DDNS_LOG_FORMAT` | 格式字符串 | `export DDNS_LOG_FORMAT="%(asctime)s: %(message)s"` |
| `DDNS_LOG_DATEFMT` | 日期格式字符串 | `export DDNS_LOG_DATEFMT="%Y-%m-%d %H:%M:%S"` |

## 基础配置参数

### 认证信息

#### DDNS_ID

- **类型**: 字符串
- **必需**: 是（部分 DNS 服务商可选）
- **说明**: API 访问 ID 或用户标识
- **示例**:

  ```bash
  export DDNS_ID="12345"
  # DNSPod 为用户 ID
  # 阿里云为 Access Key ID
  # CloudFlare 为邮箱地址（使用 Token 时可留空）
  # HE.net 可留空
  # 华为云为 Access Key ID (AK)
  ```

#### DDNS_TOKEN

- **类型**: 字符串
- **必需**: 是
- **说明**: API 授权令牌或密钥
- **示例**:

  ```bash
  export DDNS_TOKEN="your_api_token_here"
  # 部分平台称为 Secret Key
  # 注意：请妥善保管，不要泄露
  ```

### DNS 服务商

#### DDNS_DNS

- **类型**: 字符串
- **必需**: 否
- **默认值**: `dnspod`
- **可选值**: `alidns`, `cloudflare`, `dnscom`, `dnspod`, `dnspod_com`, `he`, `huaweidns`, `callback`
- **说明**: DNS 服务提供商
- **示例**:

  ```bash
  export DDNS_DNS="alidns"        # 阿里云 DNS
  export DDNS_DNS="cloudflare"    # CloudFlare
  export DDNS_DNS="dnspod"        # DNSPod 国内版
  export DDNS_DNS="dnspod_com"    # DNSPod 国际版
  export DDNS_DNS="he"            # HE.net
  export DDNS_DNS="huaweidns"     # 华为云 DNS
  export DDNS_DNS="callback"      # 自定义回调
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

### IPv6 域名列表

#### DDNS_IPV6

- **类型**: 数组（支持 JSON / Python 格式）
- **必需**: 否
- **默认值**: `[]`
- **说明**: 需要更新 IPv6 记录的域名列表
- **示例**:

  ```bash
  # 单个域名
  export DDNS_IPV6="ipv6.example.com"

  # JSON 数组格式（推荐）
  export DDNS_IPV6='["ipv6.example.com", "v6.example.com"]'

  # python 列表格式
  export DDNS_IPV6="['ipv6.example.com', 'v6.example.com']"

  # 禁用 IPv6 更新
  export DDNS_IPV6="[]"
  ```

## IP 获取方式

### IPv4 获取方式

#### DDNS_INDEX4

- **类型**: 字符串或数组
- **必需**: 否
- **默认值**: `default`
- **说明**: IPv4 地址获取方式
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
  
  # 正则匹配（注意转义）
  export DDNS_INDEX4="regex:192\\.168\\..*"
  
  # 执行命令
  export DDNS_INDEX4="cmd:curl -s http://ipv4.icanhazip.com"
  
  # Shell 命令
  export DDNS_INDEX4="shell:ip route get 8.8.8.8 | awk '{print \$7}'"
  
  # 多种方式组合（JSON 数组）
  export DDNS_INDEX4='["public", "regex:172\\..*"]'
  
  # 禁用 IPv4 获取
  export DDNS_INDEX4="false"
  ```

### IPv6 获取方式

#### DDNS_INDEX6

- **类型**: 字符串或数组
- **必需**: 否
- **默认值**: `default`
- **说明**: IPv6 地址获取方式（用法同 INDEX4）
- **示例**:

  ```bash
  # 公网 IPv6
  export DDNS_INDEX6="public"
  
  # 正则匹配 IPv6
  export DDNS_INDEX6="regex:2001:.*"
  
  # 自定义 URL
  export DDNS_INDEX6="url:http://ipv6.icanhazip.com"
  
  # 禁用 IPv6 获取
  export DDNS_INDEX6="false"
  ```

## 网络配置

### TTL 设置

#### DDNS_TTL

- **类型**: 整数
- **必需**: 否
- **默认值**: `null`（使用 DNS 默认值）
- **说明**: DNS 记录的 TTL（生存时间），单位为秒
- **示例**:

  ```bash
  export DDNS_TTL="600"     # 10 分钟
  export DDNS_TTL="3600"    # 1 小时
  export DDNS_TTL="86400"   # 24 小时
  ```

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

### 基础配置示例

```bash
#!/bin/bash
# DNSPod 配置示例
export DDNS_DNS="dnspod"
export DDNS_ID="12345"
export DDNS_TOKEN="your_token_here"
export DDNS_IPV4='["example.com", "www.example.com"]'
export DDNS_IPV6='["ipv6.example.com"]'
export DDNS_TTL="600"

# 运行 DDNS
ddns
```

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

2. **环境变量优先级**: 环境变量会被配置文件中的非 null 值覆盖

3. **大小写兼容**: 环境变量名支持大写、小写或混合大小写

4. **安全提醒**:
   - 请妥善保管 `DDNS_TOKEN` 等敏感信息
   - 在脚本中使用时避免明文存储
   - 考虑使用 `.env` 文件或密钥管理系统

5. **调试建议**: 出现问题时，可设置 `DDNS_LOG_LEVEL=DEBUG` 获取详细日志信息
