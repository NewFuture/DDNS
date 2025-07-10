# Debug Provider

Debug Provider 是一个仅用于调试和测试的虚拟DNS provider。它不进行任何实际的DNS更新操作，只是将IP地址打印到控制台。

使用场景

- 测试DDNS配置是否正确
- 调试IP地址检测功能
- 开发和调试新功能

## 配置示例

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

## 输出示例

```log
DEBUG DebugProvider: example.com(A) => 192.168.1.100
DEBUG DebugProvider: example.com(AAAA) => 2001:db8::1
```

## 注意事项

**仅用于调试**: 不会实际更新DNS记录

## 调试技巧

1. **测试配置**: 使用debug provider验证配置文件格式
2. **检查IP**: 确认IP地址检测是否正常工作

## 相关文档

- [配置文件格式](../json.md)
- [命令行使用](../cli.md)
- [环境变量配置](../env.md)
