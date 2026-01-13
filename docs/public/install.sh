#!/bin/sh
#
# One-click installation script for DDNS
# 一键安装脚本
#
# Usage:
#   curl -fsSL https://ddns.newfuture.cc/install.sh | sh
#   wget -qO- https://ddns.newfuture.cc/install.sh | sh
#
# With version:
#   curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- v4.0.2
#   curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- beta
#   curl -fsSL https://ddns.newfuture.cc/install.sh | sh -s -- latest
#
# Note: This script handles SSL certificate verification gracefully.
# In container environments where CA certificates may be missing,
# it will fallback to insecure downloads after SSL verification fails.
# 注意：此脚本会优雅地处理SSL证书验证。
# 在可能缺少CA证书的容器环境中，SSL验证失败后会回退到不安全的下载。
#

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
VERSION=""
INSTALL_DIR="/usr/local/bin"
BINARY_NAME="ddns"
REPO="NewFuture/DDNS"
USER_AGENT="DDNS-Installer/1.0"
FORCE_INSTALL=false
# Whether user explicitly passed a VERSION argument
USER_VERSION_SPECIFIED=false
# Uninstall mode
UNINSTALL_MODE=false
# Default network timeout (seconds) for downloads; override with env DOWNLOAD_TIMEOUT
DOWNLOAD_DEFAULT_TIMEOUT="${DOWNLOAD_TIMEOUT:-90}"
# Optional proxy base URL to prefix the original GitHub URL, e.g.
# Final download will be: "$PROXY_URL" + "https://github.com/..." (PROXY_URL always ends with '/')
PROXY_URL=""
PROXY_CANDIDATES="https://hub.gitmirror.com/ https://proxy.gitwarp.com/ https://gh.200112.xyz/"

# Language detection
detect_language() {
    if [ -n "$LANG" ]; then
        case "$LANG" in
            zh_* | zh-* | *zh*)
                LANGUAGE="zh"
                ;;
            *)
                LANGUAGE="en"
                ;;
        esac
    else
        LANGUAGE="en"
    fi
}

# Initialize language detection
detect_language

# Helper function to select message based on language
select_message() {
    local en="$1"
    local zh="$2"
    if [ "$LANGUAGE" = "zh" ] && [ -n "$zh" ]; then
        echo "$zh"
    else
        echo "$en"
    fi
}

# Print colored messages
print_info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$(select_message "$1" "$2")"
}

print_success() {
    printf "${GREEN}[SUCCESS]${NC} %s\n" "$(select_message "$1" "$2")"
}

print_warning() {
    printf "${YELLOW}[WARNING]${NC} %s\n" "$(select_message "$1" "$2")"
}

print_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$(select_message "$1" "$2")"
}

# Show usage information
show_usage() {
    if [ "$LANGUAGE" = "zh" ]; then
        cat << EOF
DDNS 一键安装脚本

用法:
    $0 [VERSION] [OPTIONS]

版本:
    latest          安装最新稳定版本 (默认)
    beta           安装最新测试版本
    v4.0.2         安装指定版本 (例如: v4.0.2)

选项:
    --install-dir PATH    安装目录 (默认: /usr/local/bin)
    --proxy URL          代理域名/前缀，例如: https://hub.gitmirror.com/
    --force              强制安装，即使已存在
    --uninstall          卸载已安装的 ddns 可执行文件
    --help               显示此帮助信息

说明:
    显式指定 VERSION 时(如: v4.0.2/beta/latest)，即使已安装也会覆盖，无需 --force

示例:
    $0                    # 安装最新稳定版本
    $0 beta              # 安装最新测试版本
    $0 v4.0.2            # 安装指定版本
    $0 latest --force    # 强制重新安装最新版本
    $0 --uninstall       # 卸载 ddns

EOF
    else
        cat << EOF
DDNS One-Click Installation Script

Usage:
    $0 [VERSION] [OPTIONS]

VERSION:
    latest          Install latest stable version (default)
    beta           Install latest beta version
    v4.0.2         Install specific version (e.g., v4.0.2)

OPTIONS:
    --install-dir PATH    Installation directory (default: /usr/local/bin)
    --proxy URL          Proxy domain/prefix, e.g. https://hub.gitmirror.com/
    --force              Force installation even if already exists
    --uninstall          Uninstall the ddns executable
    --help               Show this help message

Notes:
    When a VERSION is explicitly provided (e.g., v4.0.2/beta/latest), the installer
    will overwrite an existing installation without requiring --force

Examples:
    $0                    # Install latest stable version
    $0 beta              # Install latest beta version
    $0 v4.0.2            # Install specific version
    $0 latest --force    # Force reinstall latest version
    $0 --uninstall       # Uninstall ddns

EOF
    fi
}

