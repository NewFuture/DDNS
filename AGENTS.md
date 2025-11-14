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

```bash
# Check Python dependencies (should be none except dev tools)
cat pyproject.toml | grep -A 10 "dependencies"

# View dev dependencies (ruff, pytest, etc.)
cat pyproject.toml | grep -A 10 "dev ="
```

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

**Method 1: Direct Python execution** (recommended for development)
```bash
# Run with help
python3 -m ddns --help

# Run with command-line arguments
python3 -m ddns --dns=debug --ipv4=test.com

# Run with config file
python3 -m ddns -c tests/config/debug.json

# Run with remote config
python3 -m ddns -c https://ddns.newfuture.cc/tests/config/debug.json

# Enable debug mode
python3 -m ddns --debug --dns=debug
```

**Method 2: Using run.py**
```bash
python3 run.py --help
```

**Method 3: After pip install**
```bash
# Install in development mode
pip install -e .

# Run as command
ddns --help
```

#### Testing the Project

**Primary method: unittest** (no dependencies required)
```bash
# Run all tests
python3 -m unittest discover tests -v

# Run specific test module
python3 -m unittest tests.test_provider_cloudflare -v

# Run specific test class
python3 -m unittest tests.test_provider_cloudflare.TestCloudflareProvider -v

# Run specific test method
python3 -m unittest tests.test_provider_cloudflare.TestCloudflareProvider.test_init -v
```

**Alternative: pytest** (requires installation)
```bash
# Install pytest (optional)
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=ddns --cov-report=term-missing

# Run specific test file
pytest tests/test_provider_cloudflare.py -v

# Run tests matching pattern
pytest tests/ -k "cloudflare" -v
```

**Running tests in CI environment**
```bash
# This mimics the CI test flow
python3 -m unittest discover tests -v
```

#### Linting and Formatting

**Format code** (required before commit):
```bash
# Install ruff (if not already installed)
pip install ruff

# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix --unsafe-fixes .

# Format code
ruff format .
```

**Run both linting and formatting**:
```bash
# Lint and fix
ruff check --fix --unsafe-fixes .

# Format
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

### Platform Support

DDNS supports multiple platforms and installation methods:

1. **Python Source** (any platform with Python 2.7+)
2. **PyPI Package** (via pip)
3. **Docker** (multi-architecture)
4. **Binary Executables** (native, no Python required)

### 1. Running from Source

**Requirements**: Python 2.7 or Python 3.6+

```bash
# Clone repository
git clone https://github.com/NewFuture/DDNS.git
cd DDNS

# Run directly
python3 -m ddns --help
python3 -m ddns --dns=debug --ipv4=test.com

# Or use run.py
python3 run.py --help

# Run with config file
python3 -m ddns -c config.json

# Run with environment variables
export DDNS_DNS=debug
export DDNS_IPV4=test.com
python3 -m ddns
```

### 2. PyPI Installation

**Requirements**: Python 2.7 or Python 3.6+, pip

```bash
# Install from PyPI
pip install ddns

# Or install in development mode
pip install -e .

# Run
ddns --help
ddns --dns=debug --ipv4=test.com

# Or run as module
python3 -m ddns --help
```

### 3. Docker

**Requirements**: Docker

#### Using Docker Hub Image

```bash
# Pull latest image
docker pull newfuture/ddns:latest

# Run with command-line arguments
docker run --rm newfuture/ddns:latest --help
docker run --rm newfuture/ddns:latest --dns=debug --ipv4=test.com

# Run with config file
docker run -d -v /path/to/config/:/ddns/ newfuture/ddns:latest

# Run with environment variables
docker run -d \
  -e DDNS_DNS=cloudflare \
  -e DDNS_ID=your@email.com \
  -e DDNS_TOKEN=your-token \
  -e DDNS_IPV4=test.yourdomain.com \
  newfuture/ddns:latest

# Run with custom cron schedule
docker run -d \
  -e DDNS_CRON="*/10 * * * *" \
  -e DDNS_DNS=debug \
  -e DDNS_IPV4=test.com \
  newfuture/ddns:latest
