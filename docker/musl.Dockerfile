ARG PYTHON_VERSION=3.8
ARG NUITKA_VERSION=main
# build with alpine3.12 (musl-libc 1.1.24)
FROM python:${PYTHON_VERSION}-alpine3.12 AS base-builder

RUN apk add --update --no-cache clang ccache build-base ca-certificates patchelf
RUN update-ca-certificates
ARG NUITKA_VERSION
RUN python3 -m pip install --no-cache-dir https://github.com/Nuitka/Nuitka/archive/${NUITKA_VERSION}.zip #--break-system-packages

WORKDIR /app

FROM base-builder AS builder
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

# test the binary
FROM alpine
COPY --from=builder /ddns /bin/ddns
RUN ddns -h
RUN ddns || test -f config.json

FROM busybox:musl
COPY --from=builder /ddns /bin/ddns
RUN ddns -h
RUN ddns || test -f config.json

# export the binary
FROM scratch AS export
COPY --from=builder /ddns /ddns
