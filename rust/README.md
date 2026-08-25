# DDNS Rust client

`ddns-rs` is the parallel, experimental Rust implementation of
[NewFuture/DDNS](https://github.com/NewFuture/DDNS). It does not replace the stable
Python `ddns` command.

## MVP support

- All canonical Python DNS providers and their documented aliases: Cloudflare,
  AliDNS/ESA, DNSPod (China, global, and Tencent Cloud), EdgeOne, ClouDNS,
  DNS.COM, HE.net, Huawei DNS, NameSilo, No-IP, Callback, West.cn, and Debug
- IPv4 and IPv6
- Existing CLI options, `DDNS_*` environment variables, and Schema v4.1 files
- Local, remote, multiple, JSONC, and restricted Python-literal configurations
- `default`, `public`, numeric, `url:`, `regex:`, `cmd:`, and `shell:` address rule types
- Cache, proxy fallback, retries, custom CA files, and existing TLS policies
- One update run per process on Linux, macOS, and Windows

The `task`, `web`, and `mcp` commands are not implemented yet. Tag publishing
pushes the Linux amd64/arm64 image as `ghcr.io/newfuture/ddns-rs`; it runs
`ddns-rs` once and has no scheduler. Separate Release assets are named `ddns-rs-linux-x64`,
`ddns-rs-linux-arm64`, `ddns-rs-macos-x64`, `ddns-rs-macos-arm64`, and
`ddns-rs-windows-x64.exe`, each with a `.sha256` checksum. Linux and macOS can
use `docs/public/install-rust.sh`; it installs only `ddns-rs`, never `ddns`.
The Linux assets use static musl targets so the same names work on glibc and
musl distributions.

## Build and run

```bash
cargo build --manifest-path rust/Cargo.toml --release --locked
rust/target/release/ddns-rs --help
rust/target/release/ddns-rs -c config.json
```

On Windows, the binary is `rust\target\release\ddns-rs.exe`.

Existing supported configurations can be reused without changing field names:

```bash
ddns-rs --dns cloudflare --token TOKEN --index4 public --ipv4 home.example.com
```

`ssl=auto` intentionally preserves the Python client's certificate-validation
fallback and is less secure than `ssl=true`. Remote configurations that contain
`cmd:` or `shell:` rules execute local commands; only load trusted configuration
URLs.

`regex:` rules use the Rust [`regex`](https://docs.rs/regex/) syntax. Python
look-around and backreferences are not supported; invalid patterns fail with an
explicit compatibility message.

When a reused configuration specifies a custom `cache` path, `ddns-rs` writes its
versioned format to the sibling `<path>.ddns-rs` file. The Python cache at the
configured path is never modified.

## Validate

```bash
cargo fmt --manifest-path rust/Cargo.toml --check
cargo clippy --manifest-path rust/Cargo.toml --locked --all-targets --all-features -- -D warnings
cargo test --manifest-path rust/Cargo.toml --locked
```

See the [Rust development guide](../docs/en/dev/rust.md) for architecture and the
feature-parity roadmap.
