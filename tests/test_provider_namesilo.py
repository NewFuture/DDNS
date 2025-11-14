# coding=utf-8
# type: ignore[index]
"""
Unit tests for NameSilo DNS provider
@author: NewFuture & Copilot
"""

from base_test import BaseProviderTestCase, unittest, patch
from ddns.provider.namesilo import NamesiloProvider


class TestNamesiloProvider(BaseProviderTestCase):
    """Test cases for NameSilo DNS provider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestNamesiloProvider, self).setUp()
        self.provider = NamesiloProvider(self.id, self.token)

    def test_init_with_basic_config(self):
        """Test basic provider initialization"""
        self.assertProviderInitialized(self.provider)
        self.assertEqual(self.provider.endpoint, "https://www.namesilo.com")
        self.assertEqual(self.provider.content_type, "application/json")

    def test_init_with_custom_endpoint(self):
        """Test provider initialization with custom endpoint"""
        custom_endpoint = "https://api.custom.namesilo.com"
        provider = NamesiloProvider(self.id, self.token, endpoint=custom_endpoint)
        self.assertEqual(provider.endpoint, custom_endpoint)

    def test_validate_success(self):
        """Test successful credential validation"""
        # Should not raise exception
        try:
            self.provider._validate()
        except Exception as e:
            self.fail("_validate() raised unexpected exception: {}".format(e))

    def test_validate_missing_token(self):
        """Test validation with missing token"""
        with self.assertRaises(ValueError) as context:
            NamesiloProvider(self.id, "")
        self.assertIn("API key", str(context.exception))

    def test_validate_missing_id_allowed(self):
        """Test validation with missing ID (should be allowed)"""
        # Should not raise exception - ID is not strictly required for NameSilo
        try:
            provider = NamesiloProvider("", self.token)
            self.assertEqual(provider.token, self.token)
        except Exception as e:
            self.fail("_validate() raised unexpected exception with missing ID: {}".format(e))

    @patch.object(NamesiloProvider, "_http")
    def test_request_success(self, mock_http):
        """Test successful API request"""
        mock_response = {"reply": {"code": "300", "detail": "success", "data": {"test": "value"}}}
        mock_http.return_value = mock_response

        result = self.provider._request("testOperation", domain="example.com")

        # Verify request parameters
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], "/api/testOperation")

        expected_queries = {"domain": "example.com", "version": "1", "type": "json", "key": self.token}
        self.assertEqual(kwargs["queries"], expected_queries)

        # Verify response
        self.assertEqual(result["code"], "300")

    @patch.object(NamesiloProvider, "_http")
    def test_request_api_error(self, mock_http):
        """Test API request with error response"""
        mock_response = {"reply": {"code": "400", "detail": "Invalid domain"}}
        mock_http.return_value = mock_response

        # Mock logger to capture warning
        mock_logger = self.mock_logger(self.provider)

        result = self.provider._request("testOperation", domain="invalid.com")

        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0]
        self.assertIn("400", warning_call[1])
        self.assertIn("Invalid domain", warning_call[2])

        # Should return None on error
        self.assertIsNone(result)

    @patch.object(NamesiloProvider, "_request")
    def test_query_zone_id_success(self, mock_request):
        """Test successful zone ID query"""
        mock_request.return_value = {"code": "300", "domain": {"domain": "example.com"}}

        result = self.provider._query_zone_id("example.com")

        mock_request.assert_called_once_with("getDomainInfo", domain="example.com")
        self.assertEqual(result, "example.com")

    @patch.object(NamesiloProvider, "_request")
    def test_query_zone_id_not_found(self, mock_request):
        """Test zone ID query for non-existent domain"""
        mock_request.return_value = {"code": "400", "detail": "Domain not found"}

        result = self.provider._query_zone_id("nonexistent.com")

        self.assertIsNone(result)

    @patch.object(NamesiloProvider, "_request")
    def test_query_record_success_multiple_records(self, mock_request):
        """Test successful record query with multiple records"""
        mock_request.return_value = {
            "code": "300",
            "resource_record": [
                {"record_id": "12345", "host": "test", "type": "A", "value": "1.2.3.4", "ttl": "3600"},
                {"record_id": "67890", "host": "other", "type": "A", "value": "5.6.7.8", "ttl": "3600"},
            ],
        }

        result = self.provider._query_record("example.com", "test", "example.com", "A", None, {})

        self.assertIsNotNone(result)
        self.assertEqual(result["record_id"], "12345")
        self.assertEqual(result["host"], "test")

    @patch.object(NamesiloProvider, "_request")
    def test_query_record_not_found(self, mock_request):
        """Test record query when no matching record is found"""
        mock_request.return_value = {
            "code": "300",
            "resource_record": [
                {"record_id": "67890", "host": "other", "type": "A", "value": "5.6.7.8", "ttl": "3600"}
            ],
        }

        result = self.provider._query_record("example.com", "test", "example.com", "A", None, {})

        self.assertIsNone(result)

    @patch.object(NamesiloProvider, "_request")
    def test_create_record_success(self, mock_request):
        """Test successful record creation"""
        mock_request.return_value = {"code": "300", "record_id": "12345"}

        result = self.provider._create_record("example.com", "test", "example.com", "1.2.3.4", "A", 3600, None, {})

        expected_params = {
            "domain": "example.com",
            "rrtype": "A",
            "rrhost": "test",
            "rrvalue": "1.2.3.4",
            "rrttl": 3600,
        }
        mock_request.assert_called_once_with("dnsAddRecord", **expected_params)
        self.assertTrue(result)

    @patch.object(NamesiloProvider, "_request")
    def test_create_record_without_ttl(self, mock_request):
        """Test record creation without TTL"""
        mock_request.return_value = {"code": "300", "record_id": "12345"}

        result = self.provider._create_record("example.com", "test", "example.com", "1.2.3.4", "A", None, None, {})

        expected_params = {
            "domain": "example.com",
            "rrtype": "A",
            "rrhost": "test",
            "rrvalue": "1.2.3.4",
            "rrttl": None,
        }
        mock_request.assert_called_once_with("dnsAddRecord", **expected_params)
        self.assertTrue(result)

    @patch.object(NamesiloProvider, "_request")
    def test_create_record_failure(self, mock_request):
        """Test failed record creation"""
        mock_request.return_value = None

        result = self.provider._create_record("example.com", "test", "example.com", "invalid", "A", 3600, None, {})

        self.assertFalse(result)

    @patch.object(NamesiloProvider, "_request")
    def test_update_record_success(self, mock_request):
        """Test successful record update"""
        mock_request.return_value = {"code": "300"}

        old_record = {"record_id": "12345", "host": "test", "type": "A", "value": "1.2.3.4", "ttl": "3600"}

        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A", 7200, None, {})

        expected_params = {
            "domain": "example.com",
            "rrid": "12345",
            "rrhost": "test",
            "rrvalue": "5.6.7.8",
            "rrtype": "A",
            "rrttl": 7200,
        }
        mock_request.assert_called_once_with("dnsUpdateRecord", **expected_params)
        self.assertTrue(result)

    @patch.object(NamesiloProvider, "_request")
    def test_update_record_keep_existing_ttl(self, mock_request):
        """Test record update keeping existing TTL"""
        mock_request.return_value = {"code": "300"}

        old_record = {"record_id": "12345", "host": "test", "type": "A", "value": "1.2.3.4", "ttl": "3600"}

        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})

        expected_params = {
            "domain": "example.com",
            "rrid": "12345",
            "rrhost": "test",
            "rrvalue": "5.6.7.8",
            "rrtype": "A",
            "rrttl": "3600",  # Should keep existing TTL
        }
        mock_request.assert_called_once_with("dnsUpdateRecord", **expected_params)
        self.assertTrue(result)

    @patch.object(NamesiloProvider, "_request")
    def test_update_record_missing_record_id(self, mock_request):
        """Test record update with missing record_id"""
        old_record = {"host": "test", "type": "A", "value": "1.2.3.4"}

        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A", 7200, None, {})

        # Should not make API call and return False
        mock_request.assert_not_called()
        self.assertFalse(result)

    @patch.object(NamesiloProvider, "_request")
    def test_update_record_failure(self, mock_request):
        """Test failed record update"""
        mock_request.return_value = None

        old_record = {"record_id": "12345", "host": "test", "type": "A", "value": "1.2.3.4", "ttl": "3600"}

        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A", 7200, None, {})

        self.assertFalse(result)

    @patch.object(NamesiloProvider, "_request")
    def test_update_record_extra_priority_over_old_record(self, mock_request):
        """Test that extra parameters take priority over old_record values"""
        mock_request.return_value = {"reply": {"code": "300"}}

        old_record = {"record_id": "12345", "host": "test", "type": "A", "value": "1.2.3.4", "ttl": "3600"}

        # NameSilo doesn't use many extra params in update, but we verify it doesn't break
        extra = {"custom_field": "custom_value"}
        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A", 7200, None, extra)

        # Verify the basic call was made (NameSilo doesn't support extra params in update)
        mock_request.assert_called_once_with(
            "dnsUpdateRecord",
            rrid="12345",
            domain="example.com",
            rrhost="test",
            rrvalue="5.6.7.8",
            rrtype="A",
            rrttl=7200,
        )
        self.assertTrue(result)

    @patch.object(NamesiloProvider, "_http")
    def test_integration_set_record_update_flow(self, mock_http):
        """Integration test for complete set_record flow with update"""
        # Mock the sequence of API calls for an update scenario

        # 1. Domain info check (zone_id query)
        # 2. Record listing
        # 3. Record update
        mock_responses = [
            # getDomainInfo response
            {"reply": {"code": "300", "domain": {"domain": "example.com"}}},
            # dnsListRecords response
            {
                "reply": {
                    "code": "300",
                    "resource_record": [
                        {"record_id": "12345", "host": "test", "type": "A", "value": "1.2.3.4", "ttl": "3600"}
                    ],
                }
            },
            # dnsUpdateRecord response
            {"reply": {"code": "300"}},
        ]

        mock_http.side_effect = mock_responses

        # Execute set_record
        result = self.provider.set_record("test.example.com", "5.6.7.8", "A", 7200)

        # Verify result
        self.assertTrue(result)

        # Verify all expected API calls were made
        self.assertEqual(mock_http.call_count, 3)

    @patch.object(NamesiloProvider, "_http")
    def test_integration_set_record_create_flow(self, mock_http):
        """Integration test for complete set_record flow with create"""
        # Mock the sequence of API calls for a create scenario

        mock_responses = [
            # getDomainInfo response
            {"reply": {"code": "300", "domain": {"domain": "example.com"}}},
            # dnsListRecords response (no matching record)
            {"reply": {"code": "300", "resource_record": []}},
            # dnsAddRecord response
            {"reply": {"code": "300", "record_id": "67890"}},
        ]

        mock_http.side_effect = mock_responses

        # Execute set_record
        result = self.provider.set_record("newtest.example.com", "9.8.7.6", "A", 3600)

        # Verify result
        self.assertTrue(result)

        # Verify all expected API calls were made
        self.assertEqual(mock_http.call_count, 3)


if __name__ == "__main__":
    unittest.main()
