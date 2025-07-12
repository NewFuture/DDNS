# Callback Provider Configuration Guide

The Callback Provider is a universal custom callback interface that allows you to forward DDNS update requests to any custom HTTP API endpoint. This provider is highly flexible, supporting both GET and POST requests with variable substitution functionality.

## Basic Configuration

### Configuration Parameters

| Parameter  | Description                                                   | Required | Example                                                      |
|------------|---------------------------------------------------------------|----------|--------------------------------------------------------------|
| `id`       | Callback URL with variable substitution support               | ✅        | `https://api.example.com/ddns?domain=__DOMAIN__&ip=__IP__`    |
| `token`    | POST request parameters (JSON object or JSON string). Empty for GET | Optional | `{"api_key": "your_key"}` or `"{\"api_key\": \"your_key\"}"` |
| `endpoint` | Optional API endpoint base URL. If omitted, default is blank   | Optional | `https://api.example.com/ddns`                                |
| `dns`      | Must be set to `"callback"` to use callback method           | ✅        | `"callback"`                                                |

### Minimal Configuration Example

```json
{
  "id": "https://api.example.com/ddns?domain=__DOMAIN__&ip=__IP__",
  "token": "",
  "dns": "callback",
  "ipv4": ["sub.example.com"],
  "index4": ["default"]
}
```

## Request Methods

| Method | Condition        | Description              |
|--------|------------------|--------------------------|
| GET    | `token` is empty | Use URL query parameters |
| POST   | `token` provided | Use JSON request body    |

### GET Request Example

```json
{
  "id": "https://api.example.com/update?domain=__DOMAIN__&ip=__IP__&type=__RECORDTYPE__",
  "token": "",
  "dns": "callback",
  "ipv4": ["sub.example.com"],
  "index4": ["default"]
}
```

```http
GET https://api.example.com/update?domain=sub.example.com&ip=192.168.1.100&type=A
```

### POST Request Example

```json
{
  "id": "https://api.example.com/ddns",
  "token": {
    "api_key": "your_secret_key",
    "domain": "__DOMAIN__",
    "value": "__IP__"
  },
  "dns": "callback",
  "ipv4": ["sub.example.com"],
  "index4": ["default"]
}
```

```http
POST https://api.example.com/ddns
Content-Type: application/json

{
  "api_key": "your_secret_key",
  "domain": "sub.example.com",
  "value": "192.168.1.100"
}
```  

## Variable Substitution

The Callback Provider supports the following built-in variables that are automatically replaced during requests:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `__DOMAIN__` | Full domain name | `sub.example.com` |
| `__IP__` | IP address (IPv4 or IPv6) | `192.168.1.100` or `2001:db8::1` |
| `__RECORDTYPE__` | DNS record type | `A`, `AAAA`, `CNAME` |
| `__TTL__` | Time to live (seconds) | `300`, `600` |
| `__LINE__` | DNS line/route | `default`, `unicom` |
| `__TIMESTAMP__` | Current timestamp | `1634567890.123` |

### Variable Substitution Example

**Configuration:**

```json
{
    "id": "https://api.example.com/ddns/__DOMAIN__?ip=__IP__&ts=__TIMESTAMP__",
    "token": {
        "domain": "__DOMAIN__",
        "record_type": "__RECORDTYPE__",
        "ttl": "__TTL__",
        "timestamp": "__TIMESTAMP__"
    },
    "dns": "callback"
}
```

**Actual Request:**

```http
POST https://api.example.com/ddns/sub.example.com?ip=192.168.1.100&ts=1634567890.123
Content-Type: application/json

{
    "domain": "sub.example.com",
    "record_type": "A",
    "ttl": "300",
    "timestamp": "1634567890.123"
}
```

## Use Cases

### 1. Custom Webhook

Send DDNS update notifications to custom webhooks:

```json
{
    "id": "https://hooks.example.com/ddns",
    "token": {
        "event": "ddns_update",
        "domain": "__DOMAIN__",
        "new_ip": "__IP__",
        "record_type": "__RECORDTYPE__",
        "timestamp": "__TIMESTAMP__"
    },
    "dns": "callback"
}
```

### 2. JSON String Format Token

When you need to dynamically construct complex JSON strings:

```json
{
    "id": "https://api.example.com/ddns",
    "token": "{\"auth\": \"your_key\", \"record\": {\"name\": \"__DOMAIN__\", \"value\": \"__IP__\", \"type\": \"__RECORDTYPE__\"}}",
    "dns": "callback"
}
```

## Advanced Configuration

### Error Handling

The Callback Provider logs detailed information:

- **Success**: Logs callback results
- **Failure**: Logs error information and reasons
- **Empty Response**: Logs warning messages

### Security Considerations

1. **HTTPS**: Use HTTPS protocol to protect data transmission
2. **Authentication**: Include necessary authentication information in token
3. **Validation**: Server should validate request legitimacy
4. **Logging**: Avoid exposing sensitive information in logs

## Troubleshooting

### Common Issues

1. **Invalid URL**: Ensure `id` contains a complete HTTP/HTTPS URL
2. **JSON Format Error**: Check if `token` JSON format is correct
   - Object format: `{"key": "value"}`
   - String format: `"{\"key\": \"value\"}"` (note escaped quotes)
3. **Variables Not Replaced**: Ensure variable names are spelled correctly (note double underscores)
4. **Request Failed**: Check if target server is accessible
5. **Authentication Failed**: Verify API keys or authentication information are correct

### Debugging Methods

1. **Enable Debug**: Set `"debug": true` in configuration
2. **Check Logs**: Examine detailed information in DDNS runtime logs
3. **Test API**: Use curl or Postman to test callback API
4. **Network Check**: Ensure network connectivity and DNS resolution work properly

### Testing Tools

You can use online tools to test callback functionality:

```bash
# Test GET request with curl
curl "https://httpbin.org/get?domain=test.example.com&ip=192.168.1.1"

# Test POST request with curl
curl -X POST "https://httpbin.org/post" \
  -H "Content-Type: application/json" \
  -d '{"domain": "test.example.com", "ip": "192.168.1.1"}'
```

## Related Links

- [DDNS Project Home](../../README.md)
- [Configuration File Format](../json.md)
- [Command Line Usage](../cli.md)
- [Developer Guide](../dev/provider.md)
