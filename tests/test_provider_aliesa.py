# coding=utf-8
"""
测试 AliESA Provider
@author: NewFuture
"""

import unittest
from base_test import BaseProviderTestCase, patch
from ddns.provider.aliesa import AliesaProvider


class TestAliesaProvider(BaseProviderTestCase):
    """AliESA Provider 测试类"""

    def setUp(self):
        """Setup test provider with mock credentials"""
        super().setUp()
        self.provider = AliesaProvider(
            auth_id="test_access_key",
            auth_token="test_secret_key"
        )

    def test_class_constants(self):
        """Test AliesaProvider class constants"""
        self.assertEqual(self.provider.API, "https://esa.cn-hangzhou.aliyuncs.com")
        self.assertEqual(self.provider.api_version, "2024-09-10")

    def test_init_with_basic_config(self):
        """Test AliesaProvider initialization with basic configuration"""
        provider = AliesaProvider(
            auth_id="test_access_key",
            auth_token="test_secret_key"
        )
        self.assertEqual(provider.auth_id, "test_access_key")
        self.assertEqual(provider.auth_token, "test_secret_key")

    @patch.object(AliesaProvider, '_http')
    def test_request_basic(self, mock_http):
        """Test _request method with basic parameters"""
        mock_http.return_value = {"SiteId": "12345"}

        result = self.provider._request("ListSites", SiteName="example.com")

        self.assertEqual(result, {"SiteId": "12345"})
        mock_http.assert_called_once()

    @patch.object(AliesaProvider, '_http')
    def test_request_filters_none_params(self, mock_http):
        """Test _request method filters out None parameters"""
        mock_http.return_value = {"SiteId": "12345"}

        self.provider._request("ListSites", SiteName="example.com", Param=None)

        # Check that the request body doesn't contain None values
        args, kwargs = mock_http.call_args
        body = kwargs.get('body', '')
        self.assertNotIn('Param', body)

    @patch.object(AliesaProvider, '_request')
    def test_split_zone_and_sub_success(self, mock_request):
        """Test _split_zone_and_sub method with successful response"""
        mock_request.return_value = {
            "Sites": [
                {"SiteId": 12345, "SiteName": "example.com"}
            ]
        }

        result = self.provider._split_zone_and_sub("www.example.com")

        self.assertEqual(result, ("12345", "www", "example.com"))

    @patch.object(AliesaProvider, '_request')
    def test_split_zone_and_sub_root_domain(self, mock_request):
        """Test _split_zone_and_sub method with root domain"""
        mock_request.return_value = {
            "Sites": [
                {"SiteId": 12345, "SiteName": "example.com"}
            ]
        }

        result = self.provider._split_zone_and_sub("example.com")

        self.assertEqual(result, ("12345", "@", "example.com"))

    @patch.object(AliesaProvider, '_request')
    def test_split_zone_and_sub_not_found(self, mock_request):
        """Test _split_zone_and_sub method when domain is not found"""
        mock_request.return_value = {"Sites": []}

        result = self.provider._split_zone_and_sub("www.example.com")

        self.assertEqual(result, (None, None, "www.example.com"))

    def test_split_zone_and_sub_manual_site_id(self):
        """Test _split_zone_and_sub method with manual site ID"""
        result = self.provider._split_zone_and_sub("www.example.com#12345")

        self.assertEqual(result, ("12345", "www", "example.com"))

    def test_split_zone_and_sub_manual_site_id_with_plus(self):
        """Test _split_zone_and_sub method with + separator and manual site ID"""
        result = self.provider._split_zone_and_sub("www+example.com#12345")

        self.assertEqual(result, ("12345", "www", "example.com"))

    def test_split_zone_and_sub_manual_site_id_root(self):
        """Test _split_zone_and_sub method with manual site ID for root domain"""
        result = self.provider._split_zone_and_sub("example.com#12345")

        self.assertEqual(result, ("12345", "@", "example.com"))

    def test_split_zone_and_sub_manual_ids_with_record_id(self):
        """Test _split_zone_and_sub method with both site and record ID"""
        result = self.provider._split_zone_and_sub("www.example.com#12345#67890")

        self.assertEqual(result, ("12345", "www", "example.com"))

    def test_split_zone_and_sub_empty_site_id(self):
        """Test _split_zone_and_sub method with empty site ID falls back to auto"""
        with patch.object(self.provider, '_request') as mock_request:
            mock_request.return_value = {
                "Sites": [{"SiteId": 99999, "SiteName": "example.com"}]
            }

            result = self.provider._split_zone_and_sub("www.example.com##67890")

            self.assertEqual(result, ("99999", "www", "example.com"))

    @patch.object(AliesaProvider, '_request')
    def test_query_record_success_single(self, mock_request):
        """Test _query_record method with single record found"""
        mock_request.return_value = {
            "Records": [
                {
                    "RecordId": "123456",
                    "RecordName": "www.example.com",
                    "Type": "A",
                    "Value": "192.168.1.100",
                    "TTL": 300
                }
            ]
        }

        result = self.provider._query_record("12345", "www", "example.com", "A", None, {})

        expected = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.100",
            "TTL": 300
        }
        self.assertEqual(result, expected)
        mock_request.assert_called_once_with(
            "ListRecords",
            SiteId=12345,
            RecordName="www.example.com",
            Type="A",
            PageSize=100
        )

    @patch.object(AliesaProvider, '_request')
    def test_query_record_not_found(self, mock_request):
        """Test _query_record method when no matching record is found"""
        mock_request.return_value = {"Records": []}

        result = self.provider._query_record("12345", "www", "example.com", "A", None, {})

        self.assertIsNone(result)

    @patch.object(AliesaProvider, '_request')
    def test_create_record_success(self, mock_request):
        """Test _create_record method with successful creation"""
        mock_request.return_value = {"RecordId": "123456"}

        result = self.provider._create_record(
            "12345", "www", "example.com", "192.168.1.100", "A", 300, None, {}
        )

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            "CreateRecord",
            SiteId=12345,
            RecordName="www.example.com",
            Type="A",
            Value="192.168.1.100",
            TTL=300
        )

    @patch.object(AliesaProvider, '_request')
    def test_create_record_with_comment(self, mock_request):
        """Test _create_record method with comment parameter"""
        mock_request.return_value = {"RecordId": "123456"}

        result = self.provider._create_record(
            "12345", "www", "example.com", "192.168.1.100", "A", 300, None,
            {"Comment": "DDNS Auto Update"}
        )

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            "CreateRecord",
            SiteId=12345,
            RecordName="www.example.com",
            Type="A",
            Value="192.168.1.100",
            TTL=300,
            Remark="DDNS Auto Update"
        )

    @patch.object(AliesaProvider, '_request')
    def test_create_record_failure(self, mock_request):
        """Test _create_record method with failed creation"""
        mock_request.return_value = {"Error": "Invalid domain"}

        result = self.provider._create_record(
            "12345", "www", "example.com", "192.168.1.100", "A", 300, None, {}
        )

        self.assertFalse(result)

    @patch.object(AliesaProvider, '_request')
    def test_update_record_success(self, mock_request):
        """Test _update_record method with successful update"""
        mock_request.return_value = {"RecordId": "123456"}

        old_record = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.1",
            "TTL": 300
        }

        result = self.provider._update_record(
            "12345", old_record, "192.168.1.100", "A", 300, None, {}
        )

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            "UpdateRecord",
            SiteId=12345,
            RecordId="123456",
            Type="A",
            Value="192.168.1.100",
            TTL=300
        )

    @patch.object(AliesaProvider, '_request')
    def test_update_record_no_changes(self, mock_request):
        """Test _update_record method when no changes are detected"""
        old_record = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.100",
            "TTL": 300
        }

        result = self.provider._update_record(
            "12345", old_record, "192.168.1.100", "A", 300, None, {}
        )

        self.assertTrue(result)
        # Should not make API call if no changes
        mock_request.assert_not_called()

    @patch.object(AliesaProvider, '_request')
    def test_update_record_failure(self, mock_request):
        """Test _update_record method with failed update"""
        mock_request.return_value = {"Error": "Record not found"}

        old_record = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.1",
            "TTL": 300
        }

        result = self.provider._update_record(
            "12345", old_record, "192.168.1.100", "A", 300, None, {}
        )

        self.assertFalse(result)

    @patch.object(AliesaProvider, '_request')
    def test_update_record_with_comment(self, mock_request):
        """Test _update_record method with comment parameter"""
        mock_request.return_value = {"RecordId": "123456"}

        old_record = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.1",
            "TTL": 300
        }

        result = self.provider._update_record(
            "12345", old_record, "192.168.1.100", "A", 300, None,
            {"Comment": "DDNS Auto Update"}
        )

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            "UpdateRecord",
            SiteId=12345,
            RecordId="123456",
            Type="A",
            Value="192.168.1.100",
            TTL=300,
            Remark="DDNS Auto Update"
        )


