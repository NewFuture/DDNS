# 开发指南：如何实现一个新的 DNS Provider

本指南介绍如何基于 `BaseProvider` 抽象基类，快速实现一个自定义的 DNS 服务商适配类，支持动态 DNS 记录的创建与更新。

## 📦 目录结构

```text
ddns/
├── provider/
│   ├── _base.py         # 抽象基类 BaseProvider
│   └── myprovider.py    # 你的新服务商实现
```

---

## 🚀 快速开始

### 1. 创建新类并继承 `BaseProvider`

```python
# providers/myprovider.py

from ._base import BaseProvider, TYPE_JSON, TYPE_FORM

class MyProvider(BaseProvider):
    # 设置 API 域名
    API = 'api.exampledns.com'
    # 设置 Content-Type
    ContentType = TYPE_FORM  # 或 TYPE_JSON

    def _query_zone_id(self, domain):
        # 调用 API 查询 zone_id
        return "zone123"

    def _query_record_id(self, zone_id, sub, record_type, line=None):
        # 查询记录 ID，如果存在则返回，否则返回 None
        return "record456"

    def _create_record(self, zone_id, sub, value, record_type, ttl=None, line=None, extra=None):
        # 创建 DNS 记录的 API 调用逻辑
        return {"status": "created"}

    def _update_record(self, zone_id, record_id, value, record_type, ttl=None, line=None, extra=None):
        # 更新 DNS 记录的 API 调用逻辑
        res = self._https("POST", "/v1/record/update", key="value")
        return {"status": "updated"}
```

> 所有请求都通过 `_https(method, url, _headers=None, **params)` 方法发送， 以实现代理和ssl的自动配置和切换。
>
> 如需要,可再封装一层API请求方法。

---

## ✏️ 必须实现的抽象方法

每个子类都必须实现以下方法：

| 方法 | 说明 |
|------|------|
| `_update_record(zone_id, record_id, value, record_type, ...)` | 更新记录 |
| `_create_record(zone_id, sub, value, record_type, ...)` | 创建记录 |
| `_query_record_id(zone_id, sub, record_type, line=None)` | 查询 DNS 记录的 ID |
| `_query_zone_id(domain)` | 根据域名查询所属 zone 区域 ID |

---

## ✅ 推荐实现细节

### 设置 API 域名
```python
API = "api.example.com"
```

### 设置 Content-Type（默认表单，可选 JSON）
```python
ContentType = TYPE_JSON  # 或 TYPE_FORM
```

### 使用内置 HTTPS 请求工具

```python
self._https("POST", "/v1/record/create", _headers={"Authorization": "Token ..."}, key="value"...)
```


## 🧪 调试建议

- 使用 `logging` 打印 debug 信息
- 推荐开启详细日志级别：


---

## 📚 参考示例

你可以参考以下示例作：

- `Dnspod`: post form 数据，无签名
- `Cloudflare`：restful json 格式，无签名
- `AliDNS`：post form 参数签名
