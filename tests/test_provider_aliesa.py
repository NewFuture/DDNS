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
        super(TestAliesaProvider, self).setUp()
        self.provider = AliesaProvider(auth_id="test_access_key", auth_token="test_secret_key")

    def test_class_constants(self):
        """Test AliesaProvider class constants"""
        self.assertEqual(self.provider.endpoint, "https://esa.cn-hangzhou.aliyuncs.com")
        self.assertEqual(self.provider.api_version, "2024-09-10")

    def test_init_with_basic_config(self):
        """Test AliesaProvider initialization with basic configuration"""
        provider = AliesaProvider(auth_id="test_access_key", auth_token="test_secret_key")
        self.assertEqual(provider.auth_id, "test_access_key")
        self.assertEqual(provider.auth_token, "test_secret_key")
        self.assertEqual(provider.endpoint, "https://esa.cn-hangzhou.aliyuncs.com")

    def test_init_with_region_endpoint(self):
        """Test AliesaProvider initialization with custom region endpoint"""
        provider = AliesaProvider(auth_id="cn-beijing:test_access_key", auth_token="test_secret_key")
        self.assertEqual(provider.auth_id, "test_access_key")
        self.assertEqual(provider.auth_token, "test_secret_key")
        self.assertEqual(provider.endpoint, "https://esa.cn-beijing.aliyuncs.com")

    def test_init_with_invalid_region_format(self):
        """Test AliesaProvider initialization with invalid region format"""
        with self.assertRaises(ValueError):
            AliesaProvider(auth_id=":test_access_key", auth_token="test_secret_key")

    @patch.object(AliesaProvider, "_http")
    def test_request_basic(self, mock_http):
        """Test _request method with basic parameters"""
        mock_http.return_value = {"SiteId": "12345"}

        result = self.provider._request("ListSites", SiteName="example.com")

        self.assertEqual(result, {"SiteId": "12345"})
        mock_http.assert_called_once()

    @patch.object(AliesaProvider, "_http")
    def test_request_filters_none_params(self, mock_http):
        """Test _request method filters out None parameters"""
        mock_http.return_value = {"SiteId": "12345"}

        self.provider._request("ListSites", SiteName="example.com", Param=None)

        # Check that the request body doesn't contain None values
        args, kwargs = mock_http.call_args
        body = kwargs.get("body", "")
        self.assertNotIn("Param", body)

    @patch.object(AliesaProvider, "_request")
    def test_query_zone_id_success(self, mock_request):
        """Test _query_zone_id method with successful response"""
        mock_request.return_value = {"Sites": [{"SiteId": 12345, "SiteName": "example.com"}]}

        result = self.provider._query_zone_id("example.com")

        self.assertEqual(result, 12345)
        mock_request.assert_called_once_with(method="GET", action="ListSites", SiteName="example.com", PageSize=500)

    @patch.object(AliesaProvider, "_request")
    def test_query_zone_id_not_found(self, mock_request):
        """Test _query_zone_id method when domain is not found"""
        mock_request.return_value = {"Sites": []}

        result = self.provider._query_zone_id("example.com")

        self.assertIsNone(result)

    @patch.object(AliesaProvider, "_request")
    def test_query_record_success_single(self, mock_request):
        """Test _query_record method with single record found"""
        mock_request.return_value = {
            "Records": [
                {
                    "RecordId": "123456",
                    "RecordName": "www.example.com",
                    "Type": "A",
                    "Value": "192.168.1.100",
                    "TTL": 300,
                }
            ]
        }

        result = self.provider._query_record("12345", "www", "example.com", "A", None, {})

        expected = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.100",
            "TTL": 300,
        }
        self.assertEqual(result, expected)
        mock_request.assert_called_once_with(
            method="GET", action="ListRecords", SiteId=12345, RecordName="www.example.com", Type="A", PageSize=100
        )

    @patch.object(AliesaProvider, "_request")
    def test_query_record_not_found(self, mock_request):
        """Test _query_record method when no matching record is found"""
        mock_request.return_value = {"Records": []}

        result = self.provider._query_record("12345", "www", "example.com", "A", None, {})

        self.assertIsNone(result)

    @patch.object(AliesaProvider, "_request")
    def test_create_record_success(self, mock_request):
        """Test _create_record method with successful creation"""
        mock_request.return_value = {"RecordId": "123456"}

        result = self.provider._create_record("12345", "www", "example.com", "192.168.1.100", "A", 300, None, {})

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            method="POST",
            action="CreateRecord",
            SiteId=12345,
            RecordName="www.example.com",
            Type="A",
            Value="192.168.1.100",
            TTL=300,
            Comment="Managed by [DDNS v0.0.0](https://ddns.newfuture.cc)",
        )

    @patch.object(AliesaProvider, "_request")
    def test_create_record_with_comment(self, mock_request):
        """Test _create_record method with comment parameter"""
        mock_request.return_value = {"RecordId": "123456"}

        result = self.provider._create_record(
            "12345", "www", "example.com", "192.168.1.100", "A", 300, None, {"Comment": "DDNS Auto Update"}
        )

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            method="POST",
            action="CreateRecord",
            SiteId=12345,
            RecordName="www.example.com",
            Type="A",
            Value="192.168.1.100",
            TTL=300,
            Comment="DDNS Auto Update",
        )

    @patch.object(AliesaProvider, "_request")
    def test_create_record_failure(self, mock_request):
        """Test _create_record method with failed creation"""
        mock_request.return_value = {"Error": "Invalid domain"}

        result = self.provider._create_record("12345", "www", "example.com", "192.168.1.100", "A", 300, None, {})

        self.assertFalse(result)

    @patch.object(AliesaProvider, "_request")
    def test_update_record_success(self, mock_request):
        """Test _update_record method with successful update"""
        mock_request.return_value = {"RecordId": "123456"}

        old_record = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.1",
            "TTL": 300,
        }

        result = self.provider._update_record("12345", old_record, "192.168.1.100", "A", 300, None, {})

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            method="POST",
            action="UpdateRecord",
            SiteId=12345,
            RecordId="123456",
            Type="A",
            Value="192.168.1.100",
            TTL=300,
            Comment="Managed by [DDNS v0.0.0](https://ddns.newfuture.cc)",
        )

    @patch.object(AliesaProvider, "_request")
    def test_update_record_no_changes(self, mock_request):
        """Test _update_record method when no changes are detected"""
        old_record = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.100",
            "TTL": 300,
        }

        result = self.provider._update_record("12345", old_record, "192.168.1.100", "A", 300, None, {})

        self.assertTrue(result)
        # Should not make API call if no changes
        mock_request.assert_not_called()

    @patch.object(AliesaProvider, "_request")
    def test_update_record_failure(self, mock_request):
        """Test _update_record method with failed update"""
        mock_request.return_value = {"Error": "Record not found"}

        old_record = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.1",
            "TTL": 300,
        }

        result = self.provider._update_record("12345", old_record, "192.168.1.100", "A", 300, None, {})

        self.assertFalse(result)

    @patch.object(AliesaProvider, "_request")
    def test_update_record_with_comment(self, mock_request):
        """Test _update_record method with comment parameter"""
        mock_request.return_value = {"RecordId": "123456"}

        old_record = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.1",
            "TTL": 300,
        }

        result = self.provider._update_record(
            "12345", old_record, "192.168.1.100", "A", 300, None, {"Comment": "DDNS Auto Update"}
        )

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            method="POST",
            action="UpdateRecord",
            SiteId=12345,
            RecordId="123456",
            Type="A",
            Value="192.168.1.100",
            TTL=300,
            Comment="DDNS Auto Update",
        )


