#!/usr/bin/env python
# coding=utf-8
"""
BaseProvider 单元测试
支持 Python 2.7 和 Python 3
"""

from base_test import BaseProviderTestCase, unittest
from ddns.provider._base import BaseProvider, encode_params


class _TestProvider(BaseProvider):
    """测试用的具体Provider实现"""

    endpoint = "https://api.example.com"

    def __init__(self, id="test_id", token="test_token_123456789", **options):
        super(_TestProvider, self).__init__(id, token, **options)
        self._test_zone_data = {"example.com": "zone123", "test.com": "zone456"}
        self._test_records = {}

    def _query_zone_id(self, domain):
        return self._test_zone_data.get(domain)

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line=None, extra=None):
        key = "{}-{}-{}".format(zone_id, subdomain, record_type)
        return self._test_records.get(key)

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl=None, line=None, extra=None):
        key = "{}-{}-{}".format(zone_id, subdomain, record_type)
        self._test_records[key] = {"id": "rec123", "name": subdomain, "value": value, "type": record_type}
        return True

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra=None):
        old_record["value"] = value
        return True


class TestBaseProvider(BaseProviderTestCase):
    """BaseProvider 测试类"""

    def setUp(self):
        """测试初始化"""
        super(TestBaseProvider, self).setUp()
        self.provider = _TestProvider()

    def test_init_success(self):
        """测试正常初始化"""
        provider = _TestProvider("test_id", "test_token")
        self.assertEqual(provider.id, "test_id")
        self.assertEqual(provider.token, "test_token")
        self.assertIsNotNone(provider.logger)
        self.assertEqual(provider._proxy, None)  # proxy 初始化为 None
        self.assertEqual(provider._zone_map, {})

    def test_validate_missing_id(self):
        """测试缺少id的验证"""
        with self.assertRaises(ValueError) as cm:
            _TestProvider("", "token")
        self.assertIn("id must be configured", str(cm.exception))

    def test_validate_missing_token(self):
        """测试缺少token的验证"""
        with self.assertRaises(ValueError) as cm:
            _TestProvider("id", "")
        self.assertIn("token must be configured", str(cm.exception))

    def test_init_with_endpoint_override(self):
        """测试使用endpoint参数覆盖默认API"""
        custom_endpoint = "https://custom.api.com"
        provider = _TestProvider("test_id", "test_token", endpoint=custom_endpoint)
        self.assertEqual(provider.endpoint, custom_endpoint)
        self.assertEqual(provider.id, "test_id")
        self.assertEqual(provider.token, "test_token")

    def test_init_without_endpoint_uses_default(self):
        """测试不提供endpoint时使用默认API"""
        provider = _TestProvider("test_id", "test_token")
        self.assertEqual(provider.endpoint, "https://api.example.com")  # 使用类级别的默认值
        self.assertEqual(provider.id, "test_id")
        self.assertEqual(provider.token, "test_token")

    def test_init_with_empty_endpoint_ignored(self):
        """测试空endpoint参数被忽略"""
        provider = _TestProvider("test_id", "test_token", endpoint="")
        self.assertEqual(provider.endpoint, "https://api.example.com")  # 使用类级别的默认值

        provider = _TestProvider("test_id", "test_token", endpoint=None)
        self.assertEqual(provider.endpoint, "https://api.example.com")  # 使用类级别的默认值

    def test_remark_exists_and_format(self):
        """测试remark存在且格式正确"""
        provider = _TestProvider("test_id", "test_token")
        self.assertTrue(hasattr(provider, "remark"))
        self.assertIsInstance(provider.remark, str)
        self.assertGreater(len(provider.remark), 0)
        # 检查是否包含基本的说明信息
        self.assertIn("DDNS", provider.remark)

    def test_endpoint_priority_over_class_api(self):
        """测试endpoint参数优先级高于类级别API"""

        # 创建一个有不同默认API的测试类
        class _CustomAPIProvider(_TestProvider):
            endpoint = "https://different.api.com"

        # 不使用endpoint - 应该使用类级别的API
        provider1 = _CustomAPIProvider("id", "token")
        self.assertEqual(provider1.endpoint, "https://different.api.com")

        # 使用endpoint - 应该覆盖类级别的API
        custom_endpoint = "https://override.api.com"
        provider2 = _CustomAPIProvider("id", "token", endpoint=custom_endpoint)
        self.assertEqual(provider2.endpoint, custom_endpoint)

    def test_get_zone_id_from_cache(self):
        """测试从缓存获取zone_id"""
        self.provider._zone_map["cached.com"] = "cached_zone"
        zone_id = self.provider.get_zone_id("cached.com")
        self.assertEqual(zone_id, "cached_zone")

    def test_get_zone_id_query_and_cache(self):
        """测试查询并缓存zone_id"""
        zone_id = self.provider.get_zone_id("example.com")
        self.assertEqual(zone_id, "zone123")
        self.assertEqual(self.provider._zone_map["example.com"], "zone123")

    def test_split_custom_domain_with_tilde(self):
        """测试用~分隔的自定义域名"""
        from ddns.provider._base import _split_custom_domain

        sub, main = _split_custom_domain("www~example.com")
        self.assertEqual(sub, "www")
        self.assertEqual(main, "example.com")

    def test_split_custom_domain_with_plus(self):
        """测试用+分隔的自定义域名"""
        from ddns.provider._base import _split_custom_domain

        sub, main = _split_custom_domain("api+test.com")
        self.assertEqual(sub, "api")
        self.assertEqual(main, "test.com")

    def test_split_custom_domain_no_separator(self):
        """测试没有分隔符的域名"""
        from ddns.provider._base import _split_custom_domain

        sub, main = _split_custom_domain("example.com")
        self.assertIsNone(sub)
        self.assertEqual(main, "example.com")

    def test_join_domain_normal(self):
        """测试正常合并域名"""
        from ddns.provider._base import join_domain

        domain = join_domain("www", "example.com")
        self.assertEqual(domain, "www.example.com")

    def test_join_domain_empty_sub(self):
        """测试空子域名合并"""
        from ddns.provider._base import join_domain

        domain = join_domain("", "example.com")
        self.assertEqual(domain, "example.com")

        domain = join_domain("@", "example.com")
        self.assertEqual(domain, "example.com")

    def test_encode_dict(self):
        """测试编码字典参数"""
        params = {"key1": "value1", "key2": "value2"}
        result = encode_params(params)
        # 由于字典顺序可能不同，我们检查包含关系
        self.assertIn("key1=value1", result)
        self.assertIn("key2=value2", result)

    def test_encode_none(self):
        """测试编码None参数"""
        result = encode_params(None)
        self.assertEqual(result, "")

    def test_mask_sensitive_data_empty(self):
        """测试空数据打码"""
        result = self.provider._mask_sensitive_data("")
        self.assertEqual(result, "")

        result = self.provider._mask_sensitive_data(None)
        self.assertEqual(result, None)

    def test_mask_sensitive_data_long_token(self):
        """测试长token的打码"""
        data = "token=test_token_123456789&other=value"
        result = self.provider._mask_sensitive_data(data)
        expected = "token=te***89&other=value"
        self.assertEqual(result, expected)

    def test_set_record_create(self):
        """测试创建记录"""
        result = self.provider.set_record("www~example.com", "1.2.3.4", "A")
        self.assertTrue(result)
        # 验证记录是否被创建
        record = self.provider._query_record("zone123", "www", "example.com", "A", None, {})
        self.assertIsNotNone(record)
        if record:  # Type narrowing for mypy
            self.assertEqual(record["value"], "1.2.3.4")

    def test_set_record_update_existing(self):
        """测试更新现有记录"""
        # 先创建一个记录
        self.provider.set_record("www~example.com", "1.2.3.4", "A")
        # 再更新它
        result = self.provider.set_record("www~example.com", "9.8.7.6", "A")
        self.assertTrue(result)
        record = self.provider._query_record("zone123", "www", "example.com", "A", None, {})
        if record:  # Type narrowing for mypy
            self.assertEqual(record["value"], "9.8.7.6")

    def test_set_record_invalid_domain(self):
        """测试无效域名"""
        result = self.provider.set_record("invalid.notfound", "1.2.3.4", "A")
        self.assertFalse(result)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
