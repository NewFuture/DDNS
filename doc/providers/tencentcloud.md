# 腾讯云DNS 配置指南 中文文档

## 概述

腾讯云DNS（TencentCloud DNSPod）是腾讯云提供的专业DNS解析服务，适用于需要高可用性和高性能DNS解析的用户。本 DDNS 项目支持通过腾讯云API密钥进行认证。

## 认证方式

### API 密钥认证

腾讯云DNS使用`SecretId`和`SecretKey`进行API认证，这是最安全和推荐的认证方式。

#### 获取API密钥

##### 从DNSPod获取

1. 登录 [DNSPod控制台](https://console.dnspod.cn/)
2. 进入“用户中心” > “API密钥”或访问 <https://console.dnspod.cn/account/token>

##### 从腾讯云获取

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
2. 访问 [API密钥管理](https://console.cloud.tencent.com/cam/capi)
3. 点击"新建密钥"按钮
4. 复制生成的 **SecretId** 和 **SecretKey**，请妥善保存
5. 确保账号具有DNSPod相关权限

#### 配置示例

```json
{
    "dns": "tencentcloud",
    "id": "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

- `id`：腾讯云 SecretId
- `token`：腾讯云 SecretKey
- `dns`：固定为 `"tencentcloud"`

## 完整配置示例

### 基本配置

```json
{
    "id": "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "dns": "tencentcloud",
    "ipv6": ["home.example.com", "server.example.com"],
    "index6": ["default"]
}
```

### 带可选参数的配置

```json
{
    "id": "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "dns": "tencentcloud",
    "endpoint": "https://dnspod.ap-singapore.tencentcloudapi.com",
    "index4": ["default"],
    "index6": ["default"],
    "ipv4": ["example.com"],
    "ipv6": ["dynamic.mydomain.com"],
    "line": "默认",
    "ttl": 600
}
```

## 可选参数

### TTL（生存时间）

```json
{
    "ttl": 300
}
```

### 线路类型

```json
{
    "line": "默认"
}
```

- 选项："默认"、"电信"、"联通"、"移动"、"教育网"等
- 默认："默认"

### 自定义API端点

```json
{
    "endpoint": "https://dnspod.tencentcloudapi.com"
}
```

腾讯云DNSPod API支持多个区域端点，可根据网络环境选择最优节点：

#### 国内节点

- **华南地区（广州）**：`https://dnspod.ap-guangzhou.tencentcloudapi.com`
- **华东地区（上海）**：`https://dnspod.ap-shanghai.tencentcloudapi.com`
- **华北地区（北京）**：`https://dnspod.ap-beijing.tencentcloudapi.com`
- **西南地区（成都）**：`https://dnspod.ap-chengdu.tencentcloudapi.com`
- **港澳台地区（香港）**：`https://dnspod.ap-hongkong.tencentcloudapi.com`

#### 海外节点

- **亚太东南（新加坡）**：`https://dnspod.ap-singapore.tencentcloudapi.com`
- **亚太东南（曼谷）**：`https://dnspod.ap-bangkok.tencentcloudapi.com`
- **亚太南部（孟买）**：`https://dnspod.ap-mumbai.tencentcloudapi.com`
- **亚太东北（首尔）**：`https://dnspod.ap-seoul.tencentcloudapi.com`
- **亚太东北（东京）**：`https://dnspod.ap-tokyo.tencentcloudapi.com`
- **美国东部（弗吉尼亚）**：`https://dnspod.na-ashburn.tencentcloudapi.com`
- **美国西部（硅谷）**：`https://dnspod.na-siliconvalley.tencentcloudapi.com`
- **欧洲地区（法兰克福）**：`https://dnspod.eu-frankfurt.tencentcloudapi.com`

> **注意**：建议使用默认端点 `https://dnspod.tencentcloudapi.com`，腾讯云会自动路由到最优节点。只有在特殊网络环境下才需要指定特定区域端点。

## 权限要求

确保使用的腾讯云账号具有以下权限：

- **DNSPod**：域名解析管理权限
- **QcloudDNSPodFullAccess**：DNSPod完全访问权限（推荐）

可以在 [访问管理控制台](https://console.cloud.tencent.com/cam/policy) 中查看和配置权限。

## 故障排除

### 常见问题

#### "签名错误"或"认证失败"

- 检查SecretId和SecretKey是否正确
- 确认密钥没有过期
- 验证账号权限是否足够

#### "域名未找到"

- 确认域名已添加到腾讯云DNSPod
- 检查域名拼写是否正确
- 验证域名状态是否正常

#### "记录操作失败"

- 检查子域名是否存在冲突记录
- 确认TTL值在合理范围内
- 验证线路类型设置是否正确

#### "API调用超出限制"

- 腾讯云API有调用频率限制
- 适当增加更新间隔
- 检查是否有其他程序同时调用API

### 调试模式

启用调试日志查看详细信息：

```sh
ddns --debug
```

### 常见错误代码

- **AuthFailure.SignatureExpire**：签名过期
- **AuthFailure.SecretIdNotFound**：SecretId不存在
- **ResourceNotFound.NoDataOfRecord**：记录不存在
- **LimitExceeded.RequestLimitExceeded**：请求频率超限

## API限制

- **请求频率**：默认每秒20次
- **单次查询**：最多返回3000条记录
- **域名数量**：根据套餐不同而限制

## 支持与资源

- [腾讯云DNSPod产品文档](https://cloud.tencent.com/document/product/1427)
- [腾讯云DNSPod v3 API文档](https://cloud.tencent.com/document/api/1427)
- [腾讯云控制台](https://console.cloud.tencent.com/dnspod)

> 建议使用子账号API密钥并仅授予必要的DNSPod权限，以提高安全性。
