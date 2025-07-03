# No-IP 配置指南 中文文档

No-IP 是一个流行的动态 DNS 服务，提供简单的基于 HTTP 的 API 来更新 DNS 记录。此 DDNS 项目支持标准的 No-IP 动态更新协议。

## 基本配置

### 配置参数

| 参数 | 说明 | 是否必需 | 示例 |
|------|------|----------|------|
| `id` | No-IP 用户名 | ✅ | `"your_username"` |
| `token` | No-IP 密码 | ✅ | `"your_password"` |
| `dns` | 服务商名称 | ✅ | `"noip"` |

### 最小配置示例

```json
{
    "id": "your_username",
    "token": "your_password", 
    "dns": "noip",
    "ipv4": ["subdomain.example.com"],
    "ipv6": ["ipv6.example.com"]
}
```

## 认证方式

### 用户名和密码

No-IP 使用您的账户用户名和密码进行认证。通过 HTTP 基本认证发送。

#### 如何获取凭据

1. **注册 No-IP 账户**
   - 访问 [No-IP 官网](https://www.noip.com/)
   - 创建免费账户或升级到付费服务

2. **创建动态 DNS 主机名**
   - 登录到您的 No-IP 账户
   - 进入 "Dynamic DNS" > "No-IP Hostnames"
   - 创建新的主机名或使用现有的

3. **使用账户凭据**
   - **用户名**: 您的 No-IP 账户用户名或邮箱
   - **密码**: 您的 No-IP 账户密码

#### 配置示例

```json
{
    "dns": "noip",
    "id": "your_username",
    "token": "your_password"
}
```

**参数说明:**

- `id`: No-IP 账户用户名
- `token`: No-IP 账户密码
- `dns`: 必须设置为 `"noip"`、`"no-ip"` 或 `"noip_com"`

## 响应代码

No-IP API 返回纯文本响应，含义如下：

| 响应 | 含义 | 处理方式 |
|------|------|----------|
| `good <ip>` | 更新成功 | ✅ 成功 |
| `nochg <ip>` | IP 地址当前，无需更新 | ✅ 成功（无需更改） |
| `nohost` | 提供的主机名不存在 | ❌ 检查主机名拼写 |
| `badauth` | 无效的用户名/密码组合 | ❌ 检查凭据 |
| `badagent` | 客户端被禁用 | ❌ 联系 No-IP 支持 |
| `!donator` | 功能不可用（需要升级账户） | ❌ 升级账户 |
| `abuse` | 用户名因滥用被封禁 | ❌ 联系 No-IP 支持 |

## 完整配置示例

### 仅 IPv4

```json
{
    "dns": "noip",
    "id": "myusername",
    "token": "mypassword",
    "ipv4": ["home.example.com", "server.example.com"],
    "ttl": 300
}
```

### IPv4 和 IPv6

```json
{
    "dns": "noip", 
    "id": "myusername",
    "token": "mypassword",
    "ipv4": ["home.example.com"],
    "ipv6": ["ipv6.example.com"],
    "ttl": 600
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
        "server.example.com", 
        "nas.example.com"
    ],
    "debug": true
}
```

## 服务商别名

支持以下等效的服务商名称：

- `"noip"` (主要)
- `"no-ip"` (别名)
- `"noip_com"` (别名)

## API 详情

- **API 端点**: `https://dynupdate.no-ip.com/nic/update`
- **方法**: GET
- **认证**: HTTP 基本认证
- **参数**: `hostname` (域名), `myip` (IP 地址)

## 故障排除

### 常见问题

1. **"badauth" 响应**
   - 验证您的 No-IP 用户名和密码是否正确
   - 确保您可以使用相同凭据登录 No-IP 网站

2. **"nohost" 响应**
   - 检查主机名是否存在于您的 No-IP 账户中
   - 验证配置中的主机名拼写

3. **"!donator" 响应**
   - 功能需要付费 No-IP 账户
   - 升级您的账户或仅使用基本功能

4. **"abuse" 响应**
   - 您的账户已被标记为滥用
   - 联系 No-IP 客户支持

### 调试模式

启用调试模式以查看详细的 API 响应：

```json
{
    "dns": "noip",
    "id": "myusername",
    "token": "mypassword", 
    "ipv4": ["test.example.com"],
    "debug": true
}
```

## 支持的功能

- ✅ IPv4 地址更新
- ✅ IPv6 地址更新  
- ✅ 多主机名支持
- ✅ 自定义 TTL（如果账户类型支持）
- ✅ 全面的错误处理
- ✅ HTTP 基本认证

## 限制

- No-IP 免费账户功能有限
- 某些高级功能需要付费账户
- 可能适用速率限制（参考 No-IP 文档）

## 相关链接

- [No-IP 官方网站](https://www.noip.com/)
- [No-IP 动态更新 API 文档](https://www.noip.com/integrate/request)
- [No-IP 支持](https://www.noip.com/support)

## 示例

### 基本设置

```bash
# 配置文件: config.json
{
    "dns": "noip",
    "id": "your_username",
    "token": "your_password",
    "ipv4": ["home.your-domain.com"]
}

# 运行 DDNS
python run.py -c config.json
```

### 多域名高级设置

```json
{
    "dns": "noip",
    "id": "your_username", 
    "token": "your_password",
    "ipv4": [
        "home.your-domain.com",
        "server.your-domain.com"
    ],
    "ipv6": ["ipv6.your-domain.com"],
    "ttl": 300,
    "proxy": "",
    "debug": false
}
```