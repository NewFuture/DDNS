# DDNS Agent Development Guide

> Portable project instructions for coding agents. The closest `AGENTS.md` takes precedence.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Architecture](#project-architecture)
3. [Agent Development Model](#agent-development-model)
4. [Testing & Validation](#testing--validation)
5. [Troubleshooting](#troubleshooting)

---

## Project Overview

### What is DDNS?

DDNS is a standard-library-only Python Dynamic DNS client that updates DNS records to match the current IPv4 or IPv6 address. It supports multiple DNS providers, JSON/environment/CLI configuration, caching, scheduled tasks, Docker, an embedded Web dashboard, and MCP HTTP services.

### Key Technologies

- **Language**: Python 2.7 and Python 3.x (`requires-python = ">=2.7"`)
- **Testing**: Python `unittest` is the default; pytest support is optional
- **Linting/Formatting**: Ruff, configured in `pyproject.toml` (line length 120, target `py37`)
- **Documentation**: VitePress in the separate `docs/` npm project
- **CI/CD**: GitHub Actions
- **Packaging**: setuptools-compatible `pyproject.toml`, PyPI, Nuitka, and Docker

### Portable Agent Definitions

- `AGENTS.md` files contain project and directory rules; the nearest one takes precedence.
- `.agents/skills/*/SKILL.md` contains reusable workflows.
- `.github/agents/*.agent.md` contains thin GitHub Copilot adapters; shared workflow guidance belongs in `.agents/skills/`.
- Read `.github/instructions/python.instructions.md` for runtime Python and test changes, `tools/AGENTS.md` for maintenance tooling, and the nearest nested guide before editing those areas.

### Project Status

- **License**: MIT
- **Runtime dependencies**: Python standard library only
- **Platforms**: Windows, Linux, and macOS
- **Provider implementations**: 18 modules under `ddns/provider/`, with aliases registered in `ddns/provider/__init__.py`

---

## Project Architecture

```text
.github/       CI workflows, Python instructions, Copilot adapters, build patching
.agents/       Portable maintenance skills
ddns/          Runtime package: config, providers, schedulers, utilities, Web, MCP
schema/        Versioned JSON schemas
tests/         unittest suite, offline E2E tests, configs, and platform scripts
tools/         Python 3.12+ repository checks and their tests
docs/          VitePress documentation, bilingual pages, and documentation tests
web/           Standalone dashboard HTML/CSS/JavaScript packaged by Python
docker/        Dockerfiles and container entrypoint
run.py         Direct source/build entrypoint
pyproject.toml Packaging, test, Ruff, pytest, and type-checking configuration
CONTRIBUTING.md Contributor workflow and common validation commands
```

The main runtime layers are:

- `ddns/config/`: merges CLI, JSON, and environment configuration.
- `ddns/provider/`: provider implementations based on `BaseProvider` or `SimpleProvider`; update the registry, field model, schema, tests, and both language documentation together.
- `ddns/ip.py` and `ddns/util/`: IP detection, HTTP, cache, file, and command helpers.
- `ddns/scheduler/`: cron, systemd, launchd, and Windows Task Scheduler integrations.
- `ddns/web/`, `web/`, and `ddns/mcp*.py`: embedded dashboard and MCP services sharing HTTP/config behavior.

`web/` has no npm build. `docs/` is the only npm project and uses the checked-in `docs/package-lock.json`.

---

## Agent Development Model

Classify the task first, then read the nearest implementation, tests, docs, schema, and `AGENTS.md` for that lane:

- **Provider**: `ddns/provider/`, `tests/test_provider_*.py`, `docs/providers/`, `docs/en/providers/`
- **Config/schema/CLI**: `ddns/config/`, `schema/`, `tests/test_config_*.py`, `docs/config/`, `docs/en/config/`
- **IP/HTTP/cache**: `ddns/ip.py`, `ddns/util/`, and the corresponding `tests/test_ip.py` or `tests/test_util_*.py`
- **Scheduler**: `ddns/scheduler/`, `tests/test_scheduler_*.py`, and `tests/scripts/`
- **Web/MCP**: `ddns/web/`, `web/`, `ddns/mcp*.py`, `tests/test_web.py`, and `tests/test_mcp*.py`
- **Docs**: `README*.md`, `docs/`, and `docs/AGENTS.md`
- **Build/release**: `pyproject.toml`, `run.py`, `.github/patch.py`, `docker/`, and `.github/workflows/`
- **Repository tooling**: `tools/`, `.github/scripts/`, and `tools/AGENTS.md`

Keep runtime code and tests Python 2.7/3.x compatible: use standard-library dependencies, no annotations/f-strings/async syntax, and type comments where needed. Preserve CLI flags, provider aliases, configuration keys, schemas, and cache behavior unless a breaking change is explicitly approved. Keep Chinese and English documentation aligned.

Run source commands from the repository root. `python -m ddns --help` and `python run.py --help` work without installing the package. Do not use real provider credentials or mutate live DNS records.

---

## Testing & Validation

Use the smallest relevant check first, then broaden:

```bash
python -m unittest tests.test_<area> -v
python -m unittest discover tests -v
python -m unittest tests.e2e -v
python tools/check.py --changed
python tools/check.py --providers
ruff check .
ruff format --check .
npm --prefix docs ci
npm --prefix docs run build
```

`tests.e2e` is a separate offline suite and is not included in unittest discovery. `tools/check.py --changed` selects lane-specific checks from committed, staged, unstaged, and untracked changes; use `--all` for the complete check set. Provider tests use helpers from `tests/base_test.py`; other tests use `tests/__init__.py`.

The documentation commands require the locked dependencies from `docs/package-lock.json`. CI prepares Python 3.12, Node 24, and Ruff 0.16.2; local validation should use equivalent tools when available. The repository has no Makefile or pre-commit configuration.

For focused examples:

```bash
python -m unittest tests.test_provider_cloudflare -v
python -m unittest tests.test_web tests.test_mcp tests.test_mcp_http -v
python -m unittest discover tests -p "test_config*.py" -v
python -m py_compile ddns/provider/myprovider.py
```

---

## Troubleshooting

1. Reproduce with the smallest command or deterministic fixture.
2. Locate the affected layer: configuration, IP detection, provider, HTTP, cache, scheduler, Web, or MCP.
3. Read the nearest passing test and similar implementation.
4. Fix the root cause, add regression coverage for behavior changes, and rerun focused validation.

Common checks:

- Entry points: `python -m ddns --help`, `python run.py --help`.
- Provider parity: `python tools/check.py --providers`.
- Schema/config mismatch: update `schema/v4.1.json` and related config tests and docs together.
- Stale local state: remove only the relevant temporary cache while debugging; do not use destructive Git recovery.
- Network/provider failures: use mocked or offline tests, never live credentials.

Preserve user changes, avoid unrelated formatting, and report validation that could not run.

---

**Version**: 2.0.0
**Last Updated**: 2026-09-25
**Maintained by**: DDNS Project Contributors
