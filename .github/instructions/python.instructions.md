---
applyTo: '**/*.py'
---

# Python Coding Standards and Best Practices

## Core Principles

## Gihub Copilot Agent Usage

- **Minimize Terminal Usage**: Use terminal commands sparingly to reduce complexity
- **Windows Compatibility**: Avoid `&&` and `||` operators that may not work on all shells
- **No Directory Changes**: Avoid `cd` commands; you are always in the project root
- **terminal Usage**: run command `python3` instead of `python`, and this is the only command you should use

### Dependencies and Environment

- **Standard Library Only**: Use only Python standard library modules unless explicitly permitted
- **Self-Contained**: Code must run without third-party dependencies on Windows, macOS, and Linux
- **No External Dependencies**: Avoid pip packages to ensure maximum compatibility and easy deployment

### Python 2.7 and 3.x Compatibility

- **Primary Target**: Python 3.x is preferred
- **Legacy Support**: When Python 2.7 compatibility is required, use `six` library patterns
- **Forbidden Features**:
  - NO f-strings (not supported in Python 2.7)
  - NO `async`/`await` syntax
  - Avoid Python 3.6+ exclusive features when compatibility is needed

## Project Architecture

### Directory Structure

```txt
ddns/                    # Main application code
├── provider/           # DNS provider implementations
│   ├── _base.py       # Abstract base classes (SimpleProvider, BaseProvider)
│   └── *.py           # Provider-specific implementations
├── util/              # Utility functions and classes
│   ├── http.py        # HTTP client functionality
│   ├── config.py      # Configuration management
│   └── *.py           # Other utilities
└── __init__.py        # Package initialization

tests/                   # Unit tests
├── base_test.py        # Shared test utilities and base classes
├── test_provider_*.py  # Provider-specific tests
└── README.md          # Testing documentation

doc/                     # Documentation
├── cli.md              # Command line interface documentation
├── docker.md           # Docker usage and deployment guide
├── env.md              # Environment variables reference
├── json.md             # JSON configuration format
├── dev/                # Developer documentation
│   └── provider.md     # Provider development guide
├── providers/          # Provider-specific documentation
│   ├── dnspod.md       # DNSPod configuration guide
│   ├── cloudflare.md   # Cloudflare configuration guide
│   └── *.md            # Other provider guides
└── img/                # Documentation images and diagrams
    ├── ddns.png        # Project logo and icons
    └── ddns.svg        # Vector graphics and diagrams
      
schema/                  # JSON schemas
├── v2.8.json           # Legacy configuration schema v2.8
├── v2.json             # Legacy configuration schema v2
└── v4.0.json           # Current configuration schema v4.0
```

### Provider Architecture

#### SimpleProvider (Basic DNS Provider)

**Purpose**: For DNS providers that only support simple record updates without querying existing records.

**Must Implement**:

- `set_record(domain, value, record_type="A", ttl=None, line=None, **extra)`
  - Updates or creates DNS records
  - Should handle both creation and update logic, if supported by the provider
  - Must return `True` on success, `False` on failure with appropriate error logging
  - Should never raise exceptions for API failures

**Optional**:

- `_validate()` - Custom authentication validation (has default implementation)

**Available Methods**:

- `_http(method, url, ...)` - HTTP/HTTPS requests with automatic error handling
- `_mask_sensitive_data(data)` - Log-safe data masking for security (supports URL-encoded data)

#### BaseProvider (Full CRUD DNS Provider - Recommended for Most Providers)

**Purpose**: For DNS providers supporting complete DNS record management with query capabilities.

**Must Implement**:

- `_query_zone_id(domain)` - Retrieves zone ID for a domain by calling domain info or list domains/zones API
- `_query_record(zone_id, subdomain, main_domain, record_type, line, extra)` - Finds existing DNS record by calling list records or query record API
- `_create_record(zone_id, subdomain, main_domain, value, record_type, ttl, line, extra)` - Creates new DNS record by calling create record API
- `_update_record(zone_id, old_record, value, record_type, ttl, line, extra)` - Updates existing DNS record by calling update record API

**Recommended Practices**:

- Implement a `_request()` method for signed/authenticated HTTP requests:
  - Should raise `Exception` or `RuntimeError` on blocking errors for fast failure
  - Should return `None` or appropriate default on recoverable errors (e.g., NotFound)
- Use `self.logger` for consistent logging throughout the provider

**Inherited Methods**:

- `_http()` - HTTP requests with authentication error handling (raises RuntimeError on 401/403)
- `set_record()` - Automatic record management (orchestrates the above abstract methods)

## Code Quality Standards

### Type Hints and Annotations

```python
# Use complete type hints for all functions
def update_record(self, record_id, value, ttl=None):
    # type: (str, str, int | None) -> bool
    """Update DNS record with new value."""
    pass

# Use type annotations for class attributes
class Provider:
    auth_id = ""  # type: str
```

### Logging Best Practices

```python
# Use structured logging with appropriate levels and consistent formatting
self.logger.info("Updating record: %s => %s", domain, value)
self.logger.debug("API response: %s", response_data)
self.logger.warning("Record not found: %s", domain)
self.logger.error("API call failed: %s", error)
self.logger.critical("Authentication invalid: %s", auth_error)

# Always mask sensitive data in logs to prevent credential exposure
self.logger.info("Request URL: %s", self._mask_sensitive_data(url))
```

## Documentation Standards

### Documentation Guidelines

- **User Documentation** (`doc/`): End-user guides, CLI usage, and deployment instructions
- **Developer Documentation** (`doc/dev/`): API guides, architecture documentation, and contribution guidelines
- **Code Documentation**: Inline docstrings and comments within source files
- **Configuration Documentation**: JSON schemas with examples and validation rules

