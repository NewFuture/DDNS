# 📦 Nuitka Build Guide

This document explains how to compile the DDNS project into standalone binary executables using Nuitka, with support for multi-platform cross-compilation on Windows, macOS, and Linux.

## 🎯 Introduction to Nuitka

[Nuitka](https://nuitka.net/) is a Python compiler that compiles Python code into optimized machine code and packages it as standalone executables.

**Core Advantages:**

- ✅ **No Python Runtime Required** - Compiled binaries run directly
- ✅ **Performance Boost** - Faster startup and better runtime efficiency
- ✅ **Simple Deployment** - Single-file distribution with no dependency management
- ✅ **Cross-Platform Support** - Windows, macOS, Linux all supported
- ✅ **Multi-Architecture Support** - x86, x64, ARM, ARM64, and more

**Why DDNS Uses Nuitka:**

- Provide ready-to-use binary tools for users
- Run without Python environment installation
- Suitable for scheduled tasks and system service deployment
- Support embedded devices and routers

---

## 📋 Prerequisites

### Required Dependencies

1. **Python 3.12** (recommended) or Python 3.8+ - Nuitka compiler runtime
2. **Nuitka 4.0.1** (recommended) or higher - Build tool

```bash
pip install nuitka==4.0.1
```

### Platform-Specific Dependencies

#### Windows
- Visual Studio Build Tools or MinGW-w64
- No additional dependencies required

#### macOS
- Xcode Command Line Tools
- `imageio` for icon conversion

```bash
pip install imageio
```

#### Linux
- `patchelf` for binary patching
- GCC toolchain

```bash
# Debian/Ubuntu
sudo apt-get install -y patchelf gcc build-essential

# Alpine
apk add patchelf gcc build-base

# CentOS/RHEL
yum install patchelf gcc
```

---

## 🖥️ Local Compilation (Native Platform)

### Windows Compilation

#### Single-File Executable (Recommended)

```bash
python -m nuitka run.py \
  --mode=onefile \
  --output-dir=dist \
  --lto=yes \
  --windows-console-mode=attach \
  --windows-icon-from-ico=docs/public/favicon.ico
```

**Generated File:** `dist/ddns.exe`

**Parameter Description:**
- `--mode=onefile` - Package as single executable file
- `--lto=yes` - Enable link-time optimization (reduce size, improve performance)
- `--windows-console-mode=attach` - Attach to existing console (no window on double-click, normal output in command line)
- `--windows-icon-from-ico` - Set program icon

#### Standalone Directory Mode

Create a distributable folder with all dependencies:

```bash
python -m nuitka run.py \
  --mode=standalone \
  --output-dir=dist-app \
  --lto=yes \
  --file-description="DDNS Client" \
  --windows-console-mode=attach \
  --windows-icon-from-ico=docs/public/favicon.ico
```

**Generated Files:** `dist-app/run.dist/` directory

**Package as ZIP:**

```powershell
# PowerShell
$appDir = Get-ChildItem -Path 'dist-app' -Directory -Filter '*.dist' | Select-Object -First 1
Compress-Archive -Path "$($appDir.FullName)\*" -DestinationPath 'dist/ddns.zip'
```

**Use Cases:**
- View dependency libraries
- Debug issues
- Custom packaging

### macOS Compilation

```bash
python -m nuitka run.py \
  --mode=onefile \
  --output-dir=dist \
  --lto=yes \
  --macos-app-name=DDNS \
  --macos-app-icon=docs/public/img/ddns.png
```

**Generated File:** `dist/ddns`

**Parameter Description:**
- `--macos-app-name` - Application name
- `--macos-app-icon` - Application icon (PNG format)

**Notes:**
- Install `imageio` first: `pip install imageio`
- PNG icons are automatically converted to macOS required format

### Linux Compilation

```bash
sudo apt-get install -y patchelf

python -m nuitka run.py \
  --mode=onefile \
  --output-dir=dist \
  --lto=yes \
  --static-libpython=yes \
  --linux-icon=docs/public/img/ddns.svg
```

**Generated File:** `dist/ddns`

**Parameter Description:**
- `--static-libpython=yes` - Statically link Python library (improve compatibility)
- `--linux-icon` - Program icon (SVG format)

**Compatibility Notes:**
- Compiled binaries depend on system libc version (glibc or musl)
- Using Docker for builds recommended for better compatibility
- Binaries compiled on Ubuntu 24.04 may not run on older systems

---

## 🐳 Docker Cross-Platform Compilation

Use Docker to compile binaries for multiple Linux architectures and libc implementations.

### Supported Platforms

DDNS provides three Dockerfiles:

| File | Base System | libc | Supported Architectures |
|------|-------------|------|-------------------------|
| `docker/Dockerfile` | Alpine 3.20 | musl 1.2.5 | linux/386, linux/amd64, linux/arm/v6, linux/arm/v7, linux/arm64/v8 |
| `docker/musl.Dockerfile` | Alpine 3.12 | musl 1.1.24 | linux/386, linux/amd64, linux/arm/v6, linux/arm/v7, linux/arm64/v8 |
| `docker/glibc.Dockerfile` | Debian Buster | glibc 2.28 | linux/386, linux/amd64, linux/arm/v7, linux/arm64/v8 |

### Pre-built Builder Images

To accelerate builds, DDNS provides pre-built Nuitka compiler environment images:

```bash
ghcr.io/newfuture/nuitka-builder:master        # Alpine 3.20 (musl)
ghcr.io/newfuture/nuitka-builder:musl-master   # Alpine 3.12 (musl)
ghcr.io/newfuture/nuitka-builder:glibc-master  # Debian Buster (glibc)
```

These images come pre-installed with:
- Python 3.8 (Docker images use this, Python 3.12 recommended for local development)
- Nuitka main branch (or specify version like 4.0.1)
- Build toolchain (gcc, ccache, patchelf, etc.)

**Note:** Docker images use Python 3.8 for better cross-platform compatibility, but Python 3.12 is recommended for local development with Nuitka 4.0.1.

### Compilation Examples

#### 1. Compile Multi-Platform Binaries Using musl.Dockerfile

```bash
docker buildx build \
  --context . \
  --file docker/musl.Dockerfile \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --target export \
  --output type=local,dest=./output \
  --build-arg BUILDER=ghcr.io/newfuture/nuitka-builder:musl-master \
  .
```

**Output Directory Structure:**
```
output/
├── linux_amd64/
│   └── ddns
├── linux_arm64/
│   └── ddns
└── linux_arm_v7/
    └── ddns
```

#### 2. Compile Using glibc.Dockerfile

```bash
docker buildx build \
  --context . \
  --file docker/glibc.Dockerfile \
  --platform linux/amd64,linux/arm64 \
  --target export \
  --output type=local,dest=./output \
  --build-arg BUILDER=ghcr.io/newfuture/nuitka-builder:glibc-master \
  .
```

#### 3. Build Docker Image (With Runtime Environment)

```bash
docker buildx build \
  --context . \
  --file docker/Dockerfile \
  --platform linux/386,linux/amd64,linux/arm/v6,linux/arm/v7,linux/arm64/v8 \
  --tag ddns:latest \
  --build-arg BUILDER=ghcr.io/newfuture/nuitka-builder:master \
  --load \
  .
```

### Build Args Parameters

```dockerfile
ARG BUILDER=ghcr.io/newfuture/nuitka-builder:master  # Builder image
ARG PYTHON_VERSION=3.8                               # Python version (for Docker)
ARG NUITKA_VERSION=main                              # Nuitka version/branch (options: main, 4.0.1, 2.8.10, etc.)
ARG GITHUB_REF_NAME                                  # Git tag/branch name (for version tagging)
```

**Version Notes:**
- Docker images default to Python 3.8 for better cross-platform compatibility
- Python 3.12 + Nuitka 4.0.1 recommended for local development
- `NUITKA_VERSION` can be a version number (e.g., `4.0.1`) or branch name (e.g., `main`)

**Usage Example:**

```bash
docker buildx build \
  --file docker/musl.Dockerfile \
  --build-arg NUITKA_VERSION=4.0.1 \
  --build-arg GITHUB_REF_NAME=v3.0.0 \
  --platform linux/amd64 \
  --target export \
  --output type=local,dest=./output \
  .
```

### Architecture Notes

- `linux/386` - Intel/AMD 32-bit (x86)
- `linux/amd64` - Intel/AMD 64-bit (x86_64)
- `linux/arm/v6` - ARMv6 (e.g., Raspberry Pi Zero)
- `linux/arm/v7` - ARMv7 (e.g., Raspberry Pi 2/3)
- `linux/arm64/v8` - ARM64 (e.g., Raspberry Pi 4, Apple Silicon)
- `linux/ppc64le` - PowerPC 64-bit little-endian
- `linux/riscv64` - RISC-V 64-bit
- `linux/s390x` - IBM System z

---

## 🤖 GitHub Actions CI Build

DDNS uses GitHub Actions to automatically compile multi-platform binaries.

### Workflow Files

- `.github/workflows/build.yml` - Build and test on every Push/PR
- `.github/workflows/publish.yml` - Build release versions on Release

### Using Nuitka-Action

GitHub Actions uses [Nuitka/Nuitka-Action@v1.4](https://github.com/Nuitka/Nuitka-Action):

```yaml
- name: Build Executable
  uses: Nuitka/Nuitka-Action@v1.4
  with:
    nuitka-version: 4.0.1
    script-name: run.py
    mode: onefile
    output-dir: dist
    lto: yes
    file-description: "DDNS Client"
    # Windows-specific parameters
    windows-console-mode: ${{ runner.os == 'Windows' && 'attach' || '' }}
    windows-icon-from-ico: ${{ runner.os == 'Windows' && 'docs/public/favicon.ico' || '' }}
    # Linux-specific parameters
    linux-icon: ${{ runner.os == 'Linux' && 'docs/public/img/ddns.svg' || '' }}
    static-libpython: ${{ runner.os == 'Linux' && 'yes' || 'auto' }}
    # macOS-specific parameters
    macos-app-name: ${{ runner.os == 'macOS' && 'DDNS' || '' }}
    macos-app-icon: ${{ runner.os == 'macOS' && 'docs/public/img/ddns.png' || '' }}
```

### Build Matrix

#### Native Compilation (Nuitka-Action)

```yaml
strategy:
  matrix:
    include:
      - os: windows-latest
        arch: x64
      - os: windows-latest
        arch: x86
      - os: windows-11-arm
        arch: arm64
      - os: ubuntu-latest
        arch: x64
      - os: ubuntu-24.04-arm
        arch: arm64
      - os: macos-15-intel
        arch: x64
      - os: macos-latest
        arch: arm64
```

#### Docker Cross-Platform Compilation

```yaml
strategy:
  matrix:
    host: ['amd', 'arm', 'qemu']
    libc: ['musl', 'glibc']
```

**Build Platform Assignment:**
- `amd` host: `linux/386`, `linux/amd64`
- `arm` host: `linux/arm/v6`, `linux/arm/v7`, `linux/arm64/v8`
- `qemu` host: `linux/ppc64le`, `linux/riscv64`, `linux/s390x`

### Artifact Upload

After build completion, binaries are uploaded to GitHub Artifacts:

```yaml
- name: Upload Artifacts
  uses: actions/upload-artifact@v6
  with:
    name: ddns-${{ env.OS_NAME }}-${{ matrix.arch }}
    path: |
      dist/*.exe
      dist/ddns
      dist/*.zip
    retention-days: ${{ github.event_name == 'push' && 30 || 3 }}
```

**Retention Period:**
- Push events: 30 days
- PR events: 3 days

---

## 🔧 Nuitka Parameters Explained

### Core Parameters

| Parameter | Description | Options | Default |
|-----------|-------------|---------|---------|
| `--mode` | Compilation mode | `onefile`, `standalone`, `module` | `standalone` |
| `--output-dir` | Output directory | Any path | `run.dist` |
| `--lto` | Link-time optimization | `yes`, `no`, `auto` | `auto` |
| `--remove-output` | Remove temporary files after compilation | - | - |

### Optimization Parameters

| Parameter | Description | Recommended |
|-----------|-------------|-------------|
| `--lto=yes` | Enable LTO to reduce file size and improve performance | ✅ Recommended |
| `--static-libpython=yes` | Statically link Python library (Linux) | ✅ Linux Recommended |
| `python3 -O -m nuitka` | Enable Python optimization mode | ✅ Recommended |

### Platform-Specific Parameters

#### Windows

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--windows-console-mode` | Console mode | `attach`, `force`, `disable` |
| `--windows-icon-from-ico` | Program icon | `path/to/icon.ico` |
| `--file-description` | File description | `"DDNS Client"` |
| `--windows-company-name` | Company name | `"NewFuture"` |
| `--windows-product-name` | Product name | `"DDNS"` |
| `--windows-product-version` | Product version | `"3.0.0"` |

**Console Mode Explanation:**
- `attach` - Attach to existing console (recommended, no window on double-click, normal in command line)
- `force` - Force display console window
- `disable` - Completely disable console (GUI program)

#### macOS

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--macos-app-name` | Application name | `DDNS` |
| `--macos-app-icon` | Application icon (PNG) | `path/to/icon.png` |
| `--macos-create-app-bundle` | Create .app bundle | - |

#### Linux

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--linux-icon` | Program icon (SVG) | `path/to/icon.svg` |
| `--static-libpython` | Statically link Python | `yes`, `no`, `auto` |

### Dependency Exclusion

In Docker builds, DDNS automatically excludes system libraries to reduce size:

```dockerfile
# Generate exclusion list
RUN find /lib /usr/lib /usr/local/lib -name '*.so*' | \
    sed 's|.*/||' | \
    awk '{print "--noinclude-dlls="$0}' > nuitka_exclude_so.txt

# Use during compilation
RUN python3 -O -m nuitka run.py \
    --remove-output \
    --lto=yes \
    $(cat nuitka_exclude_so.txt)
```

---

## ✅ Verify Build Results

### Basic Tests

```bash
# Check version
./dist/ddns -v
./dist/ddns --version

# View help
./dist/ddns -h

# Generate config file
./dist/ddns
# Should generate config.json

# Test config file
./dist/ddns -c tests/config/debug.json
```

### Functional Tests

```bash
# Test multiple config files
./dist/ddns -c tests/config/debug.json -c tests/config/noip.json

# Test callback mode
./dist/ddns -c tests/config/callback.json

# Test remote config
./dist/ddns -c https://ddns.newfuture.cc/tests/config/debug.json

# Test proxy config
./dist/ddns -c tests/config/he-proxies.json --debug
```

### System Service Tests

#### Windows Scheduled Task

```batch
.\dist\ddns.exe task --status
.\dist\ddns.exe task --install --time=5
```

#### Linux systemd Service

```bash
./dist/ddns task --status
./dist/ddns task --install --time=10
systemctl --user status ddns
```

#### macOS launchd Service

```bash
./dist/ddns task --status
./dist/ddns task --install --time=10
launchctl list | grep ddns
```

### Performance Tests

```bash
# Startup time test
time ./dist/ddns --version

# Memory usage test
/usr/bin/time -v ./dist/ddns -c tests/config/debug.json
```

---

## 🐛 Troubleshooting

### Compilation Issues

#### 1. Windows: C Compiler Not Found

**Problem:**
```
Error: No C compiler found
```

**Solution:**
- Install Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/
- Or install MinGW-w64: https://www.mingw-w64.org/

#### 2. macOS: Icon Conversion Failed

**Problem:**
```
Error: Cannot convert PNG to ICNS
```

**Solution:**
```bash
pip install imageio
```

#### 3. Linux: Incompatible libc Version After Compilation

**Problem:**
```
./ddns: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.34' not found
```

**Solution:**
- Use Docker for compilation, choose older base image (e.g., Debian Buster)
- Or use musl libc (Alpine image) for better compatibility
- Use `--static-libpython=yes` for static linking

#### 4. Slow Compilation

**Optimization:**
- Use pre-built Builder images (Docker)
- Enable ccache to cache compilation results
- Reduce optimization level (remove `--lto=yes`)

### Runtime Issues

#### 1. Windows Defender False Positive

**Problem:**
Windows Defender or antivirus software flags the compiled exe as a threat.

**Solution:**
- This is a common issue with Python packaging tools (false positive)
- Add to exclusion list
- Use parameters like `--windows-company-name` to add file information

#### 2. macOS: Cannot Verify Developer

**Problem:**
```
"ddns" cannot be opened because the developer cannot be verified
```

**Solution:**
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine dist/ddns

# Or allow in System Preferences
```

#### 3. Large File Size

**Problem:**
Compiled binary size reaches 20MB+.

**Optimization:**
- Ensure using `--lto=yes`
- Use `--remove-output` to delete temporary files
- Exclude unnecessary dependencies (automatically handled in Docker builds)
- Use `--mode=onefile` instead of `standalone`

#### 4. Cross-Platform Compatibility Issues

**Problem:**
Cannot run on different Linux distributions or versions.

**Solution:**
- **glibc systems** (Ubuntu, Debian, CentOS): Use glibc.Dockerfile for compilation
- **musl systems** (Alpine, OpenWrt): Use musl.Dockerfile for compilation
- Compile natively on target system
- Use Docker image instead of binary

---

## 📚 Related Resources

### Official Documentation

- [Nuitka Official Website](https://nuitka.net/)
- [Nuitka User Manual](https://nuitka.net/doc/user-manual.html)
- [Nuitka GitHub](https://github.com/Nuitka/Nuitka)

### DDNS Project Resources

- Build workflow: `.github/workflows/build.yml`
- Publish workflow: `.github/workflows/publish.yml`
- Docker image config: `docker/Dockerfile`
- Musl Dockerfile: `docker/musl.Dockerfile`
- Glibc Dockerfile: `docker/glibc.Dockerfile`

### Community Support

- [DDNS Issues](https://github.com/NewFuture/DDNS/issues)
- [Nuitka Discussions](https://github.com/Nuitka/Nuitka/discussions)

---

## 💡 Development Tips

### Local Development Workflow

1. **Development Phase**: Run Python code directly
   ```bash
   python run.py -c tests/config/debug.json
   ```

2. **Testing Phase**: Compile and test binary
   ```bash
   python -m nuitka run.py --mode=onefile --output-dir=dist
   ./dist/ddns -c tests/config/debug.json
   ```

3. **Release Phase**: Use GitHub Actions for automatic multi-platform builds

### Debugging Tips

#### 1. Preserve Build Artifacts

```bash
# Don't use --remove-output, keep intermediate files for debugging
python -m nuitka run.py --mode=standalone --output-dir=dist-debug
```

#### 2. View Compilation Details

```bash
# Add --show-progress to view compilation progress
python -m nuitka run.py --show-progress --mode=onefile --output-dir=dist
```

#### 3. Enable Debug Information

```bash
# Don't use -O optimization, preserve debug information
python -m nuitka run.py --mode=onefile --output-dir=dist
```

### Version Management

DDNS uses `patch.py` script to automatically update version information:

```bash
python3 .github/patch.py version
```

In GitHub Actions, version tags are passed via `GITHUB_REF_NAME` environment variable:

```yaml
env:
  GITHUB_REF_NAME: ${{ github.ref_name }}
run: python3 .github/patch.py
```

---

## 🎓 Advanced Usage

### Custom Compilation Options

Create a `.nuitka` configuration file:

```ini
[nuitka]
mode=onefile
output-dir=dist
lto=yes
remove-output=true
```

Then run directly:

```bash
python -m nuitka run.py
```

### Plugin System

Nuitka supports plugin extensions:

```bash
python -m nuitka run.py \
  --enable-plugin=anti-bloat \
  --mode=onefile
```

**Common Plugins:**
- `anti-bloat` - Reduce unnecessary dependencies
- `numpy` - Optimize NumPy support
- `multiprocessing` - Multiprocessing support

### Performance Analysis

```bash
# Generate performance report
python -m nuitka run.py \
  --show-memory \
  --show-progress \
  --report=compilation-report.xml \
  --mode=onefile
```

---

Through this documentation, you should be able to:

✅ Compile DDNS binaries locally for various platforms  
✅ Use Docker for cross-platform compilation  
✅ Understand GitHub Actions CI/CD build process  
✅ Resolve common compilation and runtime issues  
✅ Optimize build artifact size and performance  

If you have questions or suggestions, feel free to open an issue on [GitHub Issues](https://github.com/NewFuture/DDNS/issues)!
