FROM rust:alpine AS builder

WORKDIR /build/rust
COPY rust/Cargo.toml rust/Cargo.lock ./
COPY rust/src ./src
COPY web/index.html web/dashboard.js web/dashboard.css web/ddns.svg /build/web/
COPY ddns/config/field-model.json /build/ddns/config/field-model.json
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/build/rust/target \
    cargo build --release --locked \
    && cp target/release/ddns-rs /tmp/ddns-rs

FROM alpine:3.24

RUN apk add --no-cache ca-certificates \
    && addgroup -S ddns \
    && adduser -S -G ddns -h /ddns ddns
COPY --from=builder /tmp/ddns-rs /usr/local/bin/ddns-rs

USER ddns
WORKDIR /ddns
ENTRYPOINT ["ddns-rs"]