# Check if running on supported OS
check_os() {
    case "$(uname -s)" in
        Linux*)  OS="linux" ;;
        Darwin*) OS="mac" ;;
        *)
            print_error "Unsupported operating system: $(uname -s)" "不支持的操作系统: $(uname -s)"
            print_error "This script only supports Linux and macOS" "此脚本仅支持 Linux 和 macOS"
            exit 1
            ;;
    esac
    print_info "Detected OS: $OS" "检测到操作系统: $OS"
}

# Detect system architecture
detect_arch() {
    local arch
    arch="$(uname -m)"
    
    case "$arch" in
        x86_64|amd64)
            if [ "$OS" = "mac" ]; then
                ARCH="x64"
            else
                ARCH="amd64"
            fi
            ;;
        arm64|aarch64)
            ARCH="arm64"
            ;;
        armv7l|armv7)
            ARCH="arm_v7"
            ;;
        armv6l)
            ARCH="arm_v6"
            ;;
        i386|i686)
            ARCH="386"
            ;;
        *)
            print_error "Unsupported architecture: $arch" "不支持的架构: $arch"
            exit 1
            ;;
    esac
    print_info "Detected architecture: $ARCH" "检测到架构: $ARCH"
}

# Detect libc type on Linux
detect_libc() {
    if [ "$OS" != "linux" ]; then
        return
    fi

    LIBC="glibc"
    if ldd --version 2>&1 | grep -i musl > /dev/null; then
        LIBC="musl"
    elif ldd /bin/sh 2>&1 | grep -i musl > /dev/null; then
        # musl detected via ldd on /bin/sh
        LIBC="musl"
    fi
    print_info "Detected libc: $LIBC" "检测到 libc: $LIBC"
}

# Check for download tool (curl or wget)
check_download_tool() {
    if command -v curl > /dev/null 2>&1; then
        DOWNLOAD_TOOL="curl"
        print_info "Using curl for downloads" "使用 curl 进行下载"
    elif command -v wget > /dev/null 2>&1; then
        DOWNLOAD_TOOL="wget"
        print_info "Using wget for downloads" "使用 wget 进行下载"
    else
        print_error "Neither curl nor wget found. Please install one of them." "未找到 curl 或 wget，请安装其中一个"
        exit 1
    fi
}

# Download file using available tool
download_file() {
    local url="$1"
    local output="$2"
    local timeout="$3"    # optional seconds; falls back to DOWNLOAD_DEFAULT_TIMEOUT
    local retries=1
    if [ -z "$timeout" ]; then
        timeout="$DOWNLOAD_DEFAULT_TIMEOUT"
        retries=3  # If timeout is not specified
    fi

    if [ "$DOWNLOAD_TOOL" = "curl" ]; then
        curl -#fSL --retry $retries -H "User-Agent: $USER_AGENT" --connect-timeout "$timeout" --max-time "$timeout" "$url" -o "$output"
        rc=$?
        case "$rc" in
            35|51|60|77)
                # SSL-related errors only: retry insecurely
                print_warning "Download failed due to SSL (code $rc), trying with --insecure" "下载因 SSL 问题失败(代码 $rc)，尝试使用 --insecure"
                curl -fSL --retry $retries -H "User-Agent: $USER_AGENT" --insecure --connect-timeout "$timeout" --max-time "$timeout" "$url" -o "$output"
                return $?
                ;;
            *)
                # Non-SSL errors: do not retry insecurely
                return "$rc"
                ;;
        esac
    else
        wget -q --user-agent="$USER_AGENT" --timeout="$timeout" "$url" -O "$output"
        rc=$?
        if [ "$rc" -eq 5 ]; then
            # SSL verification failure: retry insecurely
            print_warning "Download failed due to SSL (code $rc), trying with --no-check-certificate" "下载因 SSL 问题失败(代码 $rc)，尝试使用 --no-check-certificate"
            wget --user-agent="$USER_AGENT" --no-check-certificate --timeout="$timeout" "$url" -O "$output"
            return $?
        fi
        # Non-SSL errors: do not retry insecurely
        return "$rc"
    fi
}

