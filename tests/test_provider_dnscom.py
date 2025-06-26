# coding=utf-8
"""
Unit tests for DnscomProvider

@author: Github Copilot
"""

from test_base import BaseProviderTestCase, unittest, patch
from ddns.provider.dnscom import DnscomProvider


class TestDnscomProvider(BaseProviderTestCase):
    """Test cases for DnscomProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestDnscomProvider, self).setUp()
        self.auth_id = "test_api_key"
        self.auth_token = "test_api_secret"

    def test_class_constants(self):
        """Test DnscomProvider class constants"""
        self.assertEqual(DnscomProvider.API, "https://www.51dns.com")
        self.assertEqual(DnscomProvider.ContentType, "application/x-www-form-urlencoded")
        self.assertTrue(DnscomProvider.DecodeResponse)

    def test_init_with_basic_config(self):
        """Test DnscomProvider initialization with basic configuration"""
        provider = DnscomProvider(self.auth_id, self.auth_token)
        self.assertEqual(provider.auth_id, self.auth_id)
        self.assertEqual(provider.auth_token, self.auth_token)
        self.assertEqual(provider.API, "https://www.51dns.com")

    @patch("ddns.provider.dnscom.time")
    @patch("ddns.provider.dnscom.md5")
    def test_signature_generation(self, mock_md5, mock_time):
        """Test _signature method generates correct signature"""
        # Mock time and hash
        mock_time.return_value = 1640995200  # Fixed timestamp
        mock_hash = mock_md5.return_value
        mock_hash.hexdigest.return_value = "test_hash_value"

        provider = DnscomProvider(self.auth_id, self.auth_token)

        params = {"action": "test", "domain": "example.com"}
        signed_params = provider._signature(params)

        # Verify standard parameters are added
        self.assertEqual(signed_params["apiKey"], self.auth_id)
        self.assertEqual(signed_params["timestamp"], 1640995200)
        self.assertEqual(signed_params["hash"], "test_hash_value")
        self.assertIn("action", signed_params)
        self.assertIn("domain", signed_params)

    def test_signature_filters_none_params(self):
        """Test _signature method filters out None parameters"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch("ddns.provider.dnscom.time") as mock_time, patch("ddns.provider.dnscom.md5") as mock_md5:

            mock_time.return_value = 1640995200
            mock_hash = mock_md5.return_value
            mock_hash.hexdigest.return_value = "test_hash"

            params = {"action": "test", "domain": "example.com", "ttl": None, "line": None}
            signed_params = provider._signature(params)

            # Verify None parameters were filtered out
            self.assertNotIn("ttl", signed_params)
            self.assertNotIn("line", signed_params)
            self.assertIn("action", signed_params)
            self.assertIn("domain", signed_params)

    def test_request_success(self):
        """Test _request method with successful response"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_signature") as mock_signature, patch.object(provider, "_http") as mock_http:

            mock_signature.return_value = {"apiKey": self.auth_id, "hash": "test_hash"}
            mock_http.return_value = {"code": 0, "data": {"result": "success"}}

            result = provider._request("test", domain="example.com")

            mock_signature.assert_called_once_with({"domain": "example.com"})
            mock_http.assert_called_once_with(
                "POST", "/api/test/", body={"apiKey": self.auth_id, "hash": "test_hash"}
            )
            self.assertEqual(result, {"result": "success"})

    def test_request_failure_none_response(self):
        """Test _request method with None response"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_signature") as mock_signature, patch.object(provider, "_http") as mock_http:

            mock_signature.return_value = {"apiKey": self.auth_id}
            mock_http.return_value = None

            with self.assertRaises(Exception) as cm:
                provider._request("test", domain="example.com")

            self.assertIn("response data is none", str(cm.exception))

    def test_request_failure_api_error(self):
        """Test _request method with API error response"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_signature") as mock_signature, patch.object(provider, "_http") as mock_http:

            mock_signature.return_value = {"apiKey": self.auth_id}
            mock_http.return_value = {"code": 1, "message": "Invalid API key"}

            with self.assertRaises(Exception) as cm:
                provider._request("test", domain="example.com")

            self.assertIn("api error: Invalid API key", str(cm.exception))

    def test_query_zone_id_success(self):
        """Test _query_zone_id method with successful response"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"domainID": "example.com"}

            result = provider._query_zone_id("example.com")

            mock_request.assert_called_once_with("domain/getsingle", domainID="example.com")
            self.assertEqual(result, "example.com")

    def test_query_zone_id_not_found(self):
        """Test _query_zone_id method when domain is not found"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = None

            result = provider._query_zone_id("notfound.com")

            mock_request.assert_called_once_with("domain/getsingle", domainID="notfound.com")
            self.assertIsNone(result)

    def test_query_record_success(self):
        """Test _query_record method with successful response"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "data": [
                    {"record": "www", "type": "A", "recordID": "123", "value": "1.2.3.4"},
                    {"record": "mail", "type": "A", "recordID": "456", "value": "5.6.7.8"},
                ]
            }

            result = provider._query_record("example.com", "www", "example.com", "A")  # type: dict # type: ignore

            mock_request.assert_called_once_with("record/list", domainID="example.com", host="www", pageSize=500)
            self.assertEqual(result["recordID"], "123")
            self.assertEqual(result["record"], "www")

    def test_query_record_with_line(self):
        """Test _query_record method with line parameter"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "data": [
                    {"record": "www", "type": "A", "recordID": "123", "viewID": "1"},
                    {"record": "www", "type": "A", "recordID": "456", "viewID": "2"},
                ]
            }

            result = provider._query_record(
                "example.com", "www", "example.com", "A", "2"
            )  # type: dict # type: ignore

            self.assertEqual(result["recordID"], "456")
            self.assertEqual(result["viewID"], "2")

    def test_query_record_not_found(self):
        """Test _query_record method when no matching record is found"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "data": [{"record": "mail", "type": "A", "recordID": "456", "value": "5.6.7.8"}]
            }

            result = provider._query_record("example.com", "www", "example.com", "A")

            self.assertIsNone(result)

    def test_query_record_empty_response(self):
        """Test _query_record method with empty response"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = None

            result = provider._query_record("example.com", "www", "example.com", "A")

            self.assertIsNone(result)

    def test_create_record_success(self):
        """Test _create_record method with successful creation"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"recordID": "123456"}

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", 300, "1")

            mock_request.assert_called_once_with(
                "record/create",
                domainID="example.com",
                value="1.2.3.4",
                host="www",
                type="A",
                TTL=300,
                viewID="1",
                remark=provider.Remark,
            )
            self.assertTrue(result)

    def test_create_record_with_extra_params(self):
        """Test _create_record method with extra parameters"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"recordID": "123456"}

            extra = {"remark": "Custom remark", "priority": 10}
            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", 300, "1", extra)

            mock_request.assert_called_once_with(
                "record/create",
                domainID="example.com",
                value="1.2.3.4",
                host="www",
                type="A",
                TTL=300,
                viewID="1",
                remark="Custom remark",
                priority=10,
            )
            self.assertTrue(result)

    def test_create_record_failure(self):
        """Test _create_record method with failed creation"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"error": "Domain not found"}

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_update_record_success(self):
        """Test _update_record method with successful update"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        old_record = {"recordID": "123456", "remark": "Old remark"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"success": True}

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600)

            mock_request.assert_called_once_with(
                "record/modify", domainID="example.com", recordID="123456", newvalue="5.6.7.8", newTTL=600
            )
            self.assertTrue(result)

    def test_update_record_with_extra_params(self):
        """Test _update_record method with extra parameters"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        old_record = {"recordID": "123456", "remark": "Old remark"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"success": True}

            extra = {"remark": "New remark"}
            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, "1", extra)

            mock_request.assert_called_once_with(
                "record/modify", domainID="example.com", recordID="123456", newvalue="5.6.7.8", newTTL=600
            )
            self.assertTrue(result)

    def test_update_record_failure(self):
        """Test _update_record method with failed update"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        old_record = {"recordID": "123456"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = None

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A")

            self.assertFalse(result)


class TestDnscomProviderIntegration(BaseProviderTestCase):
    """Integration test cases for DnscomProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestDnscomProviderIntegration, self).setUp()
        self.auth_id = "test_api_key"
        self.auth_token = "test_api_secret"

    def test_full_workflow_create_new_record(self):
        """Test complete workflow for creating a new record"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_create_record") as mock_create:

            # Setup mocks
            mock_zone.return_value = "example.com"
            mock_query.return_value = None  # No existing record
            mock_create.return_value = True

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "1")

            self.assertTrue(result)
            mock_zone.assert_called_once_with("example.com")
            mock_query.assert_called_once_with(
                "example.com", sub_domain="www", main_domain="example.com", record_type="A", line="1", extra={}
            )
            mock_create.assert_called_once_with(
                "example.com",
                sub_domain="www",
                main_domain="example.com",
                value="1.2.3.4",
                record_type="A",
                ttl=300,
                line="1",
                extra={},
            )

    def test_full_workflow_update_existing_record(self):
        """Test complete workflow for updating an existing record"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        existing_record = {"recordID": "123456", "record": "www", "value": "5.6.7.8"}

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_update_record") as mock_update:

            # Setup mocks
            mock_zone.return_value = "example.com"
            mock_query.return_value = existing_record
            mock_update.return_value = True

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "1")

            self.assertTrue(result)
            mock_zone.assert_called_once_with("example.com")
            mock_query.assert_called_once_with(
                "example.com", sub_domain="www", main_domain="example.com", record_type="A", line="1", extra={}
            )
            mock_update.assert_called_once_with(
                "example.com",
                old_record=existing_record,
                value="1.2.3.4",
                record_type="A",
                ttl=300,
                line="1",
                extra={},
            )

    def test_full_workflow_zone_not_found(self):
        """Test complete workflow when zone is not found"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_query_zone_id") as mock_zone:
            mock_zone.return_value = None

            with self.assertRaises(ValueError) as cm:
                provider.set_record("www.nonexistent.com", "1.2.3.4", "A")

            self.assertIn("Cannot resolve zone_id", str(cm.exception))

    def test_full_workflow_create_failure(self):
        """Test complete workflow when record creation fails"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_create_record") as mock_create:

            # Setup mocks
            mock_zone.return_value = "example.com"
            mock_query.return_value = None  # No existing record
            mock_create.return_value = False  # Creation fails

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_update_failure(self):
        """Test complete workflow when record update fails"""
        provider = DnscomProvider(self.auth_id, self.auth_token)

        existing_record = {"recordID": "123456", "record": "www", "value": "5.6.7.8"}

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_update_record") as mock_update:

            # Setup mocks
            mock_zone.return_value = "example.com"
            mock_query.return_value = existing_record
            mock_update.return_value = False  # Update fails

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
