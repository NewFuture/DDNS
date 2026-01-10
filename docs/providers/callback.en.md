# Callback Provider Configuration Guide

Callback Provider is a universal custom callback interface that allows you to forward DDNS update requests to any custom HTTP API endpoint or webhook. This provider is highly flexible, supporting GET and POST requests with variable substitution functionality.

## Basic Configuration

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `id` | Callback URL address with variable substitution support | ✅ | `https://api.example.com/ddns?domain=__DOMAIN__&ip=__IP__` |
| `token` | POST request parameters (JSON object or JSON string), empty for GET requests | Optional | `{"api_key": "your_key"}` or `"{\"api_key\": \"your_key\"}"` |
| `endpoint` | Optional API endpoint address, will not participate in variable substitution | Optional | `https://api.example.com/ddns` |
| `dns` | Fixed value `"callback"`, indicates using callback method | ✅ | `"callback"` |

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "callback",
    "endpoint": "https://api.example.com", // endpoint can be merged with id parameter
    "id": "/ddns?domain=__DOMAIN__&ip=__IP__", // endpoint and id cannot both be empty
    "token": "", // empty string means using GET request, with value uses POST request
    "index4": ["url:http://api.ipify.cn", "public"],
    "index6": "public",
    "ipv4": "ddns.newfuture.cc",
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"]
}
```

### Parameter Description

| Parameter | Description | Type | Range/Options | Default | Parameter Type |
| :-------: | :---------- | :--- | :------------ | :------ | :------------- |
| index4 | IPv4 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| index6 | IPv6 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| ipv4 | IPv4 domains | Array | Domain list | None | Common Config |
| ipv6 | IPv6 domains | Array | Domain list | None | Common Config |
| proxy | Proxy settings | Array | [Reference](../config/json.en.md#proxy) | None | Common Network |
| ssl | SSL verification | Boolean/String | `"auto"`, `true`, `false` | `auto` | Common Network |
| cache | Cache settings | Boolean/String | `true`, `false`, `filepath` | `true` | Common Config |
| log | Log configuration | Object | [Reference](../config/json.en.md#log) | None | Common Config |

## Request Methods

| Method | Condition | Description |
|--------|-----------|-------------|
| GET | token is empty | Use URL query parameters |
| POST | token is not empty | Use JSON request body |

### GET Request Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "callback",
    "id": "https://api.example.com/update?domain=__DOMAIN__&ip=__IP__&type=__RECORDTYPE__",
    "index4": ["url:http://api.ipify.cn", "public"],
    "ipv4": "ddns.newfuture.cc"
}
```

```http
GET https://api.example.com/update?domain=ddns.newfuture.cc&ip=192.168.1.100&type=A
```

### POST Request Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json",
    "dns": "callback",
    "endpoint": "https://api.example.com",
    "token": {
        "api_key": "your_secret_key",
        "domain": "__DOMAIN__",
        "value": "__IP__"
    },
    "index4": ["url:http://api.ipify.cn", "public"],
    "ipv4": "ddns.newfuture.cc"
}
```

```http
POST https://api.example.com
Content-Type: application/json

{
  "api_key": "your_secret_key",
  "domain": "ddns.newfuture.cc",
  "value": "192.168.1.100"
}
```

## Variable Substitution

Callback Provider supports the following built-in variables that are automatically replaced during requests:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `__DOMAIN__` | Full domain name | `sub.example.com` |
| `__IP__` | IP address (IPv4 or IPv6) | `192.168.1.100` or `2001:db8::1` |
| `__RECORDTYPE__` | DNS record type | `A`, `AAAA`, `CNAME` |
| `__TTL__` | Time to live (seconds) | `300`, `600` |
| `__LINE__` | Resolution line | `default`, `unicom` |
| `__TIMESTAMP__` | Current timestamp | `1634567890.123` |

## Usage Scenarios

### 1. Custom Webhook

Send DDNS update notifications to custom webhooks:

```jsonc
{
    "endpoint": "https://hooks.example.com",
    "id": "/webhook",
    "token": {
        "event": "ddns_update",
        "domain": "__DOMAIN__",
        "new_ip": "__IP__",
        "record_type": "__RECORDTYPE__",
        "timestamp": "__TIMESTAMP__"
    },
    "dns": "callback",
    "index4": ["default"]
}
```

### 2. Using String Format Token

When you need to dynamically construct complex JSON strings:

```jsonc
{
    "id": "https://api.example.com/ddns",
    "token": "{\"auth\": \"your_key\", \"record\": {\"name\": \"__DOMAIN__\", \"value\": \"__IP__\", \"type\": \"__RECORDTYPE__\"}}",
    "dns": "callback"
}
```

## Troubleshooting

### Debugging Methods

1. **Enable Debug**: Set `"debug": true` in configuration
2. **View Logs**: Check detailed information in DDNS runtime logs
3. **Test API**: Use curl or Postman to test callback API
4. **Network Check**: Ensure network connectivity and DNS resolution are normal

### Testing Tools

You can use online tools to test callback functionality:

```bash
# Test GET request using curl
curl "https://httpbin.org/get?domain=test.example.com&ip=192.168.1.1"

# Test POST request using curl
curl -X POST "https://httpbin.org/post" \
  -H "Content-Type: application/json" \
  -d '{"domain": "test.example.com", "ip": "192.168.1.1"}'
```

## Related Links

- [DDNS Project Homepage](../../README.md)
- [Configuration File Format](../config/json.en.md)
- [Command Line Usage](../config/cli.en.md)
- [Developer Guide](../dev/provider.en.md)
