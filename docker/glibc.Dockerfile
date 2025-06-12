# prebuilt image to speed up: ghcr.io/newfuture/nuitka-buider:glibc-master
ARG BUILDER=base-builder
ARG PYTHON_VERSION=3.8
ARG NUITKA_VERSION=main


# build with debian-slim (glibc 2.28)
FROM python:${PYTHON_VERSION}-slim-buster AS base-builder
# 安装必要的依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ccache \
    patchelf \
    build-essential \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/* /tmp/* /var/log/*
# 安装Python依赖
ARG NUITKA_VERSION
RUN python3 -m pip install --no-cache-dir --prefer-binary \
    "https://github.com/Nuitka/Nuitka/archive/${NUITKA_VERSION}.zip" \
    --disable-pip-version-check \
    --break-system-packages \
    && rm -rf /var/cache/* /tmp/* /var/log/* /root/.cache
WORKDIR /app


FROM ${BUILDER} AS builder
# 拷贝项目文件
COPY . .
RUN python3 .github/patch.py
# 构建二进制文件，glibc arm下编译会报错，
# collect2: fatal error: ld terminated with signal 11 [Segmentation fault], core dumped compilation terminated.
# FATAL: Error, the C compiler 'gcc' crashed with segfault. Consider upgrading it or using '--clang' option.
RUN apk add clang
RUN python3 -O -m nuitka run.py \
    --mode=onefile\    
    --output-filename=ddns\
    --output-dir=dist\
    --remove-output \
    --nofollow-import-to=tkinter,unittest,pydoc,doctest,distutils,setuptools,lib2to3,test,idlelib,lzma \
    --file-description="DDNS Client 自动更新域名解析到本机IP" \
    --linux-icon=doc/img/ddns.svg \
    --lto=yes \
    $(if [ "$(uname -m)" = "aarch64" ]; then echo "--clang"; fi)
RUN cp dist/ddns /bin/ddns \
    && cp dist/ddns /ddns


# export the binary
FROM scratch AS export
COPY --from=builder /ddns /ddns
