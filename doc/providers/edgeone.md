# 腾讯云 EdgeOne 配置指南

## 概述

腾讯云 EdgeOne 是腾讯云提供的全球边缘计算和安全加速服务平台，其中包含DNS解析功能。本 DDNS 项目支持通过腾讯云EdgeOne API进行DNS记录的动态更新。

**官网**: 
- 国际版: [https://edgeone.ai/zh](https://edgeone.ai/zh)
- 国内版: [https://cloud.tencent.com/product/teo](https://cloud.tencent.com/product/teo)

## 认证方式

### API 密钥认证

腾讯云 EdgeOne 使用`SecretId`和`SecretKey`进行API认证，这是推荐的认证方式。

#### 获取API密钥

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
2. 访问 [API密钥管理](https://console.cloud.tencent.com/cam/capi)
3. 点击"新建密钥"按钮
4. 复制生成的 **SecretId** 和 **SecretKey**，请妥善保存
5. 确保账号具有EdgeOne相关权限

## 权限要求

确保用于DDNS的腾讯云账号具有以下EdgeOne相关权限：

- `teo:DescribeZones` - 查询站点信息
- `teo:DescribeRecords` - 查询DNS记录
- `teo:CreateRecord` - 创建DNS记录  
- `teo:ModifyRecord` - 修改DNS记录

建议使用子账号并分配最小必要权限，而不是使用主账号密钥。

#### 配置示例

```json
{
    "dns": "edgeone",
    "id": "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

- `id`：腾讯云 SecretId
- `token`：腾讯云 SecretKey
- `dns`：可以使用 `"edgeone"`, `"tencent_edgeone"`, 或 `"teo"`

## 完整配置示例

```json
{
    "id": "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "dns": "edgeone",
    "domains": "test.example.com"
}
```

- `id`：腾讯云 SecretId
- `token`：腾讯云 SecretKey
- `dns`：可以使用 `"edgeone"`, `"tencent_edgeone"`, 或 `"teo"`

## 服务端点

EdgeOne 支持国际版和国内版，使用不同的API端点：

- **国际版**: `https://teo.tencentcloudapi.com` (默认)
- **国内版**: `https://teo.tencentcloudapi.com` 

两个版本的API逻辑相同，只是服务器节点分布不同。

## 注意事项

1. **服务差异**: EdgeOne 与传统的DNSPod服务不同，请确保域名已在EdgeOne控制台中正确配置
2. **API限制**: EdgeOne API有调用频率限制，建议合理设置更新间隔
3. **权限管理**: 建议为DDNS创建专门的子账号并分配最小必要权限
4. **密钥安全**: SecretKey是敏感信息，请妥善保管，避免泄露
5. **记录冲突**: 确保要更新的DNS记录不与EdgeOne的其他功能（如加速、安全规则）产生冲突

## 故障排除

### 常见错误

1. **认证失败**
   - 检查SecretId和SecretKey是否正确
   - 确认账号具有EdgeOne权限
   - 验证时间同步，API签名对时间敏感

2. **域名未找到**
   - 确认域名已在EdgeOne控制台中添加
   - 检查域名状态是否正常
   - 验证DNS配置是否正确

3. **记录操作失败**
   - 检查记录类型是否支持
   - 确认TTL值在允许范围内
   - 验证记录值格式是否正确

### 日志分析

启用调试模式查看详细的API请求和响应：

```bash
ddns --debug
```

## 相关链接

- [EdgeOne 官方文档](https://edgeone.ai/zh/document)
- [API 认证与签名](https://edgeone.ai/zh/document/50458)
- [DNS 记录管理 API](https://edgeone.ai/zh/document/50484)
- [腾讯云控制台](https://console.cloud.tencent.com/)
- [EdgeOne 控制台](https://console.tencentcloud.com/edgeone)