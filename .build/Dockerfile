FROM alpine
WORKDIR /build
COPY . .
RUN find /lib /usr/lib -name '*.so*' | sed 's|.*/||' | awk '{print "--noinclude-dlls="$0}' > nuitka_exclude_so.txt
RUN apk add py3-pip python3-dev patchelf build-base libffi-dev
RUN pip3 install -U nuitka --break-system-packages
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

FROM alpine
LABEL maintainer="NN708, newfuture"
WORKDIR /ddns
COPY --from=0 /build/docker-bin/* /bin/
ENTRYPOINT [ "/bin/entrypoint.sh" ]
