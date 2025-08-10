# 一键安装脚本

DDNS 一键安装脚本，支持 Linux 和 macOS 系统自动下载安装。

## 快速安装

```bash
# 在线安装最新稳定版
curl -fsSL https://ddns.newfuture.cc/install.sh | sh
# 如需 root 权限安装到系统目录，使用 sudo
curl -fsSL https://ddns.newfuture.cc/install.sh | sudo sh

# 或使用 wget
wget -qO- https://ddns.newfuture.cc/install.sh | sh

```

> **说明：** 默认安装到 `/usr/local/bin`，如果该目录需要管理员权限，脚本会自动提示使用 sudo，或者可以预先使用 sudo 运行。

## 版本选择

```bash
# 安装最新稳定版
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- latest

# 安装最新测试版
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- beta

# 安装指定版本
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- v4.0.2
```

## 命令行选项

| 选项 | 说明 |
|------|------|
| `latest` | 安装最新稳定版（默认） |
| `beta` | 安装最新测试版 |
| `v4.0.2` | 安装指定版本 |
| `--install-dir PATH` | 指定安装目录（默认：/usr/local/bin） |
| `--proxy URL` | 指定代理域名前缀（例如：`https://hub.gitmirror.com/`），覆盖自动探测 |
| `--force` | 强制重新安装 |
| `--uninstall` | 卸载已安装的 ddns |
| `--help` | 显示帮助信息 |

## 高级用法

```bash
# 自定义安装目录
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- beta --install-dir ~/.local/bin

# 强制重新安装
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- --force

# 卸载
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- --uninstall

# 指定代理域名（覆盖自动探测）
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- --proxy https://hub.gitmirror.com/
```

## 系统支持

**操作系统：** Linux（glibc/musl）、macOS  
**架构：** x86_64、ARM64、ARM v7、ARM v6、i386  
**依赖：** curl 或 wget

### 自动检测功能
- **系统检测：** 自动识别操作系统、架构和 libc 类型
- **工具检测：** 自动选择 curl 或 wget 下载工具
- **网络优化：** 自动测试并选择最佳下载镜像（github.com → 国内镜像站）
- **手动覆盖：** 通过 `--proxy` 指定代理域名/镜像前缀，优先于自动探测

## 验证安装

```bash
ddns --version    # 检查版本
which ddns        # 检查安装位置
```

## 更新与卸载

```bash
# 更新到最新版本
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- latest

# 卸载
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- --uninstall

# 手动卸载
sudo rm -f /usr/local/bin/ddns
```

## 故障排除

**权限问题：** 使用 `sudo` 或安装到用户目录  
**网络问题：** 脚本自动使用镜像站点（hub.gitmirror.com、proxy.gitwarp.com 等）  
**架构不支持：** 查看 [releases 页面](https://github.com/NewFuture/DDNS/releases) 确认支持的架构
**代理环境:** 脚本会尊重系统代理设置（`HTTP_PROXY/HTTPS_PROXY`）；也可以使用 `--proxy https://hub.gitmirror.com/` 指定 GitHub 镜像前缀（覆盖自动探测）
