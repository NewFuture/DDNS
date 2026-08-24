# One-Click Installation Script

DDNS one-click installation script with support for automatic download and installation on Linux and macOS systems.

## Quick Installation

The default installer installs the stable Python `ddns`. The Rust client uses
the separate `ddns-rs` command and never overwrites `ddns`:

```bash
# Install latest stable version online
curl -#fSL https://ddns.newfuture.cc/install.sh | sh

# Use sudo if root permission is needed for system directory
curl -#fSL https://ddns.newfuture.cc/install.sh | sudo sh

# Or using wget
wget -qO- https://ddns.newfuture.cc/install.sh | sh
```

> **Note:** Default installation to `/usr/local/bin`. If the directory requires administrator privileges, the script will automatically prompt to use sudo, or you can run with sudo in advance.

### Experimental Rust client

The Rust installer supports Linux x64/arm64 and macOS x64/arm64. It downloads
the separate `ddns-rs-linux-x64`, `ddns-rs-linux-arm64`, `ddns-rs-macos-x64`,
or `ddns-rs-macos-arm64` Release asset and its `.sha256` checksum. Download
`ddns-rs-windows-x64.exe` from Releases on Windows x64.
It installs to `~/.local/bin/ddns-rs` by default without requiring administrator
privileges. Pass `--install-dir /usr/local/bin` explicitly for a system-wide
installation and provide the required permission yourself.
The installer applies only to tagged releases that contain `ddns-rs-*` assets.

```bash
# Install the latest stable Rust client as ddns-rs; Python ddns is unchanged
curl -fsSL https://ddns.newfuture.cc/install-rust.sh | sh

# Install beta or a version; --uninstall removes only ddns-rs
curl -fsSL https://ddns.newfuture.cc/install-rust.sh | sh -s -- beta
curl -fsSL https://ddns.newfuture.cc/install-rust.sh | sh -s -- vX.Y.Z --install-dir ~/.local/bin
curl -fsSL https://ddns.newfuture.cc/install-rust.sh | sh -s -- --uninstall
```

When `sha256sum` or `shasum` is available, the installer verifies the published
checksum. Use `--verify` to require it, or `--no-verify` only when the risk is
understood.

## Version Selection

```bash
# Install latest stable version
curl -#fSL https://ddns.newfuture.cc/install.sh | sh -s -- latest

# Install latest beta version
curl -#fSL https://ddns.newfuture.cc/install.sh | sh -s -- beta

# Install specific version
curl -#fSL https://ddns.newfuture.cc/install.sh | sh -s -- v4.0.2
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
curl -#fSL https://ddns.newfuture.cc/install.sh | sh -s -- beta --install-dir ~/.local/bin

# Force reinstallation
curl -#fSL https://ddns.newfuture.cc/install.sh | sh -s -- --force

# Uninstall
curl -#fSL https://ddns.newfuture.cc/install.sh | sh -s -- --uninstall

# Specify proxy domain (override auto-detection)
curl -#fSL https://ddns.newfuture.cc/install.sh | sh -s -- --proxy https://hub.gitmirror.com/
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
curl -#fSL https://ddns.newfuture.cc/install.sh | sh -s -- latest

# Uninstall
curl -#fSL https://ddns.newfuture.cc/install.sh | sh -s -- --uninstall

# Manual uninstall
sudo rm -f /usr/local/bin/ddns
```

## Troubleshooting

**Permission Issues:** Use `sudo` or install to user directory  
**Network Issues:** Script automatically uses mirror sites (hub.gitmirror.com, proxy.gitwarp.com, etc.)  
**Unsupported Architecture:** Check [releases page](https://github.com/NewFuture/DDNS/releases) for supported architectures  
**Proxy Environment:** The script respects system proxy settings (`HTTP_PROXY/HTTPS_PROXY`); you can also use `--proxy https://hub.gitmirror.com/` to specify a GitHub mirror prefix (overrides auto-detection)
