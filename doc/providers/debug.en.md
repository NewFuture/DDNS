# Debug Provider Configuration Guide

## Overview

Debug Provider is a virtual DNS provider specifically designed for debugging and testing purposes. It simulates the DNS record update process but does not perform any actual operations, only outputs relevant information to the console to help developers debug DDNS configuration and functionality.

Official Links:

- Project Homepage: [DDNS Project](https://github.com/NewFuture/DDNS)
- Development Documentation: [Provider Development Guide](../dev/provider.en.md)

### Important Notice

- Debug Provider **is only for debugging and testing**, it does not perform any actual DNS update operations
- Only prints detected IP addresses and domain information to the console
- Suitable for verifying configuration file format and IP address detection functionality

## Authentication Information

Debug Provider does not require any authentication information, no need to configure `id` and `token` parameters.

```jsonc
{
    "dns": "debug"  // Only need to specify provider as debug
}
```

## Complete Configuration Example

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // Format validation
    "dns": "debug",                     // Current provider
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4 address source
    "index6": "public",                     // IPv6 address source
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 domains
    "ipv6": ["ipv6.ddns.newfuture.cc"], // IPv6 domains
    "cache": false,                    // Recommend disabling cache for debugging
    "log": {
        "level": "debug"               // Log level
    }
}
```

### Parameter Description

| Parameter | Description | Type | Range/Options | Default | Parameter Type |
| :-------: | :---------- | :--- | :------------ | :------ | :------------- |
| dns | Provider identifier | String | `debug` | None | Provider Parameter |
| index4 | IPv4 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| index6 | IPv6 source | Array | [Reference](../config/json.en.md#ipv4-ipv6) | `default` | Common Config |
| proxy | Proxy settings | Array | [Reference](../config/json.en.md#proxy) | None | Common Network |
| ssl | SSL verification | Boolean/String | `"auto"`, `true`, `false` | `auto` | Common Network |
| cache | Cache settings | Boolean/String | `true`, `false`, `filepath` | `false` | Common Config |
| log | Log configuration | Object | [Reference](../config/json.en.md#log) | None | Common Config |

> **Parameter Type Description**:
>
> - **Common Config**: Standard DNS configuration parameters applicable to all supported DNS providers
> - **Common Network**: Network setting parameters applicable to all supported DNS providers

## Command Line Usage

```sh
ddns --debug
```

### Specify Parameters

```sh
ddns --dns debug --index4=0 --ipv4=ddns.newfuture.cc --debug
```

### Output Log

```log
INFO  DebugProvider: ddns.newfuture.cc(A) => 192.168.1.100
```

### Error Simulation

Debug Provider also simulates some common error scenarios to help test error handling logic.

## Troubleshooting

### Common Issues

- **No output information**: Check log level settings, ensure DEBUG level is enabled
- **IP detection failed**: Check network connection and IP source configuration
- **Configuration format error**: Use JSON validation tools to check configuration file format

## Support and Resources

- [DDNS Project Documentation](../../README.md)
- [Configuration File Format](../config/json.en.md)
- [Command Line Usage Guide](../config/cli.en.md)
- [Developer Guide](../dev/provider.en.md)