```

#### Docker Compose

```yaml
version: '3'
services:
  ddns:
    image: newfuture/ddns:latest
    container_name: ddns
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./config:/ddns/
    environment:
      - DDNS_DNS=cloudflare
      - DDNS_ID=your@email.com
      - DDNS_TOKEN=your-token
      - DDNS_IPV4=test.yourdomain.com
      - DDNS_CRON=*/5 * * * *
```

#### Building Docker Image Locally

```bash
# Build image
docker build -t ddns:local -f docker/Dockerfile .

# Build for specific architecture
docker buildx build --platform linux/amd64 -t ddns:amd64 -f docker/Dockerfile .
docker buildx build --platform linux/arm64 -t ddns:arm64 -f docker/Dockerfile .

# Build multi-architecture image
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t ddns:multi -f docker/Dockerfile .

# Run locally built image
docker run --rm ddns:local --help
```

### 4. Binary Executables

**Requirements**: None (self-contained, no Python needed)

#### Download Pre-built Binaries

```bash
# Download from GitHub Releases
wget https://github.com/NewFuture/DDNS/releases/latest/download/ddns-linux-amd64

# Make executable
chmod +x ddns-linux-amd64

# Run
./ddns-linux-amd64 --help
```

#### One-click Install Script

```bash
# Download and install (may require sudo for system directories)
curl -fsSL https://ddns.newfuture.cc/install.sh | sh

# Or with sudo
curl -fsSL https://ddns.newfuture.cc/install.sh | sudo sh

# Run
ddns --help
```

#### Building Binaries Locally

**Requirements**: Docker, buildx plugin

```bash
# Build for current architecture
docker build -t ddnsbin --target export -f docker/musl.Dockerfile --output output .

# Find binary
find output -name ddns

# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 --target export -f docker/musl.Dockerfile --output output .
```

### 5. Platform-Specific Instructions

#### Linux (Ubuntu/Debian)

```bash
# Install from source
git clone https://github.com/NewFuture/DDNS.git
cd DDNS
python3 -m ddns --help

# Or use one-click install
curl -fsSL https://ddns.newfuture.cc/install.sh | sudo sh

# Set up systemd timer (requires binary or pip install)
ddns task --install 5  # Update every 5 minutes
ddns task --enable
ddns task --status
```

#### macOS

```bash
# Install from source
git clone https://github.com/NewFuture/DDNS.git
cd DDNS
python3 -m ddns --help

# Or use pip
pip3 install ddns
ddns --help

# Set up launchd (requires binary or pip install)
ddns task --install 5  # Update every 5 minutes
ddns task --enable
ddns task --status
```

#### Windows

```bash
# Download binary from releases
# https://github.com/NewFuture/DDNS/releases/latest

# Run in PowerShell or CMD
ddns.exe --help

# Or install via pip
pip install ddns
ddns --help

# Set up Task Scheduler (requires binary or pip install)
ddns task --install 5  # Update every 5 minutes
ddns task --enable
ddns task --status
```

#### Raspberry Pi (ARM)

```bash
# Use Docker (recommended)
docker pull newfuture/ddns:latest
docker run --rm newfuture/ddns:latest --help

# Or download ARM binary
wget https://github.com/NewFuture/DDNS/releases/latest/download/ddns-linux-arm64
chmod +x ddns-linux-arm64
./ddns-linux-arm64 --help

# Or from source
git clone https://github.com/NewFuture/DDNS.git
cd DDNS
python3 -m ddns --help
```

### 6. Building PyPI Package

```bash
# Install build tools
pip install build twine

# Build package
python3 -m build

# Check built packages
ls -la dist/

# Test installation
pip install dist/ddns-*.whl

