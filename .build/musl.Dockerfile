ARG HOST_VERSION=3.6

# Build a statically linked binary using Nuitka with musl libc
FROM alpine:${HOST_VERSION} AS builder

RUN apk add --update --no-cache python3-dev py3-pip clang ccache build-base ca-certificates wget cmake
RUN update-ca-certificates
COPY .github/install-patchelf.sh /tmp/install-patchelf.sh
RUN apk add --update --no-cache patchelf\
    || /tmp/install-patchelf.sh\
    || pip3 install patchelf==0.17.2.1
RUN python3 -m pip install zstandard  "https://github.com/Nuitka/Nuitka/archive/main.zip"

# 添加可靠的架构检测
RUN apk add --update --no-cache dpkg

WORKDIR /build
COPY . .
RUN python3 .build/patch.py
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
    --linux-icon=doc/img/ddns.svg 

RUN mkdir /DDNS \
    && ARCH=$(dpkg --print-architecture 2>/dev/null || echo $(uname -m)) \
    && ARCH_FIXED=$(echo ${ARCH} | tr '/' '_') \
    && cp dist/ddns /bin/ddns \
    && cp dist/ddns /DDNS/ddns-${ARCH_FIXED}

# test the binary
FROM alpine
COPY --from=builder /bin/ddns /bin/ddns
RUN ddns -h
RUN ddns || test -f config.json

# export the binary
FROM scratch AS export
COPY --from=builder /DDNS /out
