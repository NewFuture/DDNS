# coding=utf-8
"""
Unit tests for SimpleProvider

@author: Testing Suite
"""

from test_base import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider._base import SimpleProvider, TYPE_FORM, TYPE_JSON


class TestSimpleProvider(SimpleProvider):
    """Test implementation of SimpleProvider for testing purposes"""

    API = "https://api.example.com"
    ContentType = TYPE_FORM
    DecodeResponse = True

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        """Test implementation of set_record"""
        self.logger.debug("TestSimpleProvider: %s(%s) => %s", domain, record_type, value)
        return True

    def _validate(self):
        """Test implementation of _validate"""
        if not self.auth_id:
            raise ValueError("id must be configured")
        if not self.auth_token:
            raise ValueError("token must be configured")


class TestSimpleProviderClass(BaseProviderTestCase):
    """Test cases for SimpleProvider base class"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestSimpleProviderClass, self).setUp()

    def test_init_with_basic_config(self):
        """Test SimpleProvider initialization with basic configuration"""
        provider = TestSimpleProvider(self.auth_id, self.auth_token)
        self.assertEqual(provider.auth_id, self.auth_id)
        self.assertEqual(provider.auth_token, self.auth_token)
        self.assertEqual(provider.API, "https://api.example.com")
        self.assertEqual(provider.ContentType, TYPE_FORM)
        self.assertTrue(provider.DecodeResponse)

    def test_init_with_logger(self):
        """Test SimpleProvider initialization with logger"""
        logger = MagicMock()
        provider = TestSimpleProvider(self.auth_id, self.auth_token, logger=logger)
        logger.getChild.assert_called_once_with("TestSimpleProvider")
        self.assertIsNotNone(provider.logger)

    def test_init_with_options(self):
        """Test SimpleProvider initialization with additional options"""
        options = {"debug": True, "timeout": 30}
        provider = TestSimpleProvider(self.auth_id, self.auth_token, **options)
        self.assertEqual(provider.options, options)

    def test_validate_missing_id(self):
        """Test _validate method with missing auth_id"""
        with self.assertRaises(ValueError) as cm:
            TestSimpleProvider(None, self.auth_token)  # type: ignore
        self.assertIn("id must be configured", str(cm.exception))

    def test_validate_missing_token(self):
        """Test _validate method with missing auth_token"""
        with self.assertRaises(ValueError) as cm:
            TestSimpleProvider(self.auth_id, None)  # type: ignore
        self.assertIn("token must be configured", str(cm.exception))

    def test_validate_empty_id(self):
        """Test _validate method with empty auth_id"""
        with self.assertRaises(ValueError) as cm:
            TestSimpleProvider("", self.auth_token)
        self.assertIn("id must be configured", str(cm.exception))

    def test_validate_empty_token(self):
        """Test _validate method with empty auth_token"""
        with self.assertRaises(ValueError) as cm:
            TestSimpleProvider(self.auth_id, "")
        self.assertIn("token must be configured", str(cm.exception))

    def test_set_proxy(self):
        """Test set_proxy method"""
        provider = TestSimpleProvider(self.auth_id, self.auth_token)
        proxy_str = "http://proxy.example.com:8080"

        result = provider.set_proxy(proxy_str)

        self.assertEqual(provider.proxy, proxy_str)
        self.assertIs(result, provider)  # Should return self for chaining

    def test_set_proxy_none(self):
        """Test set_proxy method with None"""
        provider = TestSimpleProvider(self.auth_id, self.auth_token)

        result = provider.set_proxy(None)

        self.assertIsNone(provider.proxy)
        self.assertIs(result, provider)

    def test_encode_dict(self):
        """Test _encode method with dictionary"""
        params = {"key1": "value1", "key2": "value2"}
        result = TestSimpleProvider._encode(params)

        # Result should be URL-encoded string
        self.assertIn("key1=value1", result)
        self.assertIn("key2=value2", result)
        self.assertIn("&", result)

    def test_encode_list(self):
        """Test _encode method with list"""
        params = [("key1", "value1"), ("key2", "value2")]
        result = TestSimpleProvider._encode(params)

        self.assertIn("key1=value1", result)
        self.assertIn("key2=value2", result)

    def test_encode_string(self):
        """Test _encode method with string"""
        params = "key1=value1&key2=value2"
        result = TestSimpleProvider._encode(params)

        self.assertEqual(result, params)

    def test_encode_none(self):
        """Test _encode method with None"""
        result = TestSimpleProvider._encode(None)
        self.assertEqual(result, "")

    def test_encode_empty_dict(self):
        """Test _encode method with empty dictionary"""
        result = TestSimpleProvider._encode({})
        self.assertEqual(result, "")

    def test_quote_basic(self):
        """Test _quote method with basic string"""
        data = "hello world"
        result = TestSimpleProvider._quote(data)
        self.assertEqual(result, "hello%20world")

    def test_quote_with_safe_chars(self):
        """Test _quote method with safe characters"""
        data = "hello/world"
        result = TestSimpleProvider._quote(data, safe="/")
        self.assertEqual(result, "hello/world")

    def test_quote_without_safe_chars(self):
        """Test _quote method without safe characters"""
        data = "hello/world"
        result = TestSimpleProvider._quote(data, safe="")
        self.assertEqual(result, "hello%2Fworld")

    def test_mask_sensitive_data_basic(self):
        """Test _mask_sensitive_data method with basic token"""
        provider = TestSimpleProvider(self.auth_id, "secret123")
        data = "url?token=secret123&other=value"

        result = provider._mask_sensitive_data(data)

        self.assertNotIn("secret123", result)
        self.assertIn("se***23", result)

    def test_mask_sensitive_data_short_token(self):
        """Test _mask_sensitive_data method with short token"""
        provider = TestSimpleProvider(self.auth_id, "abc")
        data = "url?token=abc&other=value"

        result = provider._mask_sensitive_data(data)

        self.assertNotIn("abc", result)
        self.assertIn("***", result)

    def test_mask_sensitive_data_empty_data(self):
        """Test _mask_sensitive_data method with empty data"""
        provider = TestSimpleProvider(self.auth_id, self.auth_token)

        result = provider._mask_sensitive_data("")

        self.assertEqual(result, "")

    def test_mask_sensitive_data_none_data(self):
        """Test _mask_sensitive_data method with None data"""
        provider = TestSimpleProvider(self.auth_id, self.auth_token)

        result = provider._mask_sensitive_data(None)

        self.assertIsNone(result)

    def test_mask_sensitive_data_no_token(self):
        """Test _mask_sensitive_data method with no token"""
        # Create provider normally first, then modify auth_token
        provider = TestSimpleProvider(self.auth_id, self.auth_token)
        provider.auth_token = ""  # Override after init
        data = "url?token=secret123&other=value"

        result = provider._mask_sensitive_data(data)

        self.assertEqual(result, data)  # Should be unchanged

    @patch.object(TestSimpleProvider, "_send_request")
    def test_http_get_request(self, mock_send_request):
        """Test _http method with GET request"""
        mock_send_request.return_value = '{"success": true}'
        provider = TestSimpleProvider(self.auth_id, self.auth_token)

        result = provider._http("GET", "/test", params={"key": "value"})

        # Should parse JSON response
        self.assertEqual(result, {"success": True})
        mock_send_request.assert_called_once()
        args, kwargs = mock_send_request.call_args
        self.assertEqual(kwargs["method"], "GET")
        self.assertIn("key=value", kwargs["url"])

    @patch.object(TestSimpleProvider, "_send_request")
    def test_http_post_request_form(self, mock_send_request):
        """Test _http method with POST request using form data"""
        mock_send_request.return_value = '{"success": true}'
        provider = TestSimpleProvider(self.auth_id, self.auth_token)
        provider.ContentType = TYPE_FORM

        result = provider._http("POST", "/test", body={"key": "value"})

        self.assertEqual(result, {"success": True})
        mock_send_request.assert_called_once()
        args, kwargs = mock_send_request.call_args
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["body"], "key=value")

    @patch.object(TestSimpleProvider, "_send_request")
    def test_http_post_request_json(self, mock_send_request):
        """Test _http method with POST request using JSON data"""
        mock_send_request.return_value = '{"success": true}'
        provider = TestSimpleProvider(self.auth_id, self.auth_token)
        provider.ContentType = TYPE_JSON

        result = provider._http("POST", "/test", body={"key": "value"})

        self.assertEqual(result, {"success": True})
        mock_send_request.assert_called_once()
        args, kwargs = mock_send_request.call_args
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["body"], '{"key": "value"}')

    @patch.object(TestSimpleProvider, "_send_request")
    def test_http_no_decode_response(self, mock_send_request):
        """Test _http method with DecodeResponse=False"""
        mock_send_request.return_value = "plain text response"
        provider = TestSimpleProvider(self.auth_id, self.auth_token)
        provider.DecodeResponse = False

        result = provider._http("GET", "/test")

        self.assertEqual(result, "plain text response")
        mock_send_request.assert_called_once()

    @patch.object(TestSimpleProvider, "_send_request")
    def test_http_invalid_json_response(self, mock_send_request):
        """Test _http method with invalid JSON response"""
        mock_send_request.return_value = "invalid json"
        provider = TestSimpleProvider(self.auth_id, self.auth_token)

        with self.assertRaises(Exception):
            provider._http("GET", "/test")

    def test_set_record_abstract_method(self):
        """Test that set_record is implemented in test class"""
        provider = TestSimpleProvider(self.auth_id, self.auth_token)

        result = provider.set_record("example.com", "192.168.1.1")

        self.assertTrue(result)


class TestSimpleProviderWithNoAPI(SimpleProvider):
    """Test implementation without API defined"""

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        return True


class TestSimpleProviderValidation(BaseProviderTestCase):
    """Additional validation tests for SimpleProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestSimpleProviderValidation, self).setUp()

    def test_validate_missing_api(self):
        """Test _validate method when API is not defined"""
        with self.assertRaises(ValueError) as cm:
            TestSimpleProviderWithNoAPI(self.auth_id, self.auth_token)
        self.assertIn("API endpoint must be defined", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
