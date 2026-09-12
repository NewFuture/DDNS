# Rust V5 client development

`ddns-rs` is the Rust implementation for DDNS V5, integrated on the `v5` branch.
Python maintenance continues on `master` / `v4`; Rust feature PRs should target
`v5`. The current development version is `5.0.0-alpha1`. It supports one-shot
updates and Web/MCP services, is not published, and does not replace the stable
Python `ddns` command or default installer.

## Current support

| Capability | Status |
| --- | --- |
| All Python DNS providers and documented compatibility aliases (Cloudflare, AliDNS/ESA, DNSPod, EdgeOne, ClouDNS, DNS.COM, HE.net, Huawei DNS, NameSilo, No-IP, Callback, West.cn, and Debug) | Supported |
| IPv4/IPv6 and every existing address rule type | Supported; `regex:` uses Rust syntax |
| CLI, `DDNS_*`, local/remote/multiple configs, v4.1 `providers` | Supported |
| JSON comments and restricted Python data literals | Supported |
| Cache, proxy fallback, retries, TLS, and custom CA files | Supported |
| Linux amd64/arm64 Docker image | Build and offline smoke coverage; preparation saves an OCI artifact without registry publication; `web` provides in-process scheduling |
| Linux x64/arm64, macOS x64/arm64, Windows x64 binaries | Preparation saves `ddns-rs-*` and `.sha256` Actions artifacts; Linux uses static musl targets |
| Web dashboard, configuration management, and in-process scheduling | Supported; one local config, interval 1..1440 minutes |
| MCP stdio, standalone HTTP, and Web `/mcp` | Supported; modern protocol and legacy stdio compatibility |
| `task` and OS task detection/takeover | Not ported; manually disable old Python/host tasks |

## V5 branch and release preparation

Keep the `rust/` layout, `ddns-rs` command, and existing configuration boundaries;
do not remove Python yet. The versions in `rust/Cargo.toml` and `rust/Cargo.lock`
must match. Changes to the version files, preparation workflow, embedded Web
assets/field model, or Rust Dockerfile on `v5` automatically run `Prepare Rust V5`
without requiring a tag. It also accepts manual preparation on `v5` or canonical
`v5.*` tags matching Cargo, then produces verified native and two-platform OCI
artifacts. It does not create Releases, upload release assets, or push images.
Preparation accepts only V5 prereleases with an `alpha`, `beta`, or `rc` suffix,
not stable versions.
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

The experimental `install-rust.sh` runs `--version` on the temporary binary
before moving it into place. An artifact that cannot run leaves the existing
`ddns-rs` untouched, even with `--force`.

## Web and MCP

```bash
ddns-rs web -c config.json --host 127.0.0.1 --port 8000 --interval 5 --open
ddns-rs mcp -c config.json
ddns-rs mcp -c config.json --transport http --host 127.0.0.1 --port 8001
```

`web` accepts `-c FILE`, `--host HOST`, `--port PORT`, `--http-token TOKEN`,
repeatable `--http-origin ORIGIN`, `--interval MINUTES`, and `--open` (open the
browser). Without an explicit subcommand, top-level `--interval` or a root
configuration `interval` selects Web mode. The in-process scheduler accepts
1..1440 minutes and runs only while the process is alive.

The dashboard reads, validates, and saves the full configuration, manages
backups/restores, reports status, and triggers synchronization. Web and MCP use
the same service. They require a single local configuration file, not remote or
multiple configuration sources. Web validation uses the compatible Rust runtime;
it does not promise full Python runtime parity.

`mcp` defaults to newline-delimited stdio. `--transport http` serves standalone
Streamable HTTP at `/mcp`; Web exposes the same endpoint on its own listener.
Modern MCP uses protocol `2026-07-28`; legacy `2025-11-25` is supported over stdio
only. Both expose the Python tool names `get_ddns_status` and
`update_dns_records`.

