#!/bin/sh
#
# One-click installation script for DDNS
# 一键安装脚本
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash
#   wget -qO- https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash
#
# With version:
#   curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash -s -- v4.0.2
#   curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash -s -- beta
#   curl -fsSL https://raw.githubusercontent.com/NewFuture/DDNS/master/install.sh | bash -s -- latest
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
FORCE_INSTALL=false

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

# Proxy/mirror sites for China users
GITHUB_MIRRORS="https://github.com https://hub.gitmirror.com https://proxy.gitwarp.com https://gh.200112.xyz"

# Print colored messages
print_info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$1"
}

print_success() {
    printf "${GREEN}[SUCCESS]${NC} %s\n" "$1"
}

print_warning() {
    printf "${YELLOW}[WARNING]${NC} %s\n" "$1"
}

print_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1"
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
    --force              强制安装，即使已存在
    --help               显示此帮助信息

示例:
    $0                    # 安装最新稳定版本
    $0 beta              # 安装最新测试版本
    $0 v4.0.2            # 安装指定版本
    $0 latest --force    # 强制重新安装最新版本

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
    --force              Force installation even if already exists
    --help               Show this help message

Examples:
    $0                    # Install latest stable version
    $0 beta              # Install latest beta version
    $0 v4.0.2            # Install specific version
    $0 latest --force    # Force reinstall latest version

EOF
    fi
}

# Check if running on supported OS
check_os() {
    case "$(uname -s)" in
        Linux*)  OS="linux" ;;
        Darwin*) OS="mac" ;;
        *)
            print_error "Unsupported operating system: $(uname -s)"
            print_error "This script only supports Linux and macOS"
            exit 1
            ;;
    esac
    print_info "Detected OS: $OS"
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
            print_error "Unsupported architecture: $arch"
            exit 1
            ;;
    esac
    print_info "Detected architecture: $ARCH"
}

# Detect libc type on Linux
detect_libc() {
    if [ "$OS" != "linux" ]; then
        return
    fi
    
    if ldd --version 2>&1 | grep -i glibc > /dev/null; then
        LIBC="glibc"
    elif ldd --version 2>&1 | grep -i musl > /dev/null; then
        LIBC="musl"
    else
        # Default to glibc for most distributions
        LIBC="glibc"
    fi
    print_info "Detected libc: $LIBC"
}

# Check for download tool (curl or wget)
check_download_tool() {
    if command -v curl > /dev/null 2>&1; then
        DOWNLOAD_TOOL="curl"
        print_info "Using curl for downloads"
    elif command -v wget > /dev/null 2>&1; then
        DOWNLOAD_TOOL="wget"
        print_info "Using wget for downloads"
    else
        print_error "Neither curl nor wget found. Please install one of them."
        exit 1
    fi
}

# Download file using available tool
download_file() {
    local url="$1"
    local output="$2"
    
    if [ "$DOWNLOAD_TOOL" = "curl" ]; then
        curl -fsSL "$url" -o "$output"
    else
        wget -q "$url" -O "$output"
    fi
}

# Test GitHub connectivity and find working mirror
find_working_mirror() {
    print_info "Testing GitHub connectivity..."
    
    for mirror in $GITHUB_MIRRORS; do
        print_info "Testing mirror: $mirror"
        if [ "$DOWNLOAD_TOOL" = "curl" ]; then
            if curl -fsSL --connect-timeout 10 --max-time 10 "$mirror" > /dev/null 2>&1; then
                GITHUB_URL="$mirror"
                print_success "Using mirror: $GITHUB_URL"
                return 0
            fi
        else
            if wget -q --timeout=5 -O /dev/null "$mirror" > /dev/null 2>&1; then
                GITHUB_URL="$mirror"
                print_success "Using mirror: $GITHUB_URL"
                return 0
            fi
        fi
    done
    
    print_error "All GitHub mirrors are unreachable"
    exit 1
}

# Get latest version from GitHub API
get_latest_version() {
    local api_url
    local version_type="$1"
    
    case "$version_type" in
        "beta")
            # Get the latest pre-release (beta)
            if [ "$GITHUB_URL" = "https://github.com" ]; then
                api_url="https://api.github.com/repos/$REPO/releases"
            else
                # For mirrors, try to use their API endpoint or fallback to main API
                api_url="$GITHUB_URL/api/repos/$REPO/releases"
            fi
            ;;
        *)
            # Get the latest stable release
            if [ "$GITHUB_URL" = "https://github.com" ]; then
                api_url="https://api.github.com/repos/$REPO/releases/latest"
            else
                # For mirrors, try to use their API endpoint or fallback to main API
                api_url="$GITHUB_URL/api/repos/$REPO/releases/latest"
            fi
            ;;
    esac
    
    print_info "Fetching version information from GitHub API..."
    
    local temp_file="/tmp/ddns_releases.json"
    if ! download_file "$api_url" "$temp_file"; then
        # Fallback to main GitHub API if mirror API fails
        print_warning "Mirror API failed, falling back to main GitHub API..."
        case "$version_type" in
            "beta")
                api_url="https://api.github.com/repos/$REPO/releases"
                ;;
            *)
                api_url="https://api.github.com/repos/$REPO/releases/latest"
                ;;
        esac
        
        if ! download_file "$api_url" "$temp_file"; then
            print_error "Failed to fetch release information"
            exit 1
        fi
    fi
    
    if [ "$version_type" = "beta" ]; then
        # For beta, find the latest pre-release
        VERSION=$(grep -o '"tag_name": *"[^"]*"' "$temp_file" | head -1 | cut -d'"' -f4)
    else
        # For latest stable
        VERSION=$(grep -o '"tag_name": *"[^"]*"' "$temp_file" | head -1 | cut -d'"' -f4)
    fi
    
    rm -f "$temp_file"
    
    if [ -z "$VERSION" ]; then
        print_error "Failed to parse version information"
        exit 1
    fi
    
    print_success "Found version: $VERSION"
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
    print_info "Target binary: $BINARY_FILE"
}

