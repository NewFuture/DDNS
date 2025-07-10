# Debug Provider

Debug Provider is a virtual DNS provider used for debugging and testing purposes only. It does not perform any actual DNS updates, but simply prints IP addresses to the console.

## Use Cases

- Test DDNS configuration validity
- Debug IP address detection functionality
- Develop and debug new features

## Configuration Examples

```json
{
  "dns": "debug",
  "index4": ["default"],
  "index6": ["default"],
  "ipv4": [],
  "ipv6": []
}
```

```bash
ddns --dns debug --index4 default --debug
```

## Output Examples

```text
DEBUG DebugProvider: example.com(A) => 192.168.1.100
DEBUG DebugProvider: example.com(AAAA) => 2001:db8::1
```

## Important Notes

**Debug Only**: Does not actually update DNS records

## Debugging Tips

1. **Test Configuration**: Use debug provider to verify configuration file format
2. **Check IP Detection**: Confirm IP address detection is working properly

## Related Documentation

- [Configuration File Format](../json.en.md)
- [Command Line Usage](../cli.en.md)
- [Environment Variables](../env.en.md)
