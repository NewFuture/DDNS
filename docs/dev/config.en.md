# DDNS Configuration System Development Documentation

This document is for developers, detailing how to extend and modify the DDNS configuration system.

## System Architecture

The DDNS configuration system uses a layered architecture supporting multiple configuration sources:

```text
┌─────────────────────────────────────────────┐
│           Configuration Sources (Priority)   │
├─────────────────────────────────────────────┤
│ CLI Args > JSON File > Env Vars > Defaults  │
├─────────────────────────────────────────────┤
│                Config Class                  │
│           Unified Configuration Interface    │
├─────────────────────────────────────────────┤
│           Providers and App Modules          │
└─────────────────────────────────────────────┘
```

**Core Modules:**

- `ddns/config/cli.py` - Command line argument parsing
- `ddns/config/json.py` - JSON configuration file handling
- `ddns/config/env.py` - Environment variable parsing
- `ddns/config/config.py` - Config class implementation

## Config Class Core Implementation

The Config class is the core of the configuration system, responsible for merging multiple configuration sources:

```python
class Config(object):
    def __init__(self, cli_config=None, json_config=None, env_config=None):
        self._cli_config = cli_config or {}
        self._json_config = json_config or {}  
        self._env_config = env_config or {}
        
        # Configuration attribute initialization
        self.dns = self._get("dns", "debug")
        self.endpoint = self._get("endpoint")  # New endpoint configuration
        
    def _get(self, key, default=None):
        """Get configuration value by priority: CLI > JSON > ENV > default"""
        return (
            self._cli_config.get(key) or 
            self._json_config.get(key) or 
            self._env_config.get(key) or 
            default
        )
```

## Adding New Configuration Parameters

### Step 1: Update JSON Schema

First, add the new parameter to the JSON schema files:

```jsonc
// schema/v4.0.json
{
    "properties": {
        "new_param": {
            "type": "string",
            "description": "Description of new parameter"
        }
    }
}
```

### Step 2: Add CLI Parameter

Add command line parameter support in `ddns/config/cli.py`:

```python
def load_config(description, doc, version, date):
    parser = ArgumentParser(...)
    
    # Add new parameter
    parser.add_argument(
        "--new-param",
        dest="new_param",
        help="Help text for new parameter"
    )
```

### Step 3: Add Environment Variable Support

Add environment variable parsing in `ddns/config/env.py`:

```python
def load_config():
    config = {}
    
    # Add new parameter
    config["new_param"] = os.getenv("DDNS_NEW_PARAM")
    
    return config
```

### Step 4: Update Config Class

Add the new attribute to the Config class in `ddns/config/config.py`:

```python
class Config(object):
    def __init__(self, ...):
        # ... existing code ...
        self.new_param = self._get("new_param")
```

### Step 5: Update Documentation

Update the relevant documentation files:

- `doc/config/cli.en.md` - Add CLI parameter documentation
- `doc/config/env.en.md` - Add environment variable documentation  
- `doc/config/json.en.md` - Add JSON configuration documentation

## Configuration Value Processing

### Type Conversion

The configuration system provides several utility functions for type conversion:

```python
from ddns.config.cli import str_bool

# Boolean conversion
debug = str_bool(config.get("debug", False))

# List conversion
domains = config.get("ipv4", [])
if isinstance(domains, str):
    domains = [d.strip() for d in domains.split(",") if d.strip()]
```

### Value Validation

Add validation logic in the Config class constructor:

```python
class Config(object):
    def __init__(self, ...):
        # ... existing code ...
        self.new_param = self._get("new_param")
        
        # Validation
        if self.new_param and not self._validate_new_param():
            raise ValueError("Invalid new_param value")
    
    def _validate_new_param(self):
        """Validate new parameter value"""
        return True  # Implement validation logic
```

## Configuration Loading Flow

The complete configuration loading process:

```python
def load_all_config():
    # 1. Load command line arguments
    cli_config = cli.load_config(...)
    
    # 2. Load JSON configuration file
    json_config = file.load_config(cli_config.get("config"))
    
    # 3. Load environment variables
    env_config = env.load_config()
    
    # 4. Create Config instance
    config = Config(cli_config, json_config, env_config)
    
    return config
```

## Testing Configuration System

### Unit Testing

Create comprehensive tests for each configuration module:

