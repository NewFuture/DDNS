# coding=utf-8
"""Unit tests for West.cn DNS provider"""

from base_test import BaseProviderTestCase, patch, unittest
from ddns.provider.west import WestProvider


class TestWestProvider(BaseProviderTestCase):
    """Test cases for West.cn DNS provider"""

    def setUp(self):
        """Set up provider"""
        super(TestWestProvider, self).setUp()
        self.provider = WestProvider(self.id, self.token)

    def test_init_with_defaults(self):
        """Ensure provider initialized with defaults"""
        self.assertProviderInitialized(self.provider)
        self.assertEqual(self.provider.endpoint, "https://api.west.cn")
        self.assertEqual(self.provider.content_type, "application/x-www-form-urlencoded")

    def test_validate_missing_token(self):
        """Validate missing token raises error"""
        with self.assertRaises(ValueError):
            WestProvider(self.id, "")

    def test_domain_level_auth_params(self):
        """Auth params should use domain key when id is empty"""
        provider = WestProvider("", self.token)
        params = provider._auth_params("example.com")
        self.assertIn("apidomainkey", params)
        self.assertNotIn("username", params)
        self.assertEqual(params["domain"], "example.com")

    def test_user_level_auth_params(self):
        """Auth params should include username when id provided"""
        params = self.provider._auth_params("example.com")
        self.assertEqual(params["username"], self.id)
        self.assertEqual(params["apikey"], self.token)

    @patch.object(WestProvider, "_http")
    def test_query_zone_id_success(self, mock_http):
        """Query zone id should return domain on success"""
        mock_http.return_value = {"code": 1, "data": []}
        result = self.provider._query_zone_id("example.com")
        self.assertEqual(result, "example.com")
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "POST")
        self.assertEqual(args[1], "/API/v2/domain/dns/")
        body = kwargs.get("body")
        self.assertEqual(body.get("act"), "dnsrec.list")
        self.assertEqual(body.get("domain"), "example.com")

    @patch.object(WestProvider, "_http")
    def test_query_zone_id_failure(self, mock_http):
        """Query zone id should return None on failure"""
        mock_http.return_value = {"code": 500, "msg": "error"}
        result = self.provider._query_zone_id("example.com")
        self.assertIsNone(result)

    @patch.object(WestProvider, "_http")
    def test_query_record_found(self, mock_http):
        """Query record should return matching record"""
        mock_http.return_value = {
            "code": 1,
            "data": [
                {
                    "id": "123",
                    "hostname": "test.example.com",
                    "record_type": "A",
                    "record_value": "1.2.3.4",
                    "record_line": "default",
                    "record_ttl": 600,
                }
            ],
        }
        record = self.provider._query_record("example.com", "test", "example.com", "A", None, {})
        self.assertIsNotNone(record)
        self.assertEqual(record.get("id"), "123")

    @patch.object(WestProvider, "_http")
    def test_query_record_line_mismatch(self, mock_http):
        """Query record should return None when line mismatched"""
        mock_http.return_value = {
            "code": 1,
            "data": [
                {"hostname": "test.example.com", "record_type": "A", "record_line": "other", "record_value": "1.1.1.1"}
            ],
        }
        record = self.provider._query_record("example.com", "test", "example.com", "A", "default", {})
        self.assertIsNone(record)

    @patch.object(WestProvider, "_http")
    def test_create_record_success(self, mock_http):
        """Create record should send add action"""
        mock_http.return_value = {"code": 1, "msg": "ok", "id": "456"}
        result = self.provider._create_record("example.com", "test", "example.com", "1.2.3.4", "A", 600, "default", {})
        self.assertTrue(result)
        args, kwargs = mock_http.call_args
        body = kwargs.get("body")
        self.assertEqual(body.get("act"), "dnsrec.add")
        self.assertEqual(body.get("hostname"), "test.example.com")
        self.assertEqual(body.get("record_type"), "A")
        self.assertEqual(body.get("record_value"), "1.2.3.4")
        self.assertEqual(body.get("record_ttl"), 600)
        self.assertEqual(body.get("record_line"), "default")

    @patch.object(WestProvider, "_http")
    def test_create_record_failure(self, mock_http):
        """Create record should return False on failure"""
        mock_http.return_value = {"code": 500}
        result = self.provider._create_record("example.com", "test", "example.com", "1.2.3.4", "A", None, None, {})
        self.assertFalse(result)

    @patch.object(WestProvider, "_http")
    def test_update_record_uses_existing_fields(self, mock_http):
        """Update record should reuse ttl and line when not provided"""
        mock_http.return_value = {"code": 1, "msg": "ok"}
        old_record = {
            "id": "789",
            "hostname": "test.example.com",
            "record_type": "A",
            "record_line": "default",
            "record_ttl": 300,
        }
        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})
        self.assertTrue(result)
        args, kwargs = mock_http.call_args
        body = kwargs.get("body")
        self.assertEqual(body.get("act"), "dnsrec.update")
        self.assertEqual(body.get("record_ttl"), 300)
        self.assertEqual(body.get("record_line"), "default")
        self.assertEqual(body.get("record_id"), "789")

    @patch.object(WestProvider, "_http")
    def test_update_record_failure(self, mock_http):
        """Update record should return False on failure"""
        mock_http.return_value = {"code": 500}
        old_record = {"hostname": "test.example.com", "record_type": "A"}
        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
