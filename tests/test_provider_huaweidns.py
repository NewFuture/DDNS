# coding=utf-8
"""
Unit tests for HuaweiDNSProvider

@author: Github Copilot
"""

from test_base import BaseProviderTestCase, unittest, patch
from ddns.provider.huaweidns import HuaweiDNSProvider
from datetime import datetime


class TestHuaweiDNSProvider(BaseProviderTestCase):
    """Test cases for HuaweiDNSProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestHuaweiDNSProvider, self).setUp()
        self.auth_id = "test_access_key"
        self.auth_token = "test_secret_key"

    def test_class_constants(self):
        """Test HuaweiDNSProvider class constants"""
        self.assertEqual(HuaweiDNSProvider.API, "https://dns.myhuaweicloud.com")
        self.assertEqual(HuaweiDNSProvider.ContentType, "application/json")
        self.assertTrue(HuaweiDNSProvider.DecodeResponse)
        self.assertEqual(HuaweiDNSProvider.Algorithm, "SDK-HMAC-SHA256")

    def test_init_with_basic_config(self):
        """Test HuaweiDNSProvider initialization with basic configuration"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)
        self.assertEqual(provider.auth_id, self.auth_id)
        self.assertEqual(provider.auth_token, self.auth_token)
        self.assertEqual(provider.API, "https://dns.myhuaweicloud.com")

    def test_hex_encode_sha256(self):
        """Test _hex_encode_sha256 method"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        test_data = b"test data"
        result = provider._hex_encode_sha256(test_data)

        # Should return a 64-character hex string (SHA256)
        self.assertEqual(len(result), 64)
        self.assertIsInstance(result, str)
        # SHA256 of "test data"
        expected_hash = "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
        self.assertEqual(result, expected_hash)

    def test_sign_headers(self):
        """Test _sign_headers method"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        headers = {
            "Content-Type": "application/json",
            "Host": "dns.myhuaweicloud.com",
            "X-Sdk-Date": "20230101T000000Z",
        }
        signed_headers = ["content-type", "host", "x-sdk-date"]

        result = provider._sign_headers(headers, signed_headers)

        expected = "content-type:application/json\nhost:dns.myhuaweicloud.com\nx-sdk-date:20230101T000000Z\n"
        self.assertEqual(result, expected)

    @patch("ddns.provider.huaweidns.datetime")
    def test_request_get_method(self, mock_datetime):
        """Test _request method with GET method"""
        # Mock datetime to get consistent results
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"zones": []}

            result = provider._request("GET", "/v2/zones", name="example.com", limit=500)

            mock_http.assert_called_once()
            self.assertEqual(result, {"zones": []})

    @patch("ddns.provider.huaweidns.datetime")
    def test_request_post_method(self, mock_datetime):
        """Test _request method with POST method"""
        # Mock datetime to get consistent results
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"id": "record123"}

            result = provider._request(
                "POST", "/v2.1/zones/zone123/recordsets", name="www.example.com", type="A", records=["1.2.3.4"]
            )

            mock_http.assert_called_once()
            self.assertEqual(result, {"id": "record123"})

    def test_request_filters_none_params(self):
        """Test _request method filters out None parameters"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"zones": []}

            provider._request("GET", "/v2/zones", name="example.com", limit=None, type=None)

            # Verify that _http was called (None params should be filtered)
            mock_http.assert_called_once()

    def test_query_zone_id_success(self):
        """Test _query_zone_id method with successful response"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "zones": [{"id": "zone123", "name": "example.com."}, {"id": "zone456", "name": "another.com."}]
            }

            result = provider._query_zone_id("example.com")

            mock_request.assert_called_once_with(
                "GET", "/v2/zones", search_mode="equal", limit=500, name="example.com."
            )
            self.assertEqual(result, "zone123")

    def test_query_zone_id_with_trailing_dot(self):
        """Test _query_zone_id method with domain already having trailing dot"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"zones": [{"id": "zone123", "name": "example.com."}]}

            result = provider._query_zone_id("example.com.")

            mock_request.assert_called_once_with(
                "GET", "/v2/zones", search_mode="equal", limit=500, name="example.com."
            )
            self.assertEqual(result, "zone123")

    def test_query_zone_id_not_found(self):
        """Test _query_zone_id method when domain is not found"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"zones": []}

            result = provider._query_zone_id("notfound.com")

            self.assertIsNone(result)

    def test_query_record_success(self):
        """Test _query_record method with successful response"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "recordsets": [
                    {"id": "rec123", "name": "www.example.com.", "type": "A", "records": ["1.2.3.4"]},
                    {"id": "rec456", "name": "mail.example.com.", "type": "A", "records": ["5.6.7.8"]},
                ]
            }

            result = provider._query_record("zone123", "www", "example.com", "A")  # type: dict # type: ignore

            mock_request.assert_called_once_with(
                "GET",
                "/v2.1/zones/zone123/recordsets",
                limit=500,
                name="www.example.com.",
                type="A",
                line_id=None,
                search_mode="equal",
            )
            self.assertEqual(result["id"], "rec123")
            self.assertEqual(result["name"], "www.example.com.")

    def test_query_record_with_line(self):
        """Test _query_record method with line parameter"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"recordsets": []}

            provider._query_record("zone123", "www", "example.com", "A", "line1")

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
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "recordsets": [{"id": "rec456", "name": "mail.example.com.", "type": "A", "records": ["5.6.7.8"]}]
            }

            result = provider._query_record("zone123", "www", "example.com", "A")

            self.assertIsNone(result)

    def test_create_record_success(self):
        """Test _create_record method with successful creation"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123456"}

            result = provider._create_record("zone123", "www", "example.com", "1.2.3.4", "A", 300, "line1")

            mock_request.assert_called_once_with(
                "POST",
                "/v2.1/zones/zone123/recordsets",
                name="www.example.com.",
                type="A",
                records=["1.2.3.4"],
                ttl=300,
                line="line1",
                description=provider.Remark,
            )
            self.assertTrue(result)

    def test_create_record_with_extra_params(self):
        """Test _create_record method with extra parameters"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123456"}

            extra = {"description": "Custom description", "tags": ["tag1", "tag2"]}
            result = provider._create_record("zone123", "www", "example.com", "1.2.3.4", "A", 300, None, extra)

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
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"error": "Zone not found"}

            result = provider._create_record("zone123", "www", "example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_update_record_success(self):
        """Test _update_record method with successful update"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        old_record = {"id": "rec123", "name": "www.example.com.", "ttl": 300}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123"}

            result = provider._update_record("zone123", old_record, "5.6.7.8", "A", 600)

            mock_request.assert_called_once_with(
                "PUT",
                "/v2.1/zones/zone123/recordsets/rec123",
                name="www.example.com.",
                type="A",
                records=["5.6.7.8"],
                ttl=600,
                description=provider.Remark,
            )
            self.assertTrue(result)

    def test_update_record_with_fallback_ttl(self):
        """Test _update_record method uses old record's TTL when ttl is None"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        old_record = {"id": "rec123", "name": "www.example.com.", "ttl": 300}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123"}

            result = provider._update_record("zone123", old_record, "5.6.7.8", "A", None)

            mock_request.assert_called_once_with(
                "PUT",
                "/v2.1/zones/zone123/recordsets/rec123",
                name="www.example.com.",
                type="A",
                records=["5.6.7.8"],
                ttl=300,
                description=provider.Remark,
            )
            self.assertTrue(result)

    def test_update_record_with_extra_params(self):
        """Test _update_record method with extra parameters"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

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

    def test_update_record_failure(self):
        """Test _update_record method with failed update"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        old_record = {"id": "rec123", "name": "www.example.com."}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"error": "Record not found"}

            result = provider._update_record("zone123", old_record, "5.6.7.8", "A")

            self.assertFalse(result)


class TestHuaweiDNSProviderIntegration(BaseProviderTestCase):
    """Integration test cases for HuaweiDNSProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestHuaweiDNSProviderIntegration, self).setUp()
        self.auth_id = "test_access_key"
        self.auth_token = "test_secret_key"

    def test_full_workflow_create_new_record(self):
        """Test complete workflow for creating a new record"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_create_record") as mock_create:

            # Setup mocks
            mock_zone.return_value = "zone123"
            mock_query.return_value = None  # No existing record
            mock_create.return_value = True

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "line1")

            self.assertTrue(result)
            mock_zone.assert_called_once_with("example.com")
            mock_query.assert_called_once_with(
                "zone123", sub_domain="www", main_domain="example.com", record_type="A", line="line1", extra={}
            )
            mock_create.assert_called_once_with(
                "zone123",
                sub_domain="www",
                main_domain="example.com",
                value="1.2.3.4",
                record_type="A",
                ttl=300,
                line="line1",
                extra={},
            )

    def test_full_workflow_update_existing_record(self):
        """Test complete workflow for updating an existing record"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        existing_record = {"id": "rec123", "name": "www.example.com.", "records": ["5.6.7.8"]}

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_update_record") as mock_update:

            # Setup mocks
            mock_zone.return_value = "zone123"
            mock_query.return_value = existing_record
            mock_update.return_value = True

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "line1")

            self.assertTrue(result)
            mock_zone.assert_called_once_with("example.com")
            mock_query.assert_called_once_with(
                "zone123", sub_domain="www", main_domain="example.com", record_type="A", line="line1", extra={}
            )
            mock_update.assert_called_once_with(
                "zone123",
                old_record=existing_record,
                value="1.2.3.4",
                record_type="A",
                ttl=300,
                line="line1",
                extra={},
            )

    def test_full_workflow_zone_not_found(self):
        """Test complete workflow when zone is not found"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_query_zone_id") as mock_zone:
            mock_zone.return_value = None

            with self.assertRaises(ValueError) as cm:
                provider.set_record("www.nonexistent.com", "1.2.3.4", "A")

            self.assertIn("Cannot resolve zone_id", str(cm.exception))

    def test_full_workflow_create_failure(self):
        """Test complete workflow when record creation fails"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_create_record") as mock_create:

            # Setup mocks
            mock_zone.return_value = "zone123"
            mock_query.return_value = None  # No existing record
            mock_create.return_value = False  # Creation fails

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_update_failure(self):
        """Test complete workflow when record update fails"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        existing_record = {"id": "rec123", "name": "www.example.com.", "records": ["5.6.7.8"]}

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_update_record") as mock_update:

            # Setup mocks
            mock_zone.return_value = "zone123"
            mock_query.return_value = existing_record
            mock_update.return_value = False  # Update fails

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_with_extra_options(self):
        """Test complete workflow with additional options"""
        provider = HuaweiDNSProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_create_record") as mock_create:

            # Setup mocks
            mock_zone.return_value = "zone123"
            mock_query.return_value = None  # No existing record
            mock_create.return_value = True

            result = provider.set_record(
                "www.example.com", "1.2.3.4", "A", 600, "line2", description="Custom record", tags=["production"]
            )

            self.assertTrue(result)
            # Verify that extra parameters are passed through correctly
            mock_create.assert_called_once_with(
                "zone123",
                sub_domain="www",
                main_domain="example.com",
                value="1.2.3.4",
                record_type="A",
                ttl=600,
                line="line2",
                extra={"description": "Custom record", "tags": ["production"]},
            )


if __name__ == "__main__":
    unittest.main()
