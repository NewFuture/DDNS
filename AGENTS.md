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

doc/:	Documentation
	config/
		cli.md:	CLI usage (Chinese)
		cli.en.md:	CLI usage (English)
		env.md:	Environment variables (Chinese)
		env.en.md:	Environment variables (English)
		json.md:	JSON config (Chinese)
		json.en.md:	JSON config (English)

	dev/
		provider.md:	Provider development guide (Chinese)
		provider.en.md:	Provider development guide (English)
		config.md:	Config system (Chinese)
		config.en.md:	Config system (English)

	providers/:	Provider-specific documentation
		README.md:	Provider list (Chinese)
		README.en.md:	Provider list (English)
		alidns.md:	AliDNS guide (Chinese)
		alidns.en.md:	AliDNS guide (English)
		...:	Other providers (Chinese & English versions)

	docker.md:	Docker documentation (Chinese)
	docker.en.md:	Docker documentation (English)
	install.md:	Installation guide (Chinese)
	install.en.md:	Installation guide (English)
	img/:	Images and diagrams

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

---

## Getting Started

### Installation

**From Source** (Python 2.7+/3.6+)
```bash
git clone https://github.com/NewFuture/DDNS.git
cd DDNS
python -m ddns --help
```

**PyPI**
```bash
pip install ddns
ddns --help
```

**Docker**
```bash
docker pull newfuture/ddns:latest
docker run --rm newfuture/ddns:latest --help
```

**Binary** (no Python required)
```bash
curl -fsSL https://ddns.newfuture.cc/install.sh | sh
ddns --help
```

### Quick Start

```bash
# Run with config file
python -m ddns -c config.json

# Run with command-line args
python -m ddns --dns=cloudflare --id=EMAIL --token=TOKEN --ipv4=domain.com

# Enable debug mode
python -m ddns --debug
```

### Platform Setup

**Linux/macOS/Raspberry Pi**: Set up scheduled task
```bash
ddns task --install 5  # Update every 5 minutes
ddns task --enable
# Uses systemd/cron on Linux, launchd on macOS
```

