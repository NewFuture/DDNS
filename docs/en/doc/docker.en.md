# DDNS Docker

- Basic Features
  - Based on Alpine Linux, minimal compiled image size (< 7MB)
  - Multi-architecture support (amd64, arm64, arm/v7, arm/v6, ppc64le, s390x, 386, mips64le)
  - Built-in scheduler, automatic updates every 5 minutes by default
  - No external dependencies, ready to use, optimized performance with low resource usage
- Configuration Methods:
  - [CLI Command Line Parameters](config/cli.en.md)
  - [JSON Configuration File](config/json.en.md)
  - [Environment Variables](config/env.en.md)

## Image Information

### Image Versions

DDNS image versions (Docker Tags):

- `latest`: Latest stable release (default stable release)
- `next`: Next beta version
- `edge`: Latest development build, unstable (master branch)

```bash
docker pull newfuture/ddns:latest
docker pull newfuture/ddns:next
```

You can also specify a specific version, for example:

```bash
docker pull newfuture/ddns:v4.0.0
```

### Image Sources

Images are published to the following registries:

- [Docker Hub](https://hub.docker.com/r/newfuture/ddns): `docker.io/newfuture/ddns`
- [GitHub Packages](https://github.com/newfuture/DDNS/pkgs/container/ddns): `ghcr.io/newfuture/ddns`

Supports `docker pull ghcr.io/newfuture/ddns`

## Running with docker run

DDNS Docker image supports three configuration methods: command line, environment variables, and config file.

- When command line arguments are set, the container will **run DDNS directly once without enabling the scheduler**.
- If you need scheduled updates, please use environment variables or config file methods.

**Notes** (for docker run):

- If using `-v` to mount config files or directories, ensure the `/ddns/` directory in the container contains valid config files (like `config.json`), otherwise DDNS will not work properly.
- If using `--network host`, ensure your Docker daemon is properly configured to support this mode.
- Use `-d` parameter to run the container in the background. Make sure you understand basic Docker operations before using.
- Use `-e DDNS_XXX=YYY` parameters to set environment variables, and the DDNS program in the container will automatically read these variables.

### Using Command Line Parameters (CLI)

You can refer to the [CLI parameter documentation](config/cli.en.md) for a detailed parameter list.
In this case, `docker run -v /local/config/:/ddns/ --name=ddns --network=host newfuture/ddns` is equivalent to the `ddns` command line and will not execute scheduled tasks.

This method is suitable for one-time runs or debugging scenarios. Parameters are identical to DDNS command line parameters.

```bash
# View ddns command line parameters, equivalent to ddns -h
docker run --rm newfuture/ddns -h
# Add ddns --debug parameter to enable debug mode (or --log.level=debug)
docker run --rm --network=host newfuture/ddns --debug --dns=dnspod --id=12345 --token=mytokenkey --ipv4=www.example.com --ipv4=ipv4.example.com --index4 public
# Debug inside container
docker run -it newfuture/ddns sh
```

### Using Configuration File (JSON)

The working directory inside the Docker container is `/ddns/`, and the default config file is mapped to `/ddns/config.json` inside the container.

```bash
docker run -d -v /host/config/:/ddns/ newfuture/ddns
```

Where `/host/config/` is your local directory containing `config.json`.
For details on `config.json` content, refer to [JSON Configuration File Documentation](config/json.en.md).

### Using Environment Variables (ENV)

Environment variables are similar to command line parameters, with a DDNS prefix, recommended in uppercase. Array types need to use JSON format or be wrapped in single quotes.

You can also use the `--env-file` parameter to load environment variable files.

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

To learn about all supported environment variables, please refer to [Environment Variable Configuration Documentation](config/env.en.md).

## Network Modes

### Host Network Mode

Using `--network host` allows the container to directly use the host's network, so DDNS can correctly obtain the host's IP address.

For Public or URL modes, host network is usually not required.

```bash
docker run -d \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4=example.com \
  --network host \
  newfuture/ddns
```

### Bridge Network Mode (Default)

If you don't want to use host network mode, you can also use the default bridge mode, but note that the container will have its own IP. You need to use `public` mode to get the public IP:

```bash
docker run -d \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4=example.com \
  -e DDNS_INDEX4=public \
  newfuture/ddns
```

## Advanced Configuration

### Custom Cron Schedule

By default, the DDNS container automatically updates DNS records every 5 minutes. You can customize the scheduled task execution interval using the `DDNS_CRON` environment variable.

The `DDNS_CRON` environment variable uses standard cron expression format: `minute hour day month weekday`

**Examples**:

```bash
# Run every 10 minutes
docker run -d \
  -e DDNS_CRON="*/10 * * * *" \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4=example.com \
  --network host \
  newfuture/ddns

# Run every hour
docker run -d \
  -e DDNS_CRON="0 * * * *" \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4=example.com \
  --network host \
  newfuture/ddns

# Run once daily at 2 AM
docker run -d \
  -e DDNS_CRON="0 2 * * *" \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4=example.com \
  --network host \
  newfuture/ddns

# Run every minute (most frequent for cron)
docker run -d \
  -e DDNS_CRON="* * * * *" \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4=example.com \
  --network host \
  newfuture/ddns
```

**Cron Expression Reference**:

| Field    | Allowed Values | Allowed Special Characters |
|----------|----------------|----------------------------|
| Minute   | 0-59           | * , - /                    |
| Hour     | 0-23           | * , - /                    |
| Day      | 1-31           | * , - /                    |
| Month    | 1-12           | * , - /                    |
| Weekday  | 0-7            | * , - /                    |

**Common Expression Examples**:

- `*/5 * * * *` - Every 5 minutes (default)
- `*/10 * * * *` - Every 10 minutes
- `*/15 * * * *` - Every 15 minutes
- `0 * * * *` - Every hour
- `0 */2 * * *` - Every 2 hours
- `0 0 * * *` - Daily at midnight
- `0 2 * * *` - Daily at 2 AM
- `0 0 * * 0` - Weekly on Sunday at midnight

**Docker Compose Example**:

```yaml
version: "3"
services:
    ddns:
        image: newfuture/ddns:latest
        restart: always
        network_mode: host
        environment:
            - DDNS_CRON=*/10 * * * *  # Run every 10 minutes
            - DDNS_DNS=dnspod
            - DDNS_ID=12345
            - DDNS_TOKEN=mytokenkey
            - DDNS_IPV4=example.com
```

### Multi-Domain Configuration

Environment variable method for configuring multiple domains:

```bash
docker run -d \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV4='["example.com", "www.example.com", "sub.example.com"]' \
  --network host \
  newfuture/ddns
```

Command line parameter method for configuring multiple domains:

```bash
docker run --rm --network host newfuture/ddns \
  --dns dnspod \
  --id 12345 \
  --token mytokenkey \
  --ipv4 ipv4.example.com \
  --ipv4 www.example.com
```

### Enable IPv6 Support

To use IPv6 in Docker containers, you need to ensure the Docker daemon is configured with IPv6 support:

1. Edit `/etc/docker/daemon.json`:

```json
{
    "ipv6": true,
    "fixed-cidr-v6": "fd00::/80"
}
```

2. Restart Docker service:

```bash
sudo systemctl restart docker
```

3. Enable IPv6 when starting the container:

```bash
docker run -d \
  --network host \
  -e DDNS_DNS=dnspod \
  -e DDNS_ID=12345 \
  -e DDNS_TOKEN=mytokenkey \
  -e DDNS_IPV6=example.com \
  newfuture/ddns
```

## Docker Compose Examples

Create a `docker-compose.yml` file:

### Basic Environment Variable Configuration

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

### Using Configuration File

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

Run Docker Compose:

```bash
docker-compose up -d
```

## Using Custom Images

If you need to add other tools or customize the environment in the container, you can create your own Dockerfile based on the official image:

```dockerfile
FROM newfuture/ddns:latest

# Install additional tools
RUN apk add --no-cache curl

# Add custom scripts
COPY custom-script.sh /bin/
RUN chmod +x /bin/custom-script.sh

# Override default entrypoint (optional)
# ENTRYPOINT ["/bin/custom-script.sh"]
```

## Troubleshooting & FAQ

### Container Can't Get Correct IP Address

**Problem**: DDNS cannot correctly obtain host IP

**Solution**:

1. Use `--network host` network mode
2. Or set `-e DDNS_INDEX4=public` to force using public API to get IP

### No Scheduled Updates Received

**Problem**: Container runs but doesn't automatically update DNS

**Solution**:

1. Check container logs `docker logs ddns`
2. Confirm container is not paused `docker ps -a`
3. Try manual update execution `docker exec ddns /bin/ddns`

### Exits Immediately After First Run

**Problem**: Container exits immediately after startup

**Solution**:

1. Add `-it` parameter to run interactively and see the issue `docker run -it --rm newfuture/ddns`
2. Check if environment variables or config files are set correctly

### Network Connection Issues

**Problem**: Container cannot connect to DNS provider API

**Solution**:

1. Check network connectivity `docker exec ddns ping api.dnspod.cn`
2. Configure HTTP proxy `-e DDNS_PROXY=http://proxy:port`

## More Resources

- [DDNS GitHub Repository](https://github.com/NewFuture/DDNS)
- [Docker Hub - newfuture/ddns](https://hub.docker.com/r/newfuture/ddns)
- [Environment Variable Configuration Details](config/env.en.md)
- [JSON Configuration File Details](config/json.en.md)
- [Command Line Parameter Details](config/cli.en.md)

## Configuration Examples for Different DNS Providers

### CloudFlare

```bash
docker run -d \
  -e DDNS_DNS=cloudflare \
  -e DDNS_ID=user@example.com \
  -e DDNS_TOKEN=your_cloudflare_api_token \
  -e DDNS_IPV4='["example.com"]' \
  --name ddns-cloudflare \
  newfuture/ddns
```

### Alibaba Cloud DNS

```bash
docker run -d \
  -e DDNS_DNS=alidns \
  -e DDNS_ID=your_access_key_id \
  -e DDNS_TOKEN=your_access_key_secret \
  -e DDNS_IPV4='["example.com"]' \
  --name ddns-alidns \
  newfuture/ddns
```

### Huawei Cloud DNS

```bash
docker run -d \
  -e DDNS_DNS=huaweidns \
  -e DDNS_ID=your_access_key \
  -e DDNS_TOKEN=your_secret_key \
  -e DDNS_IPV4='["example.com"]' \
  --name ddns-huawei \
  newfuture/ddns
```

### Tencent Cloud DNS

```bash
docker run -d \
  -e DDNS_DNS=tencentcloud \
  -e DDNS_ID=your_secret_id \
  -e DDNS_TOKEN=your_secret_key \
  -e DDNS_IPV4='["example.com"]' \
  --name ddns-tencent \
  newfuture/ddns
```

### Custom Callback

```bash
# GET method callback
docker run -d \
  -e DDNS_DNS=callback \
  -e DDNS_ID="https://api.example.com/ddns?domain=__DOMAIN__&ip=__IP__" \
  -e DDNS_TOKEN="" \
  -e DDNS_IPV4='["example.com"]' \
  --name ddns-callback-get \
  newfuture/ddns

# POST method callback
docker run -d \
  -e DDNS_DNS=callback \
  -e DDNS_ID="https://api.example.com/ddns" \
  -e DDNS_TOKEN='{"api_key": "your_key", "domain": "__DOMAIN__", "ip": "__IP__"}' \
  -e DDNS_IPV4='["example.com"]' \
  --name ddns-callback-post \
  newfuture/ddns
```

### Using Custom API Endpoints

```bash
docker run -d \
  -e DDNS_DNS=cloudflare \
  -e DDNS_ENDPOINT=https://api.private-cloudflare.com \
  -e DDNS_ID=user@example.com \
  -e DDNS_TOKEN=your_token \
  -e DDNS_IPV4='["example.com"]' \
  --name ddns-custom-endpoint \
  newfuture/ddns
```
