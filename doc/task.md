# Task Scheduling - DDNS 定时任务

The DDNS client supports automatic task scheduling across multiple platforms to run DDNS updates periodically.

## 功能概述 (Features Overview)

- **自动检测平台** (Auto Platform Detection): 自动检测并使用最适合的任务调度器
- **跨平台支持** (Cross-Platform Support): 支持 Linux、macOS、Windows
- **简单操作** (Simple Operations): 一键安装、卸载、查询状态

## 支持的调度器 (Supported Schedulers)

### Linux
- **systemd** (推荐/Preferred): 现代 Linux 发行版的标准服务管理器
- **cron**: 传统的 Unix 定时任务调度器

### macOS  
- **launchd** (推荐/Preferred): macOS 原生服务管理器
- **cron**: 传统的 Unix 定时任务调度器

### Windows
- **schtasks**: Windows 内置任务计划程序

## 命令用法 (Command Usage)

### 基本命令 (Basic Commands)

```bash
# 查看状态，未安装则自动安装 (Show status, auto-install if not present)
ddns task

# 查询任务状态 (Query task status)
ddns task --status

# 安装定时任务 (Install scheduled task)
ddns task --install

# 删除定时任务 (Delete scheduled task)  
ddns task --delete
```

### 高级选项 (Advanced Options)

```bash
# 指定执行间隔 (Specify execution interval)
ddns task --install --interval 10  # 每10分钟执行一次

# 指定调度器 (Specify scheduler)
ddns task --install --scheduler cron

# 指定配置文件 (Specify config file)
ddns task --install --config /path/to/config.json

# 强制重新安装 (Force reinstall)
ddns task --install --force

# 组合选项 (Combined options)
ddns task --install --interval 3 --scheduler systemd --config /etc/ddns.json --force
```

## 状态信息示例 (Status Information Examples)

### 未安装状态 (Not Installed)
```
DDNS Task Status
================
System: Linux
DDNS Version: 2.x.x

Available Schedulers: systemd, cron
Preferred Scheduler: systemd

Task Status: NOT INSTALLED
Recommended: Use 'ddns task --install' to install with systemd
```

### 已安装状态 (Installed)
```
DDNS Task Status
================
System: Linux
DDNS Version: 2.x.x

Available Schedulers: systemd, cron
Preferred Scheduler: systemd

Task Status: INSTALLED
Current Scheduler: systemd
Task Type: systemd timer
Status: ● ddns.timer - NewFuture DDNS Timer
Enabled: Yes
Interval: 5 minutes
```

## 平台特定说明 (Platform-Specific Notes)

### Linux

#### systemd 方式
- 创建 `/etc/systemd/system/ddns.service`
- 创建 `/etc/systemd/system/ddns.timer`
- 需要 sudo 权限

#### cron 方式
- 修改用户的 crontab
- 不需要 sudo 权限

### macOS

#### launchd 方式
- 创建 `~/Library/LaunchAgents/com.newfuture.ddns.plist`
- 自动加载和启动服务

#### cron 方式
- 修改用户的 crontab
- 在新版 macOS 上可能需要额外权限

### Windows

#### schtasks 方式
- 使用 Windows 任务计划程序
- 可能需要管理员权限

## 权限要求 (Permission Requirements)

| 平台 | 调度器 | 权限要求 |
|------|--------|----------|
| Linux | systemd | sudo (root) |
| Linux | cron | 当前用户 |
| macOS | launchd | 当前用户 |
| macOS | cron | 当前用户 |
| Windows | schtasks | 管理员 (推荐) |

## 故障排除 (Troubleshooting)

### 权限问题 (Permission Issues)
```bash
# Linux: 使用 sudo 安装 systemd 任务
sudo python3 -m ddns task --install --scheduler systemd

# 或者使用 cron (无需 sudo)
python3 -m ddns task --install --scheduler cron
```

### 查看日志 (View Logs)

#### systemd
```bash
# 查看服务状态
systemctl status ddns.timer
systemctl status ddns.service

# 查看日志
journalctl -u ddns.service
journalctl -u ddns.timer
```

#### cron
```bash
# 查看 cron 日志 (根据系统不同)
tail -f /var/log/cron
tail -f /var/log/syslog | grep CRON
```

#### launchd (macOS)
```bash
# 查看任务状态
launchctl list com.newfuture.ddns

# 查看日志
tail -f /tmp/ddns.log
tail -f /tmp/ddns.error.log
```

#### Windows
```bash
# 查看任务状态
schtasks /Query /TN DDNS

# 查看事件日志
eventvwr.msc  # 打开事件查看器
```

## 配置文件注意事项 (Configuration Notes)

- 任务会使用指定的配置文件运行 DDNS
- 如果未指定配置文件，使用默认配置查找路径
- 确保配置文件路径正确且可访问
- 相对路径基于当前工作目录

## 最佳实践 (Best Practices)

1. **使用绝对路径**: 为配置文件指定绝对路径
2. **测试配置**: 安装前先手动运行 DDNS 确保配置正确
3. **查看日志**: 定期检查任务执行日志
4. **合理间隔**: 根据 DNS 提供商要求设置合适的执行间隔 (建议 ≥ 5分钟)
5. **权限管理**: 使用最小必要权限原则

## API 集成 (API Integration)

对于程序化使用，可以直接调用 TaskManager 类：

```python
from ddns.task import TaskManager
import logging

logger = logging.getLogger()
task_manager = TaskManager(logger)

# 检查状态
status = task_manager.get_task_status()

# 安装任务
success = task_manager.install_task(
    scheduler='systemd',
    interval=5,
    config_file='/path/to/config.json'
)

# 卸载任务
task_manager.uninstall_task()
```