# Extra Fields Feature Examples

This document demonstrates how to use the extra fields feature in DDNS configuration.

## Overview

The extra field feature allows you to pass custom parameters to DNS providers that may require provider-specific options not covered by the standard configuration fields.

## Usage Examples

### 1. Using CLI Arguments

You can specify extra fields using the `--extra.xxx` format:

```bash
# Single extra field
python run.py --dns cloudflare --id user@example.com --token secret --extra.proxied true

# Multiple extra fields
python run.py --dns cloudflare --id user@example.com --token secret \
  --extra.proxied true \
  --extra.comment "Managed by DDNS" \
  --extra.priority 10
```

### 2. Using Environment Variables

Set environment variables with the `DDNS_EXTRA_XXX` prefix:

```bash
export DDNS_DNS=cloudflare
export DDNS_ID=user@example.com
export DDNS_TOKEN=secret
export DDNS_EXTRA_PROXIED=true
export DDNS_EXTRA_COMMENT="Managed by DDNS"
export DDNS_EXTRA_PRIORITY=10

python run.py
```

### 3. Using JSON Configuration File

Add an `extra` object in your JSON config file:

```json
{
  "dns": "cloudflare",
  "id": "user@example.com",
  "token": "secret",
  "ipv4": ["example.com"],
  "extra": {
    "proxied": true,
    "comment": "Managed by DDNS",
    "tags": ["production", "ddns"],
    "priority": 10
  }
}
```

You can also add undefined fields directly in the JSON, and they will be collected as extra fields:

```json
{
  "dns": "cloudflare",
  "id": "user@example.com",
  "token": "secret",
  "ipv4": ["example.com"],
  "proxied": true,
  "comment": "Managed by DDNS"
}
```

## Priority Order

When the same extra field is specified in multiple sources, the priority is:

**CLI Arguments > JSON File > Environment Variables**

Example:
- CLI: `--extra.comment "From CLI"`
- JSON: `"extra": {"comment": "From JSON", "field2": "value2"}`
- ENV: `DDNS_EXTRA_COMMENT="From ENV"`, `DDNS_EXTRA_FIELD3="value3"`

Result: `{"comment": "From CLI", "field2": "value2", "field3": "value3"}`

## Provider-Specific Examples

### Cloudflare

Cloudflare provider supports extra fields like `proxied`, `comment`, `tags`, and `settings`:

```json
{
  "dns": "cloudflare",
  "id": "user@example.com",
  "token": "api_token",
  "ipv4": ["example.com"],
  "extra": {
    "proxied": true,
    "comment": "DDNS managed record",
    "tags": ["production"],
    "settings": {
      "min_tls_version": "1.2"
    }
  }
}
```

### Custom Provider Implementation

If you're developing a custom provider, you can access extra fields in your provider methods:

```python
def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
    # Access extra fields
    custom_field = extra.get("custom_field", "default_value")
    
    # Use them in your API calls
    data = self._request(
        "POST",
        "/api/records",
        name=subdomain,
        type=record_type,
        content=value,
        ttl=ttl,
        custom_field=custom_field,
        **extra  # Pass all extra fields
    )
    return True
```

## Notes

- Extra fields are included in the configuration hash for cache invalidation
- Unknown fields in JSON configuration are automatically collected as extra fields
- Extra fields are passed to provider methods via the `**extra` parameter
- Providers can access extra fields through their `options` attribute
