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
    # --break-system-packages \
    && rm -rf /var/cache/* /tmp/* /var/log/* /root/.cache
WORKDIR /app


FROM ${BUILDER} AS builder
COPY run.py .github/patch.py .
COPY ddns ddns
ENV GITHUB_REF_NAME
RUN python3 patch.py
RUN python3 -O -m nuitka run.py \
    --remove-output \
    --lto=yes
RUN cp dist/ddns /bin/ddns && cp dist/ddns /ddns


# export the binary
FROM scratch AS export
COPY --from=builder /ddns /ddns
