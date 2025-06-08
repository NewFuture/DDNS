#!/usr/bin/env sh
set -e

VERSION="0.18.0"
BASE_URL="https://github.com/NixOS/patchelf/releases/download/${VERSION}"
INSTALL_DIR="/usr/local/bin"

# 优先检测 dpkg（Debian/Ubuntu）
if command -v dpkg >/dev/null 2>&1; then
  ARCH=$(dpkg --print-architecture)
else
  ARCH=$(uname -m)
fi

# 映射到 patchelf 预编译版本名称
case "$ARCH" in
  x86_64 | amd64)     FILE="patchelf-${VERSION}-x86_64.tar.gz" ;;
  i386 | i686)        FILE="patchelf-${VERSION}-i686.tar.gz" ;;
  aarch64 | arm64)    FILE="patchelf-${VERSION}-aarch64.tar.gz" ;;
  armv7l | armhf)     FILE="patchelf-${VERSION}-armv7l.tar.gz" ;;
  ppc64le)            FILE="patchelf-${VERSION}-ppc64le.tar.gz" ;;
  riscv64)            FILE="patchelf-${VERSION}-riscv64.tar.gz" ;;
  s390x)              FILE="patchelf-${VERSION}-s390x.tar.gz" ;;
  *)
    echo "❌ Unsupported or unrecognized architecture: $ARCH"
    exit 1
    ;;
esac

echo "🧠 Detected architecture: $ARCH → $FILE"
echo "⬇️ Downloading $FILE ..."
wget "${BASE_URL}/${FILE}"

echo "📦 Extracting..."
tar -xzf "${FILE}"

BIN=$(find . -type f -name patchelf | head -n 1)

if [ ! -f "$BIN" ]; then
  echo "❌ patchelf binary not found after extraction."
  exit 1
fi

echo "🚀 Installing patchelf to ${INSTALL_DIR} ..."
install -m 755 "$BIN" "${INSTALL_DIR}/patchelf"

echo "🧹 Cleaning up..."
rm -rf "$FILE" patchelf*

echo "✅ patchelf installed:"
patchelf --version
