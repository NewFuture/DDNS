# Contributing to DDNS

## Development workflow

1. Start from a clear issue or change goal.
2. Read `AGENTS.md` and the closest directory `AGENTS.md`.
3. Update implementation, tests, schemas or metadata, and Chinese/English
   documentation together when behavior changes.
4. Run focused checks while iterating and the full affected suite before
   opening a pull request.
5. Complete the pull request template with compatibility and validation
   evidence.

## Runtime constraints

- Code under `ddns/`, `run.py`, and tests supports Python 2.7 and current
  Python 3 versions.
- Runtime dependencies remain standard-library only.
- Repository tools under `tools/` target Python 3.12+.
- Preserve existing CLI, configuration, provider, schema, and cache contracts
  unless a breaking change is explicitly approved.

## Common validation

```sh
python -m unittest discover tests -v
python -m unittest tests.e2e -v
ruff check .
ruff format --check .
npm --prefix docs ci
npm --prefix docs run build
```

Run only the checks relevant to your change while iterating, but do not skip an
affected compatibility or platform suite.

## Pull requests

- Keep changes focused and reviewable.
- Use a conventional title such as `fix(http): bound retry failures`.
- Do not include credentials, private configuration, customer identifiers, or
  live provider responses.
- Do not use real DNS credentials or mutate live DNS for validation.
- Agent-authored changes follow the same review and quality requirements as
  human-authored changes.
