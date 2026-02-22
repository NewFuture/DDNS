# 📦 Nuitka 编译指南

本文档介绍如何使用 Nuitka 将 DDNS 项目编译为独立的二进制可执行文件，支持 Windows、macOS、Linux 多平台交叉编译。

## 🎯 Nuitka 简介

[Nuitka](https://nuitka.net/) 是一个 Python 编译器，可以将 Python 代码编译为优化的机器码，并打包成独立可执行文件。

**核心优势：**

- ✅ **无需 Python 环境** - 编译后的二进制文件可直接运行
- ✅ **性能提升** - 启动更快，运行效率更高
- ✅ **部署简便** - 单文件分发，无需依赖管理
- ✅ **跨平台支持** - Windows、macOS、Linux 全平台
- ✅ **多架构支持** - x86、x64、ARM、ARM64 等架构

**DDNS 使用 Nuitka 的原因：**

- 为用户提供即开即用的二进制工具
- 无需安装 Python 环境即可运行
- 适合定时任务和系统服务部署
- 支持嵌入式设备和路由器

---

## 📋 准备工作

### 必需依赖

1. **Python 3.12**（推荐）或 Python 3.8+ - Nuitka 编译器运行环境
2. **Nuitka 4.0.1**（推荐）或更高版本 - 编译工具

```bash
pip install nuitka==4.0.1
```

### 平台特定依赖

#### Windows
- Visual Studio Build Tools 或 MinGW-w64
- 无需额外依赖

#### macOS
- Xcode Command Line Tools
- `imageio` 用于图标转换

```bash
pip install imageio
```

#### Linux
- `patchelf` 用于二进制文件修补
- GCC 编译工具链

```bash
# Debian/Ubuntu
sudo apt-get install -y patchelf gcc build-essential

# Alpine
apk add patchelf gcc build-base

# CentOS/RHEL
yum install patchelf gcc
```

---

## 🖥️ 本地编译（原生平台）

### Windows 编译

#### 单文件可执行文件（推荐）

```bash
python -m nuitka run.py \
  --mode=onefile \
  --output-dir=dist \
  --lto=yes \
  --windows-console-mode=attach \
  --windows-icon-from-ico=docs/public/favicon.ico
```

**生成文件：** `dist/ddns.exe`

**参数说明：**
- `--mode=onefile` - 打包为单个可执行文件
- `--lto=yes` - 启用链接时优化（减小体积，提升性能）
- `--windows-console-mode=attach` - 附加到已有控制台（双击不显示窗口，命令行正常输出）
- `--windows-icon-from-ico` - 设置程序图标

#### 独立目录模式（Standalone）

用于创建可分发的文件夹，包含所有依赖：

```bash
python -m nuitka run.py \
  --mode=standalone \
  --output-dir=dist-app \
  --lto=yes \
  --file-description="DDNS客户端" \
  --windows-console-mode=attach \
  --windows-icon-from-ico=docs/public/favicon.ico
```

**生成文件：** `dist-app/run.dist/` 目录

**打包为 ZIP：**

```powershell
# PowerShell
$appDir = Get-ChildItem -Path 'dist-app' -Directory -Filter '*.dist' | Select-Object -First 1
Compress-Archive -Path "$($appDir.FullName)\*" -DestinationPath 'dist/ddns.zip'
```

**适用场景：**
- 需要查看依赖库
- 调试问题
- 自定义打包

### macOS 编译

```bash
python -m nuitka run.py \
  --mode=onefile \
  --output-dir=dist \
  --lto=yes \
  --macos-app-name=DDNS \
  --macos-app-icon=docs/public/img/ddns.png
```

**生成文件：** `dist/ddns`

**参数说明：**
- `--macos-app-name` - 应用程序名称
- `--macos-app-icon` - 应用程序图标（PNG 格式）

**注意事项：**
- 需要先安装 `imageio`：`pip install imageio`
- PNG 图标会自动转换为 macOS 所需格式

### Linux 编译

```bash
sudo apt-get install -y patchelf

python -m nuitka run.py \
  --mode=onefile \
  --output-dir=dist \
  --lto=yes \
  --static-libpython=yes \
  --linux-icon=docs/public/img/ddns.svg
```

**生成文件：** `dist/ddns`

**参数说明：**
- `--static-libpython=yes` - 静态链接 Python 库（提高兼容性）
- `--linux-icon` - 程序图标（SVG 格式）

**兼容性说明：**
- 编译产物依赖系统 libc 版本（glibc 或 musl）
- 建议使用 Docker 构建以获得更好的兼容性
- Ubuntu 24.04 编译的二进制在旧版系统可能无法运行

---

## 🐳 Docker 跨平台编译

使用 Docker 可以为多种 Linux 架构和 libc 实现编译二进制文件。

### 支持的平台

DDNS 提供三种 Dockerfile：

| 文件 | 基础系统 | libc | 支持架构 |
|------|---------|------|---------|
| `docker/Dockerfile` | Alpine 3.20 | musl 1.2.5 | linux/386, linux/amd64, linux/arm/v6, linux/arm/v7, linux/arm64/v8 |
| `docker/musl.Dockerfile` | Alpine 3.12 | musl 1.1.24 | linux/386, linux/amd64, linux/arm/v6, linux/arm/v7, linux/arm64/v8 |
| `docker/glibc.Dockerfile` | Debian Buster | glibc 2.28 | linux/386, linux/amd64, linux/arm/v7, linux/arm64/v8 |

### 预构建 Builder 镜像

为加速构建，DDNS 提供预构建的 Nuitka 编译环境镜像：

```bash
ghcr.io/newfuture/nuitka-builder:master        # Alpine 3.20 (musl)
ghcr.io/newfuture/nuitka-builder:musl-master   # Alpine 3.12 (musl)
ghcr.io/newfuture/nuitka-builder:glibc-master  # Debian Buster (glibc)
```

这些镜像已预装：
- Python 3.8 (Docker 镜像使用, 本地建议 Python 3.12)
- Nuitka main 分支 (或可指定版本如 4.0.1)
- 编译工具链 (gcc、ccache、patchelf 等)

**说明：** Docker 镜像使用 Python 3.8 是为了更好的跨平台兼容性，本地开发建议使用 Python 3.12 配合 Nuitka 4.0.1。

### 编译示例

#### 1. 使用 musl.Dockerfile 编译多平台二进制

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

**输出目录结构：**
```
output/
├── linux_amd64/
│   └── ddns
├── linux_arm64/
│   └── ddns
└── linux_arm_v7/
    └── ddns
```

#### 2. 使用 glibc.Dockerfile 编译

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

#### 3. 编译 Docker 镜像（包含运行环境）

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

### Build Args 参数

```dockerfile
ARG BUILDER=ghcr.io/newfuture/nuitka-builder:master  # Builder 镜像
ARG PYTHON_VERSION=3.8                               # Python 版本 (Docker 用)
ARG NUITKA_VERSION=main                              # Nuitka 版本/分支 (可用: main, 4.0.1, 2.8.10 等)
ARG GITHUB_REF_NAME                                  # Git 标签/分支名 (用于版本标记)
```

**版本说明：**
- Docker 镜像默认使用 Python 3.8 以获得更好的跨平台兼容性
- 本地开发推荐 Python 3.12 + Nuitka 4.0.1
- `NUITKA_VERSION` 可以是版本号（如 `4.0.1`）或分支名（如 `main`）

**使用示例：**

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

### 架构说明

- `linux/386` - Intel/AMD 32位（x86）
- `linux/amd64` - Intel/AMD 64位（x86_64）
- `linux/arm/v6` - ARMv6（如树莓派 Zero）
- `linux/arm/v7` - ARMv7（如树莓派 2/3）
- `linux/arm64/v8` - ARM64（如树莓派 4、Apple Silicon）
- `linux/ppc64le` - PowerPC 64位小端序
- `linux/riscv64` - RISC-V 64位
- `linux/s390x` - IBM System z

---

## 🤖 GitHub Actions CI 构建

DDNS 使用 GitHub Actions 自动化编译多平台二进制文件。

### 工作流文件

- `.github/workflows/build.yml` - 每次 Push/PR 时构建和测试
- `.github/workflows/publish.yml` - 发布 Release 时构建正式版本

### 使用 Nuitka-Action

GitHub Actions 使用 [Nuitka/Nuitka-Action@v1.4](https://github.com/Nuitka/Nuitka-Action)：

```yaml
- name: Build Executable
  uses: Nuitka/Nuitka-Action@v1.4
  with:
    nuitka-version: 4.0.1
    script-name: run.py
    mode: onefile
    output-dir: dist
    lto: yes
    file-description: "DDNS客户端"
    # Windows 特定参数
    windows-console-mode: ${{ runner.os == 'Windows' && 'attach' || '' }}
    windows-icon-from-ico: ${{ runner.os == 'Windows' && 'docs/public/favicon.ico' || '' }}
    # Linux 特定参数
    linux-icon: ${{ runner.os == 'Linux' && 'docs/public/img/ddns.svg' || '' }}
    static-libpython: ${{ runner.os == 'Linux' && 'yes' || 'auto' }}
    # macOS 特定参数
    macos-app-name: ${{ runner.os == 'macOS' && 'DDNS' || '' }}
    macos-app-icon: ${{ runner.os == 'macOS' && 'docs/public/img/ddns.png' || '' }}
```

### 构建矩阵

#### 原生编译（Nuitka-Action）

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

#### Docker 跨平台编译

```yaml
strategy:
  matrix:
    host: ['amd', 'arm', 'qemu']
    libc: ['musl', 'glibc']
```

**构建平台分配：**
- `amd` 主机：`linux/386`, `linux/amd64`
- `arm` 主机：`linux/arm/v6`, `linux/arm/v7`, `linux/arm64/v8`
- `qemu` 主机：`linux/ppc64le`, `linux/riscv64`, `linux/s390x`

### 产物上传

构建完成后，二进制文件会上传到 GitHub Artifacts：

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

**保留期限：**
- Push 事件：30 天
- PR 事件：3 天

---

## 🔧 Nuitka 参数详解

### 核心参数

| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `--mode` | 编译模式 | `onefile`, `standalone`, `module` | `standalone` |
| `--output-dir` | 输出目录 | 任意路径 | `run.dist` |
| `--lto` | 链接时优化 | `yes`, `no`, `auto` | `auto` |
| `--remove-output` | 编译后删除临时文件 | - | - |

### 优化参数

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `--lto=yes` | 启用 LTO，减小文件体积，提升性能 | ✅ 推荐 |
| `--static-libpython=yes` | 静态链接 Python 库（Linux） | ✅ Linux 推荐 |
| `python3 -O -m nuitka` | 启用 Python 优化模式 | ✅ 推荐 |

### 平台特定参数

#### Windows

| 参数 | 说明 | 示例 |
|------|------|------|
| `--windows-console-mode` | 控制台模式 | `attach`, `force`, `disable` |
| `--windows-icon-from-ico` | 程序图标 | `path/to/icon.ico` |
| `--file-description` | 文件描述 | `"DDNS客户端"` |
| `--windows-company-name` | 公司名称 | `"NewFuture"` |
| `--windows-product-name` | 产品名称 | `"DDNS"` |
| `--windows-product-version` | 产品版本 | `"3.0.0"` |

**Console Mode 说明：**
- `attach` - 附加到已有控制台（推荐，双击不显示窗口，命令行正常）
- `force` - 强制显示控制台窗口
- `disable` - 完全禁用控制台（GUI 程序）

#### macOS

| 参数 | 说明 | 示例 |
|------|------|------|
| `--macos-app-name` | 应用程序名称 | `DDNS` |
| `--macos-app-icon` | 应用图标（PNG） | `path/to/icon.png` |
| `--macos-create-app-bundle` | 创建 .app 包 | - |

#### Linux

| 参数 | 说明 | 示例 |
|------|------|------|
| `--linux-icon` | 程序图标（SVG） | `path/to/icon.svg` |
| `--static-libpython` | 静态链接 Python | `yes`, `no`, `auto` |

### 依赖排除

在 Docker 构建中，DDNS 自动排除系统库以减小体积：

```dockerfile
# 生成排除列表
RUN find /lib /usr/lib /usr/local/lib -name '*.so*' | \
    sed 's|.*/||' | \
    awk '{print "--noinclude-dlls="$0}' > nuitka_exclude_so.txt

# 编译时使用
RUN python3 -O -m nuitka run.py \
    --remove-output \
    --lto=yes \
    $(cat nuitka_exclude_so.txt)
```

---

## ✅ 验证编译结果

### 基本测试

```bash
# 查看版本
./dist/ddns -v
./dist/ddns --version

# 查看帮助
./dist/ddns -h

# 生成配置文件
./dist/ddns
# 应生成 config.json

# 测试配置文件
./dist/ddns -c tests/config/debug.json
```

### 功能测试

```bash
# 测试多个配置文件
./dist/ddns -c tests/config/debug.json -c tests/config/noip.json

# 测试回调模式
./dist/ddns -c tests/config/callback.json

# 测试远程配置
./dist/ddns -c https://ddns.newfuture.cc/tests/config/debug.json

# 测试代理配置
./dist/ddns -c tests/config/he-proxies.json --debug
```

### 系统服务测试

#### Windows 定时任务

```batch
.\dist\ddns.exe task --status
.\dist\ddns.exe task --install --time=5
```

#### Linux systemd 服务

```bash
./dist/ddns task --status
./dist/ddns task --install --time=10
systemctl --user status ddns
```

#### macOS launchd 服务

```bash
./dist/ddns task --status
./dist/ddns task --install --time=10
launchctl list | grep ddns
```

### 性能测试

```bash
# 启动时间测试
time ./dist/ddns --version

# 内存占用测试
/usr/bin/time -v ./dist/ddns -c tests/config/debug.json
```

---

## 🐛 常见问题

### 编译问题

#### 1. Windows 编译失败：找不到 C 编译器

**问题：**
```
Error: No C compiler found
```

**解决方案：**
- 安装 Visual Studio Build Tools：https://visualstudio.microsoft.com/downloads/
- 或安装 MinGW-w64：https://www.mingw-w64.org/

#### 2. macOS 图标转换失败

**问题：**
```
Error: Cannot convert PNG to ICNS
```

**解决方案：**
```bash
pip install imageio
```

#### 3. Linux 编译后无法运行：libc 版本不兼容

**问题：**
```
./ddns: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.34' not found
```

**解决方案：**
- 使用 Docker 编译，选择旧版基础镜像（如 Debian Buster）
- 或使用 musl libc（Alpine 镜像）以获得更好兼容性
- 使用 `--static-libpython=yes` 静态链接

#### 4. 编译速度慢

**优化方案：**
- 使用预构建的 Builder 镜像（Docker）
- 启用 ccache 缓存编译结果
- 减少优化级别（去掉 `--lto=yes`）

### 运行问题

#### 1. Windows Defender 误报病毒

**问题：**
Windows Defender 或杀毒软件将编译的 exe 标记为威胁。

**解决方案：**
- 这是 Python 打包工具的常见问题（误报）
- 添加到排除列表
- 使用 `--windows-company-name` 等参数添加文件信息

#### 2. macOS 无法打开："无法验证开发者"

**问题：**
```
"ddns" cannot be opened because the developer cannot be verified
```

**解决方案：**
```bash
# 移除隔离属性
xattr -d com.apple.quarantine dist/ddns

# 或在系统偏好设置中允许运行
```

#### 3. 文件体积过大

**问题：**
编译的二进制文件体积达到 20MB+。

**优化方案：**
- 确保使用 `--lto=yes`
- 使用 `--remove-output` 删除临时文件
- 排除不必要的依赖库（Docker 构建中已自动处理）
- 使用 `--mode=onefile` 而非 `standalone`

#### 4. 跨平台兼容性问题

**问题：**
在不同 Linux 发行版或版本上无法运行。

**解决方案：**
- **glibc 系统**（Ubuntu、Debian、CentOS）：使用 glibc.Dockerfile 编译
- **musl 系统**（Alpine、OpenWrt）：使用 musl.Dockerfile 编译
- 在目标系统上原生编译
- 使用 Docker 镜像代替二进制文件

---

## 📚 相关资源

### 官方文档

- [Nuitka 官网](https://nuitka.net/)
- [Nuitka 用户手册](https://nuitka.net/doc/user-manual.html)
- [Nuitka GitHub](https://github.com/Nuitka/Nuitka)

### DDNS 项目资源

- 构建工作流：`.github/workflows/build.yml`
- 发布工作流：`.github/workflows/publish.yml`
- Docker 镜像配置：`docker/Dockerfile`
- Musl Dockerfile：`docker/musl.Dockerfile`
- Glibc Dockerfile：`docker/glibc.Dockerfile`

### 社区支持

- [DDNS Issues](https://github.com/NewFuture/DDNS/issues)
- [Nuitka Discussions](https://github.com/Nuitka/Nuitka/discussions)

---

## 💡 开发建议

### 本地开发流程

1. **开发阶段**：直接运行 Python 代码
   ```bash
   python run.py -c tests/config/debug.json
   ```

2. **测试阶段**：编译并测试二进制文件
   ```bash
   python -m nuitka run.py --mode=onefile --output-dir=dist
   ./dist/ddns -c tests/config/debug.json
   ```

3. **发布阶段**：使用 GitHub Actions 自动构建多平台版本

### 调试技巧

#### 1. 保留编译产物

```bash
# 不使用 --remove-output，保留中间文件用于调试
python -m nuitka run.py --mode=standalone --output-dir=dist-debug
```

#### 2. 查看编译详情

```bash
# 添加 --show-progress 查看编译进度
python -m nuitka run.py --show-progress --mode=onefile --output-dir=dist
```

#### 3. 启用调试信息

```bash
# 不使用 -O 优化，保留调试信息
python -m nuitka run.py --mode=onefile --output-dir=dist
```

### 版本管理

DDNS 使用 `patch.py` 脚本自动更新版本信息：

```bash
python3 .github/patch.py version
```

在 GitHub Actions 中，通过 `GITHUB_REF_NAME` 环境变量传递版本标签：

```yaml
env:
  GITHUB_REF_NAME: ${{ github.ref_name }}
run: python3 .github/patch.py
```

---

## 🎓 进阶用法

### 自定义编译选项

创建 `.nuitka` 配置文件：

```ini
[nuitka]
mode=onefile
output-dir=dist
lto=yes
remove-output=true
```

然后直接运行：

```bash
python -m nuitka run.py
```

### 插件系统

Nuitka 支持插件扩展功能：

```bash
python -m nuitka run.py \
  --enable-plugin=anti-bloat \
  --mode=onefile
```

**常用插件：**
- `anti-bloat` - 减少不必要的依赖
- `numpy` - 优化 NumPy 支持
- `multiprocessing` - 多进程支持

### 性能分析

```bash
# 生成性能报告
python -m nuitka run.py \
  --show-memory \
  --show-progress \
  --report=compilation-report.xml \
  --mode=onefile
```

---

通过本文档，您应该能够：

✅ 在本地为各平台编译 DDNS 二进制文件  
✅ 使用 Docker 进行跨平台编译  
✅ 理解 GitHub Actions CI/CD 构建流程  
✅ 解决常见的编译和运行问题  
✅ 优化编译产物的体积和性能  

如有问题或建议，欢迎在 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 提出！
