#!/bin/sh

set -eu

if [ "${E2E_DOCKER_WRAPPER:-}" = "1" ]; then
    : "${E2E_DOCKER_BINARY:?E2E_DOCKER_BINARY is required}"
    : "${E2E_DOCKER_IMAGE:?E2E_DOCKER_IMAGE is required}"
    : "${E2E_DOCKER_PLATFORM:?E2E_DOCKER_PLATFORM is required}"

    binary=$(realpath "$E2E_DOCKER_BINARY")
    binary_dir=$(dirname "$binary")
    binary_name=$(basename "$binary")
    workdir=$(pwd -P)
    ddns_env=$(mktemp)
    trap 'rm -f "$ddns_env"' 0
    trap 'exit 130' 2
    trap 'exit 143' 15
    env | awk '/^DDNS_[A-Za-z0-9_]*=/ && !/^DDNS_E2E_/ { print }' > "$ddns_env"

    set +e
    docker run \
        --rm \
        --interactive \
        --network host \
        --volume "$binary_dir:/dist:ro" \
        --volume "$workdir:$workdir" \
        --workdir "$workdir" \
        --platform "$E2E_DOCKER_PLATFORM" \
        --env HOME \
        --env USERPROFILE \
        --env TMPDIR \
        --env TEMP \
        --env TMP \
        --env PYTHONIOENCODING \
        --env PYTHONUNBUFFERED \
        --env-file "$ddns_env" \
        "$E2E_DOCKER_IMAGE" \
        "/dist/$binary_name" \
        "$@"
    status=$?
    set -e
    exit "$status"
fi

platform=${1:-linux/amd64}
libc=${2:-musl}
file_path=${3:-dist/ddns}
binary=$(realpath "$file_path")
volume=$(dirname "$binary")
file=$(basename "$binary")
test_scripts=$(dirname "$(realpath "$0")")

if [ "$libc" = "glibc" ]; then
    container="ubuntu:19.04"
else
    case "$platform" in
        linux/amd64)
            container="openwrt/rootfs:x86_64"
            ;;
        linux/386 | linux/i386)
            container="openwrt/rootfs:i386_pentium4"
            platform="linux/i386_pentium4"
            ;;
        linux/arm64)
            container="openwrt/rootfs:aarch64_generic"
            platform="linux/aarch64_generic"
            ;;
        linux/arm/v8)
            container="openwrt/rootfs:armsr-armv8"
            platform="linux/aarch64_generic"
            ;;
        linux/arm/v7)
            container="openwrt/rootfs:armsr-armv7"
            platform="linux/arm_cortex-a15_neon-vfpv4"
            ;;
        linux/arm/v6)
            echo "::warning::ARMv6 runtime E2E skipped because qemu-user cannot reliably run the Nuitka onefile binary"
            exit 0
            ;;
        *)
            container="alpine:3.12"
            ;;
    esac
fi

export DDNS_E2E_EXECUTABLE="$test_scripts/test-in-docker.sh"
export E2E_DOCKER_BINARY="$binary"
export E2E_DOCKER_IMAGE="$container"
export E2E_DOCKER_PLATFORM="$platform"
export E2E_DOCKER_WRAPPER=1
export PYTHONIOENCODING=utf-8

echo "=== Offline binary E2E: $platform ($libc) in $container ==="
"$DDNS_E2E_EXECUTABLE" --help
"$DDNS_E2E_EXECUTABLE" --version
python3 -m unittest tests.e2e.TestCliE2E tests.e2e.TestMcpE2E -v

echo "=== Task command smoke test ==="
"$DDNS_E2E_EXECUTABLE" task --help
"$DDNS_E2E_EXECUTABLE" task --status

if [ "$libc" = "glibc" ]; then
    echo "Skipping task lifecycle in glibc container because systemd requires a privileged container."
else
    echo "=== Cron task lifecycle ==="
    docker run --rm \
        --volume "$volume:/dist:ro" \
        --volume "$test_scripts:/scripts:ro" \
        --platform "$platform" \
        "$container" \
        /scripts/test-task-cron.sh "/dist/$file"
fi

# A shared image tag can resolve to a different architecture for the next binary.
docker image rm "$container"
