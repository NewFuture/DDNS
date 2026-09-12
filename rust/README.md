# DDNS Rust V5

`ddns-rs` is the Rust implementation for the next major version of
[NewFuture/DDNS](https://github.com/NewFuture/DDNS), developed on the `v5`
integration branch. Python maintenance stays on `master` / `v4`; Rust changes
target `v5`, not the stable Python branch.

The current development version is `5.0.0-alpha1`, not a published release.
The crate stays under `rust/` and the command remains `ddns-rs`; it does not yet
replace the stable Python `ddns` command.

## Current V5 scope

- All canonical Python DNS providers and their documented aliases: Cloudflare,
  AliDNS/ESA, DNSPod (China, global, and Tencent Cloud), EdgeOne, ClouDNS,
  DNS.COM, HE.net, Huawei DNS, NameSilo, No-IP, Callback, West.cn, and Debug
- IPv4 and IPv6
- Existing CLI options, `DDNS_*` environment variables, and Schema v4.1 files
- Local, remote, multiple, JSONC, and restricted Python-literal configurations
- `default`, `public`, numeric, `url:`, `regex:`, `cmd:`, and `shell:` address rule types
- Cache, proxy fallback, retries, custom CA files, and existing TLS policies
- One-shot updates on Linux, macOS, and Windows
- Embedded Web dashboard, configuration management, and in-process scheduled updates
- MCP stdio and HTTP transports, with `/mcp` also available on the Web listener

The `task` command and OS scheduler migration are not implemented yet. The Linux
amd64/arm64 container defaults to one-shot updates; `web` enables its in-process
scheduler. Manually disable old Python/host tasks before enabling Rust scheduled
updates: Rust does not detect or take over those tasks. Native artifacts
are named `ddns-rs-linux-x64`, `ddns-rs-linux-arm64`, `ddns-rs-macos-x64`,
`ddns-rs-macos-arm64`, and `ddns-rs-windows-x64.exe`. Linux uses static musl
targets so the same names work on glibc and musl distributions.

## Release preparation

The Rust CI validates `v5` commits and pull requests targeting `v5`.
`Prepare Rust V5` builds and verifies native artifacts with SHA-256 checksums
and a two-platform OCI archive. Changes to the Cargo version files or this
workflow, embedded Web assets/field model, or Rust Dockerfile on `v5` automatically
start preparation without needing a tag. It also
accepts manual preparation on `v5` or a canonical `v5.*` tag matching both Cargo
version files. Outputs stay in
GitHub Actions artifacts; it does not create a release, upload release assets,
or push images to a registry.

No V5 tag or public release is created by this preparation. Before the first
public V5 tag, separate Python/Rust release selection in the installers and
download service, and explicitly prepare a Rust publication workflow. Until
then, use source builds or CI artifacts rather than `latest` / `beta` downloads.
The retained `docs/public/install-rust.sh` is future release tooling, not a
working V5 download channel. V5 docs builds do not deploy over the stable site.

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

## Validate

```bash
cargo fmt --manifest-path rust/Cargo.toml --check
cargo clippy --manifest-path rust/Cargo.toml --locked --all-targets --all-features -- -D warnings
cargo test --manifest-path rust/Cargo.toml --locked
```

See the [Rust development guide](../docs/en/dev/rust.md) for architecture and the
feature-parity roadmap.
