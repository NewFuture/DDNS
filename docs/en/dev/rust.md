# Rust client development

`ddns-rs` is an experimental implementation maintained alongside the Python
`ddns` client. The MVP performs one synchronization per process and does not
replace the stable Python `ddns` command or default installer.

## Current support

| Capability | Status |
| --- | --- |
| All Python DNS providers and documented compatibility aliases (Cloudflare, AliDNS/ESA, DNSPod, EdgeOne, ClouDNS, DNS.COM, HE.net, Huawei DNS, NameSilo, No-IP, Callback, West.cn, and Debug) | Supported |
| IPv4/IPv6 and every existing address rule type | Supported; `regex:` uses Rust syntax |
| CLI, `DDNS_*`, local/remote/multiple configs, v4.1 `providers` | Supported |
| JSON comments and restricted Python data literals | Supported |
| Cache, proxy fallback, retries, TLS, and custom CA files | Supported |
| Linux amd64/arm64 Docker image | Tag publishing pushes `ghcr.io/newfuture/ddns-rs`; it runs only `ddns-rs`, without a scheduler |
| Linux x64/arm64, macOS x64/arm64, Windows x64 Release assets | Tag publishing creates `ddns-rs-*`, each with a `.sha256` checksum; Linux uses static musl targets |
| `task`, Web, and MCP | Planned |

## Build and run

Use the current stable Rust toolchain:

```bash
cargo build --manifest-path rust/Cargo.toml --release --locked
rust/target/release/ddns-rs --help
rust/target/release/ddns-rs -c config.json
```

The Windows artifact is `rust\target\release\ddns-rs.exe`.

## Architecture

- `cli.rs`: compatible options, aliases, and list rules without a CLI framework.
- `config/`: environment, JSONC, restricted Python literals, v4.1 expansion, and precedence.
- `http.rs`: synchronous `ureq`/rustls transport, proxies, retries, TLS, and redaction.
- `ip.rs`: IPv4/IPv6 discovery and rule fallback.
- `cache.rs`: a versioned cache independent from the Python cache.
- `provider/`: shared CRUD orchestration and all DNS providers.
- `update.rs`: deterministic execution with continued attempts and aggregated failures.

Production code forbids unsafe code and does not use an async runtime, a generic
error framework, or a mock framework. Provider tests inject an HTTP client, and
integration tests only access local fixtures.

## Validation

```bash
cargo fmt --manifest-path rust/Cargo.toml --check
cargo clippy --manifest-path rust/Cargo.toml --locked --all-targets --all-features -- -D warnings
cargo test --manifest-path rust/Cargo.toml --locked
```

CI also builds, tests, and packages binaries on Linux x64/arm64, Windows x64,
and macOS x64/arm64; it builds and smoke-tests the Docker image offline on
Linux x64/arm64.

## Security boundaries

- `ssl=auto` warns and retries once without certificate verification only after a
  classified certificate-validation error. Prefer `ssl=true` in production.
- `cmd:` and `shell:` in remote configurations execute local commands. Load only
  trusted configuration URLs.
- `regex:` uses Rust `regex` syntax and does not support Python look-around or
  backreferences. Incompatible patterns return an explicit error.
- A reused custom `cache` path writes Rust data to the sibling `<path>.ddns-rs`
  file and never overwrites the Python cache.
- The Python-literal parser accepts only dictionaries, lists/tuples, strings,
  numbers, `True`, `False`, and `None`; it cannot execute expressions.
- Logs redact tokens and their percent-encoded forms. Cache files contain no credentials.

## Parity roadmap

1. Port systemd, cron, launchd, and schtasks support.
2. Port the Web dashboard and MCP server.
3. Consider renaming the binary to `ddns` only after complete parity and a
   separate stability period.
