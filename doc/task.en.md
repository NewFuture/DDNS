# Task Scheduling - DDNS Scheduled Tasks

The DDNS client supports automatic task scheduling across multiple platforms to run DDNS updates periodically.

## Features Overview

- **Auto Platform Detection**: Automatically detect and use the most appropriate task scheduler
- **Cross-Platform Support**: Supports Linux, macOS, and Windows
- **Simple Operations**: One-click install, uninstall, and status query

## Supported Schedulers

### Linux
- **systemd** (Preferred): Standard service manager for modern Linux distributions
- **cron**: Traditional Unix task scheduler

### macOS  
- **launchd** (Preferred): Native macOS service manager
- **cron**: Traditional Unix task scheduler

### Windows
- **schtasks**: Built-in Windows Task Scheduler

## Command Usage

### Basic Commands

```bash
# Show status, auto-install if not present
ddns task

# Query task status
ddns task --status

# Install scheduled task
ddns task --install

# Delete scheduled task
ddns task --delete
```

### Advanced Options

```bash
# Specify execution interval
ddns task --install --interval 10  # Execute every 10 minutes

# Specify scheduler
ddns task --install --scheduler cron

# Specify config file
ddns task --install --config /path/to/config.json

# Force reinstall
ddns task --install --force

# Combined options
ddns task --install --interval 3 --scheduler systemd --config /etc/ddns.json --force
```

## Status Information Examples

### Not Installed
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

### Installed
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

## Platform-Specific Notes

### Linux

#### systemd Method
- Creates `/etc/systemd/system/ddns.service`
- Creates `/etc/systemd/system/ddns.timer`
- Requires sudo privileges

#### cron Method
- Modifies user's crontab
- No sudo privileges required

### macOS

#### launchd Method
- Creates `~/Library/LaunchAgents/com.newfuture.ddns.plist`
- Automatically loads and starts the service

#### cron Method
- Modifies user's crontab
- May require additional permissions on newer macOS versions

### Windows

#### schtasks Method
- Uses Windows Task Scheduler
- May require administrator privileges

## Permission Requirements

| Platform | Scheduler | Permission Required |
|----------|-----------|-------------------|
| Linux | systemd | sudo (root) |
| Linux | cron | Current user |
| macOS | launchd | Current user |
| macOS | cron | Current user |
| Windows | schtasks | Administrator (recommended) |

## Troubleshooting

### Permission Issues
```bash
# Linux: Use sudo to install systemd task
sudo python3 -m ddns task --install --scheduler systemd

# Or use cron (no sudo required)
python3 -m ddns task --install --scheduler cron
```

### View Logs

#### systemd
```bash
# Check service status
systemctl status ddns.timer
systemctl status ddns.service

# View logs
journalctl -u ddns.service
journalctl -u ddns.timer
```

#### cron
```bash
# View cron logs (varies by system)
tail -f /var/log/cron
tail -f /var/log/syslog | grep CRON
```

#### launchd (macOS)
```bash
# Check task status
launchctl list com.newfuture.ddns

# View logs
tail -f /tmp/ddns.log
tail -f /tmp/ddns.error.log
```

#### Windows
```bash
# Check task status
schtasks /Query /TN DDNS

# View event logs
eventvwr.msc  # Open Event Viewer
```

## Configuration Notes

- Tasks will run DDNS using the specified configuration file
- If no config file is specified, uses default config search paths
- Ensure the config file path is correct and accessible
- Relative paths are based on the current working directory

## Best Practices

1. **Use Absolute Paths**: Specify absolute paths for configuration files
2. **Test Configuration**: Manually run DDNS first to ensure config is correct
3. **Monitor Logs**: Regularly check task execution logs
4. **Reasonable Intervals**: Set appropriate execution intervals based on DNS provider requirements (recommended ≥ 5 minutes)
5. **Permission Management**: Use principle of least privilege

## API Integration

For programmatic use, you can directly use the TaskManager class:

```python
from ddns.task import TaskManager
import logging

logger = logging.getLogger()
task_manager = TaskManager(logger)

# Check status
status = task_manager.get_task_status()

# Install task
success = task_manager.install_task(
    scheduler='systemd',
    interval=5,
    config_file='/path/to/config.json'
)

# Uninstall task
task_manager.uninstall_task()
```

## Security Considerations

- Task files are created with appropriate permissions
- Sensitive information in config files should be protected
- Consider using dedicated service accounts for scheduled tasks
- Regularly review and update scheduled tasks

## Migration from Legacy Scripts

If you were using the legacy shell scripts (`systemd.sh`, `task.sh`, `task.bat`), you can migrate to the new task command:

### From systemd.sh
```bash
# Old way
sudo ./systemd.sh install

# New way
sudo python3 -m ddns task --install --scheduler systemd
```

### From task.sh (cron)
```bash
# Old way
sudo ./task.sh

# New way
python3 -m ddns task --install --scheduler cron
```

### From task.bat (Windows)
```cmd
# Old way
task.bat

# New way
python -m ddns task --install --scheduler schtasks
```

The new task command provides more flexibility, better error handling, and cross-platform consistency.