### Docstring Format

```python
def create_record(self, zone_id, name, value, record_type="A"):
    # type: (str, str, str, str) -> bool
    """
    Create a new DNS record in the specified zone.
    
    Args:
        zone_id (str): DNS zone identifier
        name (str): Record name (subdomain)
        value (str): Record value (IP address, etc.)
        record_type (str): Record type (A, AAAA, CNAME, etc.)
        
    Returns:
        bool: True if creation successful, False otherwise
        
    Raises:
        RuntimeError: When authentication fails (401/403 errors)
        ValueError: When required parameters are invalid
    """
    pass
```

### Inline Comments

```python
# Explain complex business logic with clear, concise comments
# Attempt to resolve zone automatically by walking up the domain hierarchy
domain_parts = domain.split(".")
for i in range(2, len(domain_parts) + 1):
    candidate_zone = ".".join(domain_parts[-i:])
    zone_id = self._query_zone_id(candidate_zone)
    if zone_id:
        break
```

## Testing Guidelines

All tests must be placed in the `tests/` directory, with a shared base test class for common functionality.

### Test Structure

```python
# tests/test_provider_example.py
from base_test import BaseProviderTestCase, MagicMock, patch

class TestExampleProvider(BaseProviderTestCase):
    def setUp(self):
        super(TestExampleProvider, self).setUp()
        self.provider = ExampleProvider(self.auth_id, self.auth_token)
    
    @patch("ddns.provider.example._http")
    def test_create_record_success(self, mock_http):
        # Arrange
        mock_http.return_value = {"id": "record123", "status": "success"}
        
        # Act
        result = self.provider._create_record("zone1", "test", "example.com", "1.2.3.4", "A", None, None, {})
        
        # Assert
        self.assertTrue(result)
        mock_http.assert_called_once()
```

## Performance and Security

### HTTP Client Usage

```python
# Always use the base class _http method for consistent behavior
response = self._http("POST", "/api/records", 
                     body={"name": name, "value": value},
                     headers={"Content-Type": "application/json"})

# Handle authentication errors appropriately
# Note: 401/403 errors will automatically raise RuntimeError
if response is None:
    self.logger.error("API request failed")
    return False
```

## Development Workflow

### Code Validation

- **Linting**: Use editor's Python extensions instead of command-line tools
- **Type Checking**: Ensure Pylance compatibility
- **Testing**: Run tests before committing changes
- **Documentation**: Update relevant documentation when making changes

### Documentation Maintenance

- **API Changes**: Update docstrings and `doc/dev/provider.md` for provider interface changes
- **Configuration Changes**: Update JSON schemas in `schema/` directory
- **User-Facing Changes**: Update CLI documentation in `doc/cli.md`
- **Examples**: Keep code examples in documentation synchronized with actual implementation

### Terminal Usage Guidelines for Copilot Agent

- **Minimize Usage**: Use terminal commands sparingly to reduce complexity
- **Windows Compatibility**: Avoid `&&` and `||` operators that may not work on all shells
- **No Directory Changes**: Use absolute paths instead of `cd` commands for reliability
- **Avoid Manual Compilation**: Use editor extensions for syntax checking instead of `python -c`

### Common Anti-Patterns to Avoid

```python
# DON'T: Use f-strings (incompatible with Python 2.7)
error_msg = f"Failed to update {domain}"  # Not supported in Python 2.7

# DO: Use .format() or % formatting for compatibility
error_msg = "Failed to update {}".format(domain)
error_msg = "Failed to update %s" % domain
error_msg = "Failed to update "+ domain # Concatenation is also acceptable

# DON'T: Use broad type ignores that hide potential issues
result = api_call()  # type: ignore

# DO: Use specific ignores only when absolutely necessary
result = api_call()  # type: ignore[attr-defined]

# DON'T: Return inconsistent types that confuse callers
def get_record(self, name):
    if found:
        return {"id": "123", "name": name}
    return False  # Inconsistent return type

# DO: Return consistent types with clear semantics
def get_record(self, name):
    if found:
        return {"id": "123", "name": name}
    return None  # Consistent with Optional[dict]

# DON'T: Use bare except clauses that hide errors
try:
    result = api_call()
except:
    return None

# DO: Catch specific exceptions and handle appropriately
try:
    result = api_call()
except (ValueError, TypeError) as e:
    self.logger.error("API call failed: %s", e)
    return None
```

## Creating a New Provider

### Development Steps

To create a new DNS provider, follow these steps:

1. **Create a new file** in the `ddns/provider/` directory, e.g., `myprovider.py`.
2. **Implement the provider class** inheriting from `BaseProvider` or `SimpleProvider` as appropriate based on the API capabilities.
   - For the **BaseProvider** interface, implement these required methods:
     - `_query_zone_id(domain)`
     - `_query_record(zone_id, subdomain, main_domain, record_type, line, extra)`
     - `_create_record(zone_id, subdomain, main_domain, value, record_type, ttl, line, extra)`
     - `_update_record(zone_id, old_record, value, record_type, ttl, line, extra)`
   - For the **SimpleProvider** interface, implement this required method:
     - `set_record(domain, value, record_type="A", ttl=None, line=None, **extra)`
3. **Implement the `_request()` method** for authenticated API calls.
4. **Add the provider to the `ddns/__init__.py`** file to make it available in the main package.
5. **Add unit tests** in the `tests/` directory to cover all methods and edge cases.
6. **Update schema** in `schema/v4.0.json` if the provider requires new configuration options.
7. **Create documentation** in `doc/providers/myprovider.md` for configuration and usage instructions.
8. **Run all tests** to ensure compatibility and correctness.

For detailed implementation guidance, refer to the provider development guide in `doc/dev/provider.md`.
