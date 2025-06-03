FROM alpine
VOLUME [ "/data" ]

# RUN find /lib /usr/lib -name '*.so*' | sed 's|.*/||' | awk '{print "--noinclude-dlls="$0}' > nuitka_exclude_so.txt
RUN apk add py3-pip python3-dev patchelf build-base libffi-dev wget musl-dev gcc chrpath

ENV PYTHON_VER=3.12.10
ENV PYTHON_LIB_VER=3.12

RUN wget https://www.python.org/ftp/python/$PYTHON_VER/Python-$PYTHON_VER.tgz && tar -xzf Python-$PYTHON_VER.tgz
WORKDIR Python-$PYTHON_VER
# RUN wget https://github.com/xxh/xxh/raw/refs/heads/master/portable-musl-alpine/Setup.local -P Modules/
COPY .build/Setup.local Modules/
RUN ./configure LDFLAGS="-static" --disable-shared
RUN make LDFLAGS="-static" LINKFORSHARED=" "
RUN cp libpython$PYTHON_LIB_VER.a /usr/lib

WORKDIR /build
COPY . .
RUN pip3 install "https://github.com/Nuitka/Nuitka/archive/main.zip" --break-system-packages
RUN python3 .build/patch.py
ENV LDFLAGS="-static -l:libpython3.12.a"
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
RUN mkdir docker-bin && cp dist/ddns docker-bin/ && cp .build/entrypoint.sh docker-bin/

FROM alpine
LABEL maintainer="NN708, newfuture"
WORKDIR /ddns
COPY --from=0 /build/docker-bin/* /bin/
ENTRYPOINT [ "/bin/entrypoint.sh" ]
