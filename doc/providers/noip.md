# No-IP 配置指南 中文文档

## 概述

No-IP是流行的动态DNS服务，支持标准的DDNS动态更新协议，采用Basic Auth认证。本 DDNS 项目支持通过No-IP用户名和密码或DDNS KEY进行认证。

## 认证方式

1. 注册或登录 [No-IP 官网](https://www.noip.com/)
2. 使用注册的用户名和密码
3. 在控制面板中创建主机名（hostname）

### 用户名密码认证

使用No-IP账户用户名和密码进行认证，这是最简单的认证方式。

```json
{
    "dns": "noip",
    "id": "your_username",
    "token": "your_password"
}
```

- `id`：No-IP用户名
- `token`：No-IP密码
- `dns`：固定为 `"noip"`

### DDNS KEY + Id 认证（推荐）

使用DDNS ID和DDNS KEY进行认证，更加安全。

#### 获取DDNS KEY

1. 登录 [No-IP 官网](https://www.noip.com/)
2. 进入 **Dynamic DNS** > **No-IP Hostnames**
3. 创建或编辑动态DNS主机名
4. 生成DDNS KEY用于API认证

```json
{
    "dns": "noip",
    "id": "your_ddns_id",
    "token": "your_ddns_key"
}
```

- `id`：DDNS ID
- `token`：DDNS KEY
- `dns`：固定为 `"noip"`

## 完整配置示例

```json
{
    "id": "myusername",
    "token": "mypassword",
    "dns": "noip",
    "ipv4": ["home.example.com", "office.example.com"],
    "index4": ["public"]
}
```

### 带可选参数的配置

```json
{
    "id": "your_username",
    "token": "your_password",
    "dns": "noip",
    "endpoint": "https://dynupdate.no-ip.com",
    "index4": ["public"],
    "index6": ["public"],
    "ipv4": ["home.example.com"],
    "ipv6": ["home-v6.example.com"]
}
```

## 可选参数

### 自定义API端点

```json
{
    "endpoint": "https://dynupdate.no-ip.com"
}
```

No-IP支持自定义API端点，适用于：

#### 官方端点

- **默认端点**：`https://dynupdate.no-ip.com`（推荐）
- **备用端点**：`https://dynupdate2.no-ip.com`

#### 兼容服务

```json
{
    "dns": "noip",
    "id": "your_username",
    "token": "your_password",
    "endpoint": "https://your-ddns-server.com",
    "ipv4": ["home.example.com"]
}
```

对于No-IP兼容的其他DDNS服务或自定义部署，可以指定不同的API端点。

## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns --debug
```

### No-IP响应代码

| 响应 | 含义 | 状态 |
|------|------|------|
| `good <ip>` | 更新成功 | ✅ |
| `nochg <ip>` | IP地址无变化 | ✅ |
| `nohost` | 主机名不存在 | ❌ |
| `badauth` | 认证失败 | ❌ |
| `badagent` | 客户端被禁用 | ❌ |
| `!donator` | 需要付费账户功能 | ❌ |
| `abuse` | 账户被封禁或滥用 | ❌ |

## API限制

- **更新频率**：建议间隔不少于5分钟
- **免费账户**：30天内需至少一次登录确认
- **主机名数量**：免费账户限制3个主机名

## 支持与资源

- [No-IP官网](https://www.noip.com/)
- [No-IP API文档](https://www.noip.com/integrate/request)
- [No-IP控制面板](https://www.noip.com/members/)
- [No-IP技术支持](https://www.noip.com/support)

> 建议使用DDNS KEY认证方式以提高安全性，定期检查主机名状态确保服务正常运行。
