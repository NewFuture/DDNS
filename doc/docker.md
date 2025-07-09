# DDNS Docker

- 基本特性
  - 基于 Alpine Linux，最终编译后的镜像体积小（< 7MB）
  - 支持多种硬件架构（amd64、arm64、arm/v7、arm/v6、ppc64le、s390x、386、mips64le）
  - 内置定时任务，默认每 5 分钟自动更新一次
  - 无需外部依赖，开箱即用, 性能优化，资源占用低
- 配置方式:
  - [CLI 命令行参数](cli.md)
  - [JSON 配置文件](json.md)
  - [Env 环境变量](env.md)

## 镜像说明

### 镜像版本

DDNS 镜像版本(Docker Tag)：

- `latest`: 最新稳定版
- `next`: 下一个版本
- `edge` 最新开发版,不稳定

```bash
docker pull newfuture/ddns:latest
docker pull newfuture/ddns:next
```

您也可以指定特定版本，例如：

```bash
docker pull newfuture/ddns:v4.0.0
```

### 镜像源

镜像会同步发布到以下源：

- [Docker Hub](https://hub.docker.com/r/newfuture/ddns): `docker.io/newfuture/ddns`
- [GitHub Packages](https://github.com/newfuture/DDNS/pkgs/container/ddns): `ghcr.io/newfuture/ddns`

支持 `docker pull ghcr.io/newfuture/ddns`

## 运行方式 docker run

DDNS Docker 镜像支持三种配置方式：命令行，环境变量和配置文件。

- 当设置了命令行参数时，容器将**直接运行单次执行 DDNS 程序，而不会启用定时任务**。
- 如果您需要定时任务，请使用环境变量或配置文件方式。

**注意**:

- 使用了 `-v` 挂载配置文件或目录，确保容器内的 `/ddns/` 目录包含有效的配置文件（如 `config.json`），否则 DDNS 将无法正常工作。
- 使用了 `--network host`，请确保您的 Docker 守护进程已正确配置以支持此模式。
- 使用 `-d` 参数可以让容器在后台运行, 使用前请确保您了解 Docker 的基本操作。
- 使用 `-e DDNS_XXX=YYY` 参数可以设置环境变量，容器内的 DDNS 程序会自动读取这些变量。

### 使用命令行参数 CLI

可以参考[命令行参数说明](cli.md)获取详细的参数列表。
此时 `docker run -v /local/config/:/ddns/  --name=ddns --network=host newfuture/ddns` 就相当于 `ddns` 命令行，不会执行定时任务。

此方式适合需要一次性运行或调试的场景, 参数与 DDNS 命令行参数一致。

```bash
# 查看ddns命令行参数 等价于 ddns -h
docker run --rm newfuture/ddns -h
# 加上ddns的 --debug 参数可以启用调试模式（或者 --log.level=debug）
docker run --rm --network=host newfuture/ddns --debug --dns=dnspod --id=12345 --token=mytokenkey --ipv4=www.example.com --ipv4=ipv4.example.com --index4 public
# 容器内调试
docker run -it newfuture/ddns sh
```

### 使用配置文件 JSON

Docker 容器内的工作目录是 `/ddns/`，默认配置文件会被映射到容器内的 `/ddns/config.json`。

```bash
docker run -d -v /host/config/:/ddns/ newfuture/ddns
```

其中 `/host/config/` 是您本地包含 `config.json` 的目录。
详见 `config.json` 的内容可以参考 [JSON 配置文件说明](json.md)。

### 使用环境变量 ENV

环境变量和命令行参数类似, 加上 DDNS 前缀，推荐全大写。数组类型需要使用 JSON 格式或者单引号包裹。

当然也可以使用 `--env-file` 参数来加载环境变量文件。

```bash
docker run -d \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4='["example.com","www.example.com"]' \
  -e DDNS_INDEX4='["public",0]' \
  --network host \
  --name ddns \
  newfuture/ddns
```

想要了解所有支持的环境变量，请参考[环境变量配置说明](env.md)。

## 网络模式

### host 网络模式

使用 `--network host` 可让容器直接使用宿主机的网络，这样 DDNS 可以正确获取宿主机的 IP 地址。

对于 Public 或者 url 通常不需要设置 host。

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

如果您不想使用 host 网络模式，也可以使用默认的 bridge 模式，但需要注意此时容器具有自己的 IP，您需要使用 `public` 模式获取公网 IP：

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

### 多域名配置

环境变量方式配置多域名：

```bash
docker run -d \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4='["example.com", "www.example.com", "sub.example.com"]' \
  --network host \
  newfuture/ddns
```

命令行参数方式配置多域名：

```bash
docker run --rm --network host newfuture/ddns \
  --dns dnspod \
  --id 12345 \
  --token mytokenkey \
  --ipv4 ipv4.example.com \
  --ipv4 www.example.com
```

### 启用 IPv6 支持

要在 Docker 容器中使用 IPv6，需要确保 Docker 守护程序配置了 IPv6 支持：

1. 编辑 `/etc/docker/daemon.json`：

```json
{
    "ipv6": true,
    "fixed-cidr-v6": "fd00::/80"
}
```

2. 重启 Docker 服务：

```bash
sudo systemctl restart docker
```

3. 启动容器时启用 IPv6：

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
version: "3"
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
            - DDNS_INDEX4=['public','url:https://api.ipify.org']
            - DDNS_LOG_LEVEL=WARNING
```

### 使用配置文件

```yaml
version: "3"
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

## 排障和常见问题

### 容器无法获取正确的 IP 地址

**问题**: DDNS 无法正确获取主机 IP

**解决方案**:

1. 使用 `--network host` 网络模式
2. 或者设置 `-e DDNS_INDEX4=public` 强制使用公网 API 获取 IP

### 未收到定时任务更新

**问题**: 容器运行但不自动更新 DNS

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

**问题**: 容器无法连接到 DNS 服务商 API

**解决方案**:

1. 检查网络连接 `docker exec ddns ping api.dnspod.cn`
2. 配置 HTTP 代理 `-e DDNS_PROXY=http://proxy:port`

## 更多资源

- [DDNS GitHub 主页](https://github.com/NewFuture/DDNS)
- [Docker Hub - newfuture/ddns](https://hub.docker.com/r/newfuture/ddns)
- [环境变量配置详情](env.md)
- [JSON 配置文件详情](json.md)
- [命令行参数详情](cli.md)
