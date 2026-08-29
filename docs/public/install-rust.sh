#!/bin/sh
# Install the experimental Rust client without replacing the Python `ddns` command.
set -eu

REPO="${DDNS_RS_REPO:-NewFuture/DDNS}"
DEFAULT_INSTALL_DIR="${HOME:+$HOME/.local/bin}"
INSTALL_DIR="${DDNS_RS_INSTALL_DIR:-${DEFAULT_INSTALL_DIR:-/usr/local/bin}}"
BINARY_NAME="ddns-rs"
VERSION="latest"
FORCE_INSTALL=false
UNINSTALL_MODE=false
VERIFY_CHECKSUM="auto"

usage() {
    cat <<'EOF'
DDNS Rust client installer

Usage: install-rust.sh [latest|beta|VERSION] [OPTIONS]

Options:
  --install-dir PATH  Install to PATH (default: ~/.local/bin)
  --force             Replace an existing ddns-rs installation
  --verify            Require SHA-256 verification
  --no-verify         Do not download or verify the checksum
  --uninstall         Remove ddns-rs (never removes ddns)
  --help              Show this help

The default is latest. beta installs the latest prerelease.
EOF
}

asset_name() {
    case "$1/$2" in
        linux/x64) echo "ddns-rs-linux-x64" ;;
        linux/arm64) echo "ddns-rs-linux-arm64" ;;
        macos/x64) echo "ddns-rs-macos-x64" ;;
        macos/arm64) echo "ddns-rs-macos-arm64" ;;
        *) return 1 ;;
    esac
}

detect_platform() {
    case "$(uname -s)" in
        Linux) OS="linux" ;;
        Darwin) OS="macos" ;;
        *) echo "Unsupported operating system: $(uname -s)" >&2; return 1 ;;
    esac
    case "$(uname -m)" in
        x86_64|amd64) ARCH="x64" ;;
        arm64|aarch64) ARCH="arm64" ;;
        *) echo "Unsupported architecture: $(uname -m)" >&2; return 1 ;;
    esac
}

download_file() {
    url="$1"
    output="$2"
    if command -v curl >/dev/null 2>&1; then
        curl --fail --location --retry 3 --connect-timeout 20 "$url" -o "$output"
    elif command -v wget >/dev/null 2>&1; then
        wget -O "$output" "$url"
    else
        echo "curl or wget is required" >&2
        return 1
    fi
}

beta_version_from_file() {
    tr '{' '\n' < "$1" | awk '
        /"tag_name"[[:space:]]*:/ {
            tag = $0
            sub(/.*"tag_name"[[:space:]]*:[[:space:]]*"/, "", tag)
            sub(/".*/, "", tag)
        }
        /"prerelease"[[:space:]]*:[[:space:]]*true/ && tag != "" {
            print tag
            exit
        }
    '
}

beta_version() {
    temp_file="$(mktemp "${TMPDIR:-/tmp}/ddns-rs-releases.XXXXXX")"
    trap 'rm -f "$temp_file"' EXIT HUP INT TERM
    download_file "https://api.github.com/repos/$REPO/releases?per_page=20" "$temp_file"
    tag="$(beta_version_from_file "$temp_file")"
    rm -f "$temp_file"
    trap - EXIT HUP INT TERM
    test -n "$tag" || { echo "Could not determine the beta tag" >&2; return 1; }
    echo "$tag"
}

download_url() {
    version="$1"
    asset="$2"
    if [ "$version" = "latest" ]; then
        echo "https://github.com/$REPO/releases/latest/download/$asset"
    else
        echo "https://github.com/$REPO/releases/download/$version/$asset"
    fi
}

verify_checksum() {
    binary="$1"
    checksum_file="$2"
    expected_name="$(basename "$binary")"
    expected="$(awk -v name="$expected_name" '$2 == name { print $1; exit }' "$checksum_file")"
    test -n "$expected" || { echo "Checksum for $expected_name is missing" >&2; return 1; }

    if command -v sha256sum >/dev/null 2>&1; then
        actual="$(sha256sum "$binary" | awk '{print $1}')"
    elif command -v shasum >/dev/null 2>&1; then
        actual="$(shasum -a 256 "$binary" | awk '{print $1}')"
    else
        echo "SHA-256 tool is unavailable" >&2
        return 2
    fi

    test "$actual" = "$expected" || { echo "SHA-256 checksum mismatch for $expected_name" >&2; return 1; }
}

install_binary() {
    source_file="$1"
    target="$INSTALL_DIR/$BINARY_NAME"
    mkdir -p "$INSTALL_DIR"
    if [ -e "$target" ] && [ "$FORCE_INSTALL" != true ]; then
        echo "$target already exists; use --force to replace it" >&2
        return 1
    fi
    chmod 755 "$source_file"
    mv -f "$source_file" "$target"
}

uninstall_binary() {
    target="$INSTALL_DIR/$BINARY_NAME"
    if [ -e "$target" ]; then
        rm -f "$target"
        echo "Removed $target"
    else
        echo "ddns-rs is not installed in $INSTALL_DIR"
    fi
}

parse_args() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
            latest|beta|v*) VERSION="$1" ;;
            --install-dir)
                test "$#" -ge 2 || { echo "--install-dir requires a path" >&2; exit 1; }
                INSTALL_DIR="$2"
                shift
                ;;
            --force) FORCE_INSTALL=true ;;
            --verify) VERIFY_CHECKSUM=true ;;
            --no-verify) VERIFY_CHECKSUM=false ;;
            --uninstall) UNINSTALL_MODE=true ;;
            --help|-h) usage; exit 0 ;;
            *) echo "Unknown option or version: $1" >&2; usage >&2; exit 1 ;;
        esac
        shift
    done
}

main() {
    parse_args "$@"
    if [ "$UNINSTALL_MODE" = true ]; then
        uninstall_binary
        return
    fi

    detect_platform
    asset="$(asset_name "$OS" "$ARCH")" || { echo "Unsupported platform: $OS/$ARCH" >&2; exit 1; }
    if [ "$VERSION" = "beta" ]; then
        VERSION="$(beta_version)"
    fi

    temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/ddns-rs.XXXXXX")"
    trap 'rm -rf "$temp_dir"' EXIT HUP INT TERM
    binary="$temp_dir/$asset"
    checksum="$temp_dir/$asset.sha256"
    url="$(download_url "$VERSION" "$asset")"
    download_file "$url" "$binary"

    if [ "$VERIFY_CHECKSUM" != false ]; then
        if download_file "$url.sha256" "$checksum"; then
            if verify_checksum "$binary" "$checksum"; then
                :
            else
                verify_status=$?
                if [ "$verify_status" -eq 2 ] && [ "$VERIFY_CHECKSUM" = "auto" ]; then
                    echo "SHA-256 tool unavailable; installing without verification" >&2
                else
                    exit "$verify_status"
                fi
            fi
        elif [ "$VERIFY_CHECKSUM" = true ]; then
            echo "Checksum verification was requested but the checksum could not be downloaded" >&2
            exit 1
        else
            echo "Checksum unavailable; installing without verification" >&2
        fi
    fi

    install_binary "$binary"
    "$INSTALL_DIR/$BINARY_NAME" --version
    rm -rf "$temp_dir"
    trap - EXIT HUP INT TERM
}

if [ "${DDNS_RS_INSTALLER_TEST:-}" != "1" ]; then
    main "$@"
fi