**Windows**: Download binary from [releases](https://github.com/NewFuture/DDNS/releases/latest), then `ddns task --install 5`

---

## Development Guide

### Code Standards

**CRITICAL**: Follow `.github/instructions/python.instructions.md`

- Use **only Python standard library** (ZERO external runtime dependencies)
- Maintain **Python 2.7 and 3.x compatibility** (no f-strings, no async/await)
- Use type comments: `# type: (...) -> ReturnType`
- Format: `ruff check --fix --unsafe-fixes . && ruff format .`

### Exploring the Codebase

```bash
# Entry point
cat ddns/__main__.py

# Providers
ls ddns/provider/
cat ddns/provider/_base.py

# Find code
find ddns/provider -name "*.py" -not -name "_*"
grep -r "def set_record" ddns/provider/
```

### Creating a DNS Provider

1. Create `ddns/provider/myprovider.py` inheriting from `BaseProvider` or `SimpleProvider`
2. Implement required methods (see `doc/dev/provider.md`)
3. Register in `ddns/provider/__init__.py`
4. Add tests in `tests/test_provider_myprovider.py`
5. Create documentation: `doc/providers/myprovider.md` and `doc/providers/myprovider.en.md`

**Template**:
```python
from ._base import BaseProvider

class MyProvider(BaseProvider):
    API = 'https://api.provider.com'
    
    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        pass
    
    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict | None) -> dict | None
        pass
    
    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | None, str | None, dict | None) -> bool
        pass
    
    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | None, str | None, dict | None) -> bool
        pass
```

### Documentation

**Bilingual**: Always update both Chinese (`.md`) and English (`.en.md`) versions

**Structure**: Keep same headings, code examples identical, translate only text

**Links**: Link to Chinese versions in Chinese docs, English in English docs

### Commit Conventions

**Format**: `<type>(<scope>): <description>`

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `ci`

**Examples**:
```bash
feat(provider.cloudflare): add IPv6 support
fix(util.http): handle proxy authentication errors
docs(providers): update provider documentation
```

### Development Workflow

1. **Setup**: `pip install ruff pytest`
2. **Branch**: `copilot/feature-name` or `copilot/issue-description`
3. **Code**: Make minimal changes, follow standards
4. **Test**: `python3 -m unittest discover tests -v`
5. **Lint**: `ruff check --fix --unsafe-fixes . && ruff format .`
6. **Commit**: Follow conventional commits
7. **PR**: Update both language docs, Python 2.7 compatible, no external deps

---

## Testing & Validation

### Running Tests

**unittest** (recommended - no dependencies)
```bash
python -m unittest discover tests -v
python -m unittest tests.test_provider_cloudflare -v
```

**pytest** (optional)
```bash
pip install pytest
pytest tests/ -v
```

### Writing Tests

```python
from base_test import BaseProviderTestCase, patch, MagicMock
from ddns.provider.myprovider import MyProvider

class TestMyProvider(BaseProviderTestCase):
    def setUp(self):
        super(TestMyProvider, self).setUp()
        self.provider = MyProvider(self.id, self.token)
    
    @patch.object(MyProvider, "_http")
    def test_query_zone_id_success(self, mock_http):
        mock_http.return_value = {"zone_id": "zone123"}
        result = self.provider._query_zone_id("example.com")
        self.assertEqual(result, "zone123")
```

### Validation Commands

```bash
# Syntax
python3 -m py_compile ddns/provider/mynewprovider.py
ruff check .

# Tests
python3 -m unittest discover tests -v

# Config
python3 -c "import json; json.load(open('config.json'))"

# Provider
python3 -m ddns --dns=debug --ipv4=test.com --debug
```

### Pre-Commit Checklist

- [ ] Code syntax validated
- [ ] Tests pass
- [ ] Linting: `ruff check .`
- [ ] Python 2.7 compatible
- [ ] Documentation updated (both languages)
- [ ] No external dependencies

---

## Troubleshooting

### Common Errors

**Import Error**: Check file exists, provider registered in `__init__.py`, PYTHONPATH set

**Syntax Error**: Check Python 2.7 compatibility (no f-strings, async/await, use type comments)

**Test Failure**: Verify mock setup returns correct values, check `mock_http.call_args`

**Linting Error**: Run `ruff check --fix --unsafe-fixes . && ruff format .`

### Debug Mode

```bash
python -m ddns --debug --dns=myprovider --ipv4=test.com
python -m ddns --debug --log_file=debug.log
```

**Common Issues**:
- **Auth failed**: Verify credentials with `--debug`, test API manually
- **Record not updated**: Remove cache (`rm -f /tmp/ddns.cache`), check IP detection
- **Network/proxy**: Try `--proxy=DIRECT` or `--ssl=false`
- **Python 2.7 compat**: Use `.format()` not f-strings, type comments not annotations

### Emergency Rollback

```bash
git revert HEAD                    # Revert last commit
git checkout -- file.py            # Undo uncommitted changes
git checkout HEAD -- deleted_file  # Restore deleted file
```

---

## Best Practices

### Code Quality

- **Minimal changes**: Change only what's necessary
- **Test thoroughly**: Before and after
- **Maintain compatibility**: Don't break Python 2.7 or existing users
- **Document changes**: Update docs with code
- **Follow conventions**: Don't introduce new patterns

### Refactoring Rules

**Don't**:
- Change working code for style preferences
- Break Python 2.7 compatibility
- Remove error handling or "unnecessary" imports
- Change APIs without version bump
- Mass rename variables/functions

**Do**:
- Fix actual bugs
- Add features without breaking existing ones
- Optimize with proven benefits

**Before refactoring**: Is this broken or just different style? Will this break users? Is there test coverage?

### Large Changes

Request confirmation before:
- Renaming files/directories
- Changing file structure
- Refactoring multiple modules
- Changing configuration formats
- Mass search-and-replace

Explain what, why, impacts, and alternatives.

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
- **Provider Development**: `doc/dev/provider.md`
- **Testing Guide**: `tests/README.md`
- **Configuration**: `doc/config/*.md`

---

**Version**: 1.0.1  
**Last Updated**: 2025-11-29  
**Maintained by**: DDNS Project Contributors
