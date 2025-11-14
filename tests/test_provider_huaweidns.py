# coding=utf-8
"""
Unit tests for HuaweiDNSProvider

@author: GitHub Copilot
"""

from base_test import BaseProviderTestCase, unittest, patch
from ddns.provider.huaweidns import HuaweiDNSProvider


class TestHuaweiDNSProvider(BaseProviderTestCase):
    """Test cases for HuaweiDNSProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestHuaweiDNSProvider, self).setUp()
        self.id = "test_access_key"
        self.token = "test_secret_key"
        self.provider = HuaweiDNSProvider(self.id, self.token)

        # Mock strftime for all tests
        self.strftime_patcher = patch("ddns.provider.huaweidns.strftime")
        self.mock_strftime = self.strftime_patcher.start()
        self.mock_strftime.return_value = "20230101T120000Z"

    def tearDown(self):
        """Clean up test fixtures"""
        self.strftime_patcher.stop()
        super(TestHuaweiDNSProvider, self).tearDown()

    def test_class_constants(self):
        """Test HuaweiDNSProvider class constants"""
        self.assertEqual(HuaweiDNSProvider.endpoint, "https://dns.myhuaweicloud.com")
        self.assertEqual(HuaweiDNSProvider.content_type, "application/json")
        self.assertTrue(HuaweiDNSProvider.decode_response)
        self.assertEqual(HuaweiDNSProvider.algorithm, "SDK-HMAC-SHA256")

    def test_init_with_basic_config(self):
        """Test HuaweiDNSProvider initialization with basic configuration"""
        self.assertEqual(self.provider.id, self.id)
        self.assertEqual(self.provider.token, self.token)
        self.assertEqual(self.provider.endpoint, "https://dns.myhuaweicloud.com")

    def test_request_get_method(self):
        """Test _request method with GET method"""
        with patch.object(self.provider, "_http") as mock_http:
            mock_http.return_value = {"zones": []}

            result = self.provider._request("GET", "/v2/zones", name="example.com", limit=500)

            mock_http.assert_called_once()
            self.assertEqual(result, {"zones": []})

    def test_request_post_method(self):
        """Test _request method with POST method"""
        with patch.object(self.provider, "_http") as mock_http:
            mock_http.return_value = {"id": "record123"}

            result = self.provider._request(
                "POST", "/v2.1/zones/zone123/recordsets", name="www.example.com", type="A", records=["1.2.3.4"]
            )

            mock_http.assert_called_once()
            self.assertEqual(result, {"id": "record123"})

    def test_request_filters_none_params(self):
        """Test _request method filters out None parameters"""
        with patch.object(self.provider, "_http") as mock_http:
            mock_http.return_value = {"zones": []}

            self.provider._request("GET", "/v2/zones", name="example.com", limit=None, type=None)

            # Verify that _http was called (None params should be filtered)
            mock_http.assert_called_once()

    def test_query_zone_id_success(self):
        """Test _query_zone_id method with successful response"""
        with patch.object(self.provider, "_request") as mock_request:
            mock_request.return_value = {
                "zones": [{"id": "zone123", "name": "example.com."}, {"id": "zone456", "name": "another.com."}]
            }

            result = self.provider._query_zone_id("example.com")

            mock_request.assert_called_once_with(
                "GET", "/v2/zones", search_mode="equal", limit=500, name="example.com."
            )
            self.assertEqual(result, "zone123")

    def test_query_zone_id_with_trailing_dot(self):
        """Test _query_zone_id method with domain already having trailing dot"""
        with patch.object(self.provider, "_request") as mock_request:
            mock_request.return_value = {"zones": [{"id": "zone123", "name": "example.com."}]}

            result = self.provider._query_zone_id("example.com.")

            mock_request.assert_called_once_with(
                "GET", "/v2/zones", search_mode="equal", limit=500, name="example.com."
            )
            self.assertEqual(result, "zone123")

    def test_query_zone_id_not_found(self):
        """Test _query_zone_id method when domain is not found"""
        with patch.object(self.provider, "_request") as mock_request:
            mock_request.return_value = {"zones": []}

            result = self.provider._query_zone_id("notfound.com")

            self.assertIsNone(result)

    def test_query_record_success(self):
        """Test _query_record method with successful response"""
        with patch.object(self.provider, "_request") as mock_request:
            mock_request.return_value = {
                "recordsets": [
                    {"id": "rec123", "name": "www.example.com.", "type": "A", "records": ["1.2.3.4"]},
                    {"id": "rec456", "name": "mail.example.com.", "type": "A", "records": ["5.6.7.8"]},
                ]
            }

            result = self.provider._query_record("zone123", "www", "example.com", "A", None, {})

            mock_request.assert_called_once_with(
                "GET",
                "/v2.1/zones/zone123/recordsets",
                limit=500,
                name="www.example.com.",
                type="A",
                line_id=None,
                search_mode="equal",
            )
            self.assertIsNotNone(result)
            if result:  # Type narrowing
                self.assertEqual(result["id"], "rec123")
                self.assertEqual(result["name"], "www.example.com.")

    def test_query_record_with_line(self):
        """Test _query_record method with line parameter"""
        with patch.object(self.provider, "_request") as mock_request:
            mock_request.return_value = {"recordsets": []}

            self.provider._query_record("zone123", "www", "example.com", "A", "line1", {})

            mock_request.assert_called_once_with(
                "GET",
                "/v2.1/zones/zone123/recordsets",
                limit=500,
                name="www.example.com.",
                type="A",
                line_id="line1",
                search_mode="equal",
            )

    def test_query_record_not_found(self):
        """Test _query_record method when no matching record is found"""
        with patch.object(self.provider, "_request") as mock_request:
            mock_request.return_value = {
                "recordsets": [{"id": "rec456", "name": "mail.example.com.", "type": "A", "records": ["5.6.7.8"]}]
            }

            result = self.provider._query_record("zone123", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_create_record_success(self):
        """Test _create_record method with successful creation"""
        with patch.object(self.provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123456"}

            result = self.provider._create_record("zone123", "www", "example.com", "1.2.3.4", "A", 300, "line1", {})

            mock_request.assert_called_once_with(
                "POST",
                "/v2.1/zones/zone123/recordsets",
                name="www.example.com.",
                type="A",
                records=["1.2.3.4"],
                ttl=300,
                line="line1",
                description=self.provider.remark,
            )
            self.assertTrue(result)

    def test_create_record_with_extra_params(self):
        """Test _create_record method with extra parameters"""
        with patch.object(self.provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123456"}

            extra = {"description": "Custom description", "tags": ["tag1", "tag2"]}
            result = self.provider._create_record("zone123", "www", "example.com", "1.2.3.4", "A", 300, None, extra)

            mock_request.assert_called_once_with(
                "POST",
                "/v2.1/zones/zone123/recordsets",
                name="www.example.com.",
                type="A",
                records=["1.2.3.4"],
                ttl=300,
                line=None,
                description="Custom description",
                tags=["tag1", "tag2"],
            )
            self.assertTrue(result)

    def test_create_record_failure(self):
        """Test _create_record method with failed creation"""
        provider = HuaweiDNSProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"error": "Zone not found"}

            result = provider._create_record("zone123", "www", "example.com", "1.2.3.4", "A", None, None, {})

            self.assertFalse(result)

    def test_update_record_success(self):
        """Test _update_record method with successful update"""
        provider = HuaweiDNSProvider(self.id, self.token)

        old_record = {"id": "rec123", "name": "www.example.com.", "ttl": 300}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123"}

            result = provider._update_record("zone123", old_record, "5.6.7.8", "A", 600, None, {})

            mock_request.assert_called_once_with(
                "PUT",
                "/v2.1/zones/zone123/recordsets/rec123",
                name="www.example.com.",
                type="A",
                records=["5.6.7.8"],
                ttl=600,
                description=provider.remark,
            )
            self.assertTrue(result)

    def test_update_record_with_fallback_ttl(self):
        """Test _update_record method uses old record's TTL when ttl is None"""
        provider = HuaweiDNSProvider(self.id, self.token)

        old_record = {"id": "rec123", "name": "www.example.com.", "ttl": 300}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123"}

            result = provider._update_record("zone123", old_record, "5.6.7.8", "A", None, None, {})

            mock_request.assert_called_once_with(
                "PUT",
                "/v2.1/zones/zone123/recordsets/rec123",
                name="www.example.com.",
                type="A",
                records=["5.6.7.8"],
                ttl=300,
                description=provider.remark,
            )
            self.assertTrue(result)

    def test_update_record_with_extra_params(self):
        """Test _update_record method with extra parameters"""
        provider = HuaweiDNSProvider(self.id, self.token)

        old_record = {"id": "rec123", "name": "www.example.com.", "ttl": 300}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123"}

            extra = {"description": "Updated description", "tags": ["newtag"]}
            result = provider._update_record("zone123", old_record, "5.6.7.8", "A", 600, "line2", extra)

            mock_request.assert_called_once_with(
                "PUT",
                "/v2.1/zones/zone123/recordsets/rec123",
                name="www.example.com.",
                type="A",
                records=["5.6.7.8"],
                ttl=600,
                description="Updated description",
                tags=["newtag"],
            )
            self.assertTrue(result)

    def test_update_record_extra_priority_over_old_record(self):
        """Test that extra parameters take priority over old_record values"""
        provider = HuaweiDNSProvider(self.id, self.token)

        old_record = {"id": "rec123", "name": "www.example.com.", "ttl": 300, "description": "Old description"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123"}

            # extra should override old_record's description
            extra = {"description": "New description from extra"}
            result = provider._update_record("zone123", old_record, "5.6.7.8", "A", 600, None, extra)

            mock_request.assert_called_once_with(
                "PUT",
                "/v2.1/zones/zone123/recordsets/rec123",
                name="www.example.com.",
                type="A",
                records=["5.6.7.8"],
                ttl=600,
                description="New description from extra",  # Should use extra, not old_record
            )
            self.assertTrue(result)

    def test_update_record_failure(self):
        """Test _update_record method with failed update"""
        provider = HuaweiDNSProvider(self.id, self.token)

        old_record = {"id": "rec123", "name": "www.example.com."}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"error": "Record not found"}

            result = provider._update_record("zone123", old_record, "5.6.7.8", "A", None, None, {})

            self.assertFalse(result)

    def test_line_configuration_support(self):
        """Test that HuaweiDNSProvider supports line configuration"""
        provider = HuaweiDNSProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123456"}

            # Test create record with line parameter (line is passed as extra parameter for Huawei)
            result = provider._create_record("zone123", "www", "example.com", "1.2.3.4", "A", 300, "telecom", {})

            # For Huawei DNS, line can be passed as extra parameter
            self.assertTrue(result)
            mock_request.assert_called_once()

    def test_update_record_with_line(self):
        """Test _update_record method with line parameter"""
        provider = HuaweiDNSProvider(self.id, self.token)

        old_record = {"id": "rec123", "name": "www.example.com."}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123"}

            # Test with line parameter (line is handled as needed for different DNS providers)
            result = provider._update_record("zone123", old_record, "5.6.7.8", "A", 600, "unicom", {})

            self.assertTrue(result)
            mock_request.assert_called_once()


