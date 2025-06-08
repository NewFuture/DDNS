ARG HOST_VERSION=3.21
# https://alpinelinux.org/releases/
# https://hub.docker.com/_/alpine/tags

FROM alpine:${HOST_VERSION} AS base
RUN find /lib /usr/lib /usr/local/lib -name '*.so*' | sed 's|.*/||' | awk '{print "--noinclude-dlls="$0}' > nuitka_exclude_so.txt

FROM python:3.10-alpine${HOST_VERSION} AS builder
# RUN apk add --no-cache python3-dev py3-pip py3-cffi py3-zstandard py3-ordered-set patchelf clang ccache
RUN apk add --no-cache patchelf clang ccache

ENV NUITKA=https://github.com/Nuitka/Nuitka/archive/main.zip
RUN python3 -m pip install cffi==1.16.0 "${NUITKA}" --break-system-packages

WORKDIR /build
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
RUN mkdir docker-bin && cp dist/ddns docker-bin/ && cp .build/entrypoint.sh docker-bin/

FROM alpine:${HOST_VERSION}
LABEL maintainer="NN708, newfuture"
COPY --from=builder /build/docker-bin/* /bin/
WORKDIR /ddns
ENTRYPOINT [ "/bin/entrypoint.sh" ]
