# coding=utf-8
"""
Unit tests for TencentCloudProvider
腾讯云 DNSPod 提供商单元测试

@author: NewFuture
"""

from base_test import BaseProviderTestCase, unittest, patch
from ddns.provider.tencentcloud import TencentCloudProvider


class TestTencentCloudProvider(BaseProviderTestCase):
    """Test TencentCloudProvider functionality"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestTencentCloudProvider, self).setUp()
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

    @patch.object(TencentCloudProvider, "_http")
    def test_query_record_found(self, mock_http):
        """Test successful record query"""
        mock_http.return_value = {
            "Response": {
                "RecordList": [
                    {"RecordId": 123456, "Name": "www", "Type": "A", "Value": "1.2.3.4", "Line": "默认", "TTL": 600}
                ]
            }
        }

        record = self.provider._query_record("example.com", "www", "example.com", "A", None, {})

        self.assertIsNotNone(record)
        if record:  # Type narrowing for mypy
            self.assertEqual(record["RecordId"], 123456)
            self.assertEqual(record["Name"], "www")
            self.assertEqual(record["Type"], "A")

        # Verify HTTP call was made correctly
        mock_http.assert_called_once()
        call_args = mock_http.call_args
        self.assertEqual(call_args[0][0], "POST")  # method
        self.assertEqual(call_args[0][1], "/")  # path

    @patch.object(TencentCloudProvider, "_http")
    def test_query_record_not_found(self, mock_http):
        """Test record query when record not found"""
        mock_http.return_value = {"Response": {"RecordList": []}}

        record = self.provider._query_record(
            "example.com", "www", "example.com", "A", None, {}
        )  # type: dict # type: ignore

        self.assertIsNone(record)

    @patch.object(TencentCloudProvider, "_http")
    def test_query_record_root_domain(self, mock_http):
        """Test record query for root domain (@)"""
        mock_http.return_value = {
            "Response": {"RecordList": [{"RecordId": 123456, "Name": "@", "Type": "A", "Value": "1.2.3.4"}]}
        }

        record = self.provider._query_record(
            "example.com", "@", "example.com", "A", None, {}
        )  # type: dict # type: ignore

        self.assertIsNotNone(record)
        self.assertEqual(record["Name"], "@")

    @patch.object(TencentCloudProvider, "_http")
    def test_create_record_success(self, mock_http):
        """Test successful record creation"""
        mock_http.return_value = {"Response": {"RecordId": 789012}}

        result = self.provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", 600, None, {})

        self.assertTrue(result)
        # Verify HTTP call was made
        mock_http.assert_called_once()

    @patch.object(TencentCloudProvider, "_http")
    def test_create_record_root_domain(self, mock_http):
        """Test record creation for root domain"""
        mock_http.return_value = {"Response": {"RecordId": 789012}}

        result = self.provider._create_record("example.com", "@", "example.com", "1.2.3.4", "A", None, None, {})

        self.assertTrue(result)
        # Verify HTTP call was made
        mock_http.assert_called_once()

    @patch.object(TencentCloudProvider, "_http")
    def test_create_record_with_mx(self, mock_http):
        """Test record creation with MX priority"""
        mock_http.return_value = {"Response": {"RecordId": 789012}}

        result = self.provider._create_record(
            "example.com", "mail", "example.com", "mail.example.com", "MX", None, None, {"MX": 10}
        )

        self.assertTrue(result)
        # Verify HTTP call was made
        mock_http.assert_called_once()

    @patch.object(TencentCloudProvider, "_http")
    def test_create_record_failure(self, mock_http):
        """Test record creation failure"""
        mock_http.return_value = {"Response": {}}  # No RecordId in response

        result = self.provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", None, None, {})

        self.assertFalse(result)

    @patch.object(TencentCloudProvider, "_http")
    def test_update_record_success(self, mock_http):
        """Test successful record update"""
        mock_http.return_value = {"Response": {"RecordId": 123456}}

        old_record = {"RecordId": 123456, "Name": "www", "Type": "A", "Value": "1.2.3.4", "Line": "默认", "TTL": 300}

        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, None, {})

        self.assertTrue(result)
        # Verify HTTP call was made
        mock_http.assert_called_once()

    @patch.object(TencentCloudProvider, "_http")
    def test_update_record_preserve_old_values(self, mock_http):
        """Test record update preserves old values when not specified"""
        mock_http.return_value = {"Response": {"RecordId": 123456}}

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

        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})

        self.assertTrue(result)
        # Verify HTTP call was made
        mock_http.assert_called_once()

    @patch.object(TencentCloudProvider, "_http")
    def test_update_record_missing_record_id(self, mock_http):
        """Test record update with missing RecordId"""
        mock_http.return_value = {"Response": {}}  # No RecordId in response
        old_record = {"Name": "www", "Type": "A"}

        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})

        self.assertFalse(result)  # Returns False because response doesn't contain RecordId
        mock_http.assert_called_once()  # Request is still made

    @patch.object(TencentCloudProvider, "_http")
    def test_update_record_failure(self, mock_http):
        """Test record update failure"""
        mock_http.return_value = {"Response": {}}  # No RecordId in response

        old_record = {"RecordId": 123456}

        result = self.provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})

        self.assertFalse(result)

    @patch("ddns.provider.tencentcloud.strftime")
    @patch("ddns.provider.tencentcloud.time")
    @patch.object(TencentCloudProvider, "_http")
    def test_request_success(self, mock_http, mock_time, mock_strftime):
        """Test successful API request"""
        # Mock time functions to get consistent results
        mock_time.return_value = 1609459200
        mock_strftime.return_value = "20210101"
        mock_http.return_value = {"Response": {"RecordId": 123456, "RequestId": "test-request-id"}}

        result = self.provider._request("DescribeRecordList", Domain="example.com")

        self.assertIsNotNone(result)
        if result:  # Type narrowing for mypy
            self.assertEqual(result["RecordId"], 123456)
        mock_http.assert_called_once()

    @patch("ddns.provider.tencentcloud.strftime")
    @patch("ddns.provider.tencentcloud.time")
    @patch.object(TencentCloudProvider, "_http")
    def test_request_api_error(self, mock_http, mock_time, mock_strftime):
        """Test API request with error response"""
        mock_time.return_value = 1609459200
        mock_strftime.return_value = "20210101"
        mock_http.return_value = {
            "Response": {"Error": {"Code": "InvalidParameter", "Message": "Invalid domain name"}}
        }

        result = self.provider._request("DescribeRecordList", Domain="invalid")

        self.assertIsNone(result)

    @patch("ddns.provider.tencentcloud.strftime")
    @patch("ddns.provider.tencentcloud.time")
    @patch.object(TencentCloudProvider, "_http")
    def test_request_unexpected_response(self, mock_http, mock_time, mock_strftime):
        """Test API request with unexpected response format"""
        mock_time.return_value = 1609459200
        mock_strftime.return_value = "20210101"
        mock_http.return_value = {"UnexpectedField": "value"}

        result = self.provider._request("DescribeRecordList", Domain="example.com")

        self.assertIsNone(result)

    @patch("ddns.provider.tencentcloud.strftime")
    @patch("ddns.provider.tencentcloud.time")
    @patch.object(TencentCloudProvider, "_http")
    def test_request_exception(self, mock_http, mock_time, mock_strftime):
        """Test API request with exception"""
        mock_time.return_value = 1609459200
        mock_strftime.return_value = "20210101"
        mock_http.side_effect = Exception("Network error")

        # The implementation doesn't catch exceptions, so it will propagate
        with self.assertRaises(Exception) as cm:
            self.provider._request("DescribeRecordList", Domain="example.com")

        self.assertEqual(str(cm.exception), "Network error")

    @patch.object(TencentCloudProvider, "_http")
    def test_set_record_create_new(self, mock_http):
        """Test set_record creating a new record"""
        # Mock HTTP responses for the workflow
        responses = [
            # DescribeRecordList response (no existing records)
            {"Response": {"RecordList": []}},
            # CreateRecord response (record created successfully)
            {"Response": {"RecordId": 123456}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertTrue(result)
        self.assertEqual(mock_http.call_count, 2)

    @patch.object(TencentCloudProvider, "_http")
    def test_set_record_update_existing(self, mock_http):
        """Test set_record updating an existing record"""
        # Mock HTTP responses for the workflow
        responses = [
            # DescribeRecordList response (existing record found)
            {
                "Response": {
                    "RecordList": [
                        {
                            "RecordId": 123456,
                            "Name": "www",
                            "Type": "A",
                            "Value": "1.2.3.4",
                            "DomainId": "example.com",
                            "Line": "默认",
                        }
                    ]
                }
            },
            # ModifyRecord response (record updated successfully)
            {"Response": {"RecordId": 123456}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("www.example.com", "5.6.7.8", "A")

        self.assertTrue(result)
        self.assertEqual(mock_http.call_count, 2)

    def test_mask_sensitive_data(self):
        """Test sensitive data masking"""
        sensitive_data = "test_secret_key_12345"
        self.provider.auth_token = sensitive_data

        masked = self.provider._mask_sensitive_data("https://api.example.com?token=test_secret_key_12345")

        self.assertNotIn(sensitive_data, masked)
        self.assertIn("te***45", masked)

    @patch("ddns.provider.tencentcloud.strftime")
    def test_sign_tc3_date_format(self, mock_strftime):
        """Test that the TC3 signature uses the current date in credential scope"""
        mock_strftime.return_value = "20210323"  # Mock strftime to return a specific date

        method = "POST"
        uri = "/"
        query = ""
        headers = {"content-type": "application/json", "host": "dnspod.tencentcloudapi.com"}
        payload = "{}"
        timestamp = 1609459200  # 2021-01-01

        authorization = self.provider._sign_tc3(method, uri, query, headers, payload, timestamp)

        # Check that the mocked date is used in the credential scope
        self.assertIn("20210323/dnspod/tc3_request", authorization)


class TestTencentCloudProviderIntegration(BaseProviderTestCase):
    """Integration tests for TencentCloudProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestTencentCloudProviderIntegration, self).setUp()
        self.provider = TencentCloudProvider(self.auth_id, self.auth_token)
        self.logger = self.mock_logger(self.provider)

    @patch.object(TencentCloudProvider, "_http")
    def test_full_domain_resolution_flow(self, mock_http):
        """Test complete domain resolution flow"""
        # Mock HTTP responses for the workflow
        responses = [
            # DescribeRecordList response (no existing records)
            {"Response": {"RecordList": []}},
            # CreateRecord response (record created successfully)
            {"Response": {"RecordId": 123456}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("test.example.com", "1.2.3.4", "A", ttl=600)

        self.assertTrue(result)
        self.assertEqual(mock_http.call_count, 2)

        # Verify the CreateRecord call parameters
        create_call = mock_http.call_args_list[1]
        call_body = create_call[1]["body"]
        self.assertIn("Domain", call_body)
        self.assertIn("CreateRecord", create_call[1]["headers"]["x-tc-action"])

    @patch.object(TencentCloudProvider, "_http")
    def test_custom_domain_format(self, mock_http):
        """Test custom domain format with ~ separator"""
        # Mock HTTP responses
        responses = [
            # DescribeRecordList response (no existing records)
            {"Response": {"RecordList": []}},
            # CreateRecord response (record created successfully)
            {"Response": {"RecordId": 123456}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("test~example.com", "1.2.3.4", "A")

        self.assertTrue(result)

        # Verify the CreateRecord action was called
        create_call = mock_http.call_args_list[1]
        headers = create_call[1]["headers"]
        self.assertEqual(headers["x-tc-action"], "CreateRecord")

        # Verify the body contains the right domain data
        call_body = create_call[1]["body"]
        self.assertIn("example.com", call_body)
        self.assertIn("test", call_body)

    @patch.object(TencentCloudProvider, "_http")
    def test_update_existing_record(self, mock_http):
        """Test updating an existing record"""
        # Mock HTTP responses for the workflow
        responses = [
            # DescribeRecordList response (existing record found)
            {
                "Response": {
                    "RecordList": [
                        {
                            "RecordId": 12345,
                            "Name": "test",
                            "Type": "A",
                            "Value": "1.2.3.4",
                            "DomainId": "example.com",
                            "Line": "默认",
                        }
                    ]
                }
            },
            # ModifyRecord response (record updated successfully)
            {"Response": {"RecordId": 12345}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("test.example.com", "5.6.7.8", "A", ttl=300)

        self.assertTrue(result)
        self.assertEqual(mock_http.call_count, 2)

        # Verify the ModifyRecord call
        modify_call = mock_http.call_args_list[1]
        self.assertIn("ModifyRecord", modify_call[1]["headers"]["x-tc-action"])

    @patch.object(TencentCloudProvider, "_http")
    def test_api_error_handling(self, mock_http):
        """Test API error handling"""
        # Mock API error response for both DescribeRecordList and CreateRecord
        mock_http.return_value = {
            "Response": {"Error": {"Code": "InvalidParameter", "Message": "Invalid domain name"}}
        }

        result = self.provider.set_record("test.example.com", "1.2.3.4", "A")

        self.assertFalse(result)
        # Two calls should be made: DescribeRecordList (fails, returns None),
        # then CreateRecord (also fails)
        self.assertEqual(mock_http.call_count, 2)


if __name__ == "__main__":
    unittest.main()
