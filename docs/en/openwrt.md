# OpenWRT Installation and Scheduled Task Configuration Guide

This guide is specifically for DDNS installation and configuration on OpenWRT systems.

## System Requirements

- **Operating System**: OpenWRT 19+ (based on musl libc ≥ 1.1.24)
- **Architecture Support**: x86_64, ARM64, ARMv7, ARMv6, i386
- **Required Tools**: wget or curl, crontab

## One-Click Installation

### Method 1: Online Installation (Recommended)

```bash
# Using wget (OpenWRT default)
wget -qO- https://ddns.newfuture.cc/install.sh | sh

# Or using curl
curl -fsSL https://ddns.newfuture.cc/install.sh | sh
```

### Method 2: Offline Installation

1. Download the installation script locally:
```bash
wget https://ddns.newfuture.cc/install.sh
chmod +x install.sh
```

2. Run the installation:
```bash
./install.sh
```

## Installation Verification

After installation, verify it:

```bash
# Check version
ddns --version

# Check installation location
which ddns
# Should output: /usr/local/bin/ddns

# View help
ddns --help
```

## Configure Scheduled Tasks

OpenWRT uses cron to manage scheduled tasks. DDNS provides convenient commands to manage scheduled tasks.

### Install Scheduled Task

```bash
# Install task to run every 5 minutes
ddns task --install 5

# Install task to run every 10 minutes
ddns task --install 10

# Install task to run every 30 minutes
ddns task --install 30
```

### Check Task Status

```bash
ddns task --status
```

Example output:
```
DDNS Task Status:
  Installed: Yes
  Scheduler: cron
  Enabled: True
  Interval: 5 minutes
  Command: /usr/local/bin/ddns
  Description: auto-update v4.1.3 installed on 2026-02-08 15:31:45
```

### Enable/Disable Task

```bash
# Disable scheduled task (without removing it)
ddns task --disable

# Enable scheduled task
ddns task --enable
```

### Uninstall Scheduled Task

```bash
# Uninstall scheduled task (remove from crontab)
ddns task --uninstall
```

### Manually View crontab

If you need to manually view or edit crontab:

```bash
# View current crontab
crontab -l

# Edit crontab (not recommended, use ddns task commands instead)
crontab -e
```

## Configuration File

### Create Configuration File

On OpenWRT, it's recommended to place configuration files in the `/etc/ddns/` directory:

```bash
# Create configuration directory
mkdir -p /etc/ddns

# Create configuration file
vi /etc/ddns/config.json
```

Example configuration file (using Cloudflare):
```json
{
  "dns": "cloudflare",
  "id": "your-email@example.com",
  "token": "your-api-token",
  "ipv4": ["example.com", "subdomain.example.com"],
  "ipv6": []
}
```

### Use Configuration File

```bash
# Run with configuration file
ddns -c /etc/ddns/config.json

# Install scheduled task with configuration file
ddns task --install 5 -c /etc/ddns/config.json
```

## Custom Installation Path

If you need to install to a different directory (e.g., `/opt/ddns`):

```bash
# Install to custom directory
wget -qO- https://ddns.newfuture.cc/install.sh | sh -s -- --install-dir /opt/ddns

# Add custom directory to PATH
export PATH="/opt/ddns:$PATH"

# Permanently add to PATH (edit /etc/profile)
echo 'export PATH="/opt/ddns:$PATH"' >> /etc/profile
```

## View Logs

### System Logs

OpenWRT system logs are located in the `/var/log/` directory:

```bash
# View recent logs
logread | tail -50

# View logs in real-time
logread -f
```

### DDNS Logs

Configure DDNS to output logs to a file:

```bash
# Specify log file when running
ddns -c /etc/ddns/config.json --log_file /var/log/ddns.log

# View logs
tail -f /var/log/ddns.log
```

## Update DDNS

### Update to Latest Version

```bash
# Force reinstall latest version
wget -qO- https://ddns.newfuture.cc/install.sh | sh -s -- latest --force
```

### Update to Specific Version

```bash
# Install specific version (e.g., v4.1.3)
wget -qO- https://ddns.newfuture.cc/install.sh | sh -s -- v4.1.3
```

## Uninstall DDNS

### Complete Uninstallation

```bash
# 1. First uninstall scheduled task
ddns task --uninstall

# 2. Uninstall DDNS binary
wget -qO- https://ddns.newfuture.cc/install.sh | sh -s -- --uninstall

# Or manually remove
rm -f /usr/local/bin/ddns

# 3. Optional: Remove configuration files
rm -rf /etc/ddns
```

## Troubleshooting

### Permission Issues

If you encounter permission issues, OpenWRT runs as root by default, so permission issues are rare.

### Network Issues

If download fails, you can use a proxy:

```bash
# Use GitHub mirror
wget -qO- https://ddns.newfuture.cc/install.sh | sh -s -- --proxy https://hub.gitmirror.com/
```

### crontab Not Available

If the crontab command is unavailable, install cron:

```bash
opkg update
opkg install cron
/etc/init.d/cron start
/etc/init.d/cron enable
```

### Scheduled Task Not Running

Check the following:

1. **Verify cron service is running**:
```bash
/etc/init.d/cron status
```

2. **Check crontab entry**:
```bash
crontab -l
```

3. **Manually test DDNS command**:
```bash
ddns -c /etc/ddns/config.json
```

4. **View system logs**:
```bash
logread | grep -i ddns
```

### Architecture Mismatch

If the installed binary cannot run, it may be an architecture mismatch:

```bash
# Check system architecture
uname -m

# Check installed binary
file /usr/local/bin/ddns
```

Ensure the downloaded version matches your system architecture.

## Auto-Start on Boot

After OpenWRT system restart, the cron service will automatically start, and installed DDNS scheduled tasks will automatically take effect without additional configuration.

To verify cron auto-start:

```bash
# Check if cron is set to start on boot
ls /etc/rc.d/ | grep cron

# If not, manually enable
/etc/init.d/cron enable
```

## Advanced Configuration

### Using Environment Variables

```bash
# Set environment variables
export DDNS_DNS=cloudflare
export DDNS_ID=your-email@example.com
export DDNS_TOKEN=your-api-token
export DDNS_IPV4=example.com

# Run DDNS
ddns
```

### Multiple Configuration Files

Create multiple configuration files for different domains:

```bash
# Create multiple configuration files
vi /etc/ddns/cloudflare.json
vi /etc/ddns/dnspod.json

# Install scheduled tasks separately
ddns task --install 5 -c /etc/ddns/cloudflare.json
ddns task --install 10 -c /etc/ddns/dnspod.json
```

## Reference Materials

- [DDNS Project Homepage](https://github.com/NewFuture/DDNS)
- [Complete Documentation](https://ddns.newfuture.cc/)
- [DNS Provider Configuration](https://ddns.newfuture.cc/providers/)
- [Issue Reporting](https://github.com/NewFuture/DDNS/issues)

## Summary

DDNS installation and configuration on OpenWRT systems is very simple:

1. ✅ Use one-click installation script with automatic architecture detection
2. ✅ Installation path is `/usr/local/bin/ddns`
3. ✅ Use `ddns task` commands to manage scheduled tasks
4. ✅ Scheduled tasks are implemented via cron and auto-start on boot
5. ✅ Configuration files are recommended to be placed in `/etc/ddns/` directory

If you have any questions, please refer to the complete documentation or submit an issue on GitHub.
