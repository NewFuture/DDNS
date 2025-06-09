# build with debian-slim (glibc 2.28)
FROM python:3.10-slim-buster AS base-builder

# 安装必要的依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    ccache \
    patchelf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/*


# 安装Python依赖
ENV NUITKA_VERSION=${NUITKA_VERSION:-main}
RUN python3 -m pip install --no-cache-dir "https://github.com/Nuitka/Nuitka/archive/${NUITKA_VERSION}.zip" --break-system-packages

WORKDIR /app

FROM base-builder AS builder
# 拷贝项目文件
COPY . .

RUN python3 .github/patch.py
# 构建二进制文件
RUN python -m nuitka \
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
    --lto=yes \
    --onefile-tempdir-spec="{TEMP}/{PRODUCT}_{VERSION}" \
    --python-flag=no_site,no_asserts,no_docstrings,isolated,static_hashes \
    --file-description="DDNS Client 自动更新域名解析到本机IP" \
    --company-name="New Future" \
    --linux-icon=doc/img/ddns.svg \
    run.py

RUN cp dist/ddns /bin/ddns \
    && cp dist/ddns /ddns

# test the binary
FROM ubuntu:20.04
COPY --from=builder /ddns /bin/ddns
RUN ddns -h
RUN ddns || test -f config.json

FROM ubuntu:22.04
COPY --from=builder /ddns /bin/ddns
RUN ddns -h
RUN ddns || test -f config.json

FROM ubuntu:24.04
COPY --from=builder /ddns /bin/ddns
RUN ddns -h
RUN ddns || test -f config.json

FROM busybox:glibc
COPY --from=builder /ddns /bin/ddns
RUN ddns -h
RUN ddns || test -f config.json

# export the binary
FROM scratch AS export
COPY --from=builder /ddns /ddns
