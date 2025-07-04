# No-IP 配置指南

No-IP 是流行的动态 DNS 服务，支持标准的 No-IP 动态更新协议。

## 配置参数

| 参数 | 说明 | 必需 | 示例 |
|------|------|------|------|
| `dns` | 服务商名称 | ✅ | `"noip"` |
| `id` | No-IP 用户名或 DDNS ID | ✅ | `"your_username"` |
| `token` | No-IP 密码或 DDNS KEY | ✅ | `"your_password"` |

## 配置示例

### 基本配置

```json
{
    "dns": "noip",
    "id": "your_username",
    "token": "your_password",
    "ipv4": ["home.example.com"]
}
```

### 多个域名

```json
{
    "dns": "noip",
    "id": "myusername", 
    "token": "mypassword",
    "ipv4": [
        "home.example.com",
        "office.example.com"
    ],
    "ipv6": ["ipv6.example.com"]
}
```

## 认证方式

### 用户名密码认证

使用 No-IP 账户用户名和密码进行认证。

### DDNS KEY 认证（推荐）

使用 DDNS ID 和 DDNS KEY 进行认证，更安全。

获取方式：登录 [No-IP 官网](https://www.noip.com/) → 创建动态 DNS 主机名 → 生成 DDNS KEY

## 响应代码

| 响应 | 含义 | 状态 |
|------|------|------|
| `good <ip>` | 更新成功 | ✅ |
| `nochg <ip>` | IP 无变化 | ✅ |
| `nohost` | 主机名不存在 | ❌ |
| `badauth` | 认证失败 | ❌ |
| `badagent` | 客户端被禁用 | ❌ |
| `!donator` | 需要付费账户 | ❌ |
| `abuse` | 账户被封禁 | ❌ |

## 故障排除

- **认证失败 (badauth)**：检查用户名和密码
- **主机名不存在 (nohost)**：检查域名拼写
- **需要付费功能 (!donator)**：升级账户
- **账户被封 (abuse)**：联系客服

## 相关链接

- [No-IP 官网](https://www.noip.com/)
- [API 文档](https://www.noip.com/integrate/request)
