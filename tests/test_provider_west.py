# coding=utf-8
"""
West.cn Provider 单元测试
西部数码 DNS 服务商接口测试
支持 Python 2.7 和 Python 3
"""

from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.west import WestProvider


class TestWestProvider(BaseProviderTestCase):
    """West.cn Provider 测试类"""

    def setUp(self):
        """测试初始化"""
        super(TestWestProvider, self).setUp()
        self.provider = WestProvider(self.id, self.token)

    def test_init_with_basic_config(self):
        """Test WestProvider initialization with basic configuration"""
        provider = WestProvider(self.id, self.token)
        self.assertEqual(provider.id, self.id)
        self.assertEqual(provider.token, self.token)
        self.assertEqual(provider.endpoint, "https://api.west.cn/API/v2/domain/dns/")

    def test_class_constants(self):
        """Test WestProvider class constants"""
        self.assertEqual(WestProvider.endpoint, "https://api.west.cn/API/v2/domain/dns/")
        # ContentType should be TYPE_FORM
        from ddns.provider._base import TYPE_FORM

        self.assertEqual(WestProvider.content_type, TYPE_FORM)

    def test_init_with_custom_endpoint(self):
        """Test WestProvider initialization with custom endpoint (35.cn)"""
        custom_endpoint = "https://api.35.cn/API/v2/domain/dns/"
        provider = WestProvider(self.id, self.token, endpoint=custom_endpoint)
        self.assertEqual(provider.endpoint, custom_endpoint)

    def test_validate_with_token_only(self):
        """Test _validate passes with only token"""
        provider = WestProvider(None, self.token)
        # Should not raise exception
        self.assertIsNone(provider.id)
        self.assertEqual(provider.token, self.token)

    def test_validate_missing_token(self):
        """Test _validate raises error when token is missing"""
        with self.assertRaises(ValueError) as cm:
            WestProvider(self.id, "")
        self.assertIn("token", str(cm.exception))

    def test_validate_missing_token_none(self):
        """Test _validate raises error when token is None"""
        with self.assertRaises(ValueError) as cm:
            WestProvider(self.id, None)
        self.assertIn("token", str(cm.exception))

    def test_get_auth_params_domain_auth(self):
        """Test _get_auth_params with domain authentication (apidomainkey)"""
        # When id is a domain name or None, use apidomainkey auth
        provider = WestProvider(None, "test_apidomainkey")
        params = provider._get_auth_params()
        self.assertEqual(params, {"apidomainkey": "test_apidomainkey"})

    def test_get_auth_params_account_auth(self):
        """Test _get_auth_params with account authentication (username + apikey)"""
        provider = WestProvider("myusername", "md5_api_password")
        params = provider._get_auth_params()
        self.assertEqual(params, {"username": "myusername", "apikey": "md5_api_password"})

    def test_get_auth_params_with_email_id(self):
        """Test _get_auth_params with email as id (account auth)"""
        provider = WestProvider("user@example.com", "md5_api_password")
        params = provider._get_auth_params()
        self.assertEqual(params, {"username": "user@example.com", "apikey": "md5_api_password"})

    def test_get_auth_params_with_numeric_id(self):
        """Test _get_auth_params with numeric id (account auth)"""
        provider = WestProvider("123456", "md5_api_password")
        params = provider._get_auth_params()
        self.assertEqual(params, {"username": "123456", "apikey": "md5_api_password"})

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_success(self, mock_http):
        """Test set_record with successful response"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 118610345}}

        result = self.provider.set_record("www.example.com", "192.168.1.1")

        self.assertTrue(result)
        mock_http.assert_called()
        call_args = mock_http.call_args
        self.assertEqual(call_args[0][0], "POST")
        body = call_args[1]["body"]
        self.assertEqual(body["act"], "dnsrec.update")
        self.assertEqual(body["record_value"], "192.168.1.1")

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_with_root_domain(self, mock_http):
        """Test set_record with root domain (@)"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider.set_record("example.com", "192.168.1.1")

        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["hostname"], "@")
        self.assertEqual(body["domain"], "example.com")

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_with_ipv6(self, mock_http):
        """Test set_record with IPv6 address"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider.set_record("www.example.com", "2001:db8::1", record_type="AAAA")

        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["record_value"], "2001:db8::1")

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_with_line(self, mock_http):
        """Test set_record with line parameter (direct code)"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider.set_record("www.example.com", "192.168.1.1", line="LTEL")

        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["record_line"], "LTEL")

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_with_line_code(self, mock_http):
        """Test set_record with various line codes"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        # Test LCNC (China Unicom)
        result = self.provider.set_record("www.example.com", "192.168.1.1", line="LCNC")
        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["record_line"], "LCNC")

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_failure_api_error(self, mock_http):
        """Test set_record with API error response"""
        mock_http.return_value = {"code": 500, "msg": "Authentication failed"}

        self.provider.logger = MagicMock()
        result = self.provider.set_record("www.example.com", "192.168.1.1")

        self.assertFalse(result)
        self.provider.logger.error.assert_called()

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_failure_invalid_response(self, mock_http):
        """Test set_record with invalid response"""
        mock_http.return_value = None

        self.provider.logger = MagicMock()
        result = self.provider.set_record("www.example.com", "192.168.1.1")

        self.assertFalse(result)
        self.provider.logger.error.assert_called()

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_failure_exception(self, mock_http):
        """Test set_record when exception is raised"""
        mock_http.side_effect = RuntimeError("Network error")

        self.provider.logger = MagicMock()
        result = self.provider.set_record("www.example.com", "192.168.1.1")

        self.assertFalse(result)
        self.provider.logger.error.assert_called()

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_auth_domain_mode(self, mock_http):
        """Test set_record includes apidomainkey in request"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        provider = WestProvider(None, "test_apidomainkey")
        result = provider.set_record("www.example.com", "192.168.1.1")

        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["apidomainkey"], "test_apidomainkey")
        self.assertNotIn("username", body)
        self.assertNotIn("apikey", body)

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_auth_account_mode(self, mock_http):
        """Test set_record includes username and apikey in request"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        provider = WestProvider("myuser", "myapikey")
        result = provider.set_record("www.example.com", "192.168.1.1")

        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["username"], "myuser")
        self.assertEqual(body["apikey"], "myapikey")
        self.assertNotIn("apidomainkey", body)

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_with_tilde_domain(self, mock_http):
        """Test set_record with domain using ~ separator"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider.set_record("www~example.com", "192.168.1.1")

        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["hostname"], "www")
        self.assertEqual(body["domain"], "example.com")

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_with_plus_domain(self, mock_http):
        """Test set_record with domain using + separator"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider.set_record("subdomain+example.com", "192.168.1.1")

        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["hostname"], "subdomain")
        self.assertEqual(body["domain"], "example.com")

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_domain_lowercase(self, mock_http):
        """Test set_record converts domain to lowercase"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider.set_record("WWW.EXAMPLE.COM", "192.168.1.1")

        self.assertTrue(result)
        # The domain should be lowercased
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["hostname"], "www")
        self.assertEqual(body["domain"], "example.com")

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_domain_not_found_fallback(self, mock_http):
        """Test set_record with domain not found fallback"""
        # First call returns domain not found (code=404), second succeeds
        mock_http.side_effect = [
            {"code": 404, "msg": "Domain not found"},
            {"code": 200, "msg": "success", "body": {"record_id": 123456}},
        ]

        self.provider.logger = MagicMock()
        result = self.provider.set_record("www.example.com", "192.168.1.1")

        self.assertTrue(result)
        self.assertEqual(mock_http.call_count, 2)


