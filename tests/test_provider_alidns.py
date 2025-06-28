# coding=utf-8
"""
Unit tests for AlidnsProvider

@author: Github Copilot
"""

from base_test import BaseProviderTestCase, unittest, patch
from ddns.provider.alidns import AlidnsProvider


class TestAlidnsProvider(BaseProviderTestCase):
    """Test cases for AlidnsProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestAlidnsProvider, self).setUp()
        self.auth_id = "test_access_key_id"
        self.auth_token = "test_access_key_secret"

    def test_class_constants(self):
        """Test AlidnsProvider class constants"""
        self.assertEqual(AlidnsProvider.API, "https://alidns.aliyuncs.com")
        self.assertEqual(AlidnsProvider.content_type, "application/x-www-form-urlencoded")
        self.assertTrue(AlidnsProvider.decode_response)

    def test_init_with_basic_config(self):
        """Test AlidnsProvider initialization with basic configuration"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)
        self.assertEqual(provider.auth_id, self.auth_id)
        self.assertEqual(provider.auth_token, self.auth_token)
        self.assertEqual(provider.API, "https://alidns.aliyuncs.com")

    @patch("ddns.provider.alidns.strftime")
    @patch("ddns.provider.alidns.time")
    def test_signature_generation(self, mock_time, mock_strftime):
        """Test _signature method generates correct signature"""
        # Mock time functions to get consistent results
        mock_time.return_value = 1672574400.0  # 2023-01-01 12:00:00 UTC
        mock_strftime.return_value = "2023-01-01T12:00:00Z"

        provider = AlidnsProvider(self.auth_id, self.auth_token)

        params = {"Action": "TestAction", "DomainName": "example.com"}
        signed_params = provider._signature(params)

        # Verify standard parameters are added
        self.assertEqual(signed_params["Format"], "json")
        self.assertEqual(signed_params["Version"], "2015-01-09")
        self.assertEqual(signed_params["AccessKeyId"], self.auth_id)
        self.assertEqual(signed_params["Timestamp"], "2023-01-01T12:00:00Z")
        self.assertEqual(signed_params["SignatureMethod"], "HMAC-SHA1")
        self.assertEqual(signed_params["SignatureVersion"], "1.0")
        self.assertIn("Signature", signed_params)
        self.assertIn("SignatureNonce", signed_params)

    def test_request_basic(self):
        """Test _request method with basic parameters"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_signature") as mock_signature, patch.object(provider, "_http") as mock_http:

            mock_signature.return_value = {"Action": "TestAction", "Signature": "test_sig"}
            mock_http.return_value = {"Success": True}

            result = provider._request("TestAction", DomainName="example.com")

            mock_signature.assert_called_once()
            mock_http.assert_called_once_with("POST", "/", body={"Action": "TestAction", "Signature": "test_sig"})
            self.assertEqual(result, {"Success": True})

    def test_request_filters_none_params(self):
        """Test _request method filters out None parameters"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_signature") as mock_signature, patch.object(provider, "_http") as mock_http:

            mock_signature.return_value = {"Action": "TestAction"}
            mock_http.return_value = {}

            provider._request("TestAction", DomainName="example.com", TTL=None, Line=None)

            # Verify None parameters were filtered out before signing
            call_args = mock_signature.call_args[1] if mock_signature.call_args else {}
            self.assertNotIn("TTL", call_args)
            self.assertNotIn("Line", call_args)

    def test_query_zone_id_success(self):
        """Test _query_zone_id method with successful response"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"DomainName": "example.com"}

            result = provider._query_zone_id("sub.example.com")

            mock_request.assert_called_once_with("GetMainDomainName", InputString="sub.example.com")
            self.assertEqual(result, "example.com")

    def test_query_zone_id_not_found(self):
        """Test _query_zone_id method when domain is not found"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {}

            result = provider._query_zone_id("notfound.com")

            mock_request.assert_called_once_with("GetMainDomainName", InputString="notfound.com")
            self.assertIsNone(result)

    def test_query_record_success_single(self):
        """Test _query_record method with single record found"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "DomainRecords": {
                    "Record": [
                        {"RR": "www", "RecordId": "123", "Value": "1.2.3.4", "Type": "A"},
                        {"RR": "mail", "RecordId": "456", "Value": "5.6.7.8", "Type": "A"},
                    ]
                }
            }

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            mock_request.assert_called_once_with(
                "DescribeDomainRecords",
                DomainName="example.com",
                RRKeyWord="www",
                Type="A",
                Line=None,
                PageSize=500,
                Lang=None,
                Status=None,
            )
            self.assertIsNotNone(result)
            if result:  # Type narrowing for mypy
                self.assertEqual(result["RecordId"], "123")
                self.assertEqual(result["RR"], "www")

    def test_query_record_not_found(self):
        """Test _query_record method when no matching record is found"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "DomainRecords": {"Record": [{"RR": "mail", "RecordId": "456", "Value": "5.6.7.8", "Type": "A"}]}
            }

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_query_record_empty_response(self):
        """Test _query_record method with empty records response"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"DomainRecords": {"Record": []}}

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_query_record_with_extra_params(self):
        """Test _query_record method with extra parameters"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"DomainRecords": {"Record": []}}

            extra = {"Lang": "en", "Status": "Enable"}
            provider._query_record("example.com", "www", "example.com", "A", "default", extra)

            mock_request.assert_called_once_with(
                "DescribeDomainRecords",
                DomainName="example.com",
                RRKeyWord="www",
                Type="A",
                Line="default",
                PageSize=500,
                Lang="en",
                Status="Enable",
            )

    def test_create_record_success(self):
        """Test _create_record method with successful creation"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", 300, "default", {})

            mock_request.assert_called_once_with(
                "AddDomainRecord",
                DomainName="example.com",
                RR="www",
                Value="1.2.3.4",
                Type="A",
                TTL=300,
                Line="default",
            )
            self.assertTrue(result)

    def test_create_record_failure(self):
        """Test _create_record method with failed creation"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"Error": "Invalid domain"}

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", None, None, {})

            self.assertFalse(result)

    def test_create_record_with_extra_params(self):
        """Test _create_record method with extra parameters"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            extra = {"Priority": 10, "Remark": "Test record"}
            result = provider._create_record(
                "example.com", "www", "example.com", "1.2.3.4", "A", 300, "default", extra
            )

            mock_request.assert_called_once_with(
                "AddDomainRecord",
                DomainName="example.com",
                RR="www",
                Value="1.2.3.4",
                Type="A",
                TTL=300,
                Line="default",
                Priority=10,
                Remark="Test record",
            )
            self.assertTrue(result)

    def test_update_record_success(self):
        """Test _update_record method with successful update"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        old_record = {"RecordId": "123456", "RR": "www", "Line": "default"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, "unicom", {})

            mock_request.assert_called_once_with(
                "UpdateDomainRecord", RecordId="123456", Value="5.6.7.8", RR="www", Type="A", TTL=600, Line="unicom"
            )
            self.assertTrue(result)

    def test_update_record_with_fallback_line(self):
        """Test _update_record method uses old record's line when line is None"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        old_record = {"RecordId": "123456", "RR": "www", "Line": "default"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})

            mock_request.assert_called_once_with(
                "UpdateDomainRecord",
                RecordId="123456",
                Value="5.6.7.8",
                RR="www",
                Type="A",
                TTL=None,
                Line="default",  # Should use old record's line
            )
            self.assertTrue(result)

    def test_update_record_failure(self):
        """Test _update_record method with failed update"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        old_record = {"RecordId": "123456", "RR": "www", "Line": "default"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"Error": "Record not found"}

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})

            self.assertFalse(result)

    def test_update_record_with_extra_params(self):
        """Test _update_record method with extra parameters"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        old_record = {"RecordId": "123456", "RR": "www", "Line": "default"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            extra = {"Priority": 20, "Remark": "Updated record"}
            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, "unicom", extra)

            mock_request.assert_called_once_with(
                "UpdateDomainRecord",
                RecordId="123456",
                Value="5.6.7.8",
                RR="www",
                Type="A",
                TTL=600,
                Line="unicom",
                Priority=20,
                Remark="Updated record",
            )
            self.assertTrue(result)


class TestAlidnsProviderIntegration(BaseProviderTestCase):
    """Integration test cases for AlidnsProvider - testing with minimal mocking"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestAlidnsProviderIntegration, self).setUp()
        self.auth_id = "test_access_key_id"
        self.auth_token = "test_access_key_secret"

    def test_full_workflow_create_new_record(self):
        """Test complete workflow for creating a new record"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        # Mock only the HTTP layer to simulate API responses
        with patch.object(provider, "_request") as mock_request:
            # Simulate zone query response
            mock_request.side_effect = [
                {"DomainName": "example.com"},  # _query_zone_id response
                {"DomainRecords": {"Record": []}},  # _query_record response (no existing record)
                {"RecordId": "123456"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "default")

            self.assertTrue(result)
            # Verify the actual API calls made
            self.assertEqual(mock_request.call_count, 3)
            mock_request.assert_any_call("GetMainDomainName", InputString="example.com")
            mock_request.assert_any_call(
                "DescribeDomainRecords",
                DomainName="example.com",
                RRKeyWord="www",
                Type="A",
                Line="default",
                PageSize=500,
                Lang=None,
                Status=None,
            )
            mock_request.assert_any_call(
                "AddDomainRecord",
                DomainName="example.com",
                RR="www",
                Value="1.2.3.4",
                Type="A",
                TTL=300,
                Line="default",
            )

    def test_full_workflow_update_existing_record(self):
        """Test complete workflow for updating an existing record"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API responses
            mock_request.side_effect = [
                {"DomainName": "example.com"},  # _query_zone_id response
                {  # _query_record response (existing record found)
                    "DomainRecords": {
                        "Record": [
                            {"RecordId": "123456", "RR": "www", "Value": "5.6.7.8", "Type": "A", "Line": "default"}
                        ]
                    }
                },
                {"RecordId": "123456"},  # _update_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "default")

            self.assertTrue(result)
            # Verify the update call was made
            mock_request.assert_any_call(
                "UpdateDomainRecord", RecordId="123456", Value="1.2.3.4", RR="www", Type="A", TTL=300, Line="default"
            )

    def test_full_workflow_zone_not_found(self):
        """Test complete workflow when zone is not found"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API returning empty/null response for zone query
            mock_request.return_value = {}

            with self.assertRaises(ValueError) as cm:
                provider.set_record("www.nonexistent.com", "1.2.3.4", "A")

            self.assertIn("Cannot resolve zone_id", str(cm.exception))

    def test_full_workflow_create_failure(self):
        """Test complete workflow when record creation fails"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate responses: zone found, no existing record, creation fails
            mock_request.side_effect = [
                {"DomainName": "example.com"},  # _query_zone_id response
                {"DomainRecords": {"Record": []}},  # _query_record response (no existing record)
                {"Error": "API error", "Code": "InvalidParameter"},  # _create_record fails
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_update_failure(self):
        """Test complete workflow when record update fails"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate responses: zone found, existing record found, update fails
            mock_request.side_effect = [
                {"DomainName": "example.com"},  # _query_zone_id response
                {  # _query_record response (existing record found)
                    "DomainRecords": {
                        "Record": [
                            {"RecordId": "123456", "RR": "www", "Value": "5.6.7.8", "Type": "A", "Line": "default"}
                        ]
                    }
                },
                {"Error": "API error", "Code": "InvalidParameter"},  # _update_record fails
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_with_options(self):
        """Test complete workflow with additional options like ttl and line"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate successful creation with custom options
            mock_request.side_effect = [
                {"DomainName": "example.com"},  # _query_zone_id response
                {"DomainRecords": {"Record": []}},  # _query_record response (no existing record)
                {"RecordId": "123456"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 600, "unicom")

            self.assertTrue(result)
            # Verify that extra parameters are passed through correctly
            mock_request.assert_any_call(
                "AddDomainRecord",
                DomainName="example.com",
                RR="www",
                Value="1.2.3.4",
                Type="A",
                TTL=600,
                Line="unicom",
            )


if __name__ == "__main__":
    unittest.main()
