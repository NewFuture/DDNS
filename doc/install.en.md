# One-Click Installation Script

DDNS one-click installation script with support for automatic download and installation on Linux and macOS systems.

## Quick Installation

```bash
# Install latest stable version online
curl -fsSL https://ddns.newfuture.cc/install.sh | sh

# Use sudo if root permission is needed for system directory
curl -fsSL https://ddns.newfuture.cc/install.sh | sudo sh

# Or using wget
wget -qO- https://ddns.newfuture.cc/install.sh | sh
```

> **Note:** Default installation to `/usr/local/bin`. If the directory requires administrator privileges, the script will automatically prompt to use sudo, or you can run with sudo in advance.

## Version Selection

```bash
# Install latest stable version
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- latest

# Install latest beta version
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- beta

# Install specific version
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- v4.0.2
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `latest` | Install latest stable version (default) |
| `beta` | Install latest beta version |
| `v4.0.2` | Install specific version |
| `--install-dir PATH` | Specify installation directory (default: /usr/local/bin) |
| `--proxy URL` | Specify proxy domain/prefix (e.g., `https://hub.gitmirror.com/`), overrides auto-detection |
| `--force` | Force reinstallation |
| `--uninstall` | Uninstall installed ddns |
| `--help` | Show help information |

## Advanced Usage

```bash
# Custom installation directory
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- beta --install-dir ~/.local/bin

# Force reinstallation
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- --force

# Uninstall
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- --uninstall

# Specify proxy domain (override auto-detection)
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- --proxy https://hub.gitmirror.com/
```

## System Support

**Operating Systems:** Linux (glibc/musl), macOS  
**Architectures:** x86_64, ARM64, ARM v7, ARM v6, i386  
**Dependencies:** curl or wget

### Auto-Detection Features
- **System Detection:** Automatically identifies operating system, architecture and libc type
- **Tool Detection:** Automatically selects curl or wget download tool
- **Network Optimization:** Automatically tests and selects the best download mirror (github.com → China mirror sites)
- **Manual Override:** Use `--proxy` to specify a proxy domain/mirror prefix, which takes precedence over auto-detection

## Verify Installation

```bash
ddns --version    # Check version
which ddns        # Check installation location
```

## Update & Uninstall

```bash
# Update to latest version
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- latest

# Uninstall
curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- --uninstall

# Manual uninstall
sudo rm -f /usr/local/bin/ddns
```

## Troubleshooting

**Permission Issues:** Use `sudo` or install to user directory  
**Network Issues:** Script automatically uses mirror sites (hub.gitmirror.com, proxy.gitwarp.com, etc.)  
**Unsupported Architecture:** Check [releases page](https://github.com/NewFuture/DDNS/releases) for supported architectures  
**Proxy Environment:** The script respects system proxy settings (`HTTP_PROXY/HTTPS_PROXY`); you can also use `--proxy https://hub.gitmirror.com/` to specify a GitHub mirror prefix (overrides auto-detection)