# Download and install binary
install_binary() {
    local download_url="$GITHUB_URL/$REPO/releases/download/$VERSION/$BINARY_FILE"
    local temp_file="/tmp/ddns_binary"
    
    print_info "Downloading DDNS binary..."
    print_info "URL: $download_url"
    
    if ! download_file "$download_url" "$temp_file"; then
        print_error "Failed to download binary"
        print_error "Make sure the version $VERSION exists and supports your platform"
        exit 1
    fi
    
    # Verify download
    if [ ! -f "$temp_file" ] || [ ! -s "$temp_file" ]; then
        print_error "Downloaded file is empty or missing"
        exit 1
    fi
    
    # Check if install directory exists and create if needed
    if [ ! -d "$INSTALL_DIR" ]; then
        print_info "Creating installation directory: $INSTALL_DIR"
        if ! mkdir -p "$INSTALL_DIR"; then
            print_error "Failed to create installation directory: $INSTALL_DIR"
            print_error "Try running with sudo or choose a different directory"
            exit 1
        fi
    fi
    
    # Install binary
    local target_path="$INSTALL_DIR/$BINARY_NAME"
    
    # Check if already exists and not forcing
    if [ -f "$target_path" ] && [ "$FORCE_INSTALL" = false ]; then
        print_warning "DDNS is already installed at $target_path"
        print_info "Use --force to overwrite or run: $BINARY_NAME --version"
        exit 0
    fi
    
    print_info "Installing binary to $target_path"
    if ! cp "$temp_file" "$target_path"; then
        print_error "Failed to install binary"
        print_error "You may need to run this script with sudo"
        exit 1
    fi
    
    # Make executable
    chmod +x "$target_path"
    
    # Clean up
    rm -f "$temp_file"
    
    print_success "DDNS installed successfully!"
}

# Verify installation
verify_installation() {
    local target_path="$INSTALL_DIR/$BINARY_NAME"
    
    if [ -x "$target_path" ]; then
        print_success "Installation verified!"
        print_info "DDNS version: $($target_path --version 2>/dev/null || echo 'Version check failed')"
        print_info "Binary location: $target_path"
        
        # Check if installation directory is in PATH
        if echo "$PATH" | grep -q "$INSTALL_DIR"; then
            print_success "Installation directory is in PATH"
            print_info "You can now run: $BINARY_NAME --help"
        else
            print_warning "Installation directory is not in PATH"
            print_info "Add to PATH temporarily: export PATH=\"$INSTALL_DIR:\$PATH\""
            print_info "Add to shell profile permanently:"
            
            # Suggest adding to shell profile
            if [ -n "$BASH_VERSION" ]; then
                print_info "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.bashrc"
            elif [ -n "$ZSH_VERSION" ]; then
                print_info "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.zshrc"
            else
                print_info "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.profile"
            fi
            
            print_info "Or run directly: $target_path --help"
        fi
    else
        print_error "Installation verification failed"
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
            --force)
                FORCE_INSTALL=true
                shift
                ;;
            -*)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                if [ -z "$VERSION" ]; then
                    VERSION="$1"
                else
                    print_error "Too many arguments"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Set default version if not specified
    if [ -z "$VERSION" ]; then
        VERSION="latest"
    fi
}

# Main installation function
main() {
    if [ "$LANGUAGE" = "zh" ]; then
        print_info "DDNS 一键安装脚本"
        print_info "======================================="
    else
        print_info "DDNS One-Click Installation Script"
        print_info "======================================="
    fi
    
    # Parse arguments
    parse_args "$@"
    
    # System checks
    check_os
    detect_arch
    detect_libc
    check_download_tool
    find_working_mirror
    
    # Version handling
    if [ "$VERSION" = "latest" ] || [ "$VERSION" = "beta" ]; then
        get_latest_version "$VERSION"
    fi
    
    # Build and install
    build_binary_name
    install_binary
    verify_installation
    
    print_success "======================================="
    print_success "DDNS installation completed!"
    print_info "Get started: $BINARY_NAME --help"
    print_info "Documentation: https://ddns.newfuture.cc/"
}

# Run main function with all arguments
main "$@"