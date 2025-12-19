# coding=utf-8
"""
Unit tests for WestProvider (west.cn).
"""

from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.west import WestProvider


class TestWestProvider(BaseProviderTestCase):
    """Test cases for WestProvider."""

    def setUp(self):
        super(TestWestProvider, self).setUp()
        self.id = "user@example.com"
        self.token = "apikey123"

    def test_validate_with_account_credentials(self):
        """Validate succeeds with username/apikey."""
        provider = WestProvider(self.id, self.token)
        provider._validate()

    def test_validate_with_domain_key_only(self):
        """Validate succeeds when only apidomainkey provided."""
        provider = WestProvider("", "domainkey")
        provider._validate()
        self.assertEqual(provider.id, "")

    def test_validate_missing_token(self):
        """Validate fails when token is missing."""
        with self.assertRaises(ValueError):
            WestProvider(self.id, "")

    @patch.object(WestProvider, "_http")
    def test_set_record_success_with_domain_key(self, mock_http):
        """set_record returns True when API responds with code 200 using domain key."""
        mock_http.return_value = {"code": 200, "msg": "success", "body": {"record_id": 1}}

        provider = WestProvider("", "domainkey")

        result = provider.set_record("test.example.com", "1.2.3.4")

        self.assertTrue(result)
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], "/")
        queries = kwargs["queries"]
        self.assertEqual(queries["act"], "dnsrec.update")
        self.assertEqual(queries["domain"], "test.example.com")
        self.assertEqual(queries["hostname"], "test.example.com")
        self.assertEqual(queries["record_value"], "1.2.3.4")
        self.assertEqual(queries["apidomainkey"], "domainkey")

    @patch.object(WestProvider, "_http")
    def test_set_record_success_with_account_auth(self, mock_http):
        """set_record returns True when API responds with code 200 using username/apikey."""
        mock_http.return_value = {"code": 200, "msg": "success"}

        provider = WestProvider(self.id, self.token)

        result = provider.set_record("ipv6.example.com", "::1")

        self.assertTrue(result)
        queries = mock_http.call_args[1]["queries"]
        self.assertEqual(queries["username"], self.id)
        self.assertEqual(queries["apikey"], self.token)
        self.assertEqual(queries["record_value"], "::1")

    @patch.object(WestProvider, "_http")
    def test_set_record_error_code(self, mock_http):
        """set_record handles non-200 code as failure."""
        mock_http.return_value = {"code": 400, "msg": "error"}

        provider = WestProvider(self.id, self.token)
        provider.logger = MagicMock()

        result = provider.set_record("test.example.com", "1.1.1.1")

        self.assertFalse(result)
        provider.logger.error.assert_called_once()

    @patch.object(WestProvider, "_http")
    def test_set_record_empty_response(self, mock_http):
        """set_record returns False on empty response."""
        mock_http.return_value = None

        provider = WestProvider(self.id, self.token)
        provider.logger = MagicMock()

        self.assertFalse(provider.set_record("test.example.com", "1.1.1.1"))
        provider.logger.error.assert_called_once()

    @patch.object(WestProvider, "_http")
    def test_set_record_exception(self, mock_http):
        """set_record returns False when _http raises."""
        mock_http.side_effect = Exception("network error")

        provider = WestProvider(self.id, self.token)
        provider.logger = MagicMock()

        self.assertFalse(provider.set_record("test.example.com", "1.1.1.1"))
        provider.logger.error.assert_called_once()

    @patch.object(WestProvider, "_http")
    def test_set_record_string_success(self, mock_http):
        """set_record treats string containing success as True."""
        mock_http.return_value = "Success"

        provider = WestProvider(self.id, self.token)

        self.assertTrue(provider.set_record("test.example.com", "1.1.1.1"))


if __name__ == "__main__":
    unittest.main()
