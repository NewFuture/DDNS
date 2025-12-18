# coding=utf-8
"""
West.cn Provider 单元测试
支持 Python 2.7 和 Python 3
"""

from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.west import WestProvider


class TestWestProvider(BaseProviderTestCase):
    """West.cn Provider 测试类"""

    def setUp(self):
        """测试初始化"""
        super(TestWestProvider, self).setUp()
        # 域名级认证
        self.domain_id = "example.com"
        self.domain_token = "test_apidomainkey"
        # 用户级认证
        self.user_id = "testuser"
        self.user_token = "test_apikey"

    def test_init_with_domain_auth(self):
        """Test WestProvider initialization with domain-level authentication"""
        provider = WestProvider(self.domain_id, self.domain_token)
        self.assertEqual(provider.id, self.domain_id)
        self.assertEqual(provider.token, self.domain_token)
        self.assertEqual(provider.endpoint, "https://api.west.cn/API/v2/domain/dns/")

    def test_init_with_user_auth(self):
        """Test WestProvider initialization with user-level authentication"""
        provider = WestProvider(self.user_id, self.user_token)
        self.assertEqual(provider.id, self.user_id)
        self.assertEqual(provider.token, self.user_token)

    def test_class_constants(self):
        """Test WestProvider class constants"""
        self.assertEqual(WestProvider.endpoint, "https://api.west.cn/API/v2/domain/dns/")
        from ddns.provider._base import TYPE_FORM

        self.assertEqual(WestProvider.content_type, TYPE_FORM)

    def test_validate_success(self):
        """Test _validate method with valid configuration"""
        provider = WestProvider(self.domain_id, self.domain_token)
        # Should not raise exception
        try:
            provider._validate()
            success = True
        except ValueError:
            success = False
        self.assertTrue(success)

    def test_validate_missing_id(self):
        """Test _validate method with missing id"""
        with self.assertRaises(ValueError) as context:
            WestProvider(None, self.domain_token)
        self.assertIn("id and token must be configured", str(context.exception))

    def test_validate_missing_token(self):
        """Test _validate method with missing token"""
        with self.assertRaises(ValueError) as context:
            WestProvider(self.domain_id, None)
        self.assertIn("id and token must be configured", str(context.exception))

    def test_validate_both_missing(self):
        """Test _validate method with both id and token missing"""
        with self.assertRaises(ValueError) as context:
            WestProvider(None, None)
        self.assertIn("id and token must be configured", str(context.exception))

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_success_domain_auth(self, mock_http):
        """Test set_record with domain-level authentication - success"""
        mock_response = {"result": 200, "msg": "Success"}  # fmt: skip
        mock_http.return_value = mock_response

        provider = WestProvider(self.domain_id, self.domain_token)
        result = provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertTrue(result)
        mock_http.assert_called_once()

        # Verify request parameters
        call_args = mock_http.call_args
        self.assertEqual(call_args[0][0], "GET")  # Method
        self.assertEqual(call_args[0][1], "")  # URL path (empty for base endpoint)

        # Verify params
        params = call_args[1]["params"]
        self.assertEqual(params["act"], "dnsrec.update")
        self.assertEqual(params["hostname"], "www.example.com")
        self.assertEqual(params["record_value"], "1.2.3.4")
        self.assertEqual(params["domain"], "example.com")
        self.assertEqual(params["apidomainkey"], self.domain_token)
        self.assertNotIn("username", params)
        self.assertNotIn("apikey", params)

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_success_user_auth(self, mock_http):
        """Test set_record with user-level authentication - success"""
        mock_response = {"result": 200, "msg": "Success"}  # fmt: skip
        mock_http.return_value = mock_response

        provider = WestProvider(self.user_id, self.user_token)
        result = provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertTrue(result)
        mock_http.assert_called_once()

        # Verify request parameters
        call_args = mock_http.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["act"], "dnsrec.update")
        self.assertEqual(params["hostname"], "www.example.com")
        self.assertEqual(params["record_value"], "1.2.3.4")
        self.assertEqual(params["domain"], "example.com")
        self.assertEqual(params["username"], self.user_id)
        self.assertEqual(params["apikey"], self.user_token)
        self.assertNotIn("apidomainkey", params)

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_success_ipv6(self, mock_http):
        """Test set_record with IPv6 address - success"""
        mock_response = {"result": 200, "msg": "Success"}  # fmt: skip
        mock_http.return_value = mock_response

        provider = WestProvider(self.domain_id, self.domain_token)
        result = provider.set_record("www.example.com", "2001:db8::1", "AAAA")

        self.assertTrue(result)
        mock_http.assert_called_once()

        # Verify record value
        params = mock_http.call_args[1]["params"]
        self.assertEqual(params["record_value"], "2001:db8::1")

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_subdomain(self, mock_http):
        """Test set_record with subdomain"""
        mock_response = {"result": 200, "msg": "Success"}  # fmt: skip
        mock_http.return_value = mock_response

        provider = WestProvider(self.domain_id, self.domain_token)
        result = provider.set_record("test.sub.example.com", "1.2.3.4", "A")

        self.assertTrue(result)

        # Verify domain extraction
        params = mock_http.call_args[1]["params"]
        self.assertEqual(params["hostname"], "test.sub.example.com")
        self.assertEqual(params["domain"], "example.com")  # 应该提取最后两部分

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_api_failure(self, mock_http):
        """Test set_record with API failure"""
        mock_response = {"result": 500, "msg": "API Error"}  # fmt: skip
        mock_http.return_value = mock_response

        provider = WestProvider(self.domain_id, self.domain_token)
        provider.logger = MagicMock()

        result = provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertFalse(result)
        provider.logger.error.assert_called()

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_empty_response(self, mock_http):
        """Test set_record with empty response"""
        mock_http.return_value = None

        provider = WestProvider(self.domain_id, self.domain_token)
        provider.logger = MagicMock()

        result = provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertFalse(result)
        provider.logger.error.assert_called()

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_invalid_result_code(self, mock_http):
        """Test set_record with invalid result code"""
        mock_response = {"result": 404, "msg": "Not Found"}  # fmt: skip
        mock_http.return_value = mock_response

        provider = WestProvider(self.domain_id, self.domain_token)
        provider.logger = MagicMock()

        result = provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertFalse(result)
        provider.logger.error.assert_called()

    def test_set_record_invalid_domain(self):
        """Test set_record with invalid domain format"""
        provider = WestProvider(self.domain_id, self.domain_token)
        provider.logger = MagicMock()

        result = provider.set_record("invalid", "1.2.3.4", "A")

        self.assertFalse(result)
        provider.logger.error.assert_called()

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_unsupported_record_type(self, mock_http):
        """Test set_record with unsupported record type"""
        provider = WestProvider(self.domain_id, self.domain_token)
        provider.logger = MagicMock()

        result = provider.set_record("www.example.com", "example.org", "CNAME")

        self.assertFalse(result)
        provider.logger.warning.assert_called()
        # HTTP should not be called for unsupported types
        mock_http.assert_not_called()

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_ttl_ignored(self, mock_http):
        """Test that TTL parameter is ignored (not supported by West.cn DDNS API)"""
        mock_response = {"result": 200, "msg": "Success"}  # fmt: skip
        mock_http.return_value = mock_response

        provider = WestProvider(self.domain_id, self.domain_token)
        result = provider.set_record("www.example.com", "1.2.3.4", "A", ttl=600)

        self.assertTrue(result)

        # Verify TTL is not in params
        params = mock_http.call_args[1]["params"]
        self.assertNotIn("ttl", params)

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_line_ignored(self, mock_http):
        """Test that line parameter is ignored (not supported by West.cn DDNS API)"""
        mock_response = {"result": 200, "msg": "Success"}  # fmt: skip
        mock_http.return_value = mock_response

        provider = WestProvider(self.domain_id, self.domain_token)
        result = provider.set_record("www.example.com", "1.2.3.4", "A", line="default")  # fmt: skip

        self.assertTrue(result)

        # Verify line is not in params
        params = mock_http.call_args[1]["params"]
        self.assertNotIn("line", params)

    @patch("ddns.provider.west.WestProvider._http")
    def test_domain_auth_detection_with_dot(self, mock_http):
        """Test domain-level auth detection when id contains dot"""
        mock_response = {"result": 200, "msg": "Success"}  # fmt: skip
        mock_http.return_value = mock_response

        # id contains dot, should be treated as domain-level auth
        provider = WestProvider("test.example.com", self.domain_token)
        result = provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertTrue(result)

        # Should use domain-level auth
        params = mock_http.call_args[1]["params"]
        self.assertIn("apidomainkey", params)
        self.assertNotIn("username", params)

    @patch("ddns.provider.west.WestProvider._http")
    def test_domain_auth_detection_with_at_sign(self, mock_http):
        """Test domain-level auth detection when id contains @ sign"""
        mock_response = {"result": 200, "msg": "Success"}  # fmt: skip
        mock_http.return_value = mock_response

        # id contains @, should be treated as domain-level auth
        provider = WestProvider("user@example.com", self.domain_token)
        result = provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertTrue(result)

        # Should use domain-level auth
        params = mock_http.call_args[1]["params"]
        self.assertIn("apidomainkey", params)
        self.assertNotIn("username", params)

    @patch("ddns.provider.west.WestProvider._http")
    def test_user_auth_detection(self, mock_http):
        """Test user-level auth detection with simple username"""
        mock_response = {"result": 200, "msg": "Success"}  # fmt: skip
        mock_http.return_value = mock_response

        # id is simple username (no dot or @), should be user-level auth
        provider = WestProvider("testuser", self.user_token)
        result = provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertTrue(result)

        # Should use user-level auth
        params = mock_http.call_args[1]["params"]
        self.assertIn("username", params)
        self.assertIn("apikey", params)
        self.assertNotIn("apidomainkey", params)


if __name__ == "__main__":
    unittest.main()