# Upload to PyPI (requires credentials)
python3 -m twine upload dist/*

# Upload to Test PyPI (for testing)
python3 -m twine upload --repository testpypi dist/*
```

### 7. Development Build & Run

```bash
# Install in editable mode
pip install -e .

# Run directly
ddns --help

# Or as module
python3 -m ddns --help

# Rebuild after changes (editable mode updates automatically)
# No rebuild needed for Python code changes

# Run tests
python3 -m unittest discover tests -v

# Lint and format
ruff check --fix --unsafe-fixes .
ruff format .
```

---

## Troubleshooting Guidelines

### How to Validate Changes

#### 1. Validate Code Syntax

```bash
# Check Python syntax
python3 -m py_compile ddns/provider/mynewprovider.py

# Check all Python files
find ddns -name "*.py" -exec python3 -m py_compile {} \;

# Lint code
ruff check .

# Format check (without modifying)
ruff format --check .
```

#### 2. Validate Tests

```bash
# Run all tests
python3 -m unittest discover tests -v

# Run specific tests
python3 -m unittest tests.test_provider_mynewprovider -v

# Check test coverage
pytest tests/ --cov=ddns --cov-report=term-missing
```

#### 3. Validate Configuration

```bash
# Validate JSON schema
python3 -c "import json; json.load(open('schema/v4.1.json'))"

# Validate config file
python3 -c "import json; json.load(open('config.json'))"

# Test config loading
python3 -m ddns -c config.json --help
```

#### 4. Validate Documentation

```bash
# Check markdown syntax (requires markdownlint)
markdownlint doc/**/*.md

# Check links (requires markdown-link-check)
find doc -name "*.md" -exec markdown-link-check {} \;

# Manual check
cat doc/providers/mynewprovider.md
cat doc/providers/mynewprovider.en.md
```

#### 5. Validate Provider Implementation

```bash
# Test with debug provider first
python3 -m ddns --dns=debug --ipv4=test.com --debug

# Test new provider with real credentials (be careful!)
python3 -m ddns --dns=myprovider --id=test_id --token=test_token --ipv4=test.com --debug

# Check logs
tail -f dns.log
```

### How to Fix Build Errors

#### Common Build Errors

**Error 1: Import Error**

```bash
# Symptom
ImportError: No module named 'ddns.provider.mynewprovider'

# Solution 1: Check file exists
ls -la ddns/provider/mynewprovider.py

# Solution 2: Check provider registration
grep mynewprovider ddns/provider/__init__.py

# Solution 3: Verify Python path
python3 -c "import sys; print(sys.path)"
export PYTHONPATH=/path/to/DDNS:$PYTHONPATH
```

**Error 2: Syntax Error**

```bash
# Symptom
SyntaxError: invalid syntax

# Solution: Check Python version compatibility
python3 --version

# Common issues:
# - f-strings (not supported in Python 2.7)
# - async/await (not supported in Python 2.7)
# - Type annotations (use type comments instead)

# Fix: Use compatible syntax
# Bad:  result = f"Value: {value}"
# Good: result = "Value: {}".format(value)
```

**Error 3: Test Failures**

```bash
# Symptom
FAIL: test_query_zone_id_success
AssertionError: None != 'zone123'

# Solution: Check mock setup
# Ensure mock returns correct value
mock_http.return_value = {"zone_id": "zone123"}

# Check method calls
self.provider._query_zone_id("example.com")

# Debug: Add print statements
print("Mock called with:", mock_http.call_args)
```

**Error 4: Linting Errors**

```bash
# Symptom
E501 line too long (121 > 120 characters)

# Solution: Run auto-fix
ruff check --fix --unsafe-fixes .

# Or format code
ruff format .

# Manual fix: Break long lines
# Bad
result = self.provider.do_something_with_very_long_method_name_and_many_parameters(param1, param2, param3, param4)

# Good
result = self.provider.do_something_with_very_long_method_name_and_many_parameters(
    param1, param2, param3, param4
)
```

#### CI Build Failures

**Check GitHub Actions logs**:
1. Go to repository on GitHub
2. Click "Actions" tab
3. Click on failed workflow
4. Review logs for specific error

**Common CI failures**:

1. **Linting failure**:
   ```bash
   # Fix locally before pushing
   ruff check --fix --unsafe-fixes .
   ruff format .
   git add .
   git commit --amend --no-edit
   git push --force
   ```

2. **Test failure on specific Python version**:
   ```bash
   # Test locally with specific Python version
   python2.7 -m unittest discover tests -v
   python3.12 -m unittest discover tests -v
   
   # Fix compatibility issues
   # Use type comments, not annotations
   # Use .format() or %, not f-strings
   # Handle unicode strings carefully
   ```

3. **Docker build failure**:
   ```bash
   # Test Docker build locally
   docker build -t ddns:test -f docker/Dockerfile .
   
   # Check entrypoint script
   docker run --rm --entrypoint sh ddns:test -c "ls -la /bin/ddns"
   ```

### How to Debug Runtime Issues

#### Enable Debug Mode

```bash
# Run with debug flag
python3 -m ddns --debug --dns=myprovider --ipv4=test.com

