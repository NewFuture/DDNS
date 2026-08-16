---
applyTo: 'rust/**'
---

# Rust contribution rules

- Use the current stable Rust toolchain and Edition 2024.
- Keep the Rust client synchronous unless a measured requirement justifies an async runtime.
- Prefer the standard library and existing dependencies. New crates require a concrete portability or correctness need and must use minimal features.
- Do not add unsafe code. The crate forbids it.
- Keep credentials out of logs, errors, fixtures, and cache files.
- Provider and HTTP tests must use local fixtures or injected clients; never call live DNS provider APIs.
- Preserve the documented Python-compatible CLI, environment, and configuration behavior for supported MVP features.
- Run before committing:

  ```bash
  cargo fmt --manifest-path rust/Cargo.toml --check
  cargo clippy --manifest-path rust/Cargo.toml --locked --all-targets --all-features -- -D warnings
  cargo test --manifest-path rust/Cargo.toml --locked
  ```
