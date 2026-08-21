---
name: provider-development
description: Implement or modify a DDNS DNS provider while keeping its code, metadata, schemas, tests, and bilingual documentation consistent.
---

# Provider Development

1. Read the root `AGENTS.md`, `ddns/provider/AGENTS.md`, the nearest similar
   provider, its tests, and the affected configuration and documentation files.
2. Research the provider's official API documentation. Record the
   authentication shape, permission scope, endpoints, zone and record lookup
   behavior, record create/update behavior, supported record types, and
   TTL/route constraints. Do not use credentials or mutate a live DNS record.
3. Choose `BaseProvider` for APIs that query zones and records before creating
   or updating them; choose `SimpleProvider` only for direct update-only APIs.
   Reuse `_http()`, masking, response handling, and Python 2.7-compatible
   standard-library patterns from adjacent providers.
4. Register the canonical provider ID and intentional aliases in
   `ddns/provider/__init__.py`. Update `ddns/config/field-model.json`, both
   `provider` and `dns` enums in `schema/v4.1.json`, and every `--dns` CLI
   choice surface.
5. Add deterministic mocked provider tests. Cover the supported request and
   response paths, matching behavior, and failures without network access or
   real credentials.
6. Add equivalent Chinese and English provider documentation under
   `docs/providers/` and `docs/en/providers/`. Keep configuration keys,
   provider IDs, permissions, and examples aligned. Update the provider
   indexes, locale navigation in `docs/.vitepress/config.mts`, and
   `docs/llms.txt`.
7. Verify with focused checks:

   ```sh
   python -m unittest tests.test_provider_<provider> -v
   ruff check ddns/provider/<provider>.py tests/test_provider_<provider>.py
   ruff format --check ddns/provider/<provider>.py tests/test_provider_<provider>.py
   ```

   Then run `python -m unittest discover tests -v`, `ruff check .`, and
   `ruff format --check .`. When documentation dependencies are already
   available, run `npm --prefix docs run build`. Report changed files and any
   validation not run. Do not install dependencies, publish, or change
   repository settings.
