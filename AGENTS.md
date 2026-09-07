# DDNS Agent Development Guide

> Portable project instructions for coding agents. The closest `AGENTS.md` takes precedence.

## Project Overview

### What is DDNS?

DDNS is a Python-based Dynamic DNS client that automatically updates DNS records to match the current IP address. It supports:

- **Multiple DNS Providers**: 15+ providers including Cloudflare, DNSPod, AliDNS, etc.
- **Dual Stack**: IPv4 and IPv6 support
- **Multiple Platforms**: Docker, binary executables, pip installation, and source code
- **Flexible Configuration**: Command-line arguments, JSON files, and environment variables
- **Advanced Features**: Multi-domain support, HTTP proxy, caching, scheduled tasks

### Key Technologies

- **Language**: Python (2.7+ and 3.x compatible)
- **Testing**: unittest (default) and pytest (optional)
- **Linting/Formatting**: ruff
- **CI/CD**: GitHub Actions
- **Containerization**: Docker (multi-architecture support)
- **Packaging**: PyPI, Nuitka (for binaries)

### Portable Agent Definitions

- `AGENTS.md` files contain project and directory rules.
- `.agents/skills/*/SKILL.md` contains reusable, client-neutral workflows.
- `.github/agents/*.agent.md` is a thin GitHub Copilot adapter for tool boundaries and role selection.
- Do not duplicate a Skill in client-specific directories.
- The default coding agent owns general project work; use a domain agent only when its narrower context is useful.

### Project Status

- **License**: MIT
- **Python Versions**: 2.7, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
- **Platforms**: Windows, Linux, macOS
- **Architectures**: amd64, arm64, arm/v7, arm/v6, 386, ppc64le, riscv64, s390x

---

## Agent Development Model

### Agent Quick Start

Classify the task first, then read only the nearest code, tests, docs, and schema for that lane.

- **Provider**: `ddns/provider/`, `tests/test_provider_*.py`, `docs/providers/`, `docs/en/providers/`
- **Config/schema**: `ddns/config/`, `schema/`, `tests/test_config_*.py`, `docs/config/`, `docs/en/config/`
- **IP/HTTP**: `ddns/ip.py`, `ddns/util/http.py`, `tests/test_ip.py`, `tests/test_util_http*.py`
- **Scheduler**: `ddns/scheduler/`, `tests/test_scheduler_*.py`
- **Web/MCP**: `ddns/web/`, `web/`, `ddns/mcp.py`, `tests/test_web.py`, `tests/test_mcp.py`
- **Docs**: `README*.md`, `docs/`, `docs/AGENTS.md`
- **Build/release**: `pyproject.toml`, `run.py`, `.github/patch.py`, `docker/`, `.github/workflows/`
- **Agent control plane**: `AGENTS.md`, `.agents/skills/`, `.github/agents/`, `.github/instructions/`

Use `rg` / `rg --files` for discovery, make narrow edits, validate the touched behavior, and report any command that could not run. A task is complete only when code, tests, schemas, docs, and generated metadata affected by the behavior are consistent.

### Useful Commands

```bash
python -m ddns --help
python run.py --help
python -m ddns -c config.json
python -m ddns --dns=debug --ipv4=test.com --debug
ddns task --install 5
```

Linux/macOS scheduled tasks use systemd, cron, or launchd; Windows uses the release binary and `ddns task --install 5`.

---

## Development Rules

### Hard Rules

Follow `.github/instructions/python.instructions.md` for shipped Python and tests. Follow `tools/AGENTS.md` for maintenance tooling.

- Use only standard-library runtime dependencies.
- Preserve Python 2.7 and 3.x compatibility: no f-strings, annotations, async/await, or Python 3-only syntax.
- Use type comments, for example `# type: (...) -> ReturnType`.
- Keep CLI flags, provider names, config keys, schemas, and cache behavior backward compatible unless explicitly asked otherwise.
- Do not reformat unrelated files or modernize stable code for style alone.

### Provider Changes

- Use `BaseProvider` for query/create/update APIs and `SimpleProvider` for update-only APIs.
- Register new providers in `ddns/provider/__init__.py`.
- Update canonical metadata in `ddns/config/field-model.json`.
- Add mocked tests in `tests/test_provider_<provider>.py`; never require real credentials or live provider APIs.
- Update both `docs/providers/<provider>.md` and `docs/en/providers/<provider>.md`.
- Update both latest schema enums, CLI choices, provider indexes, navigation, and `docs/llms.txt`.
- See `docs/dev/provider.md` and `docs/en/dev/provider.md` for full provider method signatures.
- Follow `ddns/provider/AGENTS.md` and `.agents/skills/provider-development/SKILL.md`.

### Documentation

Keep Chinese and English docs aligned. Preserve code blocks, option names, JSON keys, CLI flags, and provider IDs exactly across translations. Link Chinese docs to Chinese pages and English docs to `docs/en/` pages.

Follow `docs/AGENTS.md` and `.agents/skills/documentation-maintenance/SKILL.md`. Treat `docs/public/install.sh` and `docs/esa.js` as executable, high-risk files rather than ordinary prose.

### Build and Release

Read the current workflows and Dockerfiles instead of relying on remembered versions or matrices. Do not publish, access release credentials, weaken required checks, disable caches, or remove platform coverage. Follow `.agents/skills/build-release-maintenance/SKILL.md`.

---

## Testing & Validation

Run the smallest useful test first, then broaden when shared behavior changed.

```bash
python -m unittest tests.test_provider_cloudflare -v
python -m unittest tests.test_config_config -v
python -m unittest tests.test_ip -v
python -m unittest discover tests -v
python -m unittest tests.e2e -v
python -m pytest tests/ -v  # optional, when pytest is installed
python3 -m unittest discover tools/tests -p "test_*.py" -v
python3 tools/check.py --changed
ruff check .
ruff format --check $(git ls-files '*.py')
npm --prefix docs ci
npm --prefix docs run build
```

Use these focused targets as a guide:

- Provider: `python -m unittest tests.test_provider_<provider> -v`
- Config/schema: `python -m unittest discover tests -p "test_config*.py" -v`
- IP/HTTP: `python -m unittest tests.test_ip tests.test_util_http tests.test_util_http_retry tests.test_util_http_proxy_list -v`
- Scheduler: `python -m unittest tests.test_scheduler_<name> -v`
- Broad shared change: `python -m unittest discover tests -v`

For touched files or examples:

```bash
python -m py_compile ddns/provider/myprovider.py
python -m json.tool config.json
```

Provider tests should import from `base_test`; other tests should import from `tests/__init__.py`. Mock HTTP calls and assert request details, response parsing, and error handling.

---

**Version**: 1.2.0
**Last Updated**: 2026-09-07
**Maintained by**: DDNS Project Contributors
