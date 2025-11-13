# Contributing to DDNS

Thank you for your interest in contributing to DDNS! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Adding a New DNS Provider](#adding-a-new-dns-provider)

## Code of Conduct

Please be respectful and constructive in all interactions with the project community.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/DDNS.git
   cd DDNS
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Requirements

- Python 2.7 or Python 3.6+
- Git

### Install Development Dependencies

```bash
# Optional: Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running the Application

```bash
# Run directly from source
python3 run.py --help

# Or use the installed command
ddns --help
```

## Making Changes

### Before Making Changes

1. **Understand the codebase**: Read the [Python coding standards](instructions/python.instructions.md)
2. **Check existing issues**: Look for related issues or discussions
3. **Run tests**: Ensure all tests pass before making changes
   ```bash
   python3 -m unittest discover tests -v
   ```

### Development Workflow

1. **Make your changes** following the coding standards
2. **Format your code** using ruff:
   ```bash
   ruff format .
   ```
3. **Lint your code**:
   ```bash
   ruff check --fix --unsafe-fixes .
   ```
4. **Run tests** to ensure nothing is broken:
   ```bash
   python3 -m unittest discover tests -v
   ```
5. **Add tests** for new functionality
6. **Update documentation** as needed

## Submitting Changes

1. **Commit your changes** with a descriptive commit message following [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "feat(provider): add example provider support"
   git commit -m "fix(util.http): correct authentication logic"
   git commit -m "docs(readme): update installation instructions"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a Pull Request** on GitHub:
   - Fill out the pull request template completely
   - Link any related issues
   - Provide clear description of changes
   - Include test results

## Coding Standards

Please follow the [Python Coding Standards](instructions/python.instructions.md) which include:

### Key Requirements

- **Python 2.7 and 3.x compatibility**: Avoid f-strings, async/await
- **Standard library only**: No external dependencies unless absolutely necessary
- **Type hints**: Use Python 2.7 compatible type comments
- **Logging**: Use structured logging with appropriate levels
- **Error handling**: Catch specific exceptions, not bare except clauses

### Code Style

- **Line length**: Maximum 120 characters
- **Formatting**: Use ruff for automatic formatting
- **Docstrings**: All public methods must have docstrings
- **Comments**: Explain complex logic, not obvious code

### Example

```python
def update_record(self, record_id, value, ttl=None):
    # type: (str, str, int | None) -> bool
    """
    Update DNS record with new value.
    
    Args:
        record_id (str): DNS record identifier
        value (str): New record value (IP address)
        ttl (int | None): Time to live in seconds
        
    Returns:
        bool: True if update successful, False otherwise
    """
    if not record_id or not value:
        self.logger.error("Invalid parameters: record_id=%s, value=%s", record_id, value)
        return False
    
    try:
        response = self._http("POST", "/api/update", 
                            body={"id": record_id, "value": value, "ttl": ttl})
        return response is not None
    except (ValueError, TypeError) as e:
        self.logger.error("Update failed: %s", e)
        return False
```

## Testing

### Running Tests

```bash
# Run all tests
python3 -m unittest discover tests -v

# Run specific test file
python3 -m unittest tests.test_provider_example -v

# With pytest (optional)
pytest tests/ -v
```

### Writing Tests

- Place tests in `tests/` directory
- Use `test_*.py` naming convention
- For provider tests, inherit from `BaseProviderTestCase`
- Mock all HTTP calls
- Test both success and error cases

Example test:

```python
from base_test import BaseProviderTestCase, patch, MagicMock
from ddns.provider.example import ExampleProvider

class TestExampleProvider(BaseProviderTestCase):
    def setUp(self):
        super(TestExampleProvider, self).setUp()
        self.provider = ExampleProvider(self.id, self.token)

    @patch.object(ExampleProvider, "_http")
    def test_create_record_success(self, mock_http):
        mock_http.return_value = {"id": "record123"}
        result = self.provider._create_record("zone1", "test", "example.com", 
                                              "1.2.3.4", "A", None, None, {})
        self.assertTrue(result)
```

## Adding a New DNS Provider

Follow these steps to add support for a new DNS provider:

1. **Create provider file**: `ddns/provider/myprovider.py`
2. **Implement provider class**:
   - Inherit from `BaseProvider` or `SimpleProvider`
   - Implement required methods
   - Add proper error handling and logging
3. **Register provider**: Add to `ddns/__init__.py`
4. **Add tests**: Create `tests/test_provider_myprovider.py`
5. **Update schema**: Modify `schema/v4.0.json` if needed
6. **Add documentation**: Create `doc/providers/myprovider.md`
7. **Test thoroughly**: Run all tests and lint checks

See [Provider Development Guide](doc/dev/provider.md) for detailed instructions.

## Documentation

When making changes, please update relevant documentation:

- **Code comments**: For complex logic
- **Docstrings**: For all public APIs
- **User documentation**: In `doc/` directory
- **README**: For major features or changes
- **Changelog**: Add entry for user-facing changes

## Questions?

If you have questions or need help:

1. Check existing [documentation](https://ddns.newfuture.cc)
2. Search [existing issues](https://github.com/NewFuture/DDNS/issues)
3. Open a new issue with the `question` label

## License

By contributing to DDNS, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
