set -ex
platform=${1:-linux/amd64}
libc=${2:-musl}
filePath=${3:-dist/ddns}

volume=$(dirname $(realpath "$filePath"))
file=$(basename "$filePath")

if [ "$libc" = "glibc" ]; then
    platform_flag="--platform=$platform"
    container="ubuntu:19.04"
else
    platform_flag=''
    case $platform in
        linux/amd64)
            container="openwrt/rootfs:x86_64"
            ;;
        linux/386 | linux/i386)
            container="openwrt/rootfs:i386_pentium4"
            ;;
        linux/arm64)
            container="openwrt/rootfs:aarch64_generic"
            ;;
        linux/arm/v8)
            container="openwrt/rootfs:armsr-armv8"
            ;;
        linux/arm/v7)
            container="openwrt/rootfs:armsr-armv7"
            ;;
        linux/arm/v6)
            container="alpine"
            platform_flag="--platform=linux/arm/v6"
            ;;
        *)
        echo "::warning::untested platform '$platform' ($libc)"
        exit 1
        ;;
    esac
fi

docker run --rm -v="$volume:/dist" $platform_flag $container /dist/$file -h
docker run --rm -v="$volume:/dist" $platform_flag $container sh -c "/dist/$file && test -f config.json"
