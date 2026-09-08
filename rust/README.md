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
- One update run per process on Linux, macOS, and Windows

The `task`, `web`, and `mcp` commands are not implemented yet. The Linux
amd64/arm64 container runs `ddns-rs` once and has no scheduler. Native artifacts
are named `ddns-rs-linux-x64`, `ddns-rs-linux-arm64`, `ddns-rs-macos-x64`,
`ddns-rs-macos-arm64`, and `ddns-rs-windows-x64.exe`. Linux uses static musl
targets so the same names work on glibc and musl distributions.

## Release preparation

The Rust CI validates `v5` commits and pull requests targeting `v5`.
`Prepare Rust V5` builds and verifies native artifacts with SHA-256 checksums
and a two-platform OCI archive. Changes to the Cargo version files or this
workflow on `v5` automatically start preparation without needing a tag. It also
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

## Validate

```bash
cargo fmt --manifest-path rust/Cargo.toml --check
cargo clippy --manifest-path rust/Cargo.toml --locked --all-targets --all-features -- -D warnings
cargo test --manifest-path rust/Cargo.toml --locked
```

See the [Rust development guide](../docs/en/dev/rust.md) for architecture and the
feature-parity roadmap.