# Auto-detect a working proxy (or direct GitHub) when PROXY_URL not specified
find_working_proxy() {
    print_info "Testing Github and proxy connectivity..." "测试GitHub和代理连接..."
    local mirror test_url
    # Try direct first (empty mirror), then known proxy candidates
    for mirror in "" $PROXY_CANDIDATES; do
        print_info "Testing: ${mirror:-"github.com"}" "测试: ${mirror:-"github.com"}"
        # Probe using a real release asset to validate proxy behavior
        test_url="${mirror}https://github.com/NewFuture/DDNS/releases/download/v4.0.0/create-task.sh"
        if download_file "$test_url" "/dev/null" 8; then
            PROXY_URL="$mirror"
            if [ -n "$PROXY_URL" ]; then
                print_success "Using proxy: $PROXY_URL" "使用代理: $PROXY_URL"
            else
                print_success "Using direct GitHub" "使用直连 GitHub"
            fi
            return 0
        fi
        print_info "Failed to connect to $test_url" "无法连接到 $test_url"
    done
    print_warning "All proxy checks failed; using direct GitHub" "所有代理检查失败，使用直连 GitHub"
    return 0
}

# Get latest beta version from api.github.com only
get_beta_version() {
    local temp_file url
    # Reset VERSION to avoid using a stale value on API failures
    VERSION=""
    temp_file="$(mktemp 2>/dev/null || echo "${TMPDIR:-/tmp}/ddns.releases.$$")"
    url="https://api.github.com/repos/$REPO/tags?per_page=1"

    print_info "Fetching version from api.github.com..." "正在从 api.github.com 获取版本信息..."
    
    # Simple download and parse - let download_file handle errors and retries
    if download_file "$url" "$temp_file" && [ -s "$temp_file" ]; then
        # Tags API returns objects with a "name" field for the tag
        VERSION=$(grep -m1 -o '"name":"[^"]*"' "$temp_file" | cut -d '"' -f4)
    fi

    # Cleanup temp file
    rm -f "$temp_file" 2>/dev/null || true

    # Validate result
    if [ -z "$VERSION" ]; then
        print_error "Failed to get version from GitHub API. Try using 'latest' instead." "无法从 GitHub API 获取版本，请尝试使用 'latest'。"
        exit 1
    fi

    print_success "Found version: $VERSION" "找到版本: $VERSION"
}

# Build binary filename based on OS and architecture
build_binary_name() {
    case "$OS" in
        "linux")
            BINARY_FILE="ddns-${LIBC}-linux_${ARCH}"
            ;;
        "mac")
            BINARY_FILE="ddns-mac-${ARCH}"
            ;;
    esac
    print_info "Target binary: $BINARY_FILE" "二进制文件: $BINARY_FILE"
}

