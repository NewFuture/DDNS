# DDNS Project - GitHub Copilot Instructions

This is a Python-based Dynamic DNS (DDNS) client that automatically updates DNS records to match the current IP address. It supports multiple DNS providers, IPv4/IPv6, and various configuration methods.

## Project Overview

DDNS is a production-ready, cross-platform DNS client with:
- **15+ DNS provider support**: Including Cloudflare, DNSPod, AliDNS, and more
- **Multi-platform deployment**: Docker, pip package, binary executables, or source
- **Flexible configuration**: CLI arguments, JSON files, environment variables
- **Python 2.7 & 3.x compatibility**: Ensures wide compatibility
- **Zero dependencies**: Uses only Python standard library for core functionality

Please follow these guidelines when contributing:

## Code Standards

### Required Before Each Commit
- Follow Python coding standards as defined in `.github/instructions/python.instructions.md`
- Use only Python standard library modules (no external dependencies)
- Ensure Python 2.7 and 3.x compatibility
- Run tests before committing to ensure all functionality works correctly
- Format and lint code using `ruff` before each commit:
  ```bash
  ruff check --fix --unsafe-fixes .
  ruff format .
  ```

### Development Flow
```bash
# Test: Run all unit tests
python3 -m unittest discover tests -v
# Or with pytest (optional)
python3 -m pytest tests/ -v

# Lint: Check and fix code issues
ruff check --fix --unsafe-fixes .

# Format: Auto-format code
ruff format .
```

### Add a New DNS Provider

Follow the steps below to add a new DNS provider:
- [Python coding standards](./instructions/python.instructions.md)
- [Provider development guide](../doc/dev/provider.md)
- Provider documentation template:[aliyun](../doc/provider/aliyun.md) and [dnspod](../doc/provider/dnspod.md)
  - keep the template structure and fill in the required information
  - remove the not applicable sections or fields
  - in english doc linke the documentation to the english version documentations
  - don't change the ref link [参考配置](../json.md#ipv4-ipv6) in the template. In english documentation, use the english version link [Reference](../json.en.md#ipv4-ipv6)

## Repository Structure
- `ddns/`: Main application code
  - `provider/`: DNS provider implementations (DNSPod, AliDNS, CloudFlare, etc.)
  - `config/`: Configuration management (loading, parsing, validation)
  - `util/`: Utility functions (HTTP client, configuration management, IP detection)
- `tests/`: Unit tests using unittest framework
- `doc/`: Documentation and user guides
  - `providers/`: Provider-specific configuration guides
  - `dev/`: Developer documentation
- `schema/`: JSON configuration schemas
- `docker/`: Docker-related files and scripts

## Key Guidelines
1. Follow Python best practices and maintain cross-platform compatibility
2. Use only standard library modules to ensure self-contained operation
3. Maintain Python 2.7 compatibility (avoid f-strings, async/await)
4. Write comprehensive unit tests for all new functionality
5. Use proper logging and error handling throughout the codebase
6. Document public APIs and configuration options thoroughly
7. Test provider implementations against real APIs when possible
8. Ensure all DNS provider classes inherit from BaseProvider or SimpleProvider

## Testing Guidelines

### Test Structure
- Place tests in `tests/` directory using `test_*.py` naming
- import unittest, patch, MagicMock
  - for all provider tests, use the `from base_test import BaseProviderTestCase, unittest, patch, MagicMock`
  - for all other tests, use `from __init__ import unittest, patch, MagicMock ` to ensure compatibility with both unittest and pytest
- Use unittest (default) or pytest (optional)

### Basic provider Test Template
```python
from base_test import BaseProviderTestCase, patch, MagicMock
from ddns.provider.example import ExampleProvider

class TestExampleProvider(BaseProviderTestCase):
    def setUp(self):
        super(TestExampleProvider, self).setUp()
        self.provider = ExampleProvider(self.id, self.token)

    @patch.object(ExampleProvider, "_http")
    def test_set_record_success(self, mock_http):
        mock_http.return_value = {"success": True}
        result = self.provider.set_record("test.com", "1.2.3.4")
        self.assertTrue(result)
```

### Test Requirements
1. **Unit tests**: All public methods must have tests with mocked HTTP calls
2. **Error handling**: Test invalid inputs and network failures
3. **Python 2.7 compatible**: Use standard library only
4. **Documentation**: Include docstrings for test methods

### Running Tests
```bash
# Run all tests (recommended)
python -m unittest discover tests -v

# Run specific provider
python -m unittest tests.test_provider_example -v
```

See existing tests in `tests/` directory for detailed examples.

## Additional Resources

- **Contributing Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Python Standards**: [python.instructions.md](./instructions/python.instructions.md)
- **Provider Development**: [doc/dev/provider.md](../doc/dev/provider.md)
- **Security Policy**: [SECURITY.md](SECURITY.md)
- **Pull Request Template**: [PULL_REQUEST_TEMPLATE.md](PULL_REQUEST_TEMPLATE.md)

## Quick Start for Contributors

1. Fork and clone the repository
2. Install dev dependencies: `pip install -e ".[dev]"`
3. Make your changes following the coding standards
4. Run tests: `python3 -m unittest discover tests -v`
5. Format and lint: `ruff format . && ruff check --fix --unsafe-fixes .`
6. Submit a pull request with a clear description

## Common Tasks

### Adding a New DNS Provider
1. Create `ddns/provider/newprovider.py` inheriting from `BaseProvider` or `SimpleProvider`
2. Implement required methods with proper error handling
3. Add to `ddns/__init__.py`
4. Create tests in `tests/test_provider_newprovider.py`
5. Add documentation in `doc/providers/newprovider.md`
6. Update `schema/v4.0.json` if needed

### Fixing a Bug
1. Write a failing test that reproduces the bug
2. Fix the issue with minimal changes
3. Ensure all tests pass
4. Update documentation if needed

### Improving Documentation
1. Update relevant `.md` files in `doc/` directory
2. Keep examples synchronized with code
3. Ensure both English and Chinese docs are updated (if applicable)
