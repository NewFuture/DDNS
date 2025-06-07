ARG HOST_VERSION=3.6
FROM alpine:${HOST_VERSION}

RUN apk add --update --no-cache python3-dev py3-pip patchelf clang ccache build-base
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

CMD [ "ddns -h", "cp /DDNS/* /dist" ]
