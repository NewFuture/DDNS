# HE.net (Hurricane Electric) 配置指南

> ⚠️ **重要提示：此provider等待验证**
>
> HE.net缺少充分的真实环境测试，在使用前请仔细测试。如果您使用过程中遇到问题，请及时在 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 中反馈。

## 概述

Hurricane Electric (HE.net) 是提供免费DNS托管服务的知名网络服务商，支持动态DNS更新。本 DDNS 项目支持通过HE.net的动态DNS密码进行认证。

**重要限制**：HE.net **不支持自动创建记录**，必须先在HE.net控制面板中手动创建DNS记录。

## 认证方式

### 动态DNS密码认证

HE.net使用专门的动态DNS密码进行认证，不使用账户登录密码。

#### 获取动态DNS密码

1. 登录 [HE.net DNS管理](https://dns.he.net/)
2. 选择要管理的域名
3. 找到需要动态更新的记录
4. 点击记录旁边的 **Generate a DDNS key** 或 **Enable entry for DDNS**
5. 记录生成的DDNS密码

```json
{
    "dns": "he",
    "token": "your_ddns_password"
}
```

- `token`：HE.net动态DNS密码
- `dns`：固定为 `"he"`
- `id`：**不需要设置**（HE.net不使用用户ID）

## 完整配置示例

```json
{
    "token": "your_ddns_password",
    "dns": "he",
    "index4": ["public"],
    "index6": ["public"],
    "ipv4": ["home.example.com", "server.example.com"],
    "ipv6": ["home-v6.example.com"],
    "ttl": 300
}
```

## 可选参数

| 参数   | 说明             | 范围         | 默认值 | 备注                       |
|--------|------------------|--------------|--------|----------------------------|
| `ttl`  | DNS记录生存时间  | 300-86400秒  | 自动    | 实际TTL由HE.net记录决定    |

## 使用限制

### 重要限制

- ❌ **不支持自动创建记录**：必须先在HE.net控制面板中手动创建DNS记录
- ⚠️ **仅支持更新**：只能更新现有记录的IP地址，不能创建新记录
- 🔑 **专用密码**：每个记录都有独立的DDNS密码

### 使用步骤

1. **创建DNS记录**：在HE.net控制面板中手动创建A或AAAA记录
2. **启用DDNS**：为记录启用动态DNS功能
3. **获取密码**：记录每个记录的DDNS密码
4. **配置DDNS**：使用对应的密码配置动态DNS客户端

可以在 [HE.net DNS管理](https://dns.he.net/) 中查看和管理域名。

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns --debug
```

### HE.net响应代码

| 响应 | 含义 | 状态 |
|------|------|------|
| `good <ip>` | 更新成功 | ✅ |
| `nochg <ip>` | IP地址无变化 | ✅ |
| `nohost` | 主机名不存在或未启用DDNS | ❌ |
| `badauth` | 认证失败 | ❌ |
| `badagent` | 客户端被禁用 | ❌ |
| `abuse` | 更新过于频繁 | ❌ |

## API限制

- **更新频率**：建议间隔不少于5分钟
- **记录数量**：免费账户支持多个域名和记录
- **响应格式**：纯文本响应，非JSON格式

## 支持与资源

- [HE.net官网](https://he.net/)
- [HE.net DNS管理](https://dns.he.net/)
- [HE.net DDNS文档](https://dns.he.net/docs.html)
- [HE.net技术支持](https://he.net/contact.html)

> HE.net是专业的网络服务商，提供稳定的DNS托管服务。使用前请确保已在控制面板中正确配置DNS记录并启用DDNS功能。
