# DDNS Docker 使用文档

本文档详细说明如何使用 Docker 方式运行 DDNS 工具，包括基本用法、高级配置、多种网络模式以及常见问题解决方案。
可移植性最佳。

## 基本介绍

DDNS 官方提供了优化过的 Docker 镜像，具有以下特点：

- 基于 Alpine Linux，最终编译后的镜像体积小（< 7MB）
- 支持多种硬件架构（amd64、arm64、arm/v7、arm/v6、ppc64le、s390x、386、mips64le）
- 内置定时任务，默认每 5 分钟自动更新一次
- 无需外部依赖，开箱即用
- 性能优化，资源占用低

## 快速开始

### 镜像版本

DDNS Docker 镜像特殊版本：

- `latest` 最新稳定版(默认)
- `next` 下一个版本（最新beta版）
- `edge` 最新开发版（不稳定）, 同步master分支

```bash
docker pull newfuture/ddns:latest
```

您也可以指定特定版本，例如：

```bash
docker pull newfuture/ddns:v2.8.0
```

### 基本运行方式

DDNS Docker 镜像支持三种配置方式：命令行，环境变量和配置文件。

当设置了命令行参数时，容器将直接运行 DDNS 程序，而不会启用定时任务。
如果您需要定时任务，请使用环境变量或配置文件方式。

#### 使用命令行参数

可以参考[命令行参数说明](cli.md)获取详细的参数列表。
此时 `docker run --name=ddns --network=host newfuture/ddns` 就相当于 `ddns` 命令行，不会执行定时任务。

此方式适合需要一次性运行或调试的场景。

```bash
docker run --name=ddns --network=host newfuture/ddns -h
```

#### 使用环境变量

```bash
docker run -d \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4=example.com,www.example.com \
  -e DDNS_INDEX4=['public',0] \
  -e DDNS_IPV6=example.com,ipv6.example.com \
  --network host \
  --name ddns \
  newfuture/ddns
```

想要了解所有支持的环境变量，请参考[环境变量配置说明](env.md)。

#### 使用配置文件

```bash
docker run -d \
  -v /host/config/:/ddns/ \
  --network host \
  --name ddns \
  newfuture/ddns
```

其中 `/host/config/` 是您本地包含 `config.json` 的目录。Docker 容器内的工作目录是 `/ddns/`，配置文件会被映射到容器内的 `/ddns/config.json`。

xiang `config.json` 的内容可以参考 [JSON 配置文件说明](json.md)。

## 网络模式

### host 网络模式（推荐）

使用 `--network host` 可让容器直接使用宿主机的网络，这样 DDNS 可以正确获取宿主机的 IP 地址。

对于Public 或者 url 通常不需要设置 host

```bash
docker run -d \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4=example.com \
  --network host \
  newfuture/ddns
```

### bridge 网络模式（默认）

如果您不想使用 host 网络模式，也可以使用默认的 bridge 模式，但需要注意此时容器获取的是内部 IP，您需要使用 `public` 模式获取公网 IP：

```bash
docker run -d \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4=example.com \
  -e DDNS_INDEX4=public \
  newfuture/ddns
```

## 高级配置

### 自定义定时更新频率

默认情况下，容器每 5 分钟执行一次 DDNS 更新。您可以通过挂载自定义的 crontab 文件来修改定时策略：

```bash
# 创建自定义 crontab 文件
echo "*/10 * * * * cd /ddns && /bin/ddns" > mycron
# 挂载自定义 crontab 文件
docker run -d \
  -v /path/to/config/:/ddns/ \
  -v $(pwd)/mycron:/etc/crontabs/root \
  --network host \
  newfuture/ddns
```

### 一次性运行（不启用定时任务）

如果您只想执行一次更新而不启用定时任务，可以直接传递参数给容器：

```bash
docker run --rm \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4=example.com \
  --network host \
  newfuture/ddns --debug
```

这里 `--debug` 是传递给 DDNS 程序的参数，启用调试模式。任何以 `-` 开头的参数都会被传递给 DDNS 程序。

### 多域名配置

环境变量方式配置多域名：

```bash
docker run -d \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4='["example.com", "www.example.com", "sub.example.com"]' \
  -e DDNS_IPV6='["example.com", "ipv6.example.com"]' \
  --network host \
  newfuture/ddns
```

