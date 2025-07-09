# Development Guide: How to Implement a New DNS Provider

This guide explains how to quickly implement a custom DNS provider adapter class based on different abstract base classes to support dynamic DNS record creation and updates.

## 📦 Directory Structure

```text
ddns/
├── provider/
│   ├── _base.py         # Abstract base classes SimpleProvider and BaseProvider, signature auth functions
│   └── myprovider.py    # Your new provider implementation
tests/
├── base_test.py         # Shared test utilities and base classes
├── test_provider_*.py   # Provider-specific test files
├── test_module_*.py     # Other tests
└── README.md            # Testing guide
doc/dev/
└── provider.md          # Provider development guide (this document)
```

---

## 🚀 Quick Start

DDNS provides two abstract base classes. Choose the appropriate base class based on your DNS provider's API characteristics:

### 1. SimpleProvider - Simple DNS Provider

Suitable for DNS providers that only offer simple update interfaces without support for querying existing records.

**Required Methods:**

| Method | Description | Required |
|--------|-------------|----------|
| `set_record(domain, value, record_type="A", ttl=None, line=None, **extra)` | **Update or create DNS record** | ✅ Required |
| `_validate()` | **Validate authentication info** | ❌ Optional (has default implementation) |

**Use Cases:**

- DNS providers that only offer update interfaces (like HE.net)
- Simple scenarios that don't need to query existing records
- Debugging and testing purposes
- Callback/Webhook type DNS updates

### 2. BaseProvider - Full DNS Provider ⭐️ Recommended

Suitable for standard DNS provider APIs that offer complete CRUD operations.

**Required Methods:**

| Method | Description | Required |
|--------|-------------|----------|
| `_query_zone_id(domain)` | **Query zone ID for main domain** | ✅ Required |
| `_query_record(zone_id, subdomain, main_domain, record_type, line=None, extra=None)` | **Query current DNS record** | ✅ Required |
| `_create_record(zone_id, subdomain, main_domain, value, record_type, ttl=None, line=None, extra=None)` | **Create new record** | ✅ Required |
| `_update_record(zone_id, old_record, value, record_type, ttl=None, line=None, extra=None)` | **Update existing record** | ✅ Required |
| `_validate()` | **Validate authentication info** | ❌ Optional (default requires id and token) |

**Built-in Features:**

- ✅ All SimpleProvider functionality
- 🎯 Automatic record management (complete query→create/update workflow)
- 💾 Caching mechanism
- 📝 Detailed operation logging and error handling

**Use Cases:**

- DNS providers with complete REST APIs (like Cloudflare, Alibaba Cloud DNS)
- Scenarios requiring query of existing record status
- Support for precise record management and status tracking

## 🔧 Implementation Examples

### SimpleProvider Example

Suitable for simple DNS providers, refer to existing implementations:

- [`provider/he.py`](/ddns/provider/he.py): Hurricane Electric DNS updates
- [`provider/debug.py`](/ddns/provider/debug.py): Debugging purposes, prints IP addresses
- [`provider/callback.py`](/ddns/provider/callback.py): Callback/Webhook type DNS updates

> provider/mysimpleprovider.py

```python
# coding=utf-8
"""
Custom simple DNS provider example
@author: YourGithubUsername
"""
from ._base import SimpleProvider, TYPE_FORM

class MySimpleProvider(SimpleProvider):
    """
    Example SimpleProvider implementation
    Supports simple DNS record updates, suitable for most simple DNS APIs
    """
    API = 'https://api.simpledns.com'
    content_type = TYPE_FORM          # or TYPE_JSON
    decode_response = False           # Set to False if returns plain text instead of JSON

    def _validate(self):
        """Validate authentication info (optional override)"""
        super(MySimpleProvider, self)._validate()
        # Add specific validation logic, like checking API key format
        if not self.auth_token or len(self.auth_token) < 16:
            raise ValueError("Invalid API token format")

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        """Update DNS record - must implement"""
        # logic to update DNS record
```

### BaseProvider Example

Suitable for standard DNS providers, refer to existing implementations:

- [`provider/dnspod.py`](/ddns/provider/dnspod.py): POST form data, no signature
- [`provider/cloudflare.py`](/ddns/provider/cloudflare.py): RESTful JSON, no signature
- [`provider/alidns.py`](/ddns/provider/alidns.py): POST form + sha256 parameter signature
- [`provider/huaweidns.py`](/ddns/provider/huaweidns.py): RESTful JSON, parameter header signature

> provider/myprovider.py