class TestAliesaProviderIntegration(BaseProviderTestCase):
    """AliESA Provider 集成测试类"""

    def setUp(self):
        """Setup test provider with mock credentials"""
        super(TestAliesaProviderIntegration, self).setUp()
        self.provider = AliesaProvider(auth_id="test_access_key", auth_token="test_secret_key")

    @patch.object(AliesaProvider, "get_zone_id")
    @patch.object(AliesaProvider, "_query_record")
    @patch.object(AliesaProvider, "_update_record")
    def test_full_workflow_update_existing_record(self, mock_update, mock_query_record, mock_get_zone_id):
        """Test complete workflow for updating an existing record"""
        # Setup mocks
        mock_get_zone_id.return_value = 12345
        mock_query_record.return_value = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.1",
            "TTL": 300,
        }
        mock_update.return_value = True

        # Execute
        result = self.provider.set_record("www.example.com", "192.168.1.100", "A", 300)

        # Verify
        self.assertTrue(result)
        mock_get_zone_id.assert_called_once_with("example.com")
        mock_query_record.assert_called_once()
        mock_update.assert_called_once()

    @patch.object(AliesaProvider, "get_zone_id")
    @patch.object(AliesaProvider, "_query_record")
    @patch.object(AliesaProvider, "_create_record")
    def test_full_workflow_create_new_record(self, mock_create, mock_query_record, mock_get_zone_id):
        """Test complete workflow for creating a new record"""
        # Setup mocks
        mock_get_zone_id.return_value = 12345
        mock_query_record.return_value = None  # No existing record
        mock_create.return_value = True

        # Execute
        result = self.provider.set_record("www.example.com", "192.168.1.100", "A", 300)

        # Verify
        self.assertTrue(result)
        mock_get_zone_id.assert_called_once_with("example.com")
        mock_query_record.assert_called_once()
        mock_create.assert_called_once()


