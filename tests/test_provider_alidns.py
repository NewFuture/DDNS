# coding=utf-8
"""
Unit tests for AlidnsProvider

@author: Github Copilot
"""

from test_base import BaseProviderTestCase, unittest, patch
from ddns.provider.alidns import AlidnsProvider
from datetime import datetime


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
        self.assertEqual(AlidnsProvider.ContentType, "application/x-www-form-urlencoded")
        self.assertTrue(AlidnsProvider.DecodeResponse)

    def test_init_with_basic_config(self):
        """Test AlidnsProvider initialization with basic configuration"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)
        self.assertEqual(provider.auth_id, self.auth_id)
        self.assertEqual(provider.auth_token, self.auth_token)
        self.assertEqual(provider.API, "https://alidns.aliyuncs.com")

    @patch("ddns.provider.alidns.datetime")
    def test_signature_generation(self, mock_datetime):
        """Test _signature method generates correct signature"""
        # Mock datetime to get consistent results
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

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

            result = provider._query_record("example.com", "www", "example.com", "A")  # type: dict # type: ignore

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
            self.assertEqual(result["RecordId"], "123")
            self.assertEqual(result["RR"], "www")

    def test_query_record_not_found(self):
        """Test _query_record method when no matching record is found"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "DomainRecords": {"Record": [{"RR": "mail", "RecordId": "456", "Value": "5.6.7.8", "Type": "A"}]}
            }

            result = provider._query_record("example.com", "www", "example.com", "A")

            self.assertIsNone(result)

    def test_query_record_empty_response(self):
        """Test _query_record method with empty records response"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"DomainRecords": {"Record": []}}

            result = provider._query_record("example.com", "www", "example.com", "A")

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

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", 300, "default")

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

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A")

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

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, "unicom")

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

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None)

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

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A")

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
    """Integration test cases for AlidnsProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestAlidnsProviderIntegration, self).setUp()
        self.auth_id = "test_access_key_id"
        self.auth_token = "test_access_key_secret"

    def test_full_workflow_create_new_record(self):
        """Test complete workflow for creating a new record"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_create_record") as mock_create:

            # Setup mocks
            mock_zone.return_value = "example.com"
            mock_query.return_value = None  # No existing record
            mock_create.return_value = True

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "default")

            self.assertTrue(result)
            mock_zone.assert_called_once_with("example.com")
            mock_query.assert_called_once_with(
                "example.com", sub_domain="www", main_domain="example.com", record_type="A", line="default", extra={}
            )
            mock_create.assert_called_once_with(
                "example.com",
                sub_domain="www",
                main_domain="example.com",
                value="1.2.3.4",
                record_type="A",
                ttl=300,
                line="default",
                extra={},
            )

    def test_full_workflow_update_existing_record(self):
        """Test complete workflow for updating an existing record"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        existing_record = {"RecordId": "123456", "RR": "www", "Value": "5.6.7.8"}

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_update_record") as mock_update:

            # Setup mocks
            mock_zone.return_value = "example.com"
            mock_query.return_value = existing_record
            mock_update.return_value = True

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "default")

            self.assertTrue(result)
            mock_zone.assert_called_once_with("example.com")
            mock_query.assert_called_once_with(
                "example.com", sub_domain="www", main_domain="example.com", record_type="A", line="default", extra={}
            )
            mock_update.assert_called_once_with(
                "example.com",
                old_record=existing_record,
                value="1.2.3.4",
                record_type="A",
                ttl=300,
                line="default",
                extra={},
            )

    def test_full_workflow_zone_not_found(self):
        """Test complete workflow when zone is not found"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_query_zone_id") as mock_zone:
            mock_zone.return_value = None

            with self.assertRaises(ValueError) as cm:
                provider.set_record("www.nonexistent.com", "1.2.3.4", "A")

            self.assertIn("Cannot resolve zone_id", str(cm.exception))

    def test_full_workflow_create_failure(self):
        """Test complete workflow when record creation fails"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

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
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        existing_record = {"RecordId": "123456", "RR": "www", "Value": "5.6.7.8"}

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_update_record") as mock_update:

            # Setup mocks
            mock_zone.return_value = "example.com"
            mock_query.return_value = existing_record
            mock_update.return_value = False  # Update fails

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_with_options(self):
        """Test complete workflow with additional options like ttl and line"""
        provider = AlidnsProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_query_zone_id") as mock_zone, patch.object(
            provider, "_query_record"
        ) as mock_query, patch.object(provider, "_create_record") as mock_create:

            # Setup mocks
            mock_zone.return_value = "example.com"
            mock_query.return_value = None  # No existing record
            mock_create.return_value = True

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 600, "unicom")

            self.assertTrue(result)
            # Verify that extra parameters are passed through correctly
            mock_create.assert_called_once_with(
                "example.com",
                sub_domain="www",
                main_domain="example.com",
                value="1.2.3.4",
                record_type="A",
                ttl=600,
                line="unicom",
                extra={},
            )


if __name__ == "__main__":
    unittest.main()
