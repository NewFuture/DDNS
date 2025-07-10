# 阿里云DNS 配置指南

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

```json
{
    "dns": "alidns",
    "id": "AccessKey_ID",
    "token": "AccessKey_Secret"
}
```

- `id`：阿里云 AccessKey ID
- `token`：阿里云 AccessKey Secret
- `dns`：固定为 `"alidns"`

## 权限要求

确保使用的阿里云账号具有以下权限：

- **AliyunDNSFullAccess**：云解析DNS完全访问权限（推荐）
- **AliyunDNSReadOnlyAccess + 自定义写权限**：精细化权限控制

可以在 [RAM访问控制](https://ram.console.aliyun.com/policies) 中查看和配置权限。

## 完整配置示例

```json
{
    "id": "LTAI4xxxxxxxxxxxxxxx",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "dns": "alidns",
    "endpoint": "https://alidns.ap-southeast-1.aliyuncs.com",
    "index4": ["public"],
    "index6": ["default"],
    "ipv4": ["example.com"],
    "ipv6": ["dynamic.mydomain.com"],
    "line": "telecom",
    "ttl": 600
}
```

## 可选参数

| 参数 | 描述 | 类型 | 范围/选项 | 默认 |
|------|------|------|-----------|------|
| ttl  | 生存时间（TTL） | 整数 (秒) | 1 - 86400 | 600 |
| line | 解析线路       | 字符串 | default, telecom, unicom, mobile, oversea | default |
| endpoint | 自定义API端点 | 字符串 | URL(见下表) | `https://alidns.aliyuncs.com` |

> **注意**：`ttl` 和 `line` 不同套餐支持的值可能不同。

### 自定义API端点

阿里云DNS支持多个区域端点，可根据网络环境选择最优节点：

#### 国内节点

- **默认（推荐）**：`https://alidns.aliyuncs.com`
- **华东1（杭州）**：`https://alidns.cn-hangzhou.aliyuncs.com`
- **华东2（上海）**：`https://alidns.cn-shanghai.aliyuncs.com`
- **华北1（青岛）**：`https://alidns.cn-qingdao.aliyuncs.com`
- **华北2（北京）**：`https://alidns.cn-beijing.aliyuncs.com`
- **华北3（张家口）**：`https://alidns.cn-zhangjiakou.aliyuncs.com`
- **华南1（深圳）**：`https://alidns.cn-shenzhen.aliyuncs.com`
- **西南1（成都）**：`https://alidns.cn-chengdu.aliyuncs.com`

#### 海外节点

- **亚太东南1（新加坡）**：`https://alidns.ap-southeast-1.aliyuncs.com`
- **亚太东南2（悉尼）**：`https://alidns.ap-southeast-2.aliyuncs.com`
- **亚太东南3（吉隆坡）**：`https://alidns.ap-southeast-3.aliyuncs.com`
- **亚太南部1（孟买）**：`https://alidns.ap-south-1.aliyuncs.com`
- **亚太东北1（东京）**：`https://alidns.ap-northeast-1.aliyuncs.com`
- **美国东部1（弗吉尼亚）**：`https://alidns.us-east-1.aliyuncs.com`
- **美国西部1（硅谷）**：`https://alidns.us-west-1.aliyuncs.com`
- **欧洲中部1（法兰克福）**：`https://alidns.eu-central-1.aliyuncs.com`
- **欧洲西部1（伦敦）**：`https://alidns.eu-west-1.aliyuncs.com`

> **注意**：建议使用默认端点 `https://alidns.aliyuncs.com`，阿里云会自动路由到最优节点。只有在特殊网络环境下才需要指定特定区域端点。

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
