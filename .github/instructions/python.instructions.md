---
applyTo: '**/*.py'
---

# Python Coding Standards and Preferences

## Dependencies

Do not use any external libraries or modules that are not part of the Python standard library, unless explicitly stated otherwise.

The code should be self-contained and not rely on any third-party packages.  And can be run in windows, macOS, and Linux environments without additional dependencies.

## Python 2.7 and Python 3.x Compatibility

The code should be compatible with both Python 2.7 and Python 3.x versions.

Python 3.x is preferred, but if Python 2.7 compatibility is required, use the `six` library for compatibility.

- DO NOT use f-strings, as they are not supported in Python 2.7.

## Domain Knowledge

- The code is part of a Dynamic DNS (DDNS) project, which updates DNS records dynamically.
- The code interacts with various DNS providers, each with different APIs and requirements.

### Code Structure

- `ddns/` contains the main application code.
- `provider/` contains DNS provider implementations.
  - `_base.py` contains abstract base classes for providers. provide SimpleProvider and BaseProvider.
  - `*.py` the provider implementation based on `_base.py`, specific to each DNS provider.
- `util/` contains utility functions and classes.
- `tests/` contains unit tests for the application.
  - `base_test.py` contains shared test utilities and base classes.
  - `test_provider_*.py` contains tests for each provider.
  - `README.md` contains the testing guide.

### SimpleProvider

SimpleProvider is an abstract base class for DNS providers that only support simple updates without querying existing records.

- Must implement `set_record` method to update or create DNS records.
- `_validate` method is optional and has a default implementation.
- it provides some methods for common operations:
  - `_http` for making HTTP or HTTPS requests. All provider implementations should use this method for network communication.
  - `_encode` for encoding query strings  or form data.

### BaseProvider

BaseProvider is an abstract base class for DNS providers that support full CRUD operations.
It's based on SimpleProvider but requires more methods to be implemented.

- Must implement:
  - Must implement `_query_zone_id`, it's used to query the zone ID for a given domain. you call the list domains (Zone) API or query single zone (domain) by the domain name.
  - Must implement `_query_record`, it's used to query a specific DNS record by its name.
  - Must implement `_create_record`, it's used to create a new DNS record.
  - Must implement `_update_record`, it's used to update an existing DNS record.
- Tips
  - `_validate` method is optional and has a default implementation.
  - `_request` is recommended to use for making HTTP requests with signatures and authorization.
  - logger is recommended to use for logging operations.
- It provides some methods for common operations:
  - `_http` for making HTTP or HTTPS requests. All provider implementations should use this method for network communication.
  - `_encode` for encoding query strings or form data.
  - `_join_domain` for joining subdomain and main domain.

## Typing System with Pylance

- Use type hints for function signatures and variable annotations.
- The typing system should be compatible with Pylance for better type checking and IntelliSense support.
- avoid using `# type: ignore[attr-defined]` comments unless absolutely necessary.
- avoid using `# type: ignore` as much as possible. It's too broad and can hide potential issues.

## Documentation and Comments
- Use docstrings for all public classes and functions.
  - Use Google-style docstrings for consistency for public APIs or methods.
  - Use should or one-line docstrings for private methods and functions.
- Use inline comments to explain complex logic or important decisions.

## shell cmd in agent

- call as less as possible.
- when you need to call shell cmd, avoid using `&&` or `||` in Windows.
- avoid using `cd` in shell commands.