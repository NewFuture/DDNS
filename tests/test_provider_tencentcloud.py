# coding=utf-8
"""
Unit tests for TencentCloudProvider
腾讯云 DNSPod 提供商单元测试

@author: NewFuture
"""

from test_base import BaseProviderTestCase, unittest, patch
from ddns.provider.tencentcloud import TencentCloudProvider


class TestTencentCloudProvider(BaseProviderTestCase):
    """Test TencentCloudProvider functionality"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.provider = TencentCloudProvider(self.auth_id, self.auth_token)
        self.logger = self.mock_logger(self.provider)

    def test_init(self):
        """Test provider initialization"""
        self.assertProviderInitialized(self.provider)
        self.assertEqual(self.provider.service, "dnspod")
        self.assertEqual(self.provider.version, "2021-03-23")
        self.assertEqual(self.provider.API, "https://dnspod.tencentcloudapi.com")
        self.assertEqual(self.provider.ContentType, "application/json")

    def test_validate_success(self):
        """Test successful validation"""
        # Should not raise any exception
        self.provider._validate()

    def test_validate_missing_auth_id(self):
        """Test validation with missing auth_id"""
        with self.assertRaises(ValueError) as context:
            TencentCloudProvider("", self.auth_token, self.logger)
        self.assertIn("id", str(context.exception))

    def test_validate_missing_auth_token(self):
        """Test validation with missing auth_token"""
        with self.assertRaises(ValueError) as context:
            TencentCloudProvider(self.auth_id, "", self.logger)
        self.assertIn("token", str(context.exception))

    def test_sign_tc3(self):
        """Test TC3-HMAC-SHA256 signature generation"""
        method = "POST"
        uri = "/"
        query = ""
        headers = {"Content-Type": "application/json", "Host": "dnspod.tencentcloudapi.com"}
        payload = "{}"
        timestamp = 1609459200  # 2021-01-01 00:00:00 UTC

        authorization = self.provider._sign_tc3(method, uri, query, headers, payload, timestamp)

        # Check authorization format
        self.assertIn("TC3-HMAC-SHA256", authorization)
        self.assertIn("Credential=", authorization)
        self.assertIn("SignedHeaders=", authorization)
        self.assertIn("Signature=", authorization)
        self.assertIn(self.auth_id, authorization)

    def test_query_zone_id(self):
        """Test query zone ID (returns domain itself)"""
        domain = "example.com"
        zone_id = self.provider._query_zone_id(domain)
        self.assertEqual(zone_id, domain)

    @patch.object(TencentCloudProvider, "_request")
    def test_query_record_found(self, mock_request):
        """Test successful record query"""
        mock_request.return_value = {
            "RecordList": [
                {"RecordId": 123456, "Name": "www", "Type": "A", "Value": "1.2.3.4", "Line": "默认", "TTL": 600}
            ]
        }

        record = self.provider._query_record("example.com", "www", "example.com", "A")  # type: dict # type: ignore

        self.assertIsNotNone(record)
        self.assertEqual(record["RecordId"], 123456)
        self.assertEqual(record["Name"], "www")
        self.assertEqual(record["Type"], "A")

        mock_request.assert_called_once_with(
            "DescribeRecordList", {"Domain": "example.com", "RecordType": "A", "Subdomain": "www"}
        )

    @patch.object(TencentCloudProvider, "_request")
    def test_query_record_not_found(self, mock_request):
        """Test record query when record not found"""
        mock_request.return_value = {"RecordList": []}

        record = self.provider._query_record("example.com", "www", "example.com", "A")

        self.assertIsNone(record)

    @patch.object(TencentCloudProvider, "_request")
    def test_query_record_root_domain(self, mock_request):
        """Test record query for root domain (@)"""
        mock_request.return_value = {
            "RecordList": [{"RecordId": 123456, "Name": "@", "Type": "A", "Value": "1.2.3.4"}]
        }

        record = self.provider._query_record("example.com", "@", "example.com", "A")  # type: dict # type: ignore

        self.assertIsNotNone(record)
        self.assertEqual(record["Name"], "@")

    @patch.object(TencentCloudProvider, "_request")
    def test_create_record_success(self, mock_request):
        """Test successful record creation"""
        mock_request.return_value = {"RecordId": 789012}

        result = self.provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", ttl=600)

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            "CreateRecord",
            {
                "Domain": "example.com",
                "RecordType": "A",
                "RecordLine": "默认",
                "Value": "1.2.3.4",
                "SubDomain": "www",
                "TTL": 600,
                "Remark": self.provider.Remark,
            },
        )

    @patch.object(TencentCloudProvider, "_request")
    def test_create_record_root_domain(self, mock_request):
        """Test record creation for root domain"""
        mock_request.return_value = {"RecordId": 789012}

        result = self.provider._create_record("example.com", "@", "example.com", "1.2.3.4", "A")

        self.assertTrue(result)
        # Should not include SubDomain parameter for root domain
        call_args = mock_request.call_args[0][1]
        self.assertNotIn("SubDomain", call_args)

    @patch.object(TencentCloudProvider, "_request")
    def test_create_record_with_mx(self, mock_request):
        """Test record creation with MX priority"""
        mock_request.return_value = {"RecordId": 789012}

        result = self.provider._create_record(
            "example.com", "mail", "example.com", "mail.example.com", "MX", extra={"mx": 10}
        )

        self.assertTrue(result)
        call_args = mock_request.call_args[0][1]
        self.assertEqual(call_args["MX"], 10)

    @patch.object(TencentCloudProvider, "_request")
    def test_create_record_failure(self, mock_request):
        """Test record creation failure"""
        mock_request.return_value = None

        result = self.provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A")

        self.assertFalse(result)

    @patch.object(TencentCloudProvider, "_request")
    def test_update_record_success(self, mock_request):
        """Test successful record update"""
        mock_request.return_value = {"RecordId": 123456}

        old_record = {"RecordId": 123456, "Name": "www", "Type": "A", "Value": "1.2.3.4", "Line": "默认", "TTL": 300}

        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A", ttl=600)

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            "ModifyRecord",
            {
                "Domain": "example.com",
                "RecordId": 123456,
                "RecordType": "A",
                "RecordLine": "默认",
                "Value": "5.6.7.8",
                "SubDomain": "www",
                "TTL": 600,
                "Remark": self.provider.Remark,
            },
        )

    @patch.object(TencentCloudProvider, "_request")
    def test_update_record_preserve_old_values(self, mock_request):
        """Test record update preserves old values when not specified"""
        mock_request.return_value = {"RecordId": 123456}

        old_record = {
            "RecordId": 123456,
            "Name": "www",
            "Type": "A",
            "Value": "1.2.3.4",
            "Line": "电信",
            "TTL": 300,
            "MX": 10,
            "Weight": 5,
            "Remark": "Old remark",
        }

        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A")

        self.assertTrue(result)
        call_args = mock_request.call_args[0][1]
        self.assertEqual(call_args["RecordLine"], "电信")
        self.assertEqual(call_args["TTL"], 300)
        self.assertEqual(call_args["MX"], 10)
        self.assertEqual(call_args["Weight"], 5)
        self.assertEqual(call_args["Remark"], "Old remark")

    @patch.object(TencentCloudProvider, "_request")
    def test_update_record_missing_record_id(self, mock_request):
        """Test record update with missing RecordId"""
        old_record = {"Name": "www", "Type": "A"}

        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A")

        self.assertFalse(result)
        mock_request.assert_not_called()

    @patch.object(TencentCloudProvider, "_request")
    def test_update_record_failure(self, mock_request):
        """Test record update failure"""
        mock_request.return_value = None

        old_record = {"RecordId": 123456}

        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A")

        self.assertFalse(result)

    @patch.object(TencentCloudProvider, "now")
    @patch.object(TencentCloudProvider, "_http")
    def test_request_success(self, mock_http, mock_now):
        """Test successful API request"""
        # Mock self.now().timestamp() to return consistent timestamp
        mock_now.return_value.timestamp.return_value = 1609459200
        mock_http.return_value = {"Response": {"RecordId": 123456, "RequestId": "test-request-id"}}

        result = self.provider._request("CreateRecord", {"Domain": "example.com"})  # type: dict # type: ignore

        self.assertIsNotNone(result)
        self.assertEqual(result["RecordId"], 123456)
        mock_http.assert_called_once()

    @patch.object(TencentCloudProvider, "now")
    @patch.object(TencentCloudProvider, "_http")
    def test_request_api_error(self, mock_http, mock_now):
        """Test API request with error response"""
        mock_now.return_value.timestamp.return_value = 1609459200
        mock_http.return_value = {
            "Response": {"Error": {"Code": "InvalidParameter", "Message": "Invalid domain name"}}
        }

        result = self.provider._request("CreateRecord", {"Domain": "invalid"})

        self.assertIsNone(result)

    @patch.object(TencentCloudProvider, "now")
    @patch.object(TencentCloudProvider, "_http")
    def test_request_unexpected_response(self, mock_http, mock_now):
        """Test API request with unexpected response format"""
        mock_now.return_value.timestamp.return_value = 1609459200
        mock_http.return_value = {"UnexpectedField": "value"}

        result = self.provider._request("CreateRecord", {"Domain": "example.com"})

        self.assertIsNone(result)

    @patch.object(TencentCloudProvider, "now")
    @patch.object(TencentCloudProvider, "_http")
    def test_request_exception(self, mock_http, mock_now):
        """Test API request with exception"""
        mock_now.return_value.timestamp.return_value = 1609459200
        mock_http.side_effect = Exception("Network error")

        result = self.provider._request("CreateRecord", {"Domain": "example.com"})

        self.assertIsNone(result)

    @patch.object(TencentCloudProvider, "_query_record")
    @patch.object(TencentCloudProvider, "_create_record")
    @patch.object(TencentCloudProvider, "get_zone_id")
    def test_set_record_create_new(self, mock_get_zone_id, mock_create, mock_query):
        """Test set_record creating a new record"""
        mock_get_zone_id.return_value = "example.com"
        mock_query.return_value = None  # No existing record
        mock_create.return_value = True

        result = self.provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertTrue(result)
        mock_create.assert_called_once()

    @patch.object(TencentCloudProvider, "_query_record")
    @patch.object(TencentCloudProvider, "_update_record")
    @patch.object(TencentCloudProvider, "get_zone_id")
    def test_set_record_update_existing(self, mock_get_zone_id, mock_update, mock_query):
        """Test set_record updating an existing record"""
        mock_get_zone_id.return_value = "example.com"
        mock_query.return_value = {"RecordId": 123456}  # Existing record
        mock_update.return_value = True

        result = self.provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertTrue(result)
        mock_update.assert_called_once()

    def test_mask_sensitive_data(self):
        """Test sensitive data masking"""
        sensitive_data = "test_secret_key_12345"
        self.provider.auth_token = sensitive_data

        masked = self.provider._mask_sensitive_data("https://api.example.com?token=test_secret_key_12345")

        self.assertNotIn(sensitive_data, masked)
        self.assertIn("te***45", masked)

    def test_sign_tc3_date_format(self):
        """Test that the TC3 signature uses the correct service version date"""
        method = "POST"
        uri = "/"
        query = ""
        headers = {"Content-Type": "application/json", "Host": "dnspod.tencentcloudapi.com"}
        payload = "{}"
        timestamp = 1609459200  # 2021-01-01, but should use service version date

        authorization = self.provider._sign_tc3(method, uri, query, headers, payload, timestamp)

        # Check that the service version date (2021-03-23) is used in the credential scope
        self.assertIn("2021-03-23/dnspod/tc3_request", authorization)


class TestTencentCloudProviderIntegration(BaseProviderTestCase):
    """Integration tests for TencentCloudProvider"""

    def setUp(self):
        """Set up integration test fixtures"""
        super().setUp()

    @patch.object(TencentCloudProvider, "_request")
    def test_full_domain_resolution_flow(self, mock_request):
        """Test complete domain resolution flow"""
        provider = TencentCloudProvider(self.auth_id, self.auth_token)

        # Mock the record query to return no existing record
        mock_request.side_effect = [
            {"RecordList": []},  # No existing record found
            {"RecordId": 123456},  # Record created successfully
        ]

        result = provider.set_record("test.example.com", "1.2.3.4", "A", ttl=600)

        self.assertTrue(result)
        self.assertEqual(mock_request.call_count, 2)

        # Check that DescribeRecordList was called first
        first_call = mock_request.call_args_list[0]
        self.assertEqual(first_call[0][0], "DescribeRecordList")

        # Check that CreateRecord was called second
        second_call = mock_request.call_args_list[1]
        self.assertEqual(second_call[0][0], "CreateRecord")

    @patch.object(TencentCloudProvider, "_request")
    def test_custom_domain_format(self, mock_request):
        """Test custom domain format with ~ separator"""
        provider = TencentCloudProvider(self.auth_id, self.auth_token)

        mock_request.side_effect = [{"RecordList": []}, {"RecordId": 123456}]  # No existing record  # Record created

        result = provider.set_record("test~example.com", "1.2.3.4", "A")

        self.assertTrue(result)

        # Verify the domain was properly split
        create_call = mock_request.call_args_list[1]
        create_params = create_call[0][1]
        self.assertEqual(create_params["Domain"], "example.com")
        self.assertEqual(create_params["SubDomain"], "test")


if __name__ == "__main__":
    unittest.main()
