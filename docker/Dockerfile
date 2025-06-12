# https://alpinelinux.org/releases/
# https://hub.docker.com/_/alpine/tags
ARG HOST_VERSION=3.20
# prebuilt image to speed up to speed up: ghcr.io/newfuture/nuitka-buider:master
ARG BUILDER=base-builder
ARG PYTHON_VERSION=3.8
ARG NUITKA_VERSION=main  # 新增此行，定义构建参数并提供默认值


# https://hub.docker.com/_/python/tags?name=3.8-alpine3.20
FROM python:${PYTHON_VERSION}-alpine${HOST_VERSION} AS base-builder
# RUN apk add --no-cache python3-dev py3-pip py3-cffi py3-zstandard py3-ordered-set patchelf clang ccache
RUN apk add --no-cache patchelf gcc ccache libffi-dev build-base zstd-libs\
    && rm -rf /var/lib/apt/lists/* /var/cache/* /tmp/* /var/log/*
ARG NUITKA_VERSION
RUN python3 -m pip install --no-cache-dir --prefer-binary \
    "https://github.com/Nuitka/Nuitka/archive/${NUITKA_VERSION}.zip" \
    --disable-pip-version-check \
    --break-system-packages \
    && rm -rf /var/cache/* /tmp/* /var/log/* /root/.cache
WORKDIR /app

FROM alpine:${HOST_VERSION} AS base
RUN find /lib /usr/lib /usr/local/lib -name '*.so*' | sed 's|.*/||' | awk '{print "--noinclude-dlls="$0}' > nuitka_exclude_so.txt

FROM ${BUILDER} AS builder
COPY . .
COPY --from=base /nuitka_exclude_so.txt nuitka_exclude_so.txt
RUN python3 .github/patch.py
RUN python3 -O -m nuitka run.py \
    --mode=onefile\
    --output-dir=./dist\
    --no-deployment-flag=self-execution\
    --output-filename=ddns\
    --remove-output\
    --include-module=dns.dnspod --include-module=dns.alidns --include-module=dns.dnspod_com --include-module=dns.dnscom --include-module=dns.cloudflare --include-module=dns.he --include-module=dns.huaweidns --include-module=dns.callback\
    --product-name=DDNS\
    --lto=yes \
    --onefile-tempdir-spec="{TEMP}/{PRODUCT}_{VERSION}" \
    --python-flag=no_site,no_asserts,no_docstrings,isolated,static_hashes\
    --nofollow-import-to=tkinter,unittest,pydoc,doctest,distutils,setuptools,lib2to3,test,idlelib,lzma \
    --noinclude-dlls=liblzma.so.* \
    $(cat nuitka_exclude_so.txt)
RUN mkdir /output && cp dist/ddns /output/
COPY docker/entrypoint.sh /output/

FROM alpine:${HOST_VERSION}
COPY --from=builder /output/* /bin/
WORKDIR /ddns
ENTRYPOINT [ "/bin/entrypoint.sh" ]