# Download and install binary
install_binary() {
    # Build release path and original GitHub URL
    local download_url
    if [ "$VERSION" = "latest" ]; then
        download_url="${PROXY_URL}https://github.com/$REPO/releases/latest/download/$BINARY_FILE"
    else
        download_url="${PROXY_URL}https://github.com/$REPO/releases/download/$VERSION/$BINARY_FILE"
    fi

    local temp_file
    temp_file="$(mktemp 2>/dev/null || echo "${TMPDIR:-/tmp}/ddns.bin.$$")"
    print_info "Downloading DDNS binary..." "正在下载 DDNS 二进制文件..."
    print_info "URL: $download_url"

    if ! download_file "$download_url" "$temp_file"; then
        print_error "Failed to download binary" "下载二进制文件失败"
        print_error "Make sure the version $VERSION exists and supports your platform" "请确保版本 $VERSION 存在并支持您的平台"
        rm -f "$temp_file" 2>/dev/null || true
        exit 1
    fi
    
    # Verify download
    if [ ! -f "$temp_file" ] || [ ! -s "$temp_file" ]; then
        print_error "Downloaded file is empty or missing" "下载的文件为空或缺失"
        rm -f "$temp_file" 2>/dev/null || true
        exit 1
    fi
    
    # Check if install directory exists and create if needed
    if [ ! -d "$INSTALL_DIR" ]; then
        print_info "Creating installation directory: $INSTALL_DIR" "创建安装目录: $INSTALL_DIR"
        if ! mkdir -p "$INSTALL_DIR"; then
            print_error "Failed to create installation directory: $INSTALL_DIR" "创建安装目录失败: $INSTALL_DIR"
            print_error "Try running with sudo or choose a different directory" "请尝试使用 sudo 运行或选择其他目录"
            exit 1
        fi
    fi
    
    # Install binary
    local target_path="$INSTALL_DIR/$BINARY_NAME"
    
    # Check if already exists and not forcing
    if [ -f "$target_path" ] && [ "$FORCE_INSTALL" = false ]; then
        if [ "$USER_VERSION_SPECIFIED" = true ]; then
            print_warning "DDNS already installed at $target_path; version specified, proceeding to overwrite" "DDNS 已安装在 $target_path；已指定版本，继续覆盖"
        else
            print_warning "DDNS is already installed at $target_path" "DDNS 已安装在 $target_path"
            print_info "Use --force to overwrite or run: $BINARY_NAME --version" "使用 --force 覆盖或运行: $BINARY_NAME --version"
            exit 0
        fi
    fi
    
    print_info "Installing binary to $target_path" "正在安装二进制文件到 $target_path"
    
    # Make executable before moving
    chmod +x "$temp_file"
    
    # Try to move directly, auto-detect if sudo is needed
    if ! mv "$temp_file" "$target_path" 2>/dev/null; then
        # Check if it's a permission issue and try with sudo
        if [ ! -w "$(dirname "$target_path")" ]; then
            print_warning "Permission denied, trying with sudo..." "权限被拒绝，尝试使用 sudo..."
            if command -v sudo >/dev/null 2>&1; then
                if sudo mv "$temp_file" "$target_path"; then
                    print_info "Successfully installed with sudo" "使用 sudo 安装成功"
                else
                    print_error "Failed to install binary even with sudo" "即使使用 sudo 也无法安装二进制文件"
                    rm -f "$temp_file" 2>/dev/null || true
                    exit 1
                fi
            else
                print_error "Failed to install binary: Permission denied" "安装二进制文件失败: 权限被拒绝"
                print_error "Please run this script with administrator privileges" "请以管理员权限运行此脚本"
                rm -f "$temp_file" 2>/dev/null || true
                exit 1
            fi
        else
            print_error "Failed to install binary" "安装二进制文件失败"
            rm -f "$temp_file" 2>/dev/null || true
            exit 1
        fi
    fi
    
    print_success "DDNS installed successfully!" "DDNS 安装成功！"
}

# Uninstall binary
uninstall_binary() {
    print_info "Starting uninstallation..." "开始卸载..."
    local target_path=""

    # If a specific install dir is provided, prefer that
    if [ -n "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/$BINARY_NAME" ]; then
        target_path="$INSTALL_DIR/$BINARY_NAME"
    fi

    # Otherwise look up in PATH
    if [ -z "$target_path" ]; then
        local resolved
        resolved=$(command -v "$BINARY_NAME" 2>/dev/null || true)
        if [ -n "$resolved" ] && [ -f "$resolved" ]; then
            target_path="$resolved"
        fi
    fi

    # Fallback to default location
    if [ -z "$target_path" ]; then
        if [ -f "/usr/local/bin/$BINARY_NAME" ]; then
            target_path="/usr/local/bin/$BINARY_NAME"
        fi
    fi

    if [ -z "$target_path" ]; then
        print_warning "ddns not found. Nothing to uninstall." "未找到 ddns，无需卸载"
        return 0
    fi

    print_info "Removing: $target_path" "正在移除: $target_path"
    if rm -f "$target_path" 2>/dev/null; then
        print_success "Uninstalled ddns" "已卸载 ddns"
        return 0
    fi

    # Try with sudo when permission denied
    if command -v sudo >/dev/null 2>&1; then
        if sudo rm -f "$target_path"; then
            print_success "Uninstalled ddns (with sudo)" "已卸载 ddns (使用 sudo)"
            return 0
        fi
        print_error "Failed to uninstall ddns even with sudo" "即使使用 sudo 也无法卸载 ddns"
        return 1
    else
        print_error "Permission denied removing $target_path. Try running with sudo." "删除 $target_path 权限被拒绝，请尝试使用 sudo 运行"
        return 1
    fi
}

