# 腾讯云 DNS (TencentCloud DNSPod) 配置指南

## 概述

腾讯云 DNS（TencentCloud DNSPod）是腾讯云提供的专业 DNS 解析服务，具有高可用性和高性能，支持动态 DNS 记录的创建与更新。本 DDNS 项目通过 SecretId 和 SecretKey 进行 API 认证。

官网链接：

- 官方网站：<https://cloud.tencent.com/product/dns>
- 服务商控制台：<https://console.cloud.tencent.com/dnspod>

## 认证信息

### API 密钥认证

腾讯云DNS使用`SecretId`和`SecretKey`进行API认证，这是最安全和推荐的认证方式。

#### 获取API密钥

```jsonc
{
    "dns": "tencentcloud",
    "id": "Your_Secret_Id",     // 腾讯云 SecretId
    "token": "Your_Secret_Key" // 腾讯云 SecretKey
}
```

有以下两种方式获取 API 密钥：

##### 从DNSPod获取

最为简单快捷地获取

1. 登录 [DNSPod控制台](https://console.dnspod.cn/)
2. 进入“用户中心” > “API密钥”或访问 <https://console.dnspod.cn/account/token>
3. 点击“创建密钥”，填写描述，选择域名管理权限，完成创建

##### 从腾讯云获取

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
2. 访问 [API密钥管理](https://console.cloud.tencent.com/cam/capi)
3. 点击"新建密钥"按钮
4. 复制生成的 **SecretId** 和 **SecretKey**，请妥善保存
5. 确保账号具有DNSPod相关权限

确保使用的腾讯云账号具有以下权限：

- **QcloudDNSPodFullAccess**：DNSPod 完全访问权限（推荐）
- **QcloudDNSPodReadOnlyAccess + 自定义写权限**：精细化权限控制

可以在 [访问管理控制台](https://console.cloud.tencent.com/cam/policy) 中查看和配置权限。

## 完整配置示例

```jsonc
{
    "$schema": "https://ddns.newfuture.cc/schema/v4.0.json", // 格式验证
    "dns": "tencentcloud",              // 当前服务商
    "id": "Your_Secret_Id",     // 腾讯云 SecretId
    "token": "Your_Secret_Key", // 腾讯云 SecretKey
    "index4": ["url:http://api.ipify.cn", "public"], // IPv4地址来源
    "index6": "public",                     // IPv6地址来源
    "ipv4": ["ddns.newfuture.cc"],           // IPv4 域名
    "ipv6": ["ddns.newfuture.cc", "ipv6.ddns.newfuture.cc"], // IPv6 域名
    "endpoint": "https://dnspod.tencentcloudapi.com", // API端点
    "line": "默认",                          // 解析线路
    "ttl": 600                              // DNS记录TTL（秒）
}
```

### 参数说明

| 参数    | 说明         | 类型           | 取值范围/选项                       | 默认值    | 参数类型   |
| :-----: | :----------- | :------------- | :--------------------------------- | :-------- | :--------- |
| dns     | 服务商标识   | 字符串         | `tencentcloud`                     | 无        | 服务商参数 |
| id      | 认证 ID      | 字符串         | 腾讯云 SecretId                    | 无        | 服务商参数 |
| token   | 认证密钥     | 字符串         | 腾讯云 SecretKey                   | 无        | 服务商参数 |
| index4  | IPv4 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)  | `default` | 公用配置   |
| index6  | IPv6 来源     | 数组           | [参考配置](../config/json.md#ipv4-ipv6)   | `default` | 公用配置   |
| ipv4    | IPv4 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| ipv6    | IPv6 域名     | 数组           | 域名列表                           | 无        | 公用配置   |
| endpoint| API 端点      | URL            | [参考下方](#endpoint)              | `https://dnspod.tencentcloudapi.com` | 服务商参数 |
| line    | 解析线路      | 字符串         | [参考下方](#line)                   | `默认`    | 服务商参数 |
| ttl     | TTL 时间      | 整数（秒）     | [参考下方](#ttl)                    | `600`     | 服务商参数 |
| proxy   | 代理设置      | 数组           | [参考配置](../config/json.md#proxy)        | 无        | 公用网络   |
| ssl     | SSL 验证方式  | 布尔/字符串    | `"auto"`、`true`、`false`            | `auto`    | 公用网络   |
| cache   | 缓存设置      | 布尔/字符串    | `true`、`false`、`filepath`        | `true`    | 公用配置   |
| log     | 日志配置      | 对象           | [参考配置](../config/json.md#log)             | 无        | 公用配置   |

> **参数类型说明**：  
>
> - **公用配置**：所有支持的DNS服务商均适用的标准DNS配置参数  
> - **公用网络**：所有支持的DNS服务商均适用的网络设置参数  
> - **服务商参数**：当前服务商支持,值与当前服务商相关
> **注意**：`ttl` 和 `line` 不同套餐支持的值可能不同。

### endpoint

腾讯云 DNSPod API 支持多个区域端点，可根据网络环境选择最优节点：

#### 国内节点

- **默认（推荐）**：`https://dnspod.tencentcloudapi.com`
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

### ttl

`ttl` 参数指定 DNS 记录的生存时间（TTL），单位为秒。腾讯云 DNSPod 支持的 TTL 范围为 1 到 604800 秒（即 7 天）。如果不设置，则使用默认值。

| 套餐类型 | 支持的 TTL 范围（秒） |
| :------ | :------------------- |
| 免费版   | 600 ~ 604800          |
| 专业版   | 60 ~ 604800           |
| 企业版   | 1 ~ 604800            |
| 尊享版   | 1 ~ 604800            |

> 参考：腾讯云 [云解析 TTL 说明](https://cloud.tencent.com/document/product/302/9072)

### line

`line` 参数指定 DNS 解析线路，腾讯云 DNSPod 支持的线路：

| 线路标识         | 说明         |
| :-------------- | :----------- |
| 默认            | 默认         |
| 电信            | 中国电信     |
| 联通            | 中国联通     |
| 移动            | 中国移动     |
| 教育网          | 中国教育网   |
| 境外            | 境外         |

> 更多线路参考：腾讯云 [云解析 DNS 解析线路说明](https://cloud.tencent.com/document/product/302/8643)
>
## 故障排除

### 调试模式

启用调试日志查看详细信息：

```sh
ddns -c config.json --debug
```

### 常见问题

- **签名错误**：检查 SecretId 和 SecretKey 是否正确，确认密钥没有过期
- **域名未找到**：确保域名已添加到腾讯云 DNSPod，配置拼写无误，域名处于活跃状态
- **记录创建失败**：检查子域名是否有冲突记录，TTL 设置合理，确认有修改权限
- **API 调用超出限制**：腾讯云 API 有调用频率限制，降低请求频率

### 常见错误代码

| 错误代码        | 说明             | 解决方案           |
| :------------- | :--------------- | :----------------- |
| AuthFailure.SignatureExpire | 签名过期 | 检查系统时间       |
| AuthFailure.SecretIdNotFound | SecretId不存在 | 检查密钥配置     |
| ResourceNotFound.NoDataOfRecord | 记录不存在 | 检查记录设置     |
| LimitExceeded.RequestLimitExceeded | 请求频率超限 | 降低请求频率   |

## API 限制

- **请求频率**：默认每秒 20 次
- **单次查询**：最多返回 3000 条记录
- **域名数量**：根据套餐不同而限制

## 支持与资源

- [腾讯云 DNSPod 产品文档](https://cloud.tencent.com/document/product/1427)
- [腾讯云 DNSPod V3 API 文档](https://cloud.tencent.com/document/api/1427)
- [腾讯云 DNSPod 控制台](https://console.cloud.tencent.com/dnspod)
- [腾讯云技术支持](https://cloud.tencent.com/online-service)

> **建议**：推荐使用子账号 API 密钥并仅授予必要的 DNSPod 权限，以提高安全性。定期轮换 API 密钥确保账号安全。