```python
# coding=utf-8
"""
Custom standard DNS provider example
@author: YourGithubUsername
"""
from ._base import BaseProvider, TYPE_JSON, hmac_sha256_authorization, sha256_hash

class MyProvider(BaseProvider):
    """
    Example BaseProvider implementation
    Suitable for DNS providers offering complete CRUD APIs
    """
    API = 'https://api.exampledns.com'
    content_type = TYPE_JSON  # or TYPE_FORM

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """Query zone ID for main domain"""
        # Exact lookup or list matching

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line=None, extra=None):
        # type: (str, str, str, str, str | None, dict | None) -> Any
        """Query existing DNS record"""

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, str, str, str, str, int | str | None, str | None, dict | None) -> bool
        """Create new DNS record"""

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, dict, str, str, int | str | None, str | None, dict | None) -> bool
        """Update existing DNS record"""

    def _request(self, action, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict
        """[Recommended] Encapsulate common request logic, handle auth and common parameters"""
        # Build request parameters
        request_params = {
            "Action": action,
            "Version": "2023-01-01",
            "AccessKeyId": self.auth_id,
            **{k: v for k, v in params.items() if v is not None}
        }

        res = self._http("POST", "/", params=request_params, headers=headers)
        return res.get("data", {})
```

---

## ✅ Development Best Practices

### Choosing the Right Base Class

1. **SimpleProvider** - For DNS providers with incomplete functionality
   - ✅ DNS provider only offers update API
   - ✅ No need to query existing records

2. **BaseProvider** - Suitable for standard and complex scenarios
   - ✅ DNS provider offers complete query, create, modify APIs
   - ✅ Need precise record state management
   - ✅ Support complex domain resolution logic

### General Development Recommendations

#### 🌐 HTTP Request Handling

```python
# Use built-in _http method, automatically handles proxy, encoding, logging
response = self._http("POST", path, params=params, headers=headers)
```

#### 🔒 Format Validation

```python
def _validate(self):
    """Authentication info validation example"""
    super(MyProvider, self)._validate()
    # Check API key format
    if not self.auth_token or len(self.auth_token) < 16:
        raise ValueError("API token must be at least 16 characters")
```

#### 📝 Logging

```python
if result:
    self.logger.info("DNS record got: %s", result.get("id"))
    return True
else:
    self.logger.warning("DNS record update returned false")
```

---

## 🧪 Testing and Debugging

### Unit Testing

Each Provider should have comprehensive unit tests. The project provides unified test base classes and tools:

```python
# tests/test_provider_myprovider.py
from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.myprovider import MyProvider

class TestMyProvider(BaseProviderTestCase):
    def setUp(self):
        super(TestMyProvider, self).setUp()
        # Provider-specific setup
    
    def test_init_with_basic_config(self):
        """Test basic initialization"""
```

### Running Tests

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific Provider tests
python -m unittest tests.test_provider_myprovider -v

# Run specific test method
python tests/test_provider_myprovider.py
```

---

## 📚 More Resources and Best Practices

### 🏗️ Project Structure Recommendations

```text
ddns/
├── provider/
│   ├── _base.py              # Base class definitions
│   ├── myprovider.py         # Your Provider implementation
│   └── __init__.py           # Import and registration
tests/
├── base_test.py              # Shared test base class
├── test_provider_myprovider.py  # Your Provider tests
└── README.md                 # Testing guide
```

### 📖 Reference Implementations

**SimpleProvider References:**

- [`provider/he.py`](/ddns/provider/he.py) - Hurricane Electric (simple form submission)
- [`provider/debug.py`](/ddns/provider/debug.py) - Debug tool (prints info only)
- [`provider/callback.py`](/ddns/provider/callback.py) - Callback/Webhook mode

**BaseProvider References:**

- [`provider/cloudflare.py`](/ddns/provider/cloudflare.py) - RESTful JSON API
- [`provider/alidns.py`](/ddns/provider/alidns.py) - POST + signature authentication
- [`provider/dnspod.py`](/ddns/provider/dnspod.py) - POST form data submission

---

## 🔐 Cloud Provider Authentication Signature Algorithms

For cloud providers requiring signature authentication (like Alibaba Cloud, Huawei Cloud, Tencent Cloud), DDNS provides generic HMAC-SHA256 signature authentication functions.

### Signature Authentication Utility Functions

#### `hmac_sha256_authorization()` - Generic Signature Generator

Generic cloud provider API authentication signature generation function, supporting Alibaba Cloud, Huawei Cloud, Tencent Cloud and other cloud providers.
Uses HMAC-SHA256 algorithm to generate Authorization headers compliant with various cloud provider specifications.
All cloud provider differences are passed through template parameters, achieving complete provider independence.

```python
from ddns.provider._base import hmac_sha256_authorization, sha256_hash

