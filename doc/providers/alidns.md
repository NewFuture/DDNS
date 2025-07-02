# 阿里云DNS 配置指南 中文文档

## 概述

阿里云DNS（AliDNS）是阿里云提供的权威DNS解析服务，支持高并发、高可用性的域名解析。本 DDNS 项目支持通过阿里云AccessKey进行认证。

## 认证方式

### AccessKey 认证

阿里云DNS使用AccessKey ID和AccessKey Secret进行API认证，这是阿里云标准的认证方式。

#### 获取AccessKey

1. 登录 [阿里云控制台](https://ecs.console.aliyun.com/)
2. 访问 [AccessKey管理](https://usercenter.console.aliyun.com/#/manage/ak)
3. 点击"创建AccessKey"按钮
4. 复制生成的 **AccessKey ID** 和 **AccessKey Secret**，请妥善保存
5. 确保账号具有云解析DNS的操作权限

#### 配置示例

```json
{
    "dns": "alidns",
    "id": "LTAI4xxxxxxxxxxxxxxx",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

- `id`：阿里云 AccessKey ID
- `token`：阿里云 AccessKey Secret
- `dns`：固定为 `"alidns"`

## 完整配置示例

### 基本配置

```json
{
    "id": "LTAI4xxxxxxxxxxxxxxx",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "dns": "alidns",
    "ipv6": ["home.example.com", "server.example.com"]
}
```

### 带可选参数的配置

```json
{
    "id": "LTAI4xxxxxxxxxxxxxxx",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "dns": "alidns",
    "ipv6": ["dynamic.mydomain.com"],
    "ttl": 600,
    "record_type": "A",
    "line": "telecom"
}
}
```

## 可选参数

### TTL（生存时间）

```json
{
    "ttl": 600
}
```

- 范围：1-86400 秒
- 默认：600 秒
- 推荐：300-600 秒用于动态DNS

### 记录类型

```json
{
    "record_type": "A"
}
```

- 支持：A、AAAA、CNAME、MX、TXT、SRV等
- 默认：A（IPv4）
- IPv6地址使用"AAAA"类型

### 解析线路

```json
{
    "line": "default"
}
```

- 选项："default"、"telecom"、"unicom"、"mobile"、"oversea"等
- 默认："default"
- 不同套餐支持的线路类型不同

## 权限要求

确保使用的阿里云账号具有以下权限：

- **AliyunDNSFullAccess**：云解析DNS完全访问权限（推荐）
- **AliyunDNSReadOnlyAccess + 自定义写权限**：精细化权限控制

可以在 [RAM访问控制](https://ram.console.aliyun.com/policies) 中查看和配置权限。

## 故障排除

### 常见问题

#### "签名错误"或"认证失败"

- 检查AccessKey ID和AccessKey Secret是否正确
- 确认密钥没有被删除或禁用
- 验证账号权限是否足够

#### "域名不存在"

- 确认域名已添加到阿里云DNS解析
- 检查域名拼写是否正确
- 验证域名状态是否正常

#### "记录操作失败"

- 检查子域名是否存在冲突记录
- 确认TTL值在合理范围内
- 验证解析线路设置是否正确
- 检查域名套餐是否支持该功能

#### "API调用超出限制"

- 阿里云API有QPS限制
- 个人版：20 QPS，企业版：50 QPS
- 适当增加更新间隔

### 调试模式

启用调试日志查看详细信息：

```sh
ddns --debug
```

### 常见错误代码

- **InvalidAccessKeyId.NotFound**：AccessKey不存在
- **SignatureDoesNotMatch**：签名错误
- **DomainRecordDuplicate**：记录重复
- **DomainNotExists**：域名不存在
- **Throttling.User**：用户请求过于频繁

## API限制

- **个人版QPS**：20次/秒
- **企业版QPS**：50次/秒
- **域名数量**：根据套餐不同
- **解析记录**：根据套餐不同

## 支持与资源

- [阿里云DNS产品文档](https://help.aliyun.com/product/29697.html)
- [阿里云DNS API文档](https://help.aliyun.com/document_detail/29739.html)
- [阿里云DNS控制台](https://dns.console.aliyun.com/)
- [阿里云技术支持](https://selfservice.console.aliyun.com/ticket)

> 建议使用RAM子账号并仅授予必要的DNS权限，以提高安全性。定期轮换AccessKey以确保账号安全。
