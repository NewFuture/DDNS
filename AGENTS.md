# AGENTS.md - AI Agent Guide for DDNS Project

> **Comprehensive guide for AI agents working on the DDNS (Dynamic DNS) project**

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Architecture](#project-architecture)
3. [AI Agent Role Instructions](#ai-agent-role-instructions)
4. [Development Workflow](#development-workflow)
5. [Testing Instructions](#testing-instructions)
6. [Build & Run Instructions](#build--run-instructions)
7. [Troubleshooting Guidelines](#troubleshooting-guidelines)
8. [Safety Guidelines](#safety-guidelines)

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
- **Python Versions**: 2.7, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14-dev
- **Platforms**: Windows, Linux, macOS
- **Architectures**: amd64, arm64, arm/v7, arm/v6, 386, ppc64le, riscv64, s390x

---

## Project Architecture

### Directory Structure

```text
DDNS/
├── .github/                    # GitHub configuration
│   ├── workflows/              # CI/CD workflows (build, publish, test)
│   ├── instructions/           # Agent instructions (python.instructions.md)
│   └── copilot-instructions.md # GitHub Copilot instructions
│
├── ddns/                       # Main application code
│   ├── __init__.py             # Package initialization and version info
│   ├── __main__.py             # Entry point for module execution
│   ├── cache.py                # Cache management
│   ├── ip.py                   # IP address detection logic
│   │
│   ├── config/                 # Configuration management
│   │   ├── __init__.py
│   │   ├── cli.py              # Command-line argument parsing
│   │   ├── config.py           # Configuration loading and merging
│   │   ├── env.py              # Environment variable parsing
│   │   └── file.py             # JSON file configuration
│   │
│   ├── provider/               # DNS provider implementations
│   │   ├── __init__.py         # Provider registry
│   │   ├── _base.py            # Abstract base classes (SimpleProvider, BaseProvider)
│   │   ├── _signature.py       # HMAC signature utilities
│   │   ├── alidns.py           # Alibaba Cloud DNS
│   │   ├── aliesa.py           # Alibaba Cloud ESA
│   │   ├── callback.py         # Custom webhook callbacks
│   │   ├── cloudflare.py       # Cloudflare DNS
│   │   ├── debug.py            # Debug provider
│   │   ├── dnscom.py           # DNS.COM
│   │   ├── dnspod.py           # DNSPod (China)
│   │   ├── dnspod_com.py       # DNSPod International
│   │   ├── edgeone.py          # Tencent EdgeOne
│   │   ├── he.py               # Hurricane Electric
│   │   ├── huaweidns.py        # Huawei Cloud DNS
│   │   ├── namesilo.py         # NameSilo
│   │   ├── noip.py             # No-IP
│   │   └── tencentcloud.py     # Tencent Cloud DNS
│   │
│   ├── scheduler/              # Task scheduling implementations
│   │   ├── __init__.py
│   │   ├── _base.py            # Base scheduler class
│   │   ├── cron.py             # Cron-based scheduler (Linux/macOS)
│   │   ├── launchd.py          # macOS launchd scheduler
│   │   ├── schtasks.py         # Windows Task Scheduler
│   │   └── systemd.py          # Linux systemd timer
│   │
│   └── util/                   # Utility modules
│       ├── __init__.py
│       ├── comment.py          # Comment handling
│       ├── fileio.py           # File I/O operations
│       ├── http.py             # HTTP client with proxy support
│       └── try_run.py          # Safe command execution
│
├── tests/                      # Unit tests
│   ├── __init__.py             # Test initialization (path setup)
│   ├── base_test.py            # Shared test utilities and base classes
│   ├── README.md               # Testing documentation
│   ├── config/                 # Test configuration files
│   ├── scripts/                # Test helper scripts
│   ├── test_cache.py           # Cache tests
│   ├── test_config_*.py        # Configuration tests
│   ├── test_ip.py              # IP detection tests
│   ├── test_provider_*.py      # Provider-specific tests
│   ├── test_scheduler_*.py     # Scheduler tests
│   └── test_util_*.py          # Utility tests
│
├── doc/                        # Documentation
│   ├── config/                 # Configuration documentation
│   │   ├── cli.md              # CLI usage (Chinese)
│   │   ├── cli.en.md           # CLI usage (English)
│   │   ├── env.md              # Environment variables (Chinese)
│   │   ├── env.en.md           # Environment variables (English)
│   │   ├── json.md             # JSON config (Chinese)
│   │   └── json.en.md          # JSON config (English)
│   │
│   ├── dev/                    # Developer documentation
│   │   ├── provider.md         # Provider development guide (Chinese)
│   │   ├── provider.en.md      # Provider development guide (English)
│   │   ├── config.md           # Config system (Chinese)
│   │   └── config.en.md        # Config system (English)
│   │
│   ├── providers/              # Provider-specific documentation
│   │   ├── README.md           # Provider list (Chinese)
│   │   ├── README.en.md        # Provider list (English)
│   │   ├── alidns.md           # AliDNS guide (Chinese)
│   │   ├── alidns.en.md        # AliDNS guide (English)
│   │   └── ...                 # Other providers (Chinese & English versions)
│   │
│   ├── docker.md               # Docker documentation (Chinese)
│   ├── docker.en.md            # Docker documentation (English)
│   ├── install.md              # Installation guide (Chinese)
│   ├── install.en.md           # Installation guide (English)
│   └── img/                    # Images and diagrams
│
├── docker/                     # Docker configuration
│   ├── Dockerfile              # Main Dockerfile
│   ├── glibc.Dockerfile        # glibc-based build
│   ├── musl.Dockerfile         # musl-based build
│   └── entrypoint.sh           # Container entrypoint script
│
├── schema/                     # JSON schemas
│   ├── v2.json                 # Legacy schema v2
│   ├── v2.8.json               # Legacy schema v2.8
│   ├── v4.0.json               # Current schema v4.0
│   └── v4.1.json               # Latest schema v4.1
│
├── run.py                      # Direct run script
├── install.sh                  # One-click install script
├── pyproject.toml              # Python project configuration
├── setup.cfg                   # Setup configuration
├── .gitignore                  # Git ignore rules
├── LICENSE                     # MIT License
├── README.md                   # Main README (Chinese)
└── README.en.md                # Main README (English)
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

## AI Agent Role Instructions

### How to Explore the Codebase

#### Understanding the Structure

1. **Start with the entry point**:
   ```bash
   # View the main entry point
   cat ddns/__main__.py
   ```

2. **Explore provider implementations**:
   ```bash
   # List all providers
   ls -la ddns/provider/
   
   # View base provider classes
   cat ddns/provider/_base.py
   
   # View a specific provider example
   cat ddns/provider/cloudflare.py
   ```

3. **Understand configuration system**:
   ```bash
   # View configuration modules
   ls -la ddns/config/
   cat ddns/config/config.py
   ```

4. **Check test structure**:
   ```bash
   # View test organization
   ls -la tests/
   cat tests/base_test.py
   ```

#### Finding Related Code

Use these patterns to locate code:

```bash
# Find all provider implementations
find ddns/provider -name "*.py" -not -name "_*"

# Find tests for a specific module
find tests -name "test_provider_*.py"

# Search for specific functionality
grep -r "def set_record" ddns/provider/

# Find configuration-related code
grep -r "argparse" ddns/config/
```

#### Understanding Dependencies

**CRITICAL**: This project has **ZERO** external runtime dependencies - only Python standard library.

### How to Edit or Create Files

#### Code Style Requirements

**CRITICAL**: Always follow `.github/instructions/python.instructions.md`

Key points:
- Use **only Python standard library** (no external dependencies)
- Maintain **Python 2.7 and 3.x compatibility**
  - NO f-strings
  - NO async/await
  - Use `.format()` or `%` for string formatting
- Use type hints in comments: `# type: (...) -> ReturnType`
- Follow existing code patterns

#### Creating a New DNS Provider

1. **Create the provider file**:
   ```bash
   # Create provider file
   touch ddns/provider/myprovider.py
   ```

2. **Choose base class**:
   - Use `BaseProvider` for full CRUD APIs (recommended)
   - Use `SimpleProvider` for update-only APIs

3. **Follow the template** in `doc/dev/provider.md`:
   ```python
   # coding=utf-8
   """
   MyProvider DNS Provider
   @author: YourName
   """
   from ._base import BaseProvider
   
   class MyProvider(BaseProvider):
       """MyProvider implementation"""
       API = 'https://api.myprovider.com'
       
       def _query_zone_id(self, domain):
           # type: (str) -> str | None
           """Query zone ID for domain"""
           pass
       
       def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
           # type: (str, str, str, str, str | None, dict | None) -> dict | None
           """Query existing DNS record"""
           pass
       
       def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
           # type: (str, str, str, str, str, int | None, str | None, dict | None) -> bool
           """Create new DNS record"""
           pass
       
       def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
           # type: (str, dict, str, str, int | None, str | None, dict | None) -> bool
           """Update existing DNS record"""
           pass
   ```

4. **Register the provider** in `ddns/provider/__init__.py`:
   ```python
   PROVIDERS = {
       # ... existing providers ...
       'myprovider': 'ddns.provider.myprovider',
   }
   ```

5. **Create tests** (see Testing Instructions below)

6. **Create documentation**:
   - Chinese: `doc/providers/myprovider.md`
   - English: `doc/providers/myprovider.en.md`
   - Use existing providers as templates

#### Editing Configuration Files

When editing JSON schemas:
```bash
# Edit current schema
vim schema/v4.1.json

# Validate schema format
python3 -c "import json; json.load(open('schema/v4.1.json'))"
```

#### Editing Documentation

Documentation exists in both Chinese and English:
- Always update **both** language versions
- Keep structure and formatting consistent
- Use existing docs as templates
- Link to English versions in English docs, Chinese in Chinese docs

### How to Run or Test the Project

#### Running DDNS

```bash
# Run from source (recommended for development)
python3 -m ddns --help
python3 -m ddns --dns=debug --ipv4=test.com

# Run with config file
python3 -m ddns -c tests/config/debug.json

# After pip install
ddns --help
```

#### Testing the Project

```bash
# Run all tests (unittest - no dependencies required)
python3 -m unittest discover tests -v

# Run specific test module
python3 -m unittest tests.test_provider_cloudflare -v

# Alternative: pytest (requires installation)
pip install pytest
pytest tests/ -v
```

#### Linting and Formatting

```bash
# Required before commit
ruff check --fix --unsafe-fixes .
ruff format .
```

### How to Follow Repository Conventions

#### Commit Message Format

Follow **Conventional Commits** specification:

```text
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding/updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

**Examples**:
```bash
feat(provider.cloudflare): add cloudflare provider support
fix(util.http): correct proxy authentication logic
docs(provider.alidns): update alidns configuration guide
test(provider): add tests for new provider
refactor(config): simplify configuration loading
```

#### Branching Strategy

- `master` / `main`: Main development branch
- `copilot/*`: AI-generated changes
- Feature branches: `feature/feature-name`
- Bug fixes: `fix/issue-description`

#### Pull Request Guidelines

1. **Title**: Use conventional commit format
2. **Description**: 
   - Describe changes made
   - Reference related issues
   - Include test results
3. **Checklist**:
   - [ ] Tests pass
   - [ ] Code is linted and formatted
   - [ ] Documentation updated (both languages if applicable)
   - [ ] No external dependencies added

### How to Create or Edit Document Files

#### Documentation Structure

All documentation has **Chinese** and **English** versions:
- Chinese: `filename.md`
- English: `filename.en.md`

#### Creating New Documentation

1. **Create both language versions**:
   ```bash
   touch doc/providers/newprovider.md
   touch doc/providers/newprovider.en.md
   ```

2. **Use existing templates**:
   - For provider docs: Use `doc/providers/alidns.md` and `doc/providers/alidns.en.md` as templates
   - For config docs: Use `doc/config/cli.md` and `doc/config/cli.en.md` as templates

3. **Keep structure consistent**:
   - Use same headings in both versions
   - Keep code examples identical
   - Translate only text descriptions

4. **Link correctly**:
   - In Chinese docs: Link to Chinese versions
   - In English docs: Link to English versions
   ```markdown
   # Chinese version (filename.md)
   详见[配置文档](../config/json.md)
   
   # English version (filename.en.md)
   See [configuration documentation](../config/json.en.md)
   ```

#### Editing Existing Documentation

1. **Always update both versions**:
   ```bash
   # If you edit Chinese version
   vim doc/providers/alidns.md
   # Also edit English version
   vim doc/providers/alidns.en.md
   ```

2. **Maintain formatting consistency**:
   - Use same markdown syntax
   - Keep headings at same levels
   - Preserve code block formatting

3. **Update related documentation**:
   - If changing config format, update `doc/config/*.md`
   - If changing CLI args, update `doc/config/cli.md`
   - If changing provider API, update `doc/dev/provider.md`

#### Documentation Best Practices

- Use clear, concise language
- Include code examples for all features
- Provide both simple and advanced examples
- Link to related documentation
- Keep examples tested and up-to-date
- Use consistent terminology throughout

---

## Development Workflow

### 1. Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/NewFuture/DDNS.git
cd DDNS

# Create virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Or install individual tools
pip install ruff pytest pytest-cov
```

### 2. Development Cycle

**Step 1: Create a branch**
```bash
git checkout -b feat/my-new-feature
```

**Step 2: Make changes**
- Edit code following conventions
- Write/update tests
- Update documentation (both languages)

**Step 3: Test changes**
```bash
# Run tests
python3 -m unittest discover tests -v

# Or with pytest
pytest tests/ -v
```

**Step 4: Lint and format**
```bash
# Lint
ruff check --fix --unsafe-fixes .

# Format
ruff format .
```

**Step 5: Commit changes**
```bash
git add .
git commit -m "feat(provider): add new DNS provider"
```

**Step 6: Push and create PR**
```bash
git push origin feat/my-new-feature
# Then create PR on GitHub
```

### 3. Code Review Process

- PRs require passing CI checks:
  - Linting (ruff)
  - Tests on Python 2.7, 3.8, 3.10, 3.12, 3.13, 3.14-dev
  - Docker build tests
  - Binary build tests

### 4. Branching and PR Rules

#### Branch Naming

- Feature: `feat/feature-name` or `feature/feature-name`
- Fix: `fix/issue-description` or `bugfix/issue-description`
- Docs: `docs/doc-update`
- AI-generated: `copilot/task-description`

#### PR Requirements

1. **Title**: Follow conventional commits format
2. **Description**: Clear explanation of changes
3. **Tests**: All tests must pass
4. **Linting**: Code must pass ruff checks
5. **Documentation**: Update both Chinese and English docs
6. **No breaking changes**: Unless major version bump

#### PR Review Checklist

- [ ] Code follows Python standards (`.github/instructions/python.instructions.md`)
- [ ] Python 2.7 and 3.x compatible
- [ ] Tests added/updated and passing
- [ ] Documentation updated (both languages)
- [ ] No external dependencies added
- [ ] Commit messages follow conventions
- [ ] Code is formatted with ruff

### 5. Commit Style

**Format**: `<type>(<scope>): <description>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Refactoring
- `perf`: Performance
- `chore`: Maintenance
- `ci`: CI/CD

**Scopes**:
- `provider`: Provider-related
- `provider.<name>`: Specific provider (e.g., `provider.cloudflare`)
- `config`: Configuration system
- `util`: Utilities
- `scheduler`: Task scheduling
- `cache`: Cache system
- `ip`: IP detection
- `docker`: Docker-related
- `ci`: CI/CD

**Examples**:
```bash
feat(provider.cloudflare): add IPv6 support
fix(util.http): handle proxy authentication errors
docs(providers): update provider documentation
test(provider): add integration tests
refactor(config): simplify env parsing
perf(cache): optimize cache lookup
chore(deps): update dev dependencies
ci(build): add Python 3.14 to test matrix
```

### 6. Linting and Formatting Rules

#### Ruff Configuration

Defined in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 120
target-version = "py37"

[tool.ruff.lint]
select = ["E", "W", "F", "C"]
ignore = ["E501", "UP025"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

#### Running Ruff

```bash
# Check for issues
ruff check .

# Auto-fix issues (safe fixes only)
ruff check --fix .

# Auto-fix with unsafe fixes (required before commit)
ruff check --fix --unsafe-fixes .

# Format code
ruff format .

# Check specific files
ruff check ddns/provider/mynewprovider.py
```

#### Pre-commit Checks

Before committing, always run:
```bash
# Fix and format
ruff check --fix --unsafe-fixes .
ruff format .

# Run tests
python3 -m unittest discover tests -v

# Verify changes
git diff
```

---

## Testing Instructions

### Testing Framework

DDNS uses **unittest** as the primary testing framework (Python built-in, no dependencies). **pytest** is optionally supported.

### Test Structure

```text
tests/
├── __init__.py                 # Path setup for imports
├── base_test.py                # Shared utilities and BaseProviderTestCase
├── README.md                   # Testing documentation
│
├── config/                     # Test configuration files
│   ├── debug.json
│   ├── callback.json
│   └── ...
│
├── scripts/                    # Test helper scripts
│   └── test-in-docker.sh
│
├── test_cache.py               # Cache module tests
├── test_config_*.py            # Configuration tests
├── test_ip.py                  # IP detection tests
├── test_provider_*.py          # Provider tests (one per provider)
├── test_scheduler_*.py         # Scheduler tests
└── test_util_*.py              # Utility tests
```

### Running Tests

#### Using unittest (Recommended)

```bash
# Run all tests
python3 -m unittest discover tests -v

# Run specific test file
python3 -m unittest tests.test_provider_cloudflare -v

# Run specific test class
python3 -m unittest tests.test_provider_cloudflare.TestCloudflareProvider -v

# Run specific test method
python3 -m unittest tests.test_provider_cloudflare.TestCloudflareProvider.test_query_zone_id -v

# Run tests matching pattern
python3 -m unittest discover tests -p "test_provider_*.py" -v
```

#### Using pytest (Optional)

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=ddns --cov-report=term-missing

# Run specific file
pytest tests/test_provider_cloudflare.py -v

# Run tests matching pattern
pytest tests/ -k "cloudflare" -v

# Run with verbose output
pytest tests/ -vv

# Run and stop at first failure
pytest tests/ -x
```

### Writing Tests

#### Test File Naming

- Provider tests: `test_provider_<name>.py`
- Module tests: `test_<module>_<submodule>.py`
- Use underscores, not hyphens

#### Test Class Naming

- For providers: `Test<ProviderName>Provider`
- For modules: `Test<ModuleName>`

#### Test Method Naming

- Use `test_<functionality>` pattern
- Be descriptive: `test_query_zone_id_success`, `test_create_record_with_ttl`

#### Basic Provider Test Template

```python
# coding=utf-8
"""
Tests for MyProvider
"""
from base_test import BaseProviderTestCase, patch, MagicMock
from ddns.provider.myprovider import MyProvider

class TestMyProvider(BaseProviderTestCase):
    """Tests for MyProvider"""
    
    def setUp(self):
        # type: () -> None
        """Set up test fixtures"""
        super(TestMyProvider, self).setUp()
        self.provider = MyProvider(self.id, self.token)
    
    @patch.object(MyProvider, "_http")
    def test_query_zone_id_success(self, mock_http):
        # type: (MagicMock) -> None
        """Test successful zone ID query"""
        # Arrange
        mock_http.return_value = {"zone_id": "zone123"}
        
        # Act
        result = self.provider._query_zone_id("example.com")
        
        # Assert
        self.assertEqual(result, "zone123")
        mock_http.assert_called_once()
    
    @patch.object(MyProvider, "_http")
    def test_create_record_success(self, mock_http):
        # type: (MagicMock) -> None
        """Test successful record creation"""
        # Arrange
        mock_http.return_value = {"status": "success"}
        
        # Act
        result = self.provider._create_record(
            "zone123", "www", "example.com", 
            "1.2.3.4", "A", 600, None, {}
        )
        
        # Assert
        self.assertTrue(result)
        mock_http.assert_called_once()
```

#### Test Requirements

1. **Mock external calls**: Use `@patch` for HTTP requests
2. **Test success cases**: Normal operation
3. **Test error cases**: Network failures, invalid inputs, API errors
4. **Test edge cases**: Empty values, None, special characters
5. **Python 2.7 compatible**: Use type comments, not type annotations

#### Running Tests in CI

The CI pipeline runs tests on multiple Python versions:

```bash
# Python 2.7 (on Ubuntu 22.04)
python2.7 -m unittest discover tests -v

# Python 3.x
python3 -m unittest discover tests -v

# Specific Python versions (3.8, 3.10, 3.12, 3.13, 3.14-dev)
python3.12 -m unittest discover tests -v
```

### Test Coverage

Check test coverage (requires pytest-cov):

```bash
# Install coverage tools
pip install pytest pytest-cov

# Run tests with coverage
pytest tests/ --cov=ddns --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

### Integration and E2E Tests

Currently, DDNS uses:
- **Unit tests**: Mock all external dependencies
- **Docker tests**: Test built Docker images (in CI)
- **Binary tests**: Test compiled binaries (in CI)

No dedicated integration or E2E test suite exists yet, but you can test manually:

```bash
# Test with debug provider (no external API calls)
python3 -m ddns --dns=debug --ipv4=test.com

# Test with real provider (requires credentials)
python3 -m ddns --dns=cloudflare --id=your@email.com --token=your-token --ipv4=test.yourdomain.com

# Test Docker image
docker run --rm newfuture/ddns:latest -h
docker run --rm -e DDNS_DNS=debug -e DDNS_IPV4=test.com newfuture/ddns:latest
```

---

## Build & Run Instructions

### Installation Methods

**1. From Source** (Python 2.7+/3.6+)
```bash
git clone https://github.com/NewFuture/DDNS.git
cd DDNS
python3 -m ddns --help
```

**2. PyPI**
```bash
pip install ddns
ddns --help
```

**3. Docker**
```bash
docker pull newfuture/ddns:latest
docker run --rm newfuture/ddns:latest --help
# With config: docker run -d -v /path/to/config/:/ddns/ newfuture/ddns:latest
```

**4. Binary** (no Python required)
```bash
curl -fsSL https://ddns.newfuture.cc/install.sh | sh
ddns --help
```

### Platform-Specific

**Linux/macOS/Raspberry Pi**
```bash
# Install (choose one): source, pip, one-click script, or Docker
# Set up scheduled task
ddns task --install 5  # Update every 5 minutes
ddns task --enable
# Uses systemd/cron on Linux, launchd on macOS
```

**Windows**
```bash
# Download binary from https://github.com/NewFuture/DDNS/releases/latest
ddns.exe --help
# Or: pip install ddns
# Set up: ddns task --install 5
```

---

## Troubleshooting Guidelines

### Validation

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

### Common Errors

**Import Error**: Check file exists, provider registered in `__init__.py`, PYTHONPATH set

**Syntax Error**: Check Python 2.7 compatibility (no f-strings, async/await, use type comments)

**Test Failure**: Verify mock setup returns correct values, check `mock_http.call_args`

**Linting Error**: Run `ruff check --fix --unsafe-fixes . && ruff format .`

### CI Failures

Check GitHub Actions logs. Common fixes:
- **Linting**: `ruff check --fix --unsafe-fixes . && ruff format .`
- **Python version**: Test locally with `python2.7` or `python3.12`
- **Docker**: Test with `docker build -t ddns:test -f docker/Dockerfile .`

### Runtime Issues

**Debug Mode**
```bash
python3 -m ddns --debug --dns=myprovider --ipv4=test.com
python3 -m ddns --debug --log_file=debug.log
```

**Common Issues**:
- **Auth failed**: Verify credentials with `--debug`, test API manually
- **Record not updated**: Remove cache (`rm -f /tmp/ddns.cache`), check IP detection
- **Network/proxy**: Try `--proxy=DIRECT` or `--ssl=false`
- **Python 2.7 compat**: Use `.format()` not f-strings, type comments not annotations

### Validation Checklist

Before submitting:
- [ ] Code syntax: `python3 -m py_compile ddns/**/*.py`
- [ ] Tests pass: `python3 -m unittest discover tests -v`
- [ ] Linting: `ruff check .`
- [ ] Python 2.7 compatible
- [ ] Documentation updated (both languages)
- [ ] No external dependencies

---

## Safety Guidelines

### Avoid Harmful Refactors

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

**Before refactoring**:
- Is this broken or just different style?
- Will this break existing users?
- Is there test coverage?
- Does this maintain Python 2.7 compatibility?

### Ask for Confirmation

Request confirmation before:
- Renaming files/directories
- Changing file structure
- Refactoring multiple modules
- Changing configuration formats
- Mass search-and-replace

Explain what, why, impacts, and alternatives.

### General Principles

1. **Minimal changes**: Change only what's necessary
2. **Test thoroughly**: Before and after
3. **Maintain compatibility**: Don't break users
4. **Document changes**: Update docs with code
5. **Ask when uncertain**: Better safe than sorry
6. **Review changes**: Check diff before committing
7. **Incremental**: Small PRs over rewrites
8. **Follow conventions**: Don't introduce new patterns
9. **Respect existing code**: There may be good reasons

### Emergency Rollback

```bash
git revert HEAD                    # Revert last commit
git checkout -- file.py            # Undo uncommitted changes
git checkout HEAD -- deleted_file  # Restore deleted file
```

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

**Version**: 1.0.0  
**Last Updated**: 2025-11-14  
**Maintained by**: DDNS Project Contributors