class TestWestProviderIntegration(BaseProviderTestCase):
    """West.cn Provider 集成测试类"""

    def setUp(self):
        """测试初始化"""
        super(TestWestProviderIntegration, self).setUp()
        self.provider = WestProvider(self.id, self.token)
        self.provider.logger = MagicMock()

    @patch("ddns.provider.west.WestProvider._http")
    def test_full_workflow_success(self, mock_http):
        """Test complete workflow for updating a record"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 118610345}}

        result = self.provider.set_record("ddns.example.com", "192.168.1.100", record_type="A", ttl=600, line="LTEL")

        self.assertTrue(result)
        mock_http.assert_called()

        # Verify the request parameters
        call_args = mock_http.call_args
        body = call_args[1]["body"]
        self.assertEqual(body["act"], "dnsrec.update")
        self.assertEqual(body["record_value"], "192.168.1.100")
        self.assertEqual(body["record_line"], "LTEL")

    @patch("ddns.provider.west.WestProvider._http")
    def test_full_workflow_with_multilevel_subdomain(self, mock_http):
        """Test workflow with multi-level subdomain using explicit separator"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider.set_record("a.b.c~example.com", "10.0.0.1", record_type="A")

        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["hostname"], "a.b.c")
        self.assertEqual(body["domain"], "example.com")

    @patch("ddns.provider.west.WestProvider._http")
    def test_full_workflow_api_failure(self, mock_http):
        """Test workflow when API returns failure"""
        mock_http.return_value = {"code": 500, "msg": "Authentication failed"}

        result = self.provider.set_record("www.example.com", "192.168.1.1")

        self.assertFalse(result)
        self.provider.logger.error.assert_called()

    @patch("ddns.provider.west.WestProvider._http")
    def test_workflow_with_different_record_types(self, mock_http):
        """Test workflow with different record types (A vs AAAA)"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        # Test A record
        result = self.provider.set_record("www.example.com", "192.168.1.1", record_type="A")
        self.assertTrue(result)

        # Test AAAA record
        result = self.provider.set_record("www.example.com", "2001:db8::1", record_type="AAAA")
        self.assertTrue(result)


class TestWestProviderTryUpdate(BaseProviderTestCase):
    """Test _try_update method"""

    def setUp(self):
        """测试初始化"""
        super(TestWestProviderTryUpdate, self).setUp()
        self.provider = WestProvider(self.id, self.token)
        self.provider.logger = MagicMock()

    @patch("ddns.provider.west.WestProvider._http")
    def test_try_update_success(self, mock_http):
        """Test _try_update with successful response"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider._try_update("www", "example.com", "192.168.1.1", None)

        self.assertTrue(result)

    @patch("ddns.provider.west.WestProvider._http")
    def test_try_update_not_found(self, mock_http):
        """Test _try_update returns None when domain not found (code=404)"""
        mock_http.return_value = {"code": 404, "msg": "Domain not found"}

        result = self.provider._try_update("www", "example.com", "192.168.1.1", None)

        self.assertIsNone(result)

    @patch("ddns.provider.west.WestProvider._http")
    def test_try_update_with_line(self, mock_http):
        """Test _try_update with line parameter"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider._try_update("www", "example.com", "192.168.1.1", "LTEL")

        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["record_line"], "LTEL")


class TestWestProviderFromRegistry(BaseProviderTestCase):
    """Test West.cn provider registration"""

    def test_west_provider_registered(self):
        """Test that west provider is registered in get_provider_class"""
        from ddns.provider import get_provider_class

        provider_class = get_provider_class("west")
        self.assertEqual(provider_class, WestProvider)

    def test_west_cn_alias_registered(self):
        """Test that west_cn alias is registered"""
        from ddns.provider import get_provider_class

        provider_class = get_provider_class("west_cn")
        self.assertEqual(provider_class, WestProvider)

    def test_35cn_alias_registered(self):
        """Test that 35cn alias is registered"""
        from ddns.provider import get_provider_class

        provider_class = get_provider_class("35cn")
        self.assertEqual(provider_class, WestProvider)

    def test_35_alias_not_registered(self):
        """Test that 35 alias is NOT registered (removed per review)"""
        from ddns.provider import get_provider_class

        provider_class = get_provider_class("35")
        self.assertIsNone(provider_class)


if __name__ == "__main__":
    unittest.main()
