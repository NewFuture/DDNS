# coding=utf-8
"""
Unit tests for SimpleProvider

@author: GitHub Copilot
"""

from base_test import BaseProviderTestCase, unittest, MagicMock
from ddns.provider._base import SimpleProvider, TYPE_FORM, encode_params


class _TestableSimpleProvider(SimpleProvider):
    """Test implementation of SimpleProvider for testing purposes"""

    endpoint = "https://api.example.com"

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        """Test implementation of set_record"""
        self.logger.debug("_TestableSimpleProvider: %s(%s) => %s", domain, record_type, value)
        return True


class _TestableSimpleProviderClass(BaseProviderTestCase):
    """Test cases for SimpleProvider base class"""

    def setUp(self):
        """Set up test fixtures"""
        super(_TestableSimpleProviderClass, self).setUp()

    def test_init_with_basic_config(self):
        """Test SimpleProvider initialization with basic configuration"""
        provider = _TestableSimpleProvider(self.id, self.token)
        self.assertEqual(provider.id, self.id)
        self.assertEqual(provider.token, self.token)
        self.assertEqual(provider.endpoint, "https://api.example.com")
        self.assertEqual(provider.content_type, TYPE_FORM)
        self.assertTrue(provider.decode_response)
        self.assertEqual(provider._ssl, "auto")  # Default verify_ssl should be "auto"
        self.assertEqual(provider._zone_map, {})  # Should initialize empty zone map

    def test_init_with_logger(self):
        """Test SimpleProvider initialization with logger"""
        logger = MagicMock()
        provider = _TestableSimpleProvider(self.id, self.token, logger=logger)
        logger.getChild.assert_called_once_with("_TestableSimpleProvider")
        self.assertIsNotNone(provider.logger)

    def test_init_with_options(self):
        """Test SimpleProvider initialization with additional options"""
        options = {"debug": True, "timeout": 30}
        provider = _TestableSimpleProvider(self.id, self.token, ssl=False, **options)
        self.assertEqual(provider.options, options)
        self.assertFalse(provider._ssl)  # Should respect verify_ssl parameter

    def test_init_with_verify_ssl_string(self):
        """Test SimpleProvider initialization with verify_ssl as string"""
        provider = _TestableSimpleProvider(self.id, self.token, ssl="/path/to/cert")
        self.assertEqual(provider._ssl, "/path/to/cert")

    def test_init_with_verify_ssl_false(self):
        """Test SimpleProvider initialization with verify_ssl as False"""
        provider = _TestableSimpleProvider(self.id, self.token, ssl=False)
        self.assertFalse(provider._ssl)

    def test_init_with_verify_ssl_truthy_value(self):
        """Test SimpleProvider initialization with verify_ssl as truthy value"""
        provider = _TestableSimpleProvider(self.id, self.token, ssl=1)  # type: ignore
        self.assertEqual(provider._ssl, 1)  # Should preserve the exact value

    def test_init_with_verify_ssl_falsy_value(self):
        """Test SimpleProvider initialization with verify_ssl as falsy value"""
        provider = _TestableSimpleProvider(self.id, self.token, ssl=0)  # type: ignore
        self.assertEqual(provider._ssl, 0)  # Should preserve the exact value

    def test_validate_missing_id(self):
        """Test _validate method with missing id"""
        with self.assertRaises(ValueError) as cm:
            _TestableSimpleProvider(None, self.token)  # type: ignore
        self.assertIn("id must be configured", str(cm.exception))

    def test_validate_missing_token(self):
        """Test _validate method with missing token"""
        with self.assertRaises(ValueError) as cm:
            _TestableSimpleProvider(self.id, None)  # type: ignore
        self.assertIn("token must be configured", str(cm.exception))

    def test_validate_empty_id(self):
        """Test _validate method with empty id"""
        with self.assertRaises(ValueError) as cm:
            _TestableSimpleProvider("", self.token)
        self.assertIn("id must be configured", str(cm.exception))

    def test_validate_empty_token(self):
        """Test _validate method with empty token"""
        with self.assertRaises(ValueError) as cm:
            _TestableSimpleProvider(self.id, "")
        self.assertIn("token must be configured", str(cm.exception))

    def test_encode_dict(self):
        """Test _encode method with dictionary"""
        params = {"key1": "value1", "key2": "value2"}
        result = encode_params(params)

        # Result should be URL-encoded string
        self.assertIn("key1=value1", result)
        self.assertIn("key2=value2", result)
        self.assertIn("&", result)

    def test_mask_sensitive_data_basic(self):
        """Test _mask_sensitive_data method with basic token"""
        provider = _TestableSimpleProvider(self.id, "secret123")
        data = "url?token=secret123&other=value"

        result = provider._mask_sensitive_data(data)  # type: str # type: ignore

        self.assertNotIn("secret123", result)
        self.assertIn("se***23", result)

    def test_mask_sensitive_data_short_token(self):
        """Test _mask_sensitive_data method with short token"""
        provider = _TestableSimpleProvider(self.id, "abc")
        data = "url?token=abc&other=value"

        result = provider._mask_sensitive_data(data)  # type: str # type: ignore

        self.assertNotIn("abc", result)
        self.assertIn("***", result)

    def test_mask_sensitive_data_empty_data(self):
        """Test _mask_sensitive_data method with empty data"""
        provider = _TestableSimpleProvider(self.id, self.token)

        result = provider._mask_sensitive_data("")

        self.assertEqual(result, "")

    def test_mask_sensitive_data_none_data(self):
        """Test _mask_sensitive_data method with None data"""
        provider = _TestableSimpleProvider(self.id, self.token)

        result = provider._mask_sensitive_data(None)

        self.assertIsNone(result)

    def test_mask_sensitive_data_no_token(self):
        """Test _mask_sensitive_data method with no token"""
        # Create provider normally first, then modify token
        provider = _TestableSimpleProvider(self.id, self.token)
        provider.token = ""  # Override after init
        data = "url?token=secret123&other=value"

        result = provider._mask_sensitive_data(data)

        self.assertEqual(result, data)  # Should be unchanged

    def test_mask_sensitive_data_long_token(self):
        """Test _mask_sensitive_data method with long token"""
        provider = _TestableSimpleProvider(self.id, "verylongsecrettoken123")
        data = "url?token=verylongsecrettoken123&other=value"

        result = provider._mask_sensitive_data(data)  # type: str # type: ignore
        self.assertNotIn("verylongsecrettoken123", result)
        self.assertIn("ve***23", result)

    def test_mask_sensitive_data_url_encoded(self):
        """Test _mask_sensitive_data method with URL encoded sensitive data"""
        from ddns.provider._base import quote

        provider = _TestableSimpleProvider("user@example.com", "secret_token_123")

        # 测试URL编码的token
        token_encoded = quote("secret_token_123", safe="")
        id_encoded = quote("user@example.com", safe="")
        data = "url?token={}&id={}&other=value".format(token_encoded, id_encoded)

        result = provider._mask_sensitive_data(data)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)

        # Cast result to str for type checking
        result_str = str(result)

        # 验证原始敏感token信息不泄露
        self.assertNotIn("secret_token_123", result_str)
        # 验证URL编码的敏感token信息也不泄露
        self.assertNotIn(token_encoded, result_str)
        # 验证包含打码信息
        self.assertIn("se***23", result_str)

        # id 不再被打码，应该保持原样（URL编码形式）
        self.assertIn(id_encoded, result_str)  # user%40example.com

    def test_mask_sensitive_data_bytes_url_encoded(self):
        """Test _mask_sensitive_data method with bytes containing URL encoded data"""
        from ddns.provider._base import quote

        provider = _TestableSimpleProvider("test@example.com", "token123")

        # 测试字节数据包含URL编码的敏感信息
        token_encoded = quote("token123", safe="")
        data = "url?token={}&data=something".format(token_encoded).encode()

        result = provider._mask_sensitive_data(data)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, bytes)

        # Cast result to bytes for type checking
        result_bytes = bytes(result) if isinstance(result, bytes) else result.encode() if result else b""

        # 验证原始和URL编码的token都不泄露
        self.assertNotIn(b"token123", result_bytes)
        self.assertNotIn(token_encoded.encode(), result_bytes)
        # 验证包含打码信息
        self.assertIn(b"to***23", result_bytes)

    def test_set_record_abstract_method(self):
        """Test that set_record is implemented in test class"""
        provider = _TestableSimpleProvider(self.id, self.token)

        result = provider.set_record("example.com", "192.168.1.1")

        self.assertTrue(result)


class _TestableSimpleProviderWithNoAPI(SimpleProvider):
    """Test implementation without API defined"""

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        return True


class _TestableSimpleProviderValidation(BaseProviderTestCase):
    """Additional validation tests for SimpleProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(_TestableSimpleProviderValidation, self).setUp()

    def test_validate_missing_api(self):
        """Test _validate method when API is not defined"""
        with self.assertRaises(ValueError) as cm:
            _TestableSimpleProviderWithNoAPI(self.id, self.token)
        self.assertIn("API endpoint must be defined", str(cm.exception))
        self.assertIn("_TestableSimpleProviderWithNoAPI", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