class TestAliesaProviderIntegration(BaseProviderTestCase):
    """AliESA Provider 集成测试类"""

    def setUp(self):
        """Setup test provider with mock credentials"""
        super().setUp()
        self.provider = AliesaProvider(
            auth_id="test_access_key",
            auth_token="test_secret_key"
        )

    @patch.object(AliesaProvider, '_split_zone_and_sub')
    @patch.object(AliesaProvider, '_query_record')
    @patch.object(AliesaProvider, '_update_record')
    def test_full_workflow_update_existing_record(self, mock_update, mock_query_record, mock_split):
        """Test complete workflow for updating an existing record"""
        # Setup mocks
        mock_split.return_value = ("12345", "www", "example.com")
        mock_query_record.return_value = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.1",
            "TTL": 300
        }
        mock_update.return_value = True

        # Execute
        result = self.provider.set_record("www.example.com", "192.168.1.100", "A", 300)

        # Verify
        self.assertTrue(result)
        mock_split.assert_called_once_with("www.example.com")
        mock_query_record.assert_called_once()
        mock_update.assert_called_once()

    @patch.object(AliesaProvider, '_split_zone_and_sub')
    @patch.object(AliesaProvider, '_query_record')
    @patch.object(AliesaProvider, '_create_record')
    def test_full_workflow_create_new_record(self, mock_create, mock_query_record, mock_split):
        """Test complete workflow for creating a new record"""
        # Setup mocks
        mock_split.return_value = ("12345", "www", "example.com")
        mock_query_record.return_value = None  # No existing record
        mock_create.return_value = True

        # Execute
        result = self.provider.set_record("www.example.com", "192.168.1.100", "A", 300)

        # Verify
        self.assertTrue(result)
        mock_split.assert_called_once_with("www.example.com")
        mock_query_record.assert_called_once()
        mock_create.assert_called_once()

    @patch.object(AliesaProvider, '_split_zone_and_sub')
    def test_full_workflow_zone_not_found(self, mock_split):
        """Test complete workflow when zone is not found"""
        # Setup mocks
        mock_split.return_value = (None, None, "example.com")

        # Execute
        result = self.provider.set_record("www.example.com", "192.168.1.100", "A", 300)

        # Verify
        self.assertFalse(result)
        mock_split.assert_called_once_with("www.example.com")

    @patch.object(AliesaProvider, '_split_zone_and_sub')
    @patch.object(AliesaProvider, '_query_record')
    @patch.object(AliesaProvider, '_create_record')
    def test_full_workflow_create_failure(self, mock_create, mock_query_record, mock_split):
        """Test complete workflow when record creation fails"""
        # Setup mocks
        mock_split.return_value = ("12345", "www", "example.com")
        mock_query_record.return_value = None  # No existing record
        mock_create.return_value = False  # Creation fails

        # Execute
        result = self.provider.set_record("www.example.com", "192.168.1.100", "A", 300)

        # Verify
        self.assertFalse(result)
        mock_create.assert_called_once()


