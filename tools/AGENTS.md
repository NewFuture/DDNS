# Repository Tooling Guide

## Scope

`tools/` contains repository maintenance code. It is not shipped as part of the
DDNS runtime and does not need Python 2.7 compatibility.

## Python

- Target Python 3.12 or newer.
- Prefer the standard library. Add a tooling dependency only when it removes
  substantial complexity and is already managed by the project.
- Use type annotations, `pathlib`, `subprocess.run`, and modern Python syntax.
- Resolve paths from the repository root and support Windows, Linux, and macOS.
- Never mutate user configuration, credentials, DNS records, releases, or
  repository settings.

## Tests

- Put tests in `tools/tests/` using `test_*.py`.
- Use temporary directories and injected command runners for filesystem or
  subprocess behavior.
- Keep tests offline and deterministic.
- Fail explicitly when a required tool or expected repository surface is
  missing.

## Validation

```sh
python3 -m unittest discover tools/tests -p "test_*.py" -v
ruff check tools
ruff format --check tools
```