# Verify installation
verify_installation() {
    local target_path="$INSTALL_DIR/$BINARY_NAME"
    
    if [ -x "$target_path" ]; then
        print_success "Installation verified!" "安装验证成功！"
        print_info "DDNS version: $($target_path --version 2>/dev/null || echo 'Version check failed')" "DDNS 版本: $($target_path --version 2>/dev/null || echo '版本检查失败')"
        print_info "Binary location: $target_path" "二进制文件位置: $target_path"
        
        # Check if installation directory is in PATH
        if echo "$PATH" | grep -q "$INSTALL_DIR"; then
            print_success "Installation directory is in PATH" "安装目录已在 PATH 中"
            print_info "You can now run: $BINARY_NAME --help" "现在可以运行: $BINARY_NAME --help"
        else
            print_warning "Installation directory is not in PATH" "安装目录不在 PATH 中"
            print_info "Add to PATH temporarily: export PATH=\"$INSTALL_DIR:\$PATH\"" "临时添加到 PATH: export PATH=\"$INSTALL_DIR:\$PATH\""
            print_info "Add to shell profile permanently:" "永久添加到 shell 配置文件:"
            
            # Suggest adding to shell profile
            if [ -n "$BASH_VERSION" ]; then
                print_info "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.bashrc"
            elif [ -n "$ZSH_VERSION" ]; then
                print_info "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.zshrc"
            else
                print_info "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.profile"
            fi
            
            print_info "Or run directly: $target_path --help" "或直接运行: $target_path --help"
        fi
    else
        print_error "Installation verification failed" "安装验证失败"
        exit 1
    fi
}

# Parse command line arguments
parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --help|-h)
                show_usage
                exit 0
                ;;
            --install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --proxy)
                PROXY_URL="$2"
                shift 2
                ;;
            --force)
                FORCE_INSTALL=true
                shift
                ;;
            --uninstall)
                UNINSTALL_MODE=true
                shift
                ;;
            -*)
                print_error "Unknown option: $1" "未知选项: $1"
                show_usage
                exit 1
                ;;
            *)
                if [ -z "$VERSION" ]; then
                    VERSION="$1"
                    USER_VERSION_SPECIFIED=true
                else
                    print_error "Too many arguments" "参数过多"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Normalize PROXY_URL: add https:// if missing, ensure trailing slash
    if [ -n "$PROXY_URL" ]; then
        case "$PROXY_URL" in
            http://*|https://*) : ;; # keep
            *) PROXY_URL="https://$PROXY_URL" ;;
        esac
        PROXY_URL="${PROXY_URL%/}/"
    fi
    
    # Set default version if not specified
    if [ -z "$VERSION" ]; then
        VERSION="latest"
    fi
}

# Main installation function
main() {
    print_info "DDNS One-Click Installation Script" "DDNS 一键安装脚本"
    print_info "======================================="
    
    # Parse arguments
    parse_args "$@"
    
    # Uninstall early: no network required
    if [ "$UNINSTALL_MODE" = true ]; then
        uninstall_binary
        print_success "======================================="
        print_success "DDNS uninstallation completed" "DDNS 卸载完成"
        exit 0
    fi

    # System checks (only needed for install)
    check_os
    detect_arch
    detect_libc
    check_download_tool
    # Auto-select proxy only when not explicitly set
    if [ -z "$PROXY_URL" ]; then
        find_working_proxy
    fi
    
    # Version handling
    # For 'latest', skip API query and use GitHub's latest download URL directly.
    # For 'beta', fetch the latest available tag via API.
    if [ "$VERSION" = "beta" ]; then
        get_beta_version
    fi
    
    # Build and install
    build_binary_name
    install_binary
    verify_installation
    
    print_success "======================================="
    print_success "DDNS installation completed" "DDNS 安装完成"
    print_info "Get started: $BINARY_NAME --help" "开始使用: $BINARY_NAME --help"
    print_info "Documentation: https://ddns.newfuture.cc/" "文档: https://ddns.newfuture.cc/"
}

# Run main function with all arguments
main "$@"
