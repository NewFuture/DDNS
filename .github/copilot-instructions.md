This is a Python-based Dynamic DNS (DDNS) client that automatically updates DNS records to match the current IP address. It supports multiple DNS providers, IPv4/IPv6, and various configuration methods. Please follow these guidelines when contributing:

## Code Standards

### Required Before Each Commit
- Follow Python coding standards as defined in `.github/instructions/python.instructions.md`
- Use only Python standard library modules (no external dependencies)
- Ensure Python 2.7 and 3.x compatibility
- Run tests before committing to ensure all functionality works correctly
- check the lint 

### Development Flow
- Test: `python -m unittest discover tests` or `python -m pytest tests/`
- Format: Use black and flake8 for code formatting

### Add a New DNS Provider

Follow the steps below to add a new DNS provider:
- [Python coding standards](./instructions/python.instructions.md)
- [Provider development guide](../doc/dev/provider.md)

## Repository Structure
- `ddns/`: Main application code
  - `provider/`: DNS provider implementations (DNSPod, AliDNS, CloudFlare, etc.)
  
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
- Inherit from `BaseProviderTestCase` for consistency
- Use unittest (default) or pytest (optional)

### Basic Test Template
```python
from base_test import BaseProviderTestCase, patch, MagicMock
from ddns.provider.example import ExampleProvider

class TestExampleProvider(BaseProviderTestCase):
    def setUp(self):
        super(TestExampleProvider, self).setUp()
        self.provider = ExampleProvider(self.auth_id, self.auth_token)
    
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