class TestAliesaProviderAPIResponse(BaseProviderTestCase):
    """Test AliesaProvider API response handling based on official documentation"""

    def setUp(self):
        """Setup test provider with mock credentials"""
        super().setUp()
        self.provider = AliesaProvider(
            auth_id="test_access_key",
            auth_token="test_secret_key"
        )

    @patch.object(AliesaProvider, '_request')
    def test_list_sites_multiple_sites(self, mock_request):
        """Test ListSites API response with multiple sites (following official docs)"""
        mock_request.return_value = {
            "RequestId": "CB1A380B-09F0-41BB-802B-72F8FD6DA2FE",
            "Sites": [
                {"SiteId": 12345, "SiteName": "example.com", "Status": "activated"},
                {"SiteId": 12346, "SiteName": "test.com", "Status": "activated"},
                {"SiteId": 12347, "SiteName": "demo.com", "Status": "pending"}
            ]
        }

        zone_id = self.provider._query_zone_id("example.com")

        self.assertEqual(zone_id, "12345")
        mock_request.assert_called_once_with("ListSites", SiteName="example.com", PageSize=500)

    @patch.object(AliesaProvider, '_request')
    def test_list_sites_no_matching_site(self, mock_request):
        """Test ListSites API when no site matches the domain name"""
        mock_request.return_value = {
            "RequestId": "CB1A380B-09F0-41BB-802B-72F8FD6DA2FE",
            "Sites": [
                {"SiteId": 12346, "SiteName": "other.com", "Status": "activated"}
            ]
        }

        zone_id = self.provider._query_zone_id("example.com")

        self.assertIsNone(zone_id)

    @patch.object(AliesaProvider, '_request')
    def test_list_records_multiple_matching_records(self, mock_request):
        """Test ListRecords API with multiple matching records"""
        mock_request.return_value = {
            "RequestId": "CB1A380B-09F0-41BB-802B-72F8FD6DA2FE",
            "Records": [
                {
                    "RecordId": "123456",
                    "RecordName": "www.example.com",
                    "Type": "A",
                    "Value": "192.168.1.100",
                    "TTL": 300,
                    "Status": "activated"
                },
                {
                    "RecordId": "123457",
                    "RecordName": "www.example.com",
                    "Type": "A",
                    "Value": "192.168.1.101",
                    "TTL": 600,
                    "Status": "activated"
                }
            ]
        }

        result = self.provider._query_record("12345", "www", "example.com", "A", None, {})

        # Should return the first matching record
        self.assertEqual(result["RecordId"], "123456")
        self.assertEqual(result["Value"], "192.168.1.100")

    @patch.object(AliesaProvider, '_request')
    def test_create_record_with_all_parameters(self, mock_request):
        """Test CreateRecord API with all optional parameters"""
        mock_request.return_value = {
            "RequestId": "CB1A380B-09F0-41BB-802B-72F8FD6DA2FE",
            "RecordId": "123456"
        }

        result = self.provider._create_record(
            "12345", "www", "example.com", "192.168.1.100", "A", 600, None,
            {"Comment": "Test record creation"}
        )

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            "CreateRecord",
            SiteId=12345,
            RecordName="www.example.com",
            Type="A",
            Value="192.168.1.100",
            TTL=600,
            Remark="Test record creation"
        )

    @patch.object(AliesaProvider, '_request')
    def test_create_record_minimal_parameters(self, mock_request):
        """Test CreateRecord API with minimal required parameters"""
        mock_request.return_value = {
            "RequestId": "CB1A380B-09F0-41BB-802B-72F8FD6DA2FE",
            "RecordId": "123456"
        }

        result = self.provider._create_record(
            "12345", "@", "example.com", "192.168.1.100", "A", None, None, {}
        )

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            "CreateRecord",
            SiteId=12345,
            RecordName="example.com",
            Type="A",
            Value="192.168.1.100"
        )

    @patch.object(AliesaProvider, '_request')
    def test_update_record_all_fields_changed(self, mock_request):
        """Test UpdateRecord API when all fields are changed"""
        mock_request.return_value = {
            "RequestId": "CB1A380B-09F0-41BB-802B-72F8FD6DA2FE",
            "RecordId": "123456"
        }

        old_record = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.1",
            "TTL": 300
        }

        result = self.provider._update_record(
            "12345", old_record, "192.168.1.100", "A", 600, None,
            {"Comment": "Updated via DDNS"}
        )

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            "UpdateRecord",
            SiteId=12345,
            RecordId="123456",
            Type="A",
            Value="192.168.1.100",
            TTL=600,
            Remark="Updated via DDNS"
        )

    @patch.object(AliesaProvider, '_request')
    def test_api_error_response_handling(self, mock_request):
        """Test handling of API error responses following ESA documentation"""
        mock_request.return_value = {
            "RequestId": "CB1A380B-09F0-41BB-802B-72F8FD6DA2FE",
            "Code": "InvalidParameter.SiteId",
            "Message": "The specified site ID does not exist."
        }

        # Test with CreateRecord error
        result = self.provider._create_record(
            "99999", "www", "example.com", "192.168.1.100", "A", 300, None, {}
        )

        self.assertFalse(result)

    @patch.object(AliesaProvider, '_request')
    def test_api_empty_response_handling(self, mock_request):
        """Test handling of empty API responses"""
        mock_request.return_value = {}

        # Test with empty CreateRecord response
        result = self.provider._create_record(
            "12345", "www", "example.com", "192.168.1.100", "A", 300, None, {}
        )

        self.assertFalse(result)

    @patch.object(AliesaProvider, '_request')
    def test_different_record_types(self, mock_request):
        """Test support for different DNS record types (A, AAAA, CNAME, etc.)"""
        test_cases = [
            ("A", "192.168.1.100"),
            ("AAAA", "2001:db8::1"),
            ("CNAME", "target.example.com"),
            ("MX", "10 mail.example.com"),
            ("TXT", "v=spf1 include:_spf.google.com ~all")
        ]

        for record_type, value in test_cases:
            with self.subTest(record_type=record_type):
                mock_request.return_value = {"RecordId": "123456"}

                result = self.provider._create_record(
                    "12345", "test", "example.com", value, record_type, 300, None, {}
                )

                self.assertTrue(result)
                mock_request.assert_called_with(
                    "CreateRecord",
                    SiteId=12345,
                    RecordName="test.example.com",
                    Type=record_type,
                    Value=value,
                    TTL=300
                )

    def test_domain_parsing_edge_cases(self):
        """Test domain parsing for various edge cases following ESA domain format specs"""
        test_cases = [
            # (input_domain, expected_site_id, expected_subdomain, expected_main_domain)
            ("example.com#12345", "12345", "@", "example.com"),
            ("www.example.com#12345", "12345", "www", "example.com"),
            ("api.v2.example.com#12345", "12345", "api.v2", "example.com"),
            ("sub+example.com#12345", "12345", "sub", "example.com"),
            ("_dmarc.example.com#12345", "12345", "_dmarc", "example.com"),
            ("*.example.com#12345", "12345", "*", "example.com"),
        ]

        for input_domain, expected_site_id, expected_subdomain, expected_main_domain in test_cases:
            with self.subTest(domain=input_domain):
                result = self.provider._split_zone_and_sub(input_domain)
                self.assertEqual(result, (expected_site_id, expected_subdomain, expected_main_domain))


if __name__ == '__main__':
    unittest.main()
