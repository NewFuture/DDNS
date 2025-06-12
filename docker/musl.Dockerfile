# use the prebuid base builder to speed up: ghcr.io/newfuture/nuitka-buider:musl-master
ARG BUILDER=base-builder
ARG PYTHON_VERSION=3.8
ARG NUITKA_VERSION=main


# build with alpine3.12 (musl-libc 1.1.24)
FROM python:${PYTHON_VERSION}-alpine3.12 AS base-builder
RUN apk add --update --no-cache gcc ccache build-base ca-certificates patchelf \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/* /var/cache/* /tmp/* /var/log/*

ARG NUITKA_VERSION
RUN python3 -m pip install --no-cache-dir --prefer-binary \
    "https://github.com/Nuitka/Nuitka/archive/${NUITKA_VERSION}.zip" \
    --disable-pip-version-check \
    --break-system-packages \
    && rm -rf /var/cache/* /tmp/* /var/log/* /root/.cache
WORKDIR /app


FROM ${BUILDER} AS builder
COPY . .
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
    --noinclude-dlls=liblzma.so.*
RUN cp dist/ddns /bin/ddns \
    && cp dist/ddns /ddns


# export the binary
FROM scratch AS export
COPY --from=builder /ddns /ddns
