# AGENTS.md - AI Agent Guide for DDNS Project

> **Comprehensive guide for AI agents working on the DDNS (Dynamic DNS) project**

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Architecture](#project-architecture)
3. [Getting Started](#getting-started)
4. [Development Guide](#development-guide)
5. [Testing & Validation](#testing--validation)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

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

### Project Status

- **License**: MIT
- **Python Versions**: 2.7, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
- **Platforms**: Windows, Linux, macOS
- **Architectures**: amd64, arm64, arm/v7, arm/v6, 386, ppc64le, riscv64, s390x

---

## Project Architecture

### Directory Structure

Here is the folder and file structure for the DDNS project.

**Format:** `<TAB depth>{filename}:<TAB>{description}`

```text
.github/:	GitHub configuration
	workflows/:	CI/CD workflows (build, publish, test)
	instructions/:	Agent instructions (python.instructions.md)
	copilot-instructions.md:	GitHub Copilot instructions

ddns/:	Main application code
	__init__.py:	Package initialization and version info
	__main__.py:	Entry point for module execution
	cache.py:	Cache management
	ip.py:	IP address detection logic

	config/:	Configuration management
		__init__.py
		cli.py:	Command-line argument parsing
		config.py:	Configuration loading and merging
		env.py:	Environment variable parsing
		file.py:	JSON file configuration

	provider/:	DNS provider implementations
		__init__.py:	Provider registry
		_base.py:	Abstract base classes (SimpleProvider, BaseProvider)
		_signature.py:	HMAC signature utilities
		alidns.py:	Alibaba Cloud DNS
		aliesa.py:	Alibaba Cloud ESA
		callback.py:	Custom webhook callbacks
		cloudflare.py:	Cloudflare DNS
		cloudns.py:	ClouDNS
		debug.py:	Debug provider
		dnscom.py:	DNS.COM
		dnspod.py:	DNSPod (China)
		dnspod_com.py:	DNSPod International
		edgeone.py:	Tencent EdgeOne
		edgeone_dns.py:	Tencent EdgeOne DNS
		he.py:	Hurricane Electric
		huaweidns.py:	Huawei Cloud DNS
		namesilo.py:	NameSilo
		noip.py:	No-IP
		tencentcloud.py:	Tencent Cloud DNS
		west.py:	West.cn DNS

	scheduler/:	Task scheduling implementations
		__init__.py
		_base.py:	Base scheduler class
		cron.py:	Cron-based scheduler (Linux/macOS)
		launchd.py:	macOS launchd scheduler
		schtasks.py:	Windows Task Scheduler
		systemd.py:	Linux systemd timer

	util/:	Utility modules
		__init__.py
		comment.py:	Comment handling
		fileio.py:	File I/O operations
		http.py:	HTTP client with proxy support
		try_run.py:	Safe command execution

tests/:	Unit tests
	__init__.py:	Test initialization (path setup)
	base_test.py:	Shared test utilities and base classes
	README.md:	Testing documentation
	config/:	Test configuration files
	scripts/:	Test helper scripts
	test_cache.py:	Cache tests
	test_config_*.py:	Configuration tests
	test_ip.py:	IP detection tests
	test_provider_*.py:	Provider-specific tests
	test_scheduler_*.py:	Scheduler tests
	test_util_*.py:	Utility tests

docs/:	Documentation (VitePress-based)
	.vitepress/:	VitePress configuration and theme
	
	config/:	Configuration documentation (Chinese)
		cli.md:	CLI usage guide
		env.md:	Environment variables guide
		json.md:	JSON configuration guide

	dev/:	Developer guides (Chinese)
		provider.md:	Provider development guide
		config.md:	Configuration system design

	providers/:	Provider-specific documentation (Chinese)
		README.md:	Provider list and overview
		51dns.md:	51DNS provider guide
		alidns.md:	Alibaba Cloud DNS guide
		aliesa.md:	Alibaba Cloud ESA guide
		callback.md:	Custom webhook callbacks guide
		cloudflare.md:	Cloudflare DNS guide
		cloudns.md:	ClouDNS guide
		debug.md:	Debug provider guide
		dnscom.md:	DNS.COM provider guide
		dnspod.md:	DNSPod (China) guide
		dnspod_com.md:	DNSPod International guide
		edgeone.md:	Tencent EdgeOne guide
		edgeone_dns.md:	Tencent EdgeOne DNS guide
		he.md:	Hurricane Electric guide
		huaweidns.md:	Huawei Cloud DNS guide
		namesilo.md:	NameSilo guide
		noip.md:	No-IP guide
		tencentcloud.md:	Tencent Cloud DNS guide
		west.md:	West.cn DNS guide

	en/:	English documentation
		config/:	Configuration documentation
			cli.md:	CLI usage guide
			env.md:	Environment variables guide
			json.md:	JSON configuration guide
		dev/:	Developer guides
			provider.md:	Provider development guide
			config.md:	Configuration system design
		providers/:	Provider-specific documentation
			README.md:	Provider list and overview
			51dns.md:	51DNS provider guide
			alidns.md:	Alibaba Cloud DNS guide
			aliesa.md:	Alibaba Cloud ESA guide
			callback.md:	Custom webhook callbacks guide
			cloudflare.md:	Cloudflare DNS guide
			cloudns.md:	ClouDNS guide
			debug.md:	Debug provider guide
			dnscom.md:	DNS.COM provider guide
			dnspod.md:	DNSPod (China) guide
			dnspod_com.md:	DNSPod International guide
			edgeone.md:	Tencent EdgeOne guide
			edgeone_dns.md:	Tencent EdgeOne DNS guide
			he.md:	Hurricane Electric guide
			huaweidns.md:	Huawei Cloud DNS guide
			namesilo.md:	NameSilo guide
			noip.md:	No-IP guide
			tencentcloud.md:	Tencent Cloud DNS guide
			west.md:	West.cn DNS guide
		docker.md:	Docker documentation
		install.md:	Installation guide

	public/:	Public static assets
		img/:	Images and diagrams
		schema/:	JSON schema files (symlink)
		tests/:	Test configuration examples

	docker.md:	Docker documentation (Chinese)
	install.md:	Installation guide (Chinese)
	release.md:	Release notes (Chinese)

docker/:	Docker configuration
	Dockerfile:	Main Dockerfile
	glibc.Dockerfile:	glibc-based build
	musl.Dockerfile:	musl-based build
	entrypoint.sh:	Container entrypoint script

schema/:	JSON schemas
	v2.json:	Legacy schema v2
	v2.8.json:	Legacy schema v2.8
	v4.0.json:	Previous schema v4.0
	v4.1.json:	Latest schema v4.1

run.py:	Direct run script
install.sh:	One-click install script
pyproject.toml:	Python project configuration
setup.cfg:	Setup configuration
.gitignore:	Git ignore rules
LICENSE:	MIT License
README.md:	Main README (Chinese)
README.en.md:	Main README (English)
```

### Module Dependencies

```text
ddns/__main__.py
    ├── ddns.config.*           # Configuration loading
    │   ├── cli                 # Command-line parsing
    │   ├── env                 # Environment variables
    │   ├── file                # JSON file loading
    │   └── config              # Config merging and validation
    │
    ├── ddns.ip                 # IP address detection
    │   └── ddns.util.http      # HTTP client for public IP APIs
    │
    ├── ddns.provider.*         # DNS provider implementations
    │   ├── _base               # Base classes (SimpleProvider, BaseProvider)
    │   ├── _signature          # HMAC signature for cloud APIs
    │   └── ddns.util.http      # HTTP client for API requests
    │
    ├── ddns.cache              # Caching to reduce API calls
    │   └── ddns.util.fileio    # File operations
    │
    └── ddns.scheduler.*        # Task scheduling
        └── ddns.util.try_run   # Safe command execution
```

### Core Components

#### 1. Provider System

- **BaseProvider**: Full CRUD DNS provider (query, create, update records)
  - Used by: Cloudflare, AliDNS, DNSPod, TencentCloud, EdgeOne, etc.
  - Features: Automatic zone detection, record management, caching support

- **SimpleProvider**: Simple update-only DNS provider
  - Used by: HE.net, No-IP, Debug, Callback
  - Features: Direct record updates without querying

#### 2. Configuration System

Three-layer priority system:
1. **Command-line arguments** (highest priority) - via `ddns.config.cli`
2. **JSON configuration files** - via `ddns.config.file`
3. **Environment variables** (lowest priority) - via `ddns.config.env`

#### 3. IP Detection System

Multiple methods supported (via `ddns.ip`):
- Network interface (by index number)
- Default route IP
- Public IP (via external APIs)
- URL-based (custom API endpoint)
- Regex matching (from ifconfig/ipconfig output)
- Command execution (custom script)
- Shell execution (system shell command)

#### 4. Scheduler System

Platform-specific implementations:
- **Linux**: systemd timers or cron
- **macOS**: launchd or cron
- **Windows**: Task Scheduler (schtasks)
- **Docker**: Built-in cron with configurable intervals

---

## Getting Started

### Agent Quick Start

Classify the task first, then read only the nearest code, tests, docs, and schema for that lane.

- **Provider**: `ddns/provider/`, `tests/test_provider_*.py`, `docs/providers/`, `docs/en/providers/`
- **Config/schema**: `ddns/config/`, `schema/`, `tests/test_config_*.py`, `docs/config/`, `docs/en/config/`
- **IP/HTTP**: `ddns/ip.py`, `ddns/util/http.py`, `tests/test_ip.py`, `tests/test_util_http*.py`
- **Scheduler**: `ddns/scheduler/`, `tests/test_scheduler_*.py`
- **Docs/packaging**: `README*.md`, `docs/`, `pyproject.toml`, `setup.cfg`, `docker/`, `.github/workflows/`

Use `rg` / `rg --files` for discovery, make narrow edits, validate the touched behavior, and report any command that could not run.

### Useful Commands

```bash
python -m ddns --help
python run.py --help
pip install ddns
ddns --help
docker run --rm newfuture/ddns:latest --help
curl -fsSL https://ddns.newfuture.cc/install.sh | sh
python -m ddns -c config.json
python -m ddns --dns=cloudflare --id=EMAIL --token=TOKEN --ipv4=domain.com
python -m ddns --debug
python -m ddns --dns=debug --ipv4=test.com --debug
ddns task --install 5
ddns task --enable
```

Linux/macOS scheduled tasks use systemd, cron, or launchd; Windows uses the release binary and `ddns task --install 5`.

---

## Development Guide

### Hard Rules

Follow `.github/instructions/python.instructions.md` for Python files.

- Use only standard-library runtime dependencies.
- Preserve Python 2.7 and 3.x compatibility: no f-strings, annotations, async/await, or Python 3-only syntax.
- Use type comments, for example `# type: (...) -> ReturnType`.
- Keep CLI flags, provider names, config keys, schemas, and cache behavior backward compatible unless explicitly asked otherwise.
- Do not reformat unrelated files or modernize stable code for style alone.

### Change Flow

1. Read the closest existing implementation and matching tests.
2. Mirror established patterns instead of inventing new abstractions.
3. Change code, tests, schema, and docs together when behavior is user-facing.
4. Run focused validation first; run the full suite for shared modules.
5. Summarize changes, validation, and residual risk.

### Provider Changes

- Use `BaseProvider` for query/create/update APIs and `SimpleProvider` for update-only APIs.
- Register new providers in `ddns/provider/__init__.py`.
- Add mocked tests in `tests/test_provider_<provider>.py`; never require real credentials or live provider APIs.
- Update both `docs/providers/<provider>.md` and `docs/en/providers/<provider>.md`.
- Update schema, README lists, or docs navigation when a new provider or option needs discovery.
- See `docs/dev/provider.md` and `docs/en/dev/provider.md` for full provider method signatures.

### Documentation

Keep Chinese and English docs aligned. Preserve code blocks, option names, JSON keys, CLI flags, and provider IDs exactly across translations. Link Chinese docs to Chinese pages and English docs to `docs/en/` pages.

---

## Testing & Validation

Run the smallest useful test first, then broaden when shared behavior changed.

```bash
python -m unittest tests.test_provider_cloudflare -v
python -m unittest tests.test_config_config -v
python -m unittest tests.test_ip -v
python -m unittest discover tests -v
python -m pytest tests/ -v  # optional, when pytest is installed
ruff check --fix --unsafe-fixes .
ruff format .
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
python -c "import json; json.load(open('config.json'))"
```

Provider tests should import from `base_test`; other tests should import from `tests/__init__.py`. Mock HTTP calls and assert request details, response parsing, and error handling.

---

## Troubleshooting

1. Reproduce with the smallest command, fixture, or unit test.
2. Locate the layer: config parsing, IP detection, provider mapping, HTTP transport, cache, or scheduler.
3. Read the nearest passing test and nearest similar implementation.
4. Fix root cause, add a regression test when behavior changed, and re-run focused validation.

Common checks:

- Import error: file exists, provider registered, test path setup uses `tests/__init__.py` or `tests/base_test.py`.
- Syntax error: remove Python 3-only syntax and keep Python 2.7 compatibility.
- Auth/signature issue: verify credential shape and signing with mocked tests; never print real tokens.
- Record not updated: inspect cache, record type, line, TTL, domain split, and provider response parsing.
- Proxy/network issue: compare with `ddns/util/http.py`; use `--proxy=DIRECT` or `--ssl=false` only as diagnostics.
- Schema mismatch: update `schema/v4.1.json` and matching config tests together.
- Test failure: inspect mock return values and `mock_http.call_args`.
- Linting issue: run `ruff check --fix --unsafe-fixes .` and `ruff format .`.

```bash
python -m ddns --debug --dns=myprovider --ipv4=test.com
python -m ddns --debug --log_file=debug.log
python -m ddns --dns=debug --ipv4=test.com --debug
rm -f /tmp/ddns.cache
```

Use cache removal only when debugging stale local state. Avoid destructive git recovery unless the user explicitly requests it.

---

## Best Practices

- Prefer small, reviewable changes that follow existing patterns.
- Fix root causes and add tests for regressions.
- Preserve user changes in the working tree; never reset or reformat unrelated files.
- Treat configs, logs, environment variables, API tokens, and provider credentials as sensitive.
- Prefer mocked or dry-run validation; ask before using real credentials, provider APIs, or scheduler installation on a host.
- Use structured parsers for JSON, URLs, and HTTP data.
- Refactor only when it directly supports the task or removes clear local duplication.
- Ask before renaming files/providers/config keys, moving directories, mass search-and-replace, multi-module refactors, changing cache/schema compatibility, or running commands against real external services.
- For large changes, explain goal, impact, validation plan, and safer alternatives first.
- When asked to commit or draft PR text, use conventional commits such as `fix(util.http): handle proxy errors`.

---

## Summary

This guide provides comprehensive instructions for AI agents working on the DDNS project. Key points:

1. **Architecture**: Modular Python project with provider system, configuration management, and task scheduling
2. **Development**: Follow Python standards, maintain Python 2.7 compatibility, use ruff for linting
3. **Testing**: Use unittest (primary) or pytest (optional), write comprehensive tests
4. **Building**: Support for Python source, PyPI, Docker, and binary executables
5. **Documentation**: Maintain both Chinese and English versions
6. **Safety**: Avoid unnecessary changes, ask before large edits, respect existing code

For detailed information on specific topics, refer to:
- **Python Standards**: `.github/instructions/python.instructions.md`
- **Repository Instructions**: `.github/copilot-instructions.md`
- **Provider Development**: `docs/dev/provider.md`
- **Testing Guide**: `tests/README.md`
- **Configuration**: `docs/config/*.md`

---

**Version**: 1.0.6
**Last Updated**: 2026-06-15
**Maintained by**: DDNS Project Contributors
