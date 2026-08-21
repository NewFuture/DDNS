# Provider Development Guide

## Scope

This directory contains DNS provider implementations. Apply these rules to new
providers and changes to existing providers.

## Implementation

- Use `BaseProvider` when the API can find zones and records and create or
  update records. Use `SimpleProvider` only for direct update-only APIs.
- Preserve Python 2.7 and Python 3 compatibility and standard-library-only
  runtime dependencies. Use existing compatibility patterns and type comments;
  do not use annotations, f-strings, or Python-3-only syntax.
- Use the inherited `_http()` transport and `_mask_sensitive_data()` for
  request details that may contain credentials. Do not add a separate HTTP
  client or log secrets.
- Follow adjacent providers for error handling, record types, TTL, line/route,
  and return values. Keep provider failures handled and logged rather than
  exposing provider responses or credentials.
- Register the canonical ID and intentional aliases in
  `ddns/provider/__init__.py`.

## Parity

Provider behavior is not complete until all affected surfaces agree:

- Add the provider and credential metadata to
  `ddns/config/field-model.json`.
- Update both `provider` and `dns` enums in `schema/v4.1.json`, and every
  `--dns` CLI choice surface.
- Add deterministic mocked tests in `tests/test_provider_<provider>.py`;
  mock `_http()` and cover supported operations, response failures, and record
  matching without credentials or live API access.
- Add matching Chinese and English pages in `docs/providers/` and
  `docs/en/providers/`. Update both provider indexes, both locale navigation
  entries in `docs/.vitepress/config.mts`, and `docs/llms.txt`.

## Validation

Run focused validation after replacing `<provider>`:

```sh
python -m unittest tests.test_provider_<provider> -v
ruff check ddns/provider/<provider>.py tests/test_provider_<provider>.py
ruff format --check ddns/provider/<provider>.py tests/test_provider_<provider>.py
```

Then run full validation:

```sh
python -m unittest discover tests -v
ruff check .
ruff format --check .
npm --prefix docs run build
```

Run the documentation build only when its dependencies are already available.
Do not install dependencies or use live credentials to validate a provider.
