# OpenWRT 安装和定时任务配置指南

本指南专门针对 OpenWRT 系统的 DDNS 安装和配置。

## 系统要求

- **操作系统**: OpenWRT 19+ (基于 musl libc ≥ 1.1.24)
- **架构支持**: x86_64, ARM64, ARMv7, ARMv6, i386
- **必需工具**: wget 或 curl, crontab

## 一键安装

### 方式一：在线安装（推荐）

```bash
# 使用 wget（OpenWRT 默认）
wget -qO- https://ddns.newfuture.cc/install.sh | sh

# 或使用 curl
curl -fsSL https://ddns.newfuture.cc/install.sh | sh
```

### 方式二：离线安装

1. 下载安装脚本到本地：
```bash
wget https://ddns.newfuture.cc/install.sh
chmod +x install.sh
```

2. 运行安装：
```bash
./install.sh
```

## 安装验证

安装完成后，验证安装：

```bash
# 检查版本
ddns --version

# 检查安装位置
which ddns
# 应该输出: /usr/local/bin/ddns

# 查看帮助
ddns --help
```

## 配置定时任务

OpenWRT 使用 cron 来管理定时任务。DDNS 提供了便捷的命令来管理定时任务。

### 安装定时任务

```bash
# 安装定时任务，每5分钟执行一次
ddns task --install 5

# 安装定时任务，每10分钟执行一次
ddns task --install 10

# 安装定时任务，每30分钟执行一次
ddns task --install 30
```

### 查看任务状态

```bash
ddns task --status
```

输出示例：
```
DDNS Task Status:
  Installed: Yes
  Scheduler: cron
  Enabled: True
  Interval: 5 minutes
  Command: /usr/local/bin/ddns
  Description: auto-update v4.1.3 installed on 2026-02-08 15:31:45
```

### 启用/禁用任务

```bash
# 禁用定时任务（不删除）
ddns task --disable

# 启用定时任务
ddns task --enable
```

### 卸载定时任务

```bash
# 卸载定时任务（从 crontab 中移除）
ddns task --uninstall
```

### 手动查看 crontab

如果需要手动查看或编辑 crontab：

```bash
# 查看当前 crontab
crontab -l

# 编辑 crontab（不推荐，建议使用 ddns task 命令）
crontab -e
```

## 配置文件

### 创建配置文件

在 OpenWRT 上，推荐将配置文件放在 `/etc/ddns/` 目录：

```bash
# 创建配置目录
mkdir -p /etc/ddns

# 创建配置文件
vi /etc/ddns/config.json
```

配置文件示例（以 Cloudflare 为例）：
```json
{
  "dns": "cloudflare",
  "id": "your-email@example.com",
  "token": "your-api-token",
  "ipv4": ["example.com", "subdomain.example.com"],
  "ipv6": []
}
```

### 使用配置文件

```bash
# 使用配置文件运行
ddns -c /etc/ddns/config.json

# 安装定时任务时使用配置文件
ddns task --install 5 -c /etc/ddns/config.json
```

## 自定义安装路径

如果需要安装到其他目录（例如 `/opt/ddns`）：

```bash
# 安装到自定义目录
wget -qO- https://ddns.newfuture.cc/install.sh | sh -s -- --install-dir /opt/ddns

# 将自定义目录添加到 PATH
export PATH="/opt/ddns:$PATH"

# 永久添加到 PATH（编辑 /etc/profile）
echo 'export PATH="/opt/ddns:$PATH"' >> /etc/profile
```

## 日志查看

### 系统日志

OpenWRT 系统日志位于 `/var/log/` 目录：

```bash
# 查看最新日志
logread | tail -50

# 实时查看日志
logread -f
```

### DDNS 日志

配置 DDNS 输出日志到文件：

```bash
# 运行时指定日志文件
ddns -c /etc/ddns/config.json --log_file /var/log/ddns.log

# 查看日志
tail -f /var/log/ddns.log
```

## 更新 DDNS

### 更新到最新版本

```bash
# 强制重新安装最新版本
wget -qO- https://ddns.newfuture.cc/install.sh | sh -s -- latest --force
```

### 更新到特定版本

```bash
# 安装指定版本（例如 v4.1.3）
wget -qO- https://ddns.newfuture.cc/install.sh | sh -s -- v4.1.3
```

## 卸载 DDNS

### 完整卸载

```bash
# 1. 先卸载定时任务
ddns task --uninstall

# 2. 卸载 DDNS 二进制文件
wget -qO- https://ddns.newfuture.cc/install.sh | sh -s -- --uninstall

# 或手动删除
rm -f /usr/local/bin/ddns

# 3. 可选：删除配置文件
rm -rf /etc/ddns
```

## 故障排除

### 权限问题

如果遇到权限问题，OpenWRT 默认以 root 权限运行，通常不会有权限问题。

### 网络问题

如果下载失败，可以使用代理：

```bash
# 使用 GitHub 镜像
wget -qO- https://ddns.newfuture.cc/install.sh | sh -s -- --proxy https://hub.gitmirror.com/
```

### crontab 不可用

如果 crontab 命令不可用，安装 cron：

```bash
opkg update
opkg install cron
/etc/init.d/cron start
/etc/init.d/cron enable
```

### 定时任务不执行

检查以下几点：

1. **验证 cron 服务正在运行**：
```bash
/etc/init.d/cron status
```

2. **检查 crontab 条目**：
```bash
crontab -l
```

3. **手动测试 DDNS 命令**：
```bash
ddns -c /etc/ddns/config.json
```

4. **查看系统日志**：
```bash
logread | grep -i ddns
```

### 架构不匹配

如果安装的二进制文件无法运行，可能是架构不匹配：

```bash
# 检查系统架构
uname -m

# 检查安装的二进制文件
file /usr/local/bin/ddns
```

确保下载的版本与系统架构匹配。

## 开机自启动

OpenWRT 系统重启后，cron 服务会自动启动，已安装的 DDNS 定时任务会自动生效，无需额外配置。

如需确认 cron 开机自启动：

```bash
# 检查 cron 是否设置为开机启动
ls /etc/rc.d/ | grep cron

# 如果没有，手动启用
/etc/init.d/cron enable
```

## 高级配置

### 使用环境变量

```bash
# 设置环境变量
export DDNS_DNS=cloudflare
export DDNS_ID=your-email@example.com
export DDNS_TOKEN=your-api-token
export DDNS_IPV4=example.com

# 运行 DDNS
ddns
```

### 多配置文件

为不同域名创建多个配置文件：

```bash
# 创建多个配置文件
vi /etc/ddns/cloudflare.json
vi /etc/ddns/dnspod.json

# 分别安装定时任务
ddns task --install 5 -c /etc/ddns/cloudflare.json
ddns task --install 10 -c /etc/ddns/dnspod.json
```

## 参考资料

- [DDNS 项目主页](https://github.com/NewFuture/DDNS)
- [完整文档](https://ddns.newfuture.cc/)
- [DNS 提供商配置](https://ddns.newfuture.cc/providers/)
- [问题反馈](https://github.com/NewFuture/DDNS/issues)

## 总结

OpenWRT 系统上的 DDNS 安装和配置非常简单：

1. ✅ 使用一键安装脚本，自动识别架构
2. ✅ 安装路径为 `/usr/local/bin/ddns`
3. ✅ 使用 `ddns task` 命令管理定时任务
4. ✅ 定时任务通过 cron 实现，开机自动启动
5. ✅ 配置文件推荐放在 `/etc/ddns/` 目录

如有问题，请查阅完整文档或在 GitHub 上提交 issue。