# Enable debug logging in config
python3 -m ddns -c config.json --log_level=DEBUG

# Write debug log to file
python3 -m ddns --debug --log_file=debug.log
```

#### Common Runtime Issues

**Issue 1: Authentication Failed**

```bash
# Symptom
ERROR: Authentication failed: 401 Unauthorized

# Debug steps:
# 1. Verify credentials
python3 -m ddns --dns=myprovider --id=YOUR_ID --token=YOUR_TOKEN --debug

# 2. Check provider API endpoint
# Look for API calls in debug output

# 3. Test API manually
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.provider.com/zones

# 4. Check provider implementation
# Verify authentication headers/params in provider code
```

**Issue 2: DNS Record Not Updated**

```bash
# Symptom
INFO: IP not changed, skipping update

# Debug steps:
# 1. Check cache
rm -f /tmp/ddns.cache
python3 -m ddns --no-cache --debug

# 2. Force update
python3 -m ddns --debug --ipv4=test.com

# 3. Check IP detection
python3 -c "from ddns.ip import get_ip; print(get_ip('default', 4))"

# 4. Verify DNS record
nslookup test.com
dig test.com A
```

**Issue 3: Network/Proxy Issues**

```bash
# Symptom
ERROR: Connection timeout

# Debug steps:
# 1. Test without proxy
python3 -m ddns --dns=myprovider --debug

# 2. Test with proxy
python3 -m ddns --dns=myprovider --proxy=http://127.0.0.1:1080 --debug

# 3. Test with multiple proxies (fallback)
python3 -m ddns --dns=myprovider --proxy=SYSTEM --proxy=DIRECT --debug

# 4. Check SSL certificate
python3 -m ddns --dns=myprovider --ssl=false --debug
```

**Issue 4: Python Compatibility Issues**

```bash
# Symptom (Python 2.7)
SyntaxError: invalid syntax
AttributeError: 'str' object has no attribute 'format_map'

# Debug steps:
# 1. Check Python version
python --version

# 2. Test with Python 3
python3 -m ddns --help

# 3. Fix compatibility issues
# Use type comments, not annotations
# Use .format() or %, not f-strings
# Import from __future__ for Python 2.7 features
```

#### Using Python Debugger

```bash
# Run with pdb debugger
python3 -m pdb -m ddns --dns=debug --ipv4=test.com

# Set breakpoint in code
# Add this line where you want to break:
import pdb; pdb.set_trace()

# Common pdb commands:
# n - next line
# s - step into function
# c - continue execution
# p variable - print variable
# l - list source code
# q - quit debugger
```

#### Checking Logs

```bash
# Enable file logging
python3 -m ddns --log_file=ddns.log --log_level=DEBUG

# View logs
tail -f ddns.log

# Search logs
grep ERROR ddns.log
grep "API" ddns.log
```

### Validation Checklist

Before submitting changes, verify:

- [ ] **Code syntax**: `python3 -m py_compile ddns/**/*.py`
- [ ] **Tests pass**: `python3 -m unittest discover tests -v`
- [ ] **Linting**: `ruff check .` (no errors)
- [ ] **Formatting**: `ruff format --check .` (no changes needed)
- [ ] **Python 2.7 compatible**: No f-strings, no async/await, type comments
- [ ] **Documentation updated**: Both Chinese and English versions
- [ ] **No external dependencies**: Only standard library
- [ ] **Manual testing**: Tested with debug provider at minimum
- [ ] **Commit message**: Follows conventional commits format

---

## Safety Guidelines

### Never Delete Files Unless Explicitly Told

**Rules**:
- Do NOT delete files unless specifically requested
- Do NOT remove "unused" code without verification
- Do NOT delete test files, even if tests are outdated
- Always ask for confirmation before large-scale deletions

**Safe operations**:
- Adding new files
- Editing existing files
- Creating backup copies before major changes
- Renaming files (with confirmation)

**Example safe workflow**:
```bash
# Safe: Adding new provider
touch ddns/provider/newprovider.py
# OK to create

