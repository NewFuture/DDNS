# 华为云DNS 配置指南

> ⚠️ **重要提示：此provider等待验证**
>
> 华为云DNS缺少充分的真实环境测试，在使用前请仔细测试。如果您使用过程中遇到问题，请及时在 [GitHub Issues](https://github.com/NewFuture/DDNS/issues) 中反馈。

## 概述

华为云DNS是华为云提供的权威DNS解析服务，具有高可用性、高扩展性和高安全性。本 DDNS 项目支持通过华为云访问密钥进行认证。

## 认证方式

### 访问密钥认证

华为云DNS使用Access Key ID和Secret Access Key进行API认证，这是华为云标准的认证方式。

#### 获取访问密钥

1. 登录 [华为云控制台](https://www.huaweicloud.com/)
2. 进入 **我的凭证** > **访问密钥**
3. 点击"新增访问密钥"按钮
4. 复制生成的 **Access Key ID** 和 **Secret Access Key**，请妥善保存
5. 确保账号具有云解析DNS的操作权限

```json
{
    "dns": "huaweidns",
    "id": "your_access_key_id",
    "token": "your_secret_access_key"
}
```

- `id`：华为云 Access Key ID
- `token`：华为云 Secret Access Key
- `dns`：固定为 `"huaweidns"`

## 权限要求

确保使用的华为云账号具有以下权限：

- **DNS Administrator**：云解析DNS完全管理权限（推荐）
- **DNS ReadOnlyAccess + 自定义写权限**：精细化权限控制

可以在 [统一身份认证服务](https://console.huaweicloud.com/iam/) 中查看和配置权限。

## 完整配置示例

```json
{
    "dns": "huaweidns",
    "id": "your_access_key_id",
    "token": "your_secret_access_key",
    "endpoint": "https://dns.myhuaweicloud.com",
    "index4": ["default"],
    "index6": ["default"],
    "ipv4": ["example.com"],
    "ipv6": ["dynamic.mydomain.com"],
    "ttl": 600
}
```

## 可选参数

## 可选参数一览

| 参数名      | 默认值                                   | 说明                                   | 取值范围/选项                         |
|-------------|------------------------------------------|----------------------------------------|----------------------------------------|
| `ttl`       | 自动                                    | DNS记录生存时间（秒）                  | 1-86400                                |
| `line`      | `"default"`                              | 解析线路类型                           | `"default"`、`"unicom"`、`"telecom"`、`"mobile"`、`"overseas"`、`"edu"` 等 |
| `endpoint`  | `"https://dns.myhuaweicloud.com"`         | API服务端点（区域节点）                | 见下方端点列表                          |

> **注意**：`ttl` 和 `line` 的取值范围可能因套餐类型而异。

### 可用端点

- **全球服务**：`https://dns.myhuaweicloud.com`（默认，推荐）

#### 中国大陆

- **华北-北京四**：`https://dns.cn-north-4.myhuaweicloud.com`
- **华东-上海一**：`https://dns.cn-east-3.myhuaweicloud.com`
- **华南-广州**：`https://dns.cn-south-1.myhuaweicloud.com`
- **华北-乌兰察布一**：`https://dns.cn-north-9.myhuaweicloud.com`
- **西南-贵阳一**：`https://dns.cn-southwest-2.myhuaweicloud.com`

#### 海外节点

- **亚太-新加坡**：`https://dns.ap-southeast-3.myhuaweicloud.com`
- **亚太-香港**：`https://dns.ap-southeast-1.myhuaweicloud.com`
- **亚太-曼谷**：`https://dns.ap-southeast-2.myhuaweicloud.com`
- **非洲-约翰内斯堡**：`https://dns.af-south-1.myhuaweicloud.com`
- **拉美-圣地亚哥**：`https://dns.la-south-2.myhuaweicloud.com`
- **拉美-墨西哥城一**：`https://dns.la-north-2.myhuaweicloud.com`
- **拉美-圣保罗一**：`https://dns.sa-brazil-1.myhuaweicloud.com`

#### 选择端点的建议

- **网络优化**：如果在特定地区网络延迟较高，可选择就近的区域端点
- **合规要求**：如果有数据主权要求，选择对应区域的端点

> **注意**：华为云DNS会根据用户的网络位置自动选择最优节点，推荐使用默认的全球服务端点。只有在特殊网络环境或有特定合规要求时，才需要指定区域端点。
>
## 故障排除

### 常见问题

#### "签名错误"或"认证失败"

- 检查Access Key ID和Secret Access Key是否正确
- 确认密钥没有被删除或禁用
- 验证账号权限是否足够

#### "域名不存在"

- 确认域名已添加到华为云DNS解析
- 检查域名拼写是否正确
- 验证域名状态是否正常

#### "记录操作失败"

- 检查子域名是否存在冲突记录
- 确认TTL值在合理范围内
- 验证解析线路设置是否正确
- 检查域名套餐是否支持该功能

#### "API调用超出限制"

- 华为云API有调用频率限制
- 适当增加更新间隔
- 检查是否有其他程序同时调用API

### 调试模式

启用调试日志查看详细信息：

```sh
ddns --debug
```

### 常见错误代码

- **APIGW.0301**：认证失败
- **DNS.0101**：域名不存在  
- **DNS.0102**：记录集不存在
- **DNS.0103**：记录集已存在
- **DNS.0203**：请求频率过高

## 支持与资源

- [华为云DNS产品文档](https://support.huaweicloud.com/dns/)
- [华为云DNS API文档](https://support.huaweicloud.com/api-dns/)
- [华为云控制台](https://console.huaweicloud.com/dns/)
- [华为云技术支持](https://support.huaweicloud.com/)

> 建议使用子用户并仅授予必要的DNS权限，以提高安全性。定期轮换访问密钥以确保账号安全。
