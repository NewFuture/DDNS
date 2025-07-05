# 阿里云边缘安全加速 (ESA) 配置指南

## 概述

阿里云边缘安全加速（ESA）是阿里云提供的边缘安全加速服务，支持CDN加速和边缘安全防护。本 DDNS 项目支持通过阿里云AccessKey进行ESA DNS记录的管理。

## 认证方式

### AccessKey 认证

ESA API使用与阿里云其他服务相同的AccessKey认证方式，需要提供AccessKey ID和AccessKey Secret。

```json
{
    "id": "your_access_key_id",
    "token": "your_access_key_secret",
    "dns": "aliesa"
}
```

## 完整配置示例

### 基础配置

```json
{
    "id": "LTAI4xxx",
    "token": "xxx",
    "dns": "aliesa",
    "ipv4": ["www.example.com", "api.example.com"],
    "ipv6": ["ipv6.example.com"]
}
```

### 高级配置

```json
{
    "id": "LTAI4xxx", 
    "token": "xxx",
    "dns": "aliesa",
    "ipv4": ["www.example.com", "api.example.com"],
    "ipv6": ["ipv6.example.com"],
    "ttl": 300
}
```

## 可选参数

| 参数 | 说明 | 类型 | 默认值 | 示例 |
|------|------|------|--------|------|
| `ttl` | DNS记录的TTL值 | 整数 | 600 | 300 |

## 使用场景

### 动态IP的CDN源站

当你的NAS或其他服务作为ESA的CDN源站时，可以使用此DDNS来自动更新源站IP：

```json
{
    "id": "LTAI4xxx",
    "token": "xxx", 
    "dns": "aliesa",
    "ipv4": ["origin.example.com"]
}
```

## 权限要求

确保使用的阿里云账号具有以下ESA权限：

- **ESA站点查询权限**：用于查询站点ID (`esa:ListSites`)
- **ESA DNS记录管理权限**：用于查询、创建和更新DNS记录 (`esa:ListRecords`, `esa:CreateRecord`, `esa:UpdateRecord`)

推荐创建专门的RAM子账号并仅授予必要的ESA权限。

### 如何获取站点ID

1. 登录[阿里云ESA控制台](https://esa.console.aliyun.com/)
2. 选择对应的站点
3. 在站点详情页面的URL中可以看到站点ID，或使用API调用`ListSites`获取

## API限制

- **站点数量**：根据ESA套餐不同
- **DNS记录数量**：根据ESA套餐不同
- **API调用频率**：遵循阿里云ESA API限制

## 故障排除

### 常见问题

#### "Site not found for domain"

- 检查域名是否已添加到ESA服务
- 确认域名格式正确（不包含协议前缀）
- 验证AccessKey权限

#### "Failed to create/update record"

- 检查DNS记录类型是否支持
- 确认记录值格式正确
- 验证TTL值在允许范围内

#### "API调用失败"

- 检查AccessKey ID和Secret是否正确
- 确认网络连接正常
- 查看详细错误日志

### 调试模式

启用调试模式查看详细的API交互信息：

```json
{
    "id": "LTAI4xxx",
    "token": "xxx",
    "dns": "aliesa",
    "debug": true,
    "ipv4": ["www.example.com"]
}
```

## 支持与资源

- [阿里云ESA产品文档](https://help.aliyun.com/product/122312.html)
- [阿里云ESA API文档](https://help.aliyun.com/zh/edge-security-acceleration/esa/api-esa-2024-09-10-overview)
- [阿里云ESA控制台](https://esa.console.aliyun.com/)
- [阿里云技术支持](https://selfservice.console.aliyun.com/ticket)

> 建议使用RAM子账号并仅授予必要的ESA权限，以提高安全性。定期轮换AccessKey以确保账号安全。
