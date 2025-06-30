# coding=utf-8
"""
Unit tests for AliESAProvider

@author: Github Copilot
"""

from base_test import BaseProviderTestCase, unittest, patch
from ddns.provider.aliesa import AliESAProvider


class TestAliESAProvider(BaseProviderTestCase):
    """Test cases for AliESAProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestAliESAProvider, self).setUp()
        self.auth_id = "test_access_key_id"
        self.auth_token = "test_access_key_secret"

    def test_class_constants(self):
        """Test AliESAProvider class constants"""
        self.assertEqual(AliESAProvider.API, "https://esa.aliyuncs.com")
        self.assertEqual(AliESAProvider.content_type, "application/x-www-form-urlencoded")
        self.assertTrue(AliESAProvider.decode_response)

    def test_init_with_basic_config(self):
        """Test AliESAProvider initialization with basic configuration"""
        provider = AliESAProvider(self.auth_id, self.auth_token)
        self.assertEqual(provider.auth_id, self.auth_id)
        self.assertEqual(provider.auth_token, self.auth_token)
        self.assertEqual(provider.API, "https://esa.aliyuncs.com")

    @patch("ddns.provider.aliesa.strftime")
    @patch("ddns.provider.aliesa.time")
    def test_signature_generation(self, mock_time, mock_strftime):
        """Test _signature method generates correct signature"""
        # Mock time functions to get consistent results
        mock_time.return_value = 1672574400.0  # 2023-01-01 12:00:00 UTC
        mock_strftime.return_value = "2023-01-01T12:00:00Z"

        provider = AliESAProvider(self.auth_id, self.auth_token)

        params = {"Action": "TestAction", "SiteId": "12345"}
        signed_params = provider._signature(params)

        # Verify standard parameters are added
        self.assertEqual(signed_params["Format"], "json")
        self.assertEqual(signed_params["Version"], "2024-09-10")
        self.assertEqual(signed_params["AccessKeyId"], self.auth_id)
        self.assertEqual(signed_params["Timestamp"], "2023-01-01T12:00:00Z")
        self.assertEqual(signed_params["SignatureMethod"], "ACS3-HMAC-SHA256")
        self.assertEqual(signed_params["SignatureVersion"], "1.0")
        self.assertIn("Signature", signed_params)
        self.assertIn("SignatureNonce", signed_params)

    def test_request_basic(self):
        """Test _request method with basic parameters"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_signature") as mock_signature, patch.object(provider, "_http") as mock_http:

            mock_signature.return_value = {"Action": "TestAction", "Signature": "test_sig"}
            mock_http.return_value = {"Success": True}

            result = provider._request("TestAction", SiteId="12345")

            mock_signature.assert_called_once()
            mock_http.assert_called_once_with("POST", "/", body={"Action": "TestAction", "Signature": "test_sig"})
            self.assertEqual(result, {"Success": True})

    def test_request_filters_none_params(self):
        """Test _request method filters out None parameters"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_signature") as mock_signature, patch.object(provider, "_http") as mock_http:

            mock_signature.return_value = {"Action": "TestAction"}
            mock_http.return_value = {}

            provider._request("TestAction", SiteId="12345", TTL=None, Comment=None)

            # Verify None parameters were filtered out before signing
            call_args = mock_signature.call_args[1] if mock_signature.call_args else {}
            self.assertNotIn("TTL", call_args)
            self.assertNotIn("Comment", call_args)

    def test_query_zone_id_success(self):
        """Test _query_zone_id method with successful response"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "Sites": [
                    {"SiteId": "123456", "SiteName": "example.com"},
                    {"SiteId": "789012", "SiteName": "other.com"}
                ]
            }

            result = provider._query_zone_id("example.com")

            mock_request.assert_called_once_with("ListSites", SiteName="example.com")
            self.assertEqual(result, "123456")

    def test_query_zone_id_not_found(self):
        """Test _query_zone_id method when domain is not found"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"Sites": []}

            result = provider._query_zone_id("notfound.com")

            mock_request.assert_called_once_with("ListSites", SiteName="notfound.com")
            self.assertIsNone(result)

    def test_query_zone_id_no_matching_site(self):
        """Test _query_zone_id method when no matching site is found"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "Sites": [
                    {"SiteId": "789012", "SiteName": "other.com"}
                ]
            }

            result = provider._query_zone_id("example.com")

            self.assertIsNone(result)

    def test_query_record_success(self):
        """Test _query_record method with successful response"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "Records": [
                    {"RecordId": "123", "RecordName": "www.example.com", "Value": "1.2.3.4", "Type": "A"},
                    {"RecordId": "456", "RecordName": "mail.example.com", "Value": "5.6.7.8", "Type": "A"},
                ]
            }

            result = provider._query_record("site123", "www", "example.com", "A", None, {})

            mock_request.assert_called_once_with(
                "ListRecords",
                SiteId="site123",
                RecordName="www.example.com",
                Type="A",
                PageSize=500,
            )
            self.assertIsNotNone(result)
            if result:  # Type narrowing for mypy
                self.assertEqual(result["RecordId"], "123")
                self.assertEqual(result["RecordName"], "www.example.com")

    def test_query_record_not_found(self):
        """Test _query_record method when no records are found"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"Records": []}

            result = provider._query_record("site123", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_query_record_invalid_format(self):
        """Test _query_record method with invalid records format"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"Records": "invalid"}

            result = provider._query_record("site123", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_create_record_success(self):
        """Test _create_record method with successful creation"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            result = provider._create_record("site123", "www", "example.com", "1.2.3.4", "A", 300, None, {})

            mock_request.assert_called_once_with(
                "CreateRecord",
                SiteId="site123",
                RecordName="www.example.com",
                Value="1.2.3.4",
                Type="A",
                TTL=300,
                Comment=None,
            )
            self.assertTrue(result)

    def test_create_record_failure(self):
        """Test _create_record method with failed creation"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"Error": "Invalid domain"}

            result = provider._create_record("site123", "www", "example.com", "1.2.3.4", "A", None, None, {})

            self.assertFalse(result)

    def test_create_record_with_extra_params(self):
        """Test _create_record method with extra parameters"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            extra = {"Remark": "Test record", "Priority": 10}
            result = provider._create_record(
                "site123", "www", "example.com", "1.2.3.4", "A", 300, None, extra
            )

            mock_request.assert_called_once_with(
                "CreateRecord",
                SiteId="site123",
                RecordName="www.example.com",
                Value="1.2.3.4",
                Type="A",
                TTL=300,
                Comment="Test record",
                Priority=10,
            )
            self.assertTrue(result)

    def test_update_record_success(self):
        """Test _update_record method with successful update"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        old_record = {"RecordId": "123456", "RecordName": "www.example.com", "Comment": "Old comment"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            result = provider._update_record("site123", old_record, "5.6.7.8", "A", 600, None, {})

            mock_request.assert_called_once_with(
                "UpdateRecord", 
                RecordId="123456", 
                Value="5.6.7.8", 
                RecordName="www.example.com", 
                Type="A", 
                TTL=600, 
                Comment="Old comment"
            )
            self.assertTrue(result)

    def test_update_record_with_new_comment(self):
        """Test _update_record method with new comment in extra"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        old_record = {"RecordId": "123456", "RecordName": "www.example.com", "Comment": "Old comment"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            extra = {"Remark": "New comment", "Priority": 20}
            result = provider._update_record("site123", old_record, "5.6.7.8", "A", None, None, extra)

            mock_request.assert_called_once_with(
                "UpdateRecord",
                RecordId="123456",
                Value="5.6.7.8",
                RecordName="www.example.com",
                Type="A",
                TTL=None,
                Comment="New comment",
                Priority=20,
            )
            self.assertTrue(result)

    def test_update_record_failure(self):
        """Test _update_record method with failed update"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        old_record = {"RecordId": "123456", "RecordName": "www.example.com"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"Error": "Record not found"}

            result = provider._update_record("site123", old_record, "5.6.7.8", "A", None, None, {})

            self.assertFalse(result)


class TestAliESAProviderIntegration(BaseProviderTestCase):
    """Integration test cases for AliESAProvider - testing with minimal mocking"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestAliESAProviderIntegration, self).setUp()
        self.auth_id = "test_access_key_id"
        self.auth_token = "test_access_key_secret"

    def test_full_workflow_create_new_record(self):
        """Test complete workflow for creating a new record"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        # Mock only the HTTP layer to simulate API responses
        with patch.object(provider, "_request") as mock_request:
            # Simulate zone query response
            mock_request.side_effect = [
                {"Sites": [{"SiteId": "site123", "SiteName": "example.com"}]},  # _query_zone_id response
                {"Records": []},  # _query_record response (no existing record)
                {"RecordId": "123456"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300)

            self.assertTrue(result)
            # Verify the actual API calls made
            self.assertEqual(mock_request.call_count, 3)
            mock_request.assert_any_call("ListSites", SiteName="example.com")
            mock_request.assert_any_call(
                "ListRecords",
                SiteId="site123",
                RecordName="www.example.com",
                Type="A",
                PageSize=500,
            )
            mock_request.assert_any_call(
                "CreateRecord",
                SiteId="site123",
                RecordName="www.example.com",
                Value="1.2.3.4",
                Type="A",
                TTL=300,
                Comment=None,
            )

    def test_full_workflow_update_existing_record(self):
        """Test complete workflow for updating an existing record"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API responses
            mock_request.side_effect = [
                {"Sites": [{"SiteId": "site123", "SiteName": "example.com"}]},  # _query_zone_id response
                {  # _query_record response (existing record found)
                    "Records": [
                        {"RecordId": "123456", "RecordName": "www.example.com", "Value": "5.6.7.8", "Type": "A"}
                    ]
                },
                {"RecordId": "123456"},  # _update_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300)

            self.assertTrue(result)
            # Verify the update call was made
            mock_request.assert_any_call(
                "UpdateRecord", 
                RecordId="123456", 
                Value="1.2.3.4", 
                RecordName="www.example.com", 
                Type="A", 
                TTL=300, 
                Comment=None
            )

    def test_full_workflow_zone_not_found(self):
        """Test complete workflow when zone is not found"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API returning empty response for zone query
            mock_request.return_value = {"Sites": []}

            with self.assertRaises(ValueError) as cm:
                provider.set_record("www.nonexistent.com", "1.2.3.4", "A")

            self.assertIn("Cannot resolve zone_id", str(cm.exception))

    def test_full_workflow_create_failure(self):
        """Test complete workflow when record creation fails"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate responses: zone found, no existing record, creation fails
            mock_request.side_effect = [
                {"Sites": [{"SiteId": "site123", "SiteName": "example.com"}]},  # _query_zone_id response
                {"Records": []},  # _query_record response (no existing record)
                {"Error": "API error", "Code": "InvalidParameter"},  # _create_record fails
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_update_failure(self):
        """Test complete workflow when record update fails"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate responses: zone found, existing record found, update fails
            mock_request.side_effect = [
                {"Sites": [{"SiteId": "site123", "SiteName": "example.com"}]},  # _query_zone_id response
                {  # _query_record response (existing record found)
                    "Records": [
                        {"RecordId": "123456", "RecordName": "www.example.com", "Value": "5.6.7.8", "Type": "A"}
                    ]
                },
                {"Error": "API error", "Code": "InvalidParameter"},  # _update_record fails
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_with_extra_options(self):
        """Test complete workflow with additional options like ttl and extra parameters"""
        provider = AliESAProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate successful creation with custom options
            mock_request.side_effect = [
                {"Sites": [{"SiteId": "site123", "SiteName": "example.com"}]},  # _query_zone_id response
                {"Records": []},  # _query_record response (no existing record)
                {"RecordId": "123456"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 600, None, Remark="Test record")

            self.assertTrue(result)
            # Verify that extra parameters are passed through correctly
            mock_request.assert_any_call(
                "CreateRecord",
                SiteId="site123",
                RecordName="www.example.com",
                Value="1.2.3.4",
                Type="A",
                TTL=600,
                Comment="Test record",
            )


if __name__ == "__main__":
    unittest.main()