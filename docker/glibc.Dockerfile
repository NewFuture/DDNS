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
# 构建二进制文件
RUN python3 -O -m nuitka \
    --onefile \
    --output-dir=dist \
    --output-filename=ddns \
    --remove-output \
    --no-deployment-flag=self-execution \
    --include-module=dns.dnspod \
    --include-module=dns.alidns \
    --include-module=dns.dnspod_com \
    --include-module=dns.dnscom \
    --include-module=dns.cloudflare \
    --include-module=dns.he \
    --include-module=dns.huaweidns \
    --include-module=dns.callback \
    --nofollow-import-to=tkinter,unittest,pydoc,doctest,distutils,setuptools,lib2to3,test,idlelib,lzma \
    --product-name=DDNS \
    --onefile-tempdir-spec="{TEMP}/{PRODUCT}_{VERSION}" \
    --python-flag=no_site,no_asserts,no_docstrings,isolated,static_hashes \
    --file-description="DDNS Client 自动更新域名解析到本机IP" \
    --company-name="New Future" \
    --linux-icon=doc/img/ddns.svg
    run.py
RUN cp dist/ddns /bin/ddns \
    && cp dist/ddns /ddns


# export the binary
FROM scratch AS export
COPY --from=builder /ddns /ddns