```python
# tests/test_config_new_param.py
import unittest
from ddns.config.config import Config

class TestConfigNewParam(unittest.TestCase):
    def test_new_param_from_cli(self):
        cli_config = {"new_param": "cli_value"}
        config = Config(cli_config=cli_config)
        self.assertEqual(config.new_param, "cli_value")
    
    def test_new_param_priority(self):
        cli_config = {"new_param": "cli_value"}
        json_config = {"new_param": "json_value"}
        env_config = {"new_param": "env_value"}
        
        config = Config(cli_config, json_config, env_config)
        self.assertEqual(config.new_param, "cli_value")  # CLI has highest priority
```

### Integration Testing

Test the complete configuration loading process:

```python
def test_full_config_loading():
    # Test with actual configuration files and environment variables
    import os
    os.environ["DDNS_NEW_PARAM"] = "test_value"
    
    config = load_all_config()
    assert config.new_param == "test_value"
```

## Best Practices

### 1. Backward Compatibility

When adding new parameters, ensure backward compatibility:

```python
# Support both old and new parameter names
self.new_param = self._get("new_param") or self._get("old_param")
```

### 2. Default Values

Provide sensible defaults for all parameters:

```python
self.new_param = self._get("new_param", "default_value")
```

### 3. Type Safety

Use appropriate type conversion and validation:

```python
# Convert string to integer with validation
try:
    self.timeout = int(self._get("timeout", 30))
except ValueError:
    raise ValueError("Invalid timeout value")
```

### 4. Documentation

Always update documentation when adding new parameters:

- Add parameter to all relevant documentation files
- Include usage examples
- Document default values and valid ranges

## Configuration Schema Validation

The DDNS configuration system uses JSON Schema for validation:

### Schema Structure

```jsonc
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "dns": {
            "type": "string",
            "enum": ["dnspod", "cloudflare", "alidns", ...]
        }
    },
    "required": ["dns"]
}
```

### Adding Schema Validation

Add validation for new parameters:

```json
{
    "properties": {
        "new_param": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_-]+$",
            "minLength": 1,
            "maxLength": 100,
            "description": "New parameter description"
        }
    }
}
```

## Error Handling

### Configuration Errors

Implement proper error handling for configuration issues:

```python
class ConfigError(Exception):
    """Configuration-related errors"""
    pass

class Config(object):
    def __init__(self, ...):
        try:
            self._validate_config()
        except Exception as e:
            raise ConfigError("Configuration validation failed: {}".format(e))
    
    def _validate_config(self):
        """Validate complete configuration"""
        if not self.dns:
            raise ValueError("DNS provider is required")
```

### User-Friendly Messages

Provide clear error messages for common configuration mistakes:

```python
def _validate_dns_provider(self):
    valid_providers = ["dnspod", "cloudflare", "alidns", ...]
    if self.dns not in valid_providers:
        raise ValueError(
            "Invalid DNS provider '{}'. Valid options: {}".format(
                self.dns, ", ".join(valid_providers)
            )
        )
```

## Performance Considerations

### Lazy Loading

Implement lazy loading for expensive configuration operations:

```python
class Config(object):
    def __init__(self, ...):
        self._domains_cache = None
    
    @property
    def domains(self):
        if self._domains_cache is None:
            self._domains_cache = self._parse_domains()
        return self._domains_cache
```

### Configuration Caching

Cache parsed configuration to avoid repeated processing:

```python
import functools

@functools.lru_cache(maxsize=1)
def load_json_config(config_file):
    """Load and cache JSON configuration"""
    return json.load(open(config_file))
```

## Debugging Configuration

### Debug Output

Add debug output for configuration troubleshooting:

```python
def debug_config(self):
    """Print configuration debug information"""
    print("Configuration Sources:")
    print("  CLI: {}".format(self._cli_config))
    print("  JSON: {}".format(self._json_config))
    print("  ENV: {}".format(self._env_config))
    print("Final Configuration:")
    for attr in dir(self):
        if not attr.startswith("_"):
            print("  {}: {}".format(attr, getattr(self, attr)))
```

### Configuration Validation

Add validation checks that can be enabled in debug mode:

```python
def validate_all(self):
    """Comprehensive configuration validation"""
    errors = []
    
    if not self.dns:
        errors.append("DNS provider not specified")
    
    if not self.token:
        errors.append("Authentication token not provided")
    
    if errors:
        raise ConfigError("Configuration errors: {}".format("; ".join(errors)))
```

## Summary

The DDNS configuration system is designed to be:

- **Flexible**: Support multiple configuration sources
- **Extensible**: Easy to add new parameters
- **Robust**: Comprehensive validation and error handling
- **User-friendly**: Clear documentation and error messages

When extending the configuration system, always follow these principles and update all relevant documentation and tests.
