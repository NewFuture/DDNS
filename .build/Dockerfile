FROM alpine:latest
WORKDIR /build
COPY . .
RUN apk add py3-pip python3-dev patchelf build-base libffi-dev
RUN pip3 install -U nuitka --break-system-packages
RUN python3 -m nuitka run.py \
    --mode=onefile\
    --output-dir=./dist\
    --no-deployment-flag=self-execution\
    --output-filename=ddns\
    --remove-output\
    --include-module=dns.dnspod --include-module=dns.alidns --include-module=dns.dnspod_com --include-module=dns.dnscom --include-module=dns.cloudflare --include-module=dns.he --include-module=dns.huaweidns --include-module=dns.callback\
    --product-name=DDNS\
    --python-flag=no_site,no_asserts,no_docstrings,isolated,static_hashes\
    --nofollow-import-to=unittest,pydoc\
    --onefile-tempdir-spec="{CACHE_DIR}/{PRODUCT}/{VERSION}"
RUN mkdir bin
RUN cp dist/ddns bin/
RUN cp .build/entrypoint.sh bin/

FROM alpine:latest
LABEL maintainer="NN708, newfuture"
WORKDIR /ddns
COPY --from=0 /build/bin/* /bin/
ENTRYPOINT [ "/bin/entrypoint.sh" ]