### 启用IPv6支持

要在Docker容器中使用IPv6，需要确保Docker守护程序配置了IPv6支持：

1. 编辑 `/etc/docker/daemon.json`：

```json
{
  "ipv6": true,
  "fixed-cidr-v6": "fd00::/80"
}
```

2. 重启Docker服务：

```bash
sudo systemctl restart docker
```

3. 启动容器时启用IPv6：

```bash
docker run -d \
  --network host \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV6=example.com \
  newfuture/ddns
```

## Docker Compose 示例

创建 `docker-compose.yml` 文件：

### 基本环境变量配置

```yaml
version: '3'
services:
  ddns:
    image: newfuture/ddns:latest
    restart: always
    network_mode: host
    environment:
      - DDNS_DNS=dnspod
      - DDNS_ID=12345
      - DDNS_TOKEN=mytokenkey
      - DDNS_IPV4=example.com,www.example.com
      - DDNS_IPV6=example.com,ipv6.example.com
      - DDNS_TTL=600
      - DDNS_LOG_LEVEL=INFO
```

### 使用配置文件

```yaml
version: '3'
services:
  ddns:
    image: newfuture/ddns:latest
    restart: always
    network_mode: host
    volumes:
      - ./config:/ddns
```

运行 Docker Compose：

```bash
docker-compose up -d
```

## 使用自定义镜像

如果您需要在容器中添加其他工具或自定义环境，可以基于官方镜像创建自己的 Dockerfile：

```dockerfile
FROM newfuture/ddns:latest

# 安装额外的工具
RUN apk add --no-cache curl

# 添加自定义脚本
COPY custom-script.sh /bin/
RUN chmod +x /bin/custom-script.sh

# 覆盖默认入口点（可选）
# ENTRYPOINT ["/bin/custom-script.sh"]
```

## 容器日志查看

查看容器输出日志：

```bash
docker logs ddns
```

实时跟踪日志：

```bash
docker logs -f ddns
```

## 排障和常见问题

### 容器无法获取正确的IP地址

**问题**: DDNS无法正确获取主机IP

**解决方案**:

1. 使用 `--network host` 网络模式
2. 或者设置 `-e DDNS_INDEX4=public` 强制使用公网API获取IP

### 未收到定时任务更新

**问题**: 容器运行但不自动更新DNS

**解决方案**:

1. 检查容器日志 `docker logs ddns`
2. 确认容器没有被暂停 `docker ps -a`
3. 尝试手动执行更新 `docker exec ddns /bin/ddns`

### 首次运行后立即退出

**问题**: 容器启动后立即退出

**解决方案**:

1. 添加 `-it` 参数以交互方式运行查看问题 `docker run -it --rm newfuture/ddns`
2. 检查环境变量或配置文件是否正确设置

### 网络连接问题

**问题**: 容器无法连接到DNS服务商API

**解决方案**:

1. 检查网络连接 `docker exec ddns ping api.dnspod.cn`
2. 配置HTTP代理 `-e DDNS_PROXY=http://proxy:port`

## 高级主题

### 持久化数据

为了保存DDNS的缓存数据，避免频繁API调用，可以挂载缓存目录：

```bash
docker run -d \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4=example.com \
  -e DDNS_CACHE=/ddns/cache.json \
  -v /path/to/cache:/ddns \
  --network host \
  newfuture/ddns
```

### 容器健康检查

Docker Compose配置添加健康检查：

```yaml
version: '3'
services:
  ddns:
    image: newfuture/ddns:latest
    restart: always
    network_mode: host
    environment:
      - DDNS_DNS=dnspod
      - DDNS_ID=12345
      - DDNS_TOKEN=mytokenkey
      - DDNS_IPV4=example.com
    healthcheck:
      test: ["CMD", "pgrep", "crond"]
      interval: 5m
      timeout: 10s
      retries: 3
```

## 更多资源

- [DDNS GitHub 主页](https://github.com/NewFuture/DDNS)
- [Docker Hub - newfuture/ddns](https://hub.docker.com/r/newfuture/ddns)
- [环境变量配置详情](env.md)
- [JSON 配置文件详情](json.md)
- [命令行参数详情](cli.md)
