set -ex
platform=${1:-linux/amd64}
libc=${2:-musl}
filePath=${3:-dist/ddns}

volume=$(dirname $(realpath "$filePath"))
file=$(basename "$filePath")

if [ "$libc" = "glibc" ]; then
    container="ubuntu:19.04"
else
    case $platform in
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
            # v6 不支持直接测试，需要qume仿真
            echo "::warn::untested platform '$platform' ($libc)"
            exit 0
            ;;
        *)
        container="alpine"
        ;;
    esac
fi

docker run --rm -v="$volume:/dist" --platform=$platform $container /dist/$file -h
docker run --rm -v="$volume:/dist" --platform=$platform $container /dist/$file --version
docker run --rm -v="$volume:/dist" --platform=$platform $container sh -c "/dist/$file || test -f config.json"
# delete to avoid being reused
docker image rm $container
