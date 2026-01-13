# prebuilt image to speed up: ghcr.io/newfuture/nuitka-buider:glibc-master
ARG BUILDER=base-builder
ARG PYTHON_VERSION=3.8
ARG NUITKA_VERSION=main


FROM python:${PYTHON_VERSION}-slim-buster AS base-builder
# 安装必要的依赖
# Use Debian archive for buster
RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list \
    && sed -i '/security.debian.org/d' /etc/apt/sources.list \
    && echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99no-check-valid-until
RUN apt-get update && apt-get install -y --no-install-recommends \
    ccache \
    patchelf \
    build-essential \
    libffi-dev \
    clang \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/* /tmp/* /var/log/*
# 安装Python依赖
ARG NUITKA_VERSION
RUN python3 -m pip install --no-cache-dir --prefer-binary \
    "https://github.com/Nuitka/Nuitka/archive/${NUITKA_VERSION}.zip" \
    --disable-pip-version-check \
    --break-system-packages \
    && rm -rf /var/cache/* /tmp/* /var/log/* /root/.cache
WORKDIR /app


FROM ${BUILDER} AS builder
# 拷贝项目文件
COPY run.py .github/patch.py docs/public/img/ddns.svg .
COPY ddns ddns
ARG GITHUB_REF_NAME
ENV GITHUB_REF_NAME=${GITHUB_REF_NAME}
RUN python3 patch.py
# 构建二进制文件，glibc arm下编译会报错，
RUN python3 -O -m nuitka run.py \
    --remove-output \
    --linux-icon=ddns.svg \
    $( [ "$(uname -m)" = "aarch64" ] || echo --lto=yes )
RUN cp dist/ddns /bin/ddns && cp dist/ddns /ddns


# export the binary
FROM scratch AS export
COPY --from=builder /ddns /ddns
