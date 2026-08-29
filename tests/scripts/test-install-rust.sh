#!/bin/sh
set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/ddns-rs-installer-test.XXXXXX")"
test_root="$temp_dir"
trap 'rm -rf "$temp_dir"' EXIT HUP INT TERM
HOME="$temp_dir/home"
export HOME
mkdir -p "$HOME"
DDNS_RS_INSTALLER_TEST=1
export DDNS_RS_INSTALLER_TEST
. "$repo_root/docs/public/install-rust.sh"

test "$INSTALL_DIR" = "$HOME/.local/bin"
test "$(asset_name linux x64)" = "ddns-rs-linux-x64"
test "$(asset_name linux arm64)" = "ddns-rs-linux-arm64"
test "$(asset_name macos x64)" = "ddns-rs-macos-x64"
test "$(asset_name macos arm64)" = "ddns-rs-macos-arm64"
test "$(download_url latest ddns-rs-linux-x64)" = "https://github.com/NewFuture/DDNS/releases/latest/download/ddns-rs-linux-x64"
test "$(download_url v4.0.2 ddns-rs-linux-x64)" = "https://github.com/NewFuture/DDNS/releases/download/v4.0.2/ddns-rs-linux-x64"
if asset_name windows x64 >/dev/null 2>&1; then
    echo "unsupported platform unexpectedly mapped" >&2
    exit 1
fi

printf '%s\n' \
    '[' \
    '  {"tag_name":"v4.0.2",' \
    '   "prerelease":false},' \
    '  {"tag_name":"v4.1.0-beta.1",' \
    '   "prerelease":true}' \
    ']' \
    > "$temp_dir/releases.json"
test "$(beta_version_from_file "$temp_dir/releases.json")" = "v4.1.0-beta.1"
printf '%s\n' '#!/bin/sh' 'echo ddns-rs test' > "$temp_dir/ddns-rs-linux-x64"
expected="$(sha256sum "$temp_dir/ddns-rs-linux-x64" | awk '{print $1}')"
printf '%s  %s\n' "$expected" "ddns-rs-linux-x64" > "$temp_dir/ddns-rs-linux-x64.sha256"
verify_checksum "$temp_dir/ddns-rs-linux-x64" "$temp_dir/ddns-rs-linux-x64.sha256"
printf '%s  %s\n' "0000000000000000000000000000000000000000000000000000000000000000" "ddns-rs-linux-x64" > "$temp_dir/invalid.sha256"
if verify_checksum "$temp_dir/ddns-rs-linux-x64" "$temp_dir/invalid.sha256"; then
    echo "invalid checksum unexpectedly passed" >&2
    exit 1
fi

INSTALL_DIR="$temp_dir/bin"
install_binary "$temp_dir/ddns-rs-linux-x64"
test -x "$temp_dir/bin/ddns-rs"
test ! -e "$temp_dir/bin/ddns"
uninstall_binary
test ! -e "$temp_dir/bin/ddns-rs"

fixture_dir="$temp_dir/fixture"
mkdir -p "$fixture_dir"
printf '%s\n' '#!/bin/sh' 'echo ddns-rs v-test' > "$fixture_dir/ddns-rs-linux-x64"
fixture_hash="$(sha256sum "$fixture_dir/ddns-rs-linux-x64" | awk '{print $1}')"
printf '%s  %s\n' "$fixture_hash" "ddns-rs-linux-x64" > "$fixture_dir/ddns-rs-linux-x64.sha256"

detect_platform() {
    OS="linux"
    ARCH="x64"
}

download_file() {
    case "$1" in
        *.sha256) cp "$fixture_dir/ddns-rs-linux-x64.sha256" "$2" ;;
        *) cp "$fixture_dir/ddns-rs-linux-x64" "$2" ;;
    esac
}

VERSION="latest"
FORCE_INSTALL=false
UNINSTALL_MODE=false
VERIFY_CHECKSUM="auto"
e2e_install_dir="$temp_dir/e2e-bin"
main v-test --install-dir "$e2e_install_dir" --verify
test -x "$e2e_install_dir/ddns-rs"
test ! -e "$e2e_install_dir/ddns"

verify_checksum() {
    return 2
}
VERSION="latest"
FORCE_INSTALL=false
UNINSTALL_MODE=false
VERIFY_CHECKSUM="auto"
main v-test --install-dir "$test_root/no-checksum-tool"
test -x "$test_root/no-checksum-tool/ddns-rs"

echo "Rust installer offline tests passed"
