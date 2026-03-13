---
name: nuitka-build
description: Guide for compiling DDNS project into standalone binary executables using Nuitka across different platforms (Windows, macOS, Linux) and environments (local, Docker, GitHub Actions CI).
---

# Nuitka Build Guide for DDNS

This skill provides instructions for compiling the DDNS project into standalone binary executables using [Nuitka](https://nuitka.net/).

## Prerequisites

### Required Dependencies

1. **Python 3.12** (recommended) or Python 3.8+
2. **Nuitka 4.0.1** (recommended) or higher

```bash
pip install nuitka==4.0.1
```

### Platform-Specific Dependencies

#### Windows
- Visual Studio Build Tools or MinGW-w64

#### macOS
- Xcode Command Line Tools
- `imageio` for icon conversion: `pip install imageio`

#### Linux
- `patchelf` for binary patching
- GCC toolchain

```bash
# Debian/Ubuntu
sudo apt-get install -y patchelf gcc build-essential

# Alpine
apk add patchelf gcc build-base
```

## Local Compilation (Native Platform)

### Windows — Single-File Executable (Recommended)

```bash
python -m nuitka run.py \
  --mode=onefile \
  --output-dir=dist \
  --lto=yes \
  --windows-console-mode=attach \
  --windows-icon-from-ico=docs/public/favicon.ico
```

Output: `dist/ddns.exe`

### Windows — Standalone Directory Mode

```bash
python -m nuitka run.py \
  --mode=standalone \
  --output-dir=dist-app \
  --lto=yes \
  --file-description="DDNS Client" \
  --windows-console-mode=attach \
  --windows-icon-from-ico=docs/public/favicon.ico
```

Output: `dist-app/run.dist/` directory

Package as ZIP (PowerShell):
```powershell
$appDir = Get-ChildItem -Path 'dist-app' -Directory -Filter '*.dist' | Select-Object -First 1
Compress-Archive -Path "$($appDir.FullName)\*" -DestinationPath 'dist/ddns.zip'
```

### macOS

```bash
pip install imageio

python -m nuitka run.py \
  --mode=onefile \
  --output-dir=dist \
  --lto=yes \
  --macos-app-name=DDNS \
  --macos-app-icon=docs/public/img/ddns.png
```

Output: `dist/ddns`

### Linux

```bash
sudo apt-get install -y patchelf

python -m nuitka run.py \
  --mode=onefile \
  --output-dir=dist \
  --lto=yes \
  --static-libpython=yes \
  --linux-icon=docs/public/img/ddns.svg
```

Output: `dist/ddns`

Note: Compiled binaries depend on system libc version (glibc or musl). Use Docker for better cross-platform compatibility.

## Docker Cross-Platform Compilation

### Supported Platforms

| File | Base System | libc | Architectures |
|------|-------------|------|---------------|
| `docker/Dockerfile` | Alpine 3.20 | musl 1.2.5 | linux/386, linux/amd64, linux/arm/v6, linux/arm/v7, linux/arm64/v8 |
| `docker/musl.Dockerfile` | Alpine 3.12 | musl 1.1.24 | linux/386, linux/amd64, linux/arm/v6, linux/arm/v7, linux/arm64/v8 |
| `docker/glibc.Dockerfile` | Debian Buster | glibc 2.28 | linux/386, linux/amd64, linux/arm/v7, linux/arm64/v8 |

### Pre-built Builder Images

```bash
ghcr.io/newfuture/nuitka-builder:master        # Alpine 3.20 (musl)
ghcr.io/newfuture/nuitka-builder:musl-master   # Alpine 3.12 (musl)
ghcr.io/newfuture/nuitka-builder:glibc-master  # Debian Buster (glibc)
```

These images include: Python 3.8, Nuitka (main branch), and build toolchain (gcc, ccache, patchelf).

### Build Examples

#### musl multi-platform binaries

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

#### glibc binaries

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

#### Docker image (with runtime environment)

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

### Build Args

```dockerfile
ARG BUILDER=ghcr.io/newfuture/nuitka-builder:master  # Builder image
ARG PYTHON_VERSION=3.8                               # Python version (for Docker)
ARG NUITKA_VERSION=main                              # Nuitka version/branch (main, 4.0.1, etc.)
ARG GITHUB_REF_NAME                                  # Git tag/branch name (for version tagging)
```

Custom version example:
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

## GitHub Actions CI

### Workflow Files

- `.github/workflows/build.yml` — Build and test on every Push/PR
- `.github/workflows/publish.yml` — Build release versions on tag push

### Using Nuitka-Action

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
    # Windows
    windows-console-mode: ${{ runner.os == 'Windows' && 'attach' || '' }}
    windows-icon-from-ico: ${{ runner.os == 'Windows' && 'docs/public/favicon.ico' || '' }}
    # Linux
    linux-icon: ${{ runner.os == 'Linux' && 'docs/public/img/ddns.svg' || '' }}
    static-libpython: ${{ runner.os == 'Linux' && 'yes' || 'auto' }}
    # macOS
    macos-app-name: ${{ runner.os == 'macOS' && 'DDNS' || '' }}
    macos-app-icon: ${{ runner.os == 'macOS' && 'docs/public/img/ddns.png' || '' }}
```

### Build Matrix (Native)

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

### Build Matrix (Docker cross-platform)

```yaml
strategy:
  matrix:
    host: ['amd', 'arm', 'qemu']
    libc: ['musl', 'glibc']
```

- `amd` host: `linux/386`, `linux/amd64`
- `arm` host: `linux/arm/v6`, `linux/arm/v7`, `linux/arm64/v8`
- `qemu` host: `linux/ppc64le`, `linux/riscv64`, `linux/s390x`

## Nuitka Parameters Reference

### Core Parameters

| Parameter | Description | Options | Default |
|-----------|-------------|---------|---------|
| `--mode` | Compilation mode | `onefile`, `standalone`, `module` | `standalone` |
| `--output-dir` | Output directory | Any path | `run.dist` |
| `--lto` | Link-time optimization | `yes`, `no`, `auto` | `auto` |
| `--remove-output` | Remove temporary files after compilation | — | — |

### Optimization

| Parameter | Description | Recommended |
|-----------|-------------|-------------|
| `--lto=yes` | Enable LTO (reduce size, improve performance) | ✅ |
| `--static-libpython=yes` | Statically link Python library (Linux) | ✅ Linux |
| `python3 -O -m nuitka` | Python optimization mode | ✅ |

### Windows Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--windows-console-mode` | Console mode | `attach`, `force`, `disable` |
| `--windows-icon-from-ico` | Program icon | `docs/public/favicon.ico` |
| `--file-description` | File description | `"DDNS Client"` |

Console mode: `attach` (recommended) — attaches to existing console, no window on double-click.

### macOS Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--macos-app-name` | Application name | `DDNS` |
| `--macos-app-icon` | Application icon (PNG) | `docs/public/img/ddns.png` |

### Linux Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--linux-icon` | Program icon (SVG) | `docs/public/img/ddns.svg` |
| `--static-libpython` | Statically link Python | `yes`, `no`, `auto` |

### Dependency Exclusion (Docker)

```dockerfile
RUN find /lib /usr/lib /usr/local/lib -name '*.so*' | \
    sed 's|.*/||' | \
    awk '{print "--noinclude-dlls="$0}' > nuitka_exclude_so.txt

RUN python3 -O -m nuitka run.py \
    --remove-output \
    --lto=yes \
    $(cat nuitka_exclude_so.txt)
```

## Verify Build Results

```bash
./dist/ddns -v
./dist/ddns --version
./dist/ddns -h
./dist/ddns                                    # generates config.json
./dist/ddns -c tests/config/debug.json
./dist/ddns -c tests/config/callback.json
./dist/ddns -c tests/config/debug.json -c tests/config/noip.json
./dist/ddns -c tests/config/he-proxies.json --debug
```

## Troubleshooting

### Windows: C Compiler Not Found
Install Visual Studio Build Tools or MinGW-w64.

### macOS: Icon Conversion Failed
Run `pip install imageio`.

### Linux: libc Version Incompatibility
Use Docker with older base image (Debian Buster) or musl libc (Alpine). Use `--static-libpython=yes`.

### Windows Defender False Positive
Common with Python packagers. Add to exclusion list or use `--windows-company-name` for file info.

### macOS: "Cannot Verify Developer"
```bash
xattr -d com.apple.quarantine dist/ddns
```

### Large File Size
Ensure `--lto=yes`, use `--remove-output`, prefer `--mode=onefile`.

## Related Resources

- [Nuitka Official Site](https://nuitka.net/)
- [Nuitka User Manual](https://nuitka.net/doc/user-manual.html)
- [Nuitka GitHub](https://github.com/Nuitka/Nuitka)
- Build workflow: `.github/workflows/build.yml`
- Publish workflow: `.github/workflows/publish.yml`
- Docker configs: `docker/Dockerfile`, `docker/musl.Dockerfile`, `docker/glibc.Dockerfile`
