# coding=utf-8
"""
Unit tests for DnscomProvider

@author: GitHub Copilot
"""

from base_test import BaseProviderTestCase, unittest, patch
from ddns.provider.dnscom import DnscomProvider


class TestDnscomProvider(BaseProviderTestCase):
    """Test cases for DnscomProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestDnscomProvider, self).setUp()
        self.id = "test_api_key"
        self.token = "test_api_secret"

    def test_class_constants(self):
        """Test DnscomProvider class constants"""
        self.assertEqual(DnscomProvider.endpoint, "https://www.51dns.com")
        self.assertEqual(DnscomProvider.content_type, "application/x-www-form-urlencoded")
        self.assertTrue(DnscomProvider.decode_response)

    def test_init_with_basic_config(self):
        """Test DnscomProvider initialization with basic configuration"""
        provider = DnscomProvider(self.id, self.token)
        self.assertEqual(provider.id, self.id)
        self.assertEqual(provider.token, self.token)
        self.assertEqual(provider.endpoint, "https://www.51dns.com")

    @patch("ddns.provider.dnscom.time")
    @patch("ddns.provider.dnscom.md5")
    def test_signature_generation(self, mock_md5, mock_time):
        """Test _signature method generates correct signature"""
        # Mock time and hash
        mock_time.return_value = 1640995200  # Fixed timestamp
        mock_hash = mock_md5.return_value
        mock_hash.hexdigest.return_value = "test_hash_value"

        provider = DnscomProvider(self.id, self.token)

        params = {"action": "test", "domain": "example.com"}
        signed_params = provider._signature(params)

        # Verify standard parameters are added
        self.assertEqual(signed_params["apiKey"], self.id)
        self.assertEqual(signed_params["timestamp"], 1640995200)
        self.assertEqual(signed_params["hash"], "test_hash_value")
        self.assertIn("action", signed_params)
        self.assertIn("domain", signed_params)

    def test_signature_filters_none_params(self):
        """Test _signature method filters out None parameters"""
        provider = DnscomProvider(self.id, self.token)

        with patch("ddns.provider.dnscom.time") as mock_time, patch("ddns.provider.dnscom.md5") as mock_md5:
            # Mock time to return a fixed timestamp
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
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_signature") as mock_signature, patch.object(provider, "_http") as mock_http:
            mock_signature.return_value = {"apiKey": self.id, "hash": "test_hash"}
            mock_http.return_value = {"code": 0, "data": {"result": "success"}}

            result = provider._request("test", domain="example.com")

            mock_signature.assert_called_once_with({"domain": "example.com"})
            mock_http.assert_called_once_with("POST", "/api/test/", body={"apiKey": self.id, "hash": "test_hash"})
            self.assertEqual(result, {"result": "success"})

    def test_request_failure_none_response(self):
        """Test _request method with None response"""
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_signature") as mock_signature, patch.object(provider, "_http") as mock_http:
            mock_signature.return_value = {"apiKey": self.id}
            mock_http.return_value = None

            with self.assertRaises(Exception) as cm:
                provider._request("test", domain="example.com")

            self.assertIn("response data is none", str(cm.exception))

    def test_request_failure_api_error(self):
        """Test _request method with API error response"""
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_signature") as mock_signature, patch.object(provider, "_http") as mock_http:
            mock_signature.return_value = {"apiKey": self.id}
            mock_http.return_value = {"code": 1, "message": "Invalid API key"}

            with self.assertRaises(Exception) as cm:
                provider._request("test", domain="example.com")

            self.assertIn("api error: Invalid API key", str(cm.exception))

    def test_query_zone_id_success(self):
        """Test _query_zone_id method with successful response"""
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"domainID": "example.com"}

            result = provider._query_zone_id("example.com")

            mock_request.assert_called_once_with("domain/getsingle", domainID="example.com")
            self.assertEqual(result, "example.com")

    def test_query_zone_id_not_found(self):
        """Test _query_zone_id method when domain is not found"""
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = None

            result = provider._query_zone_id("notfound.com")

            mock_request.assert_called_once_with("domain/getsingle", domainID="notfound.com")
            self.assertIsNone(result)

    def test_query_record_success(self):
        """Test _query_record method with successful response"""
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "data": [
                    {"record": "www", "type": "A", "recordID": "123", "value": "1.2.3.4"},
                    {"record": "mail", "type": "A", "recordID": "456", "value": "5.6.7.8"},
                ]
            }

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            mock_request.assert_called_once_with("record/list", domainID="example.com", host="www", pageSize=500)
            self.assertIsNotNone(result)
            if result:  # Type narrowing
                self.assertEqual(result["recordID"], "123")
                self.assertEqual(result["record"], "www")

    def test_query_record_with_line(self):
        """Test _query_record method with line parameter"""
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "data": [
                    {"record": "www", "type": "A", "recordID": "123", "viewID": "1"},
                    {"record": "www", "type": "A", "recordID": "456", "viewID": "2"},
                ]
            }

            result = provider._query_record("example.com", "www", "example.com", "A", "2", {})

            self.assertIsNotNone(result)
            if result:  # Type narrowing
                self.assertEqual(result["recordID"], "456")
                self.assertEqual(result["viewID"], "2")

    def test_query_record_not_found(self):
        """Test _query_record method when no matching record is found"""
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "data": [{"record": "mail", "type": "A", "recordID": "456", "value": "5.6.7.8"}]
            }

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_query_record_empty_response(self):
        """Test _query_record method with empty response"""
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = None

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_create_record_success(self):
        """Test _create_record method with successful creation"""
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"recordID": "123456"}

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", 300, "1", {})

            mock_request.assert_called_once_with(
                "record/create",
                domainID="example.com",
                value="1.2.3.4",
                host="www",
                type="A",
                TTL=300,
                viewID="1",
                remark=provider.remark,
            )
            self.assertTrue(result)

    def test_create_record_with_extra_params(self):
        """Test _create_record method with extra parameters"""
        provider = DnscomProvider(self.id, self.token)

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
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"error": "Domain not found"}

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", None, None, {})

            self.assertFalse(result)

    def test_update_record_success(self):
        """Test _update_record method with successful update"""
        provider = DnscomProvider(self.id, self.token)

        old_record = {"recordID": "123456", "remark": "Old remark"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"success": True}

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, None, {})

            mock_request.assert_called_once_with(
                "record/modify", domainID="example.com", recordID="123456", newvalue="5.6.7.8", newTTL=600
            )
            self.assertTrue(result)

    def test_update_record_with_extra_params(self):
        """Test _update_record method with extra parameters"""
        provider = DnscomProvider(self.id, self.token)

        old_record = {"recordID": "123456", "remark": "Old remark"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"success": True}

            extra = {"remark": "New remark"}
            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, "1", extra)

            mock_request.assert_called_once_with(
                "record/modify", domainID="example.com", recordID="123456", newvalue="5.6.7.8", newTTL=600
            )
            self.assertTrue(result)

    def test_update_record_extra_priority_over_old_record(self):
        """Test that extra parameters take priority over old_record values"""
        provider = DnscomProvider(self.id, self.token)

        old_record = {"recordID": "123456", "remark": "Old remark"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"success": True}

            # extra should override old_record's remark
            extra = {"remark": "New remark from extra"}
            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, "1", extra)

            # Verify that extra["remark"] was set correctly with priority
            self.assertEqual(extra["remark"], "New remark from extra")
            self.assertTrue(result)

    def test_update_record_failure(self):
        """Test _update_record method with failed update"""
        provider = DnscomProvider(self.id, self.token)

        old_record = {"recordID": "123456"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = None

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})

            self.assertFalse(result)


class TestDnscomProviderIntegration(BaseProviderTestCase):
    """Integration test cases for DnscomProvider - testing with minimal mocking"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestDnscomProviderIntegration, self).setUp()
        self.id = "test_api_key"
        self.token = "test_api_secret"

    def test_full_workflow_create_new_record(self):
        """Test complete workflow for creating a new record"""
        provider = DnscomProvider(self.id, self.token)

        # Mock only the HTTP layer to simulate API responses
        with patch.object(provider, "_request") as mock_request:
            # Simulate API responses in order: zone query, record query, record creation
            mock_request.side_effect = [
                {"domainID": "example.com"},  # _query_zone_id response
                {"data": []},  # _query_record response (no existing record)
                {"recordID": "123456"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "1")

            self.assertTrue(result)
            # Verify the actual API calls made
            self.assertEqual(mock_request.call_count, 3)
            mock_request.assert_any_call("domain/getsingle", domainID="example.com")
            mock_request.assert_any_call("record/list", domainID="example.com", host="www", pageSize=500)
            mock_request.assert_any_call(
                "record/create",
                domainID="example.com",
                value="1.2.3.4",
                host="www",
                type="A",
                TTL=300,
                viewID="1",
                remark="Managed by [DDNS](https://ddns.newfuture.cc)",
            )

    def test_full_workflow_update_existing_record(self):
        """Test complete workflow for updating an existing record"""
        provider = DnscomProvider(self.id, self.token)

        # Mock only the HTTP layer to simulate raw API responses
        with patch.object(provider, "_http") as mock_http:
            # Simulate raw HTTP API responses as they would come from the server
            mock_http.side_effect = [
                {"code": 0, "data": {"domainID": "example.com"}},  # domain/getsingle response
                {
                    "code": 0,
                    "data": {  # record/list response
                        "data": [{"record": "www", "type": "A", "recordID": "123456", "value": "5.6.7.8"}]
                    },
                },
                {"code": 0, "data": {"recordID": "123456", "success": True}},  # record/modify response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "1")

            self.assertTrue(result)
            # Verify the actual HTTP calls were made (3 calls total)
            self.assertEqual(mock_http.call_count, 3)

    def test_full_workflow_zone_not_found(self):
        """Test complete workflow when zone is not found"""
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API returning None for zone query
            mock_request.return_value = None

            result = provider.set_record("www.nonexistent.com", "1.2.3.4", "A")
            self.assertFalse(result)

    def test_full_workflow_create_failure(self):
        """Test complete workflow when record creation fails"""
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate responses: zone found, no existing record, creation fails
            mock_request.side_effect = [
                {"domainID": "example.com"},  # _query_zone_id response
                {"data": []},  # _query_record response (no existing record)
                {"error": "Domain not found"},  # _create_record fails
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_update_failure(self):
        """Test complete workflow when record update fails"""
        provider = DnscomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate responses: zone found, existing record found, update fails
            mock_request.side_effect = [
                {"domainID": "example.com"},  # _query_zone_id response
                {  # _query_record response (existing record found)
                    "data": [{"record": "www", "type": "A", "recordID": "123456", "value": "5.6.7.8"}]
                },
                None,  # _update_record fails
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
