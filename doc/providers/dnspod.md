# DNSPod 中国版 配置指南

## 概述

DNSPod (dnspod.cn) 在中国大陆地区广泛使用，后被腾讯云收购。本 DDNS 项目支持两种认证方式连接 DNSPod：

1. **API Token**（推荐）
2. **邮箱 + 密码**（传统）
3. AccessKey（腾讯云 DNSPod）[参考](tencentcloud.md)

## 认证方式

### 1. API Token（推荐）

API Token 方式更安全，是 DNSPod 推荐的集成方法。

#### 获取 API Token

1. 登录 [DNSPod 控制台](https://console.dnspod.cn/)
2. 进入“用户中心” > “API 密钥”或访问 <https://console.dnspod.cn/account/token/token>
3. 点击“创建密钥”，填写描述，选择域名管理权限，完成创建
4. 复制 **ID**（数字）和 **Token**（字符串），密钥只显示一次，请妥善保存

```json
{
    "dns": "dnspod",
    "id": "123456",
    "token": "abcdef1234567890abcdef1234567890"
}
```

- `id`：API Token ID
- `token`：API Token 密钥
- `dns`：固定为 `"dnspod"`

### 2. 邮箱 + 密码（传统）

使用 DNSPod 账号邮箱和密码，安全性较低，仅建议特殊场景使用。

```json
{
    "id": "your-email@example.com",
    "token": "your-account-password",
    "dns": "dnspod"
}
```

- `id`：DNSPod 账号邮箱
- `token`：DNSPod 账号密码
- `dns`：固定为 `"dnspod"`

## 完整配置示例

```json
{
    "id": "123456",
    "token": "abcdef1234567890abcdef1234567890abcdef12",
    "dns": "dnspod",
    "index4": ["public"],
    "index6": ["public"],
    "ipv4": ["home.example.com"],
    "ipv6": ["home.example.com", "nas.example.com"],
    "line": "默认",
    "ttl": 600
}
```

## 可选参数

### 可选参数一览

| 参数   | 说明         | 类型   | 取值范围/示例         | 默认值   |
|--------|--------------|--------|-----------------------|----------|
| ttl    | 生存时间     | int    | 1-604800（秒）        | 600      |
| line   | 线路        | str    | "默认"、"电信"、"联通"、"移动"等 | "默认"   |

> **注意**：`ttl` 和 `line` 不同套餐支持的值可能不同。

## 故障排除

### 常见问题

#### “认证失败”

- 检查 API Token 或邮箱/密码是否正确
- 确认有域名管理权限

#### “域名未找到”

- 域名已添加到 DNSPod 账号
- 配置拼写无误
- 域名处于活跃状态

#### “记录创建失败”

- 检查子域名是否有冲突记录
- TTL 合理
- 有修改权限

### 调试模式

启用调试日志：

```sh
ddns --debug
```

## 支持与资源

- [DNSPod 文档](https://docs.dnspod.cn/)
- [API 参考](https://docs.dnspod.cn/api/)
- [腾讯云DNSPod(AccessKey)](./tencentcloud.md) (DNSPod 的 AccessKey 方式)

> 推荐使用 API Token 方式，提升安全性与管理便捷性。
