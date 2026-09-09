# Rust V5 client development

`ddns-rs` is the Rust implementation for DDNS V5, integrated on the `v5` branch.
Python maintenance continues on `master` / `v4`; Rust feature PRs should target
`v5`. The current development version is `5.0.0-alpha1`. It performs one
synchronization per process, is not published, and does not replace the stable
Python `ddns` command or default installer.

## Current support

| Capability | Status |
| --- | --- |
| All Python DNS providers and documented compatibility aliases (Cloudflare, AliDNS/ESA, DNSPod, EdgeOne, ClouDNS, DNS.COM, HE.net, Huawei DNS, NameSilo, No-IP, Callback, West.cn, and Debug) | Supported |
| IPv4/IPv6 and every existing address rule type | Supported; `regex:` uses Rust syntax |
| CLI, `DDNS_*`, local/remote/multiple configs, v4.1 `providers` | Supported |
| JSON comments and restricted Python data literals | Supported |
| Cache, proxy fallback, retries, TLS, and custom CA files | Supported |
| Linux amd64/arm64 Docker image | Build and offline smoke coverage; preparation saves an OCI artifact without registry publication or a scheduler |
| Linux x64/arm64, macOS x64/arm64, Windows x64 binaries | Preparation saves `ddns-rs-*` and `.sha256` Actions artifacts; Linux uses static musl targets |
| `task`, Web, and MCP | Planned |

## V5 branch and release preparation

Keep the `rust/` layout, `ddns-rs` command, and existing configuration boundaries;
do not remove Python yet. The versions in `rust/Cargo.toml` and `rust/Cargo.lock`
must match. Changes to the version files or preparation workflow on `v5`
automatically run `Prepare Rust V5` without requiring a tag. It also accepts
manual preparation on `v5` or canonical `v5.*` tags matching Cargo, then produces verified native and two-platform OCI
artifacts. It does not create Releases, upload release assets, or push images.
V5 documentation builds do not deploy over the stable site. The Python publisher
retained on this branch rejects `v5.*` inputs; stable-branch publishing
configuration is unchanged.

There is no installable V5 release yet; use source or CI artifacts. Before the
first public V5 tag, isolate Python/Rust version selection in installers and
the download service, and separately confirm the Rust publication workflow.
Do not use repository-wide `latest` / `beta` downloads as V5 install channels yet.

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

Compatibility handling stays at the CLI and configuration boundary. Inside the
core, providers use the `ProviderId` enum and aliases are parsed once. Providers
use trait objects only for runtime dispatch and borrow the synchronous HTTP
client; each update request borrows its domain, address, and provider extras
instead of copying the full configuration per domain. Provider-specific
`extra` values remain dynamic JSON because their fields are defined by each DNS
API.

Cloudflare and Tencent Cloud lookups use `Result<Option<_>>` to distinguish absence
from request failure. Only valid empty lists or known lookup-miss error codes permit further lookup or
creation. Cloudflare and Tencent Cloud mutation responses must contain a valid
result identifier; malformed responses are not cached as successful updates.
An enum selects the service and API version for Tencent DNSPod, EdgeOne
acceleration, and EdgeOne DNS instead of freely combining strings and booleans.

Both DNSPod endpoints merge `extra` after standard mutation parameters, preserving
its override priority. IP extraction validates complete addresses with the
standard-library `IpAddr` type and supports compact labels such as
`IP:2001:db8::1` and `address:192.0.2.1`; malformed IPv6 literals are not truncated
into usable fragments.

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
- URL diagnostics hide userinfo, non-root paths, query values, and fragments to
  protect credentials embedded in callback or remote-configuration paths. The
  actual request URL is unchanged.

## Parity roadmap

1. Port systemd, cron, launchd, and schtasks support.
2. Port the Web dashboard and MCP server.
3. Consider renaming the binary to `ddns` only after complete parity and a
   separate stability period.
