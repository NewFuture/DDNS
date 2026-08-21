---
applyTo: "ddns/**/*.py,run.py,tests/**/*.py"
---

# Runtime Python Rules

These rules apply to shipped DDNS Python code and its tests. Repository maintenance tooling under `tools/` and Python-only `.github` scripts may use modern Python as documented by their nearest `AGENTS.md`.

## Compatibility and dependencies

- Support Python 2.7 and current Python 3 versions.
- Use only Python standard-library runtime modules.
- Do not add f-strings, annotations, `async`/`await`, assignment expressions, structural pattern matching, or other Python 3-only syntax.
- Use type comments: `# type: (...) -> ReturnType`.
- Use `.format()` or `%` formatting.
- Preserve `u""` literals when Python 2 Unicode semantics require them; use a line-local `# fmt: skip` when Ruff would remove the prefix.
- Handle `str`/`unicode`, `bytes`, queue imports, URL libraries, and `unittest.mock` using existing compatibility patterns.

## Architecture and reuse

- Reuse helpers and patterns from adjacent modules before adding abstractions.
- Provider classes inherit `BaseProvider` or `SimpleProvider`.
- Use provider `_http()` and the shared HTTP/config/cache utilities rather than third-party or duplicate implementations.
- Keep imports at module scope unless a real circular/optional dependency requires a local import.
- Preserve public CLI/config/provider/cache behavior unless a human explicitly approves a compatibility change.

## Error handling and logging

- Catch specific exceptions where recovery is expected.
- Do not add bare `except` or broad success-shaped fallbacks.
- At top-level boundaries, log unexpected failures with `logger.exception`.
- Do not expose credentials, authorization headers, configuration documents, or provider response secrets.
- Use `_mask_sensitive_data()` where provider request details may contain credentials.

## Testing

- Provider tests import from `base_test` and inherit `BaseProviderTestCase` where appropriate.
- Other tests import compatibility helpers from `tests/__init__.py`.
- Mock provider HTTP and public network access; do not require real credentials.
- Add focused success, failure, invalid-input, and compatibility coverage.
- Prefer existing test files and helpers before creating new ones.
- Keep tests deterministic: use events/fixtures instead of sleeps and external services.

## Validation

```bash
python -m unittest discover tests -v
ruff check .
ruff format --check .
```

Run the smallest relevant unittest target while iterating, then the full affected suite. Use `/AGENTS.md` for lane-specific validation.