# Generic signature function call example
authorization = hmac_sha256_authorization(
    secret_key=secret_key,                    # Signature key (already derived)
    method="POST",                            # HTTP method
    path="/v1/domains/records",               # API path
    query="limit=20&offset=0",                # Query string
    headers=request_headers,                  # Request headers dictionary
    body_hash=sha256_hash(request_body),      # Request body hash
    signing_string_format=signing_template,   # Signing string template
    authorization_format=auth_template        # Authorization header template
)
```

**Function Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `secret_key` | `str \| bytes` | Signature key, already processed through key derivation |
| `method` | `str` | HTTP request method (GET, POST, etc.) |
| `path` | `str` | API request path |
| `query` | `str` | URL query string |
| `headers` | `dict[str, str]` | HTTP request headers |
| `body_hash` | `str` | SHA256 hash of request body |
| `signing_string_format` | `str` | Signing string template with `{HashedCanonicalRequest}` placeholder |
| `authorization_format` | `str` | Authorization header template with `{SignedHeaders}`, `{Signature}` placeholders |

**Template Variables:**

- `{HashedCanonicalRequest}` - SHA256 hash of canonical request
- `{SignedHeaders}` - Alphabetically sorted list of signed headers
- `{Signature}` - Final HMAC-SHA256 signature value

### Cloud Provider Signature Implementation Examples

#### Alibaba Cloud (ACS3-HMAC-SHA256)

```python
def _request(self, action, **params):
    # Build request headers
    headers = {
        "host": "alidns.aliyuncs.com",
        "x-acs-action": action,
        "x-acs-content-sha256": sha256_hash(body),
        "x-acs-date": timestamp,
        "x-acs-signature-nonce": nonce,
        "x-acs-version": "2015-01-09"
    }
    
    # Alibaba Cloud signature template
    auth_template = (
        "ACS3-HMAC-SHA256 Credential={access_key},"
        "SignedHeaders={{SignedHeaders}},Signature={{Signature}}"
    )
    signing_template = "ACS3-HMAC-SHA256\n{timestamp}\n{{HashedCanonicalRequest}}"
    
    # Generate signature
    authorization = hmac_sha256_authorization(
        secret_key=self.auth_token,
        method="POST",
        path="/",
        query=query_string,
        headers=headers,
        body_hash=sha256_hash(body),
        signing_string_format=signing_template,
        authorization_format=auth_template
    )
    
    headers["authorization"] = authorization
    return self._http("POST", "/", body=body, headers=headers)
```

#### Tencent Cloud (TC3-HMAC-SHA256)

```python
def _request(self, action, **params):
    # Tencent Cloud requires derived key
    derived_key = self._derive_signing_key(date, service, self.auth_token)
    
    # Build request headers
    headers = {
        "content-type": "application/json",
        "host": "dnspod.tencentcloudapi.com",
        "x-tc-action": action,
        "x-tc-timestamp": timestamp,
        "x-tc-version": "2021-03-23"
    }
    
    # Tencent Cloud signature template
    auth_template = (
        "TC3-HMAC-SHA256 Credential={secret_id}/{date}/{service}/tc3_request, "
        "SignedHeaders={{SignedHeaders}}, Signature={{Signature}}"
    )
    signing_template = "TC3-HMAC-SHA256\n{timestamp}\n{date}/{service}/tc3_request\n{{HashedCanonicalRequest}}"
    
    # Generate signature
    authorization = hmac_sha256_authorization(
        secret_key=derived_key,  # Note: use derived key
        method="POST",
        path="/",
        query="",
        headers=headers,
        body_hash=sha256_hash(body),
        signing_string_format=signing_template,
        authorization_format=auth_template
    )
    
    headers["authorization"] = authorization
    return self._http("POST", "/", body=body, headers=headers)
```

### Helper Utility Functions

#### `sha256_hash()` - SHA256 Hash Calculation

```python
from ddns.provider._base import sha256_hash

# Calculate SHA256 hash of string
hash_value = sha256_hash("request body content")
# Calculate SHA256 hash of binary data
hash_value = sha256_hash(b"binary data")
```

#### `hmac_sha256()` - HMAC-SHA256 Signature Object

```python
from ddns.provider._base import hmac_sha256

# Generate HMAC-SHA256 byte signature
# Get HMAC object, can call .digest() for bytes or .hexdigest() for hex string
hmac_obj = hmac_sha256("secret_key", "message_to_sign")
signature_bytes = hmac_obj.digest()        # Byte format
signature_hex = hmac_obj.hexdigest()       # Hex string format
```

---

### 🛠️ Recommended Development Tools

- Local development environment: VSCode
- Online code editor: GitHub Codespaces or github.dev

### 🎯 Common Issue Solutions

1. **Q: Why choose SimpleProvider over BaseProvider?**
   - A: If the DNS provider only offers update API without query API, SimpleProvider is simpler and more efficient

---

## 🎉 Summary

### Quick Checklist

- [ ] Choose appropriate base class (`SimpleProvider` vs `BaseProvider`)
- [ ] Implement all required methods (with GPT or Copilot assistance)
- [ ] Add appropriate error handling and logging
- [ ] Write comprehensive unit tests (using GPT or Copilot generation)
- [ ] Test various edge cases and error scenarios
- [ ] Update relevant documentation

## Happy Coding! 🚀