HTTP listeners default to loopback. A non-loopback bind requires
`--http-token TOKEN`; clients authenticate with `Authorization: Bearer TOKEN`.
Use repeated `--http-origin ORIGIN` flags for additional allowed browser origins.
Origin checks and authentication apply to both Web and MCP HTTP. Do not expose
plain HTTP on an untrusted network; use a trusted TLS reverse proxy or tunnel.
Status responses exclude credentials, but the authenticated configuration API
intentionally returns the full configuration, including provider credentials.
Treat listener tokens, configuration files, and backups as secrets. With no
listener token on loopback, local access is still a trust boundary.
The listener token grants sensitive configuration access and DNS update authority,
not read-only monitoring. Web updates execute `cmd:`/`shell:` rules from the
authenticated local configuration with the process user's permissions; grant
access only to trusted administrators.

The binary embeds the existing `web/` dashboard assets and
`ddns/config/field-model.json` at compile time; no frontend server or Python
runtime is needed to serve them. Rebuild after changing these inputs. Source
builds require the repository layout, not an isolated copy of `rust/`.

**Migration limitation:** `task`, OS scheduler detection, and automatic takeover
are not implemented. Manually disable old Python/host systemd, cron, launchd, or
schtasks jobs before enabling Rust scheduled updates to avoid duplicate runs.
The Web scheduler does not install or replace a host service. Existing Rust
`regex:` and separate-cache limits still apply. `log_format` and `log_datefmt`
are accepted for configuration compatibility, not Python formatting parity.

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
The configuration layer rejects only empty domain entries, allowing `debug`
and `callback` to use single labels such as `localhost`. Provider-specific
domain constraints are handled by each provider.
Integer log levels support both `--log-level -5` and `--log-level=-5`.

Cloudflare and Tencent Cloud lookups use `Result<Option<_>>` to distinguish absence
from request failure. Only valid empty lists or known lookup-miss error codes permit further lookup or
creation. Cloudflare and Tencent Cloud mutation responses must contain a valid
result identifier; malformed responses are not cached as successful updates.
An enum selects the service and API version for Tencent DNSPod, EdgeOne
acceleration, and EdgeOne DNS instead of freely combining strings and booleans.

NameSilo and ClouDNS try the next candidate zone only for documented zone-lookup
misses. Authentication, permission, HTTP, and malformed-response errors propagate
instead of becoming "zone not found". ClouDNS, Huawei, and NameSilo record lookups
reject malformed collections and records missing matching fields to avoid
duplicate creation; ClouDNS still accepts both `{}` and `[]` as empty collections.
Huawei signing and requests use the same RFC3986 query string, encoding spaces
as `%20` rather than `+` without a second form-encoding pass. Form encoding for
other providers is unchanged.

AliDNS and ESA send updates when `extra` is supplied even if the address and TTL
are unchanged. The existing unchanged-record shortcut remains when no extras
are supplied.

Both DNSPod endpoints merge `extra` after standard mutation parameters, preserving
its override priority. IP extraction validates complete addresses with the
standard-library `IpAddr` type and supports compact labels such as
`IP:2001:db8::1` and `address:192.0.2.1`; malformed IPv6 literals are not truncated
into usable fragments.
`regex:` matches from the start of the extracted original address, preserving
IPv6 zero padding, case, and compression for matching. For example, `^2001:0db8:`
matches `2001:0db8::1`; the returned value remains a validated `IpAddr`.
`local` and numeric indices exclude loopback and unspecified addresses within
the requested family before indexing from `0` in the original order. No usable
address or an out-of-range index returns an error; private and link-local
addresses remain selectable.

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
- Logs and errors replace registered IDs, tokens, and their percent-encoded and form-encoded forms
  with the constant `***` marker, without retaining credential prefixes or suffixes.
  Cache files contain no credentials.
- DNS.COM signed request bodies are not logged, echoed current signatures are
  redacted from API error messages, and JSON errors omit the raw response.
  HTTP errors for sensitive requests retain only the status code.
- URL diagnostics hide userinfo, non-root paths, query values, and fragments to
  protect credentials embedded in callback or remote-configuration paths. The
  actual request URL is unchanged.

## Parity roadmap

1. Port systemd, cron, launchd, and schtasks support.
2. Validate Web/MCP compatibility in long-running deployments and platform migrations.
3. Consider renaming the binary to `ddns` only after complete parity and a
   separate stability period.
