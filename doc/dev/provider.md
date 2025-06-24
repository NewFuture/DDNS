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

支持两种实现

1. 标准DNS: 自动查询是否存在，自动创建，修改DNS记录
2. 非标准DNS: 只能特定操作，不支持查询和创建

### 1. 标准DNS每个子类都必须实现以下方法：

| 方法 | 说明 |
|------|------|
| `_query_zone_id(domain)` | **查询主域名的Id** (zone_id) |
| `_query_record(zone_id, sub_domain, main_domain, record_type, line=None, extra=None)` | **查询当前 DNS 记录** |
| `_create_record(zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra=None)` | 创建记录 |
| `_update_record(zone_id, old_record, value, record_type, ttl=None, line=None, extra=None)` | **更新记录** |

### 2. 非标准DNS

每个子类只需实现以下方法：
| 方法 | 说明 |
|------|------|
| `set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):` | 更新记录 |


## 🔧 例子

### 标准DNS Provider

标准实现可参考
   - [`providers/dnspod.py`](/ddns/provider/dnspod.py): POST 表单数据，无签名
   - [`provider/cloudflare.py`](/ddns/provider/cloudflare.py): RESTful JSON，无签名
   - [`provider/alidns.py`](/ddns/provider/alidns.py): POST 表单+sha256参数签名
   - [`provider/huaweidns.py`](/ddns/provider/huaweidns.py): RESTful JSON，参数header签名

> provider/myprovider.py
```python
#coding=utf-8
"""
自定义 DNS 服务商示例
@author: YourGithubUsername
"""
from ._base import BaseProvider, TYPE_JSON
class MyProvider(BaseProvider):
    API = 'https://api.exampledns.com'
    ContentType = TYPE_JSON  # 或 TYPE_FORM

    def _request(self, action, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict
        """
        [可选]推荐，请求认证和参数封装，添加公共请求头和身份验证信息。
        """

    def _query_zone_id(self, domain):
        # type: (str) -> str
        """
        查询主域名的Id（zone_id），返回字符串类型的 zone_id。
        """

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line=None, extra=None):
        # type: (str, str, str, int | None, str | None, dict | None) -> Any
        """
        查询当前 DNS 记录，返回记录信息。
        """

    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, str, str, str, int | None, str | None, dict | None) -> bool
        """
        创建 DNS 记录，返回是否成功的布尔值。
        """

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, str, str, str, int | None, str | None, dict | None) -> bool
        """
        更新 DNS 记录，返回是否成功的布尔值。
        """
```

### 非标准DNS Provider

非标准实现可参考:
    - [`provider/he.py`](/ddns/provider/he.py): 简单更新记录
    - [`provider/denig.py`](/ddns/provider/denig.py): 打印IP地址到控制台

```python
#coding=utf-8
"""
自定义非标准 DNS 服务商示例
@author: YourGithubUsername
"""
from ._base import BaseProvider
class MyProvider(BaseProvider):

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        # type: (str, str, str, int | None, str | None, dict | None) -> bool
        """
        更新 DNS 记录，返回是否成功的布尔值。
        """
        # 实现更新逻辑
        pass
```

---

## ✅ 推荐实现细节

- 推荐在 `_request` 方法中封装请求逻辑，处理认证、参数封装、公共请求头等。
- 调用方法中使用 `self.logger` 记录日志，便于调试和排查问题。
- 务必通过 `self._http(...)` 方法发送，自动处理代理、编码、异常和日志。
- 支持 `Remark` (备注) 字段的，在创建或者更新时候，同步Remark。
- 内置 `set_record(domain, value, ...)` 方法，标准DNS无需重复实现。

---

## 🧪 调试建议

- 使用 `self.logger.info/debug/warning/error` 打印日志。
- 推荐在开发和测试时设置日志级别为 DEBUG