class TestHuaweiDNSProviderIntegration(BaseProviderTestCase):
    """Integration test cases for HuaweiDNSProvider - testing with minimal mocking"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestHuaweiDNSProviderIntegration, self).setUp()
        self.id = "test_access_key"
        self.token = "test_secret_key"

    def test_full_workflow_create_new_record(self):
        """Test complete workflow for creating a new record"""
        provider = HuaweiDNSProvider(self.id, self.token)

        # Mock only the HTTP layer to simulate API responses
        with patch.object(provider, "_request") as mock_request:
            # Simulate API responses in order: zone query, record query, record creation
            mock_request.side_effect = [
                {"zones": [{"id": "zone123", "name": "example.com."}]},  # _query_zone_id response
                {"recordsets": []},  # _query_record response (no existing record)
                {"id": "rec123456"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "line1")

            self.assertTrue(result)
            # Verify the actual API calls made
            self.assertEqual(mock_request.call_count, 3)
            mock_request.assert_any_call("GET", "/v2/zones", search_mode="equal", limit=500, name="example.com.")
            mock_request.assert_any_call(
                "GET",
                "/v2.1/zones/zone123/recordsets",
                limit=500,
                name="www.example.com.",
                type="A",
                line_id="line1",
                search_mode="equal",
            )
            mock_request.assert_any_call(
                "POST",
                "/v2.1/zones/zone123/recordsets",
                name="www.example.com.",
                type="A",
                records=["1.2.3.4"],
                ttl=300,
                line="line1",
                description="Managed by [DDNS](https://ddns.newfuture.cc)",
            )

    def test_full_workflow_update_existing_record(self):
        """Test complete workflow for updating an existing record"""
        provider = HuaweiDNSProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API responses
            mock_request.side_effect = [
                {"zones": [{"id": "zone123", "name": "example.com."}]},  # _query_zone_id response
                {  # _query_record response (existing record found)
                    "recordsets": [
                        {"id": "rec123", "name": "www.example.com.", "type": "A", "records": ["5.6.7.8"], "ttl": 300}
                    ]
                },
                {"id": "rec123"},  # _update_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "line1")

            self.assertTrue(result)
            # Verify the update call was made
            mock_request.assert_any_call(
                "PUT",
                "/v2.1/zones/zone123/recordsets/rec123",
                name="www.example.com.",
                type="A",
                records=["1.2.3.4"],
                ttl=300,
                description="Managed by [DDNS](https://ddns.newfuture.cc)",
            )

    def test_full_workflow_zone_not_found(self):
        """Test complete workflow when zone is not found"""
        provider = HuaweiDNSProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API returning empty zones array
            mock_request.return_value = {"zones": []}

            result = provider.set_record("www.nonexistent.com", "1.2.3.4", "A")
            self.assertFalse(result)

    def test_full_workflow_create_failure(self):
        """Test complete workflow when record creation fails"""
        provider = HuaweiDNSProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate responses: zone found, no existing record, creation fails
            mock_request.side_effect = [
                {"zones": [{"id": "zone123", "name": "example.com."}]},  # _query_zone_id response
                {"recordsets": []},  # _query_record response (no existing record)
                {"error": "Zone not found"},  # _create_record fails
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_update_failure(self):
        """Test complete workflow when record update fails"""
        provider = HuaweiDNSProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate responses: zone found, existing record found, update fails
            mock_request.side_effect = [
                {"zones": [{"id": "zone123", "name": "example.com."}]},  # _query_zone_id response
                {  # _query_record response (existing record found)
                    "recordsets": [
                        {"id": "rec123", "name": "www.example.com.", "type": "A", "records": ["5.6.7.8"], "ttl": 300}
                    ]
                },
                {"error": "Update failed"},  # _update_record fails
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_with_extra_options(self):
        """Test complete workflow with additional options"""
        provider = HuaweiDNSProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate successful creation with custom options
            mock_request.side_effect = [
                {"zones": [{"id": "zone123", "name": "example.com."}]},  # _query_zone_id response
                {"recordsets": []},  # _query_record response (no existing record)
                {"id": "rec123456"},  # _create_record response
            ]

            result = provider.set_record(
                "www.example.com", "1.2.3.4", "A", 600, "line2", description="Custom record", tags=["production"]
            )

            self.assertTrue(result)
            # Verify that extra parameters are passed through correctly
            mock_request.assert_any_call(
                "POST",
                "/v2.1/zones/zone123/recordsets",
                name="www.example.com.",
                type="A",
                records=["1.2.3.4"],
                ttl=600,
                line="line2",
                description="Custom record",
                tags=["production"],
            )


if __name__ == "__main__":
    unittest.main()