# Safe: Editing existing file
vim ddns/provider/cloudflare.py
# OK to edit

# UNSAFE: Deleting provider without confirmation
rm ddns/provider/oldprovider.py
# Ask user first!

# UNSAFE: Removing "unused" tests
rm tests/test_old_feature.py
# Tests may be needed for compatibility!
```

### Avoid Harmful Refactors

**Harmful refactors** to avoid:
- Changing working code just for style preferences
- Breaking Python 2.7 compatibility for "modern" syntax
- Removing "redundant" error handling
- Changing API interfaces without version bump
- Mass renaming of variables/functions
- Removing "unnecessary" imports (may be used elsewhere)

**Safe refactors**:
- Fixing actual bugs
- Improving error messages
- Adding new features without breaking existing ones
- Optimizing performance with proven benefits
- Reducing code duplication with clear benefits

**Before refactoring, ask**:
1. Is this code actually broken or just different style?
2. Will this break existing users?
3. Is there a test covering this code?
4. Does this maintain Python 2.7 compatibility?
5. Is this change necessary or just preference?

**Refactoring checklist**:
- [ ] Tests pass before refactoring
- [ ] Tests pass after refactoring
- [ ] No breaking changes to public APIs
- [ ] Python 2.7 compatibility maintained
- [ ] Documentation updated if API changed
- [ ] Performance not degraded (if applicable)

### Ask for Confirmation Before Large-Scale Edits

**Large-scale edits** requiring confirmation:
- Renaming files or directories
- Changing file structure
- Refactoring multiple modules
- Changing configuration formats
- Updating all providers
- Mass search-and-replace operations

**Always confirm before**:
```bash
# Renaming files
mv ddns/provider/old.py ddns/provider/new.py

# Mass changes
find ddns -name "*.py" -exec sed -i 's/old_function/new_function/g' {} \;

# Restructuring
mv ddns/utils ddns/util

# Changing formats
# Converting all config files from JSON to YAML
```

**How to ask for confirmation**:
1. Explain what you want to do
2. Explain why it's necessary
3. List potential impacts
4. Ask explicitly for permission
5. Provide alternative approaches

**Example**:
```text
I noticed the provider implementations have duplicated error handling.
I'd like to refactor this into a shared utility function.

Changes:
- Add ddns/util/error.py with shared error handler
- Update 15 provider files to use it
- Add tests for new utility

Potential impacts:
- All providers will be modified
- May introduce bugs if not careful
- Will require extensive testing

Alternatives:
- Leave as-is (no risk)
- Refactor incrementally (lower risk)
- Refactor only new providers (minimal risk)

May I proceed with this refactoring? Or would you prefer an alternative?
```

### General Safety Principles

1. **Make minimal changes**: Change only what's necessary
2. **Test thoroughly**: Test before and after changes
3. **Maintain compatibility**: Don't break existing users
4. **Document changes**: Update docs with code changes
5. **Ask when uncertain**: Better to ask than break things
6. **Review changes**: Review diff before committing
7. **Incremental changes**: Small PRs over large rewrites
8. **Backup first**: Keep original code accessible
9. **Follow conventions**: Don't introduce new patterns
10. **Respect existing code**: There may be reasons for "odd" code

### Emergency Rollback

If you make a mistake:

```bash
# Revert last commit
git revert HEAD

# Undo uncommitted changes
git checkout -- file.py

# Restore deleted file
git checkout HEAD -- deleted_file.py

# Reset to previous state (WARNING: loses changes)
git reset --hard HEAD~1

# Restore from backup
cp file.py.backup file.py
```

---

## Summary

This guide provides comprehensive instructions for AI agents working on the DDNS project. Key points:

1. **Architecture**: Modular Python project with provider system, configuration management, and task scheduling
2. **Development**: Follow Python standards, maintain Python 2.7 compatibility, use ruff for linting
3. **Testing**: Use unittest (primary) or pytest (optional), write comprehensive tests
4. **Building**: Support for Python source, PyPI, Docker, and binary executables
5. **Documentation**: Maintain both Chinese and English versions
6. **Safety**: Avoid unnecessary changes, ask before large edits, never delete without confirmation

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