class TestAliesaProviderAPIResponse(BaseProviderTestCase):
    """Test AliesaProvider API response handling based on official docs"""

    def setUp(self):
        """Setup test provider with mock credentials"""
        super(TestAliesaProviderAPIResponse, self).setUp()
        self.provider = AliesaProvider(auth_id="test_access_key", auth_token="test_secret_key")

    @patch.object(AliesaProvider, "_request")
    def test_list_sites_multiple_sites(self, mock_request):
        """Test ListSites API response with multiple sites (official docs)"""
        mock_request.return_value = {
            "RequestId": "CB1A380B-09F0-41BB-802B-72F8FD6DA2FE",
            "Sites": [
                {"SiteId": 12345, "SiteName": "example.com", "Status": "activated"},
                {"SiteId": 12346, "SiteName": "test.com", "Status": "activated"},
                {"SiteId": 12347, "SiteName": "demo.com", "Status": "pending"},
            ],
        }

        zone_id = self.provider._query_zone_id("example.com")

        self.assertEqual(zone_id, 12345)
        mock_request.assert_called_once_with(method="GET", action="ListSites", SiteName="example.com", PageSize=500)

    @patch.object(AliesaProvider, "_request")
    def test_list_sites_no_matching_site(self, mock_request):
        """Test ListSites API when no site matches the domain name"""
        mock_request.return_value = {
            "RequestId": "CB1A380B-09F0-41BB-802B-72F8FD6DA2FE",
            "Sites": [{"SiteId": 12346, "SiteName": "other.com", "Status": "activated"}],
        }

        zone_id = self.provider._query_zone_id("example.com")

        self.assertIsNone(zone_id)

    @patch.object(AliesaProvider, "_request")
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
                    "Status": "activated",
                },
                {
                    "RecordId": "123457",
                    "RecordName": "www.example.com",
                    "Type": "A",
                    "Value": "192.168.1.101",
                    "TTL": 600,
                    "Status": "activated",
                },
            ],
        }

        result = self.provider._query_record(
            "12345", "www", "example.com", "A", None, {}
        )  # type: dict # type: ignore

        # Should return the first matching record
        self.assertEqual(result["RecordId"], "123456")
        self.assertEqual(result["Value"], "192.168.1.100")

    @patch.object(AliesaProvider, "_request")
    def test_create_record_with_all_parameters(self, mock_request):
        """Test CreateRecord API with all optional parameters"""
        mock_request.return_value = {"RequestId": "CB1A380B-09F0-41BB-802B-72F8FD6DA2FE", "RecordId": "123456"}

        result = self.provider._create_record(
            "12345", "www", "example.com", "192.168.1.100", "A", 600, None, {"Comment": "Test record creation"}
        )

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            method="POST",
            action="CreateRecord",
            SiteId=12345,
            RecordName="www.example.com",
            Type="A",
            Value="192.168.1.100",
            TTL=600,
            Comment="Test record creation",
        )

    @patch.object(AliesaProvider, "_request")
    def test_create_record_minimal_parameters(self, mock_request):
        """Test CreateRecord API with minimal required parameters"""
        mock_request.return_value = {"RequestId": "CB1A380B-09F0-41BB-802B-72F8FD6DA2FE", "RecordId": "123456"}

        result = self.provider._create_record("12345", "@", "example.com", "192.168.1.100", "A", None, None, {})

        self.assertTrue(result)

    @patch.object(AliesaProvider, "_request")
    def test_different_record_types_a(self, mock_request):
        """Test support for A record type"""
        mock_request.return_value = {"RecordId": "123456"}
        result = self.provider._create_record("12345", "test", "example.com", "192.168.1.100", "A", 300, None, {})
        self.assertTrue(result)

    @patch.object(AliesaProvider, "_request")
    def test_different_record_types_aaaa(self, mock_request):
        """Test support for AAAA record type"""
        mock_request.return_value = {"RecordId": "123456"}
        result = self.provider._create_record("12345", "test", "example.com", "2001:db8::1", "AAAA", 300, None, {})
        self.assertTrue(result)

    @patch.object(AliesaProvider, "_request")
    def test_different_record_types_cname(self, mock_request):
        """Test support for CNAME record type"""
        mock_request.return_value = {"RecordId": "123456"}
        result = self.provider._create_record(
            "12345", "test", "example.com", "target.example.com", "CNAME", 300, None, {}
        )
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
