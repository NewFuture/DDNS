# Debug Provider 配置指南

## 概述

Debug Provider 是一个专门用于调试和测试的虚拟 DNS 服务商。它模拟 DNS 记录更新过程，但不进行任何查询修改操作，只是将相关信息输出到控制台，帮助开发者调试 DDNS 配置和功能。

官网链接：

- 项目主页：[DDNS 项目](https://github.com/NewFuture/DDNS)
- 开发文档：[Provider 开发指南](../dev/provider.md)

### 重要提示

- Debug Provider **仅用于调试和测试**，不会进行任何实际的 DNS 更新操作
- 只会将检测到的 IP 地址和域名信息打印到控制台
- 适合用于验证配置文件格式和 IP 地址检测功能

## 认证信息

Debug Provider 不需要任何认证信息，无需配置 `id` 和 `token` 参数。

```jsonc
{
    "dns": "debug"  // 仅需指定服务商为 debug
}
```

## 完整配置示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "debug",                     // 当前服务商
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 域名
    "ipv6": ["ipv6.ddns.newfuture.cc"], // IPv6 域名
    "cache": false,                    // 建议关闭缓存以便调试
    "log": {
        "level": "debug",               // 日志级别
    }
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `debug`                            | 无        | 服务商参数 |
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `false`   | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数

## 命令行使用

```sh
ddns --debug
```

### 指定参数

```sh
ddns --dns debug --index4=0 --ipv4=ddns.newfuture.cc --debug
```

### 输出Log

```log
INFO  DebugProvider: ddns.newfuture.cc(A) => 192.168.1.100
```

### 错误模拟

Debug Provider 也会模拟一些常见错误场景，帮助测试错误处理逻辑。

## 故障排除

### 常见问题

- **无输出信息**：检查日志级别设置，确保启用了 DEBUG 级别
- **IP 检测失败**：检查网络连接和 IP 来源配置
- **配置格式错误**：使用 JSON 验证工具检查配置文件格式

## 支持与资源

- [DDNS 项目文档](../../README.md)
- [配置文件格式说明](../config/json.md)
- [命令行使用指南](../config/cli.md)
- [开发者指南](../dev/provider.md)
