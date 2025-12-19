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

    def test_line_mapping(self):
        """Test LINE_MAPPING contains expected values"""
        mapping = WestProvider.LINE_MAPPING
        self.assertEqual(mapping["默认"], "")
        self.assertEqual(mapping["电信"], "LTEL")
        self.assertEqual(mapping["联通"], "LCNC")
        self.assertEqual(mapping["移动"], "LMOB")
        self.assertEqual(mapping["教育网"], "LEDU")
        self.assertEqual(mapping["搜索引擎"], "LSEO")
        self.assertEqual(mapping["境外"], "LFOR")

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

    def test_parse_domain_simple(self):
        """Test _parse_domain with simple subdomain"""
        subdomain, main = self.provider._parse_domain("www.example.com")
        self.assertEqual(subdomain, "www")
        self.assertEqual(main, "example.com")

    def test_parse_domain_root(self):
        """Test _parse_domain with root domain"""
        subdomain, main = self.provider._parse_domain("example.com")
        self.assertEqual(subdomain, "@")
        self.assertEqual(main, "example.com")

    def test_parse_domain_multi_level(self):
        """Test _parse_domain with multi-level subdomain"""
        subdomain, main = self.provider._parse_domain("sub.www.example.com")
        self.assertEqual(subdomain, "sub.www")
        self.assertEqual(main, "example.com")

    def test_parse_domain_with_tilde_separator(self):
        """Test _parse_domain with ~ separator"""
        subdomain, main = self.provider._parse_domain("www~example.com")
        self.assertEqual(subdomain, "www")
        self.assertEqual(main, "example.com")

    def test_parse_domain_with_plus_separator(self):
        """Test _parse_domain with + separator"""
        subdomain, main = self.provider._parse_domain("subdomain+example.com")
        self.assertEqual(subdomain, "subdomain")
        self.assertEqual(main, "example.com")

    def test_parse_domain_single_level(self):
        """Test _parse_domain with single level domain (TLD)"""
        subdomain, main = self.provider._parse_domain("localhost")
        self.assertEqual(subdomain, "@")
        self.assertEqual(main, "localhost")

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_success(self, mock_http):
        """Test set_record with successful response"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 118610345}}

        result = self.provider.set_record("www.example.com", "192.168.1.1")

        self.assertTrue(result)
        mock_http.assert_called_once()
        call_args = mock_http.call_args
        self.assertEqual(call_args[0][0], "POST")
        body = call_args[1]["body"]
        self.assertEqual(body["act"], "dnsrec.update")
        self.assertEqual(body["domain"], "example.com")
        self.assertEqual(body["hostname"], "www")
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
        """Test set_record with line parameter"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider.set_record("www.example.com", "192.168.1.1", line="电信")

        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["record_line"], "LTEL")

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_with_line_default(self, mock_http):
        """Test set_record with default line (should not add record_line)"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider.set_record("www.example.com", "192.168.1.1", line="默认")

        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        # Default line maps to empty string, should not be in body
        self.assertNotIn("record_line", body)

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_with_custom_line(self, mock_http):
        """Test set_record with custom line value not in mapping"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider.set_record("www.example.com", "192.168.1.1", line="CUSTOM")

        self.assertTrue(result)
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["record_line"], "CUSTOM")

    @patch("ddns.provider.west.WestProvider._http")
    def test_set_record_failure_api_error(self, mock_http):
        """Test set_record with API error response"""
        mock_http.return_value = {"code": 500, "msg": "Domain not found"}

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
    def test_set_record_domain_lowercase(self, mock_http):
        """Test set_record converts domain to lowercase"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider.set_record("WWW.EXAMPLE.COM", "192.168.1.1")

        self.assertTrue(result)
        # The domain should be lowercased in logging and parsing
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["hostname"], "www")
        self.assertEqual(body["domain"], "example.com")


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

        result = self.provider.set_record("ddns.example.com", "192.168.1.100", record_type="A", ttl=600, line="电信")

        self.assertTrue(result)
        mock_http.assert_called_once()

        # Verify the request parameters
        call_args = mock_http.call_args
        body = call_args[1]["body"]
        self.assertEqual(body["act"], "dnsrec.update")
        self.assertEqual(body["domain"], "example.com")
        self.assertEqual(body["hostname"], "ddns")
        self.assertEqual(body["record_value"], "192.168.1.100")
        self.assertEqual(body["record_line"], "LTEL")

    @patch("ddns.provider.west.WestProvider._http")
    def test_full_workflow_with_multilevel_subdomain(self, mock_http):
        """Test workflow with multi-level subdomain"""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 123456}}

        result = self.provider.set_record("a.b.c.example.com", "10.0.0.1", record_type="A")

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

    def test_35_alias_registered(self):
        """Test that 35 (三五互联) alias is registered"""
        from ddns.provider import get_provider_class

        provider_class = get_provider_class("35")
        self.assertEqual(provider_class, WestProvider)

    def test_35cn_alias_registered(self):
        """Test that 35cn alias is registered"""
        from ddns.provider import get_provider_class

        provider_class = get_provider_class("35cn")
        self.assertEqual(provider_class, WestProvider)


if __name__ == "__main__":
    unittest.main()
