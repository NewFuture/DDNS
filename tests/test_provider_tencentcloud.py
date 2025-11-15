# coding=utf-8
"""
Unit tests for TencentCloudProvider
腾讯云 DNSPod 提供商单元测试

@author: NewFuture
"""

from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.tencentcloud import TencentCloudProvider


class TestTencentCloudProvider(BaseProviderTestCase):
    """Test TencentCloudProvider functionality"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestTencentCloudProvider, self).setUp()
        self.provider = TencentCloudProvider(self.id, self.token)
        self.logger = self.mock_logger(self.provider)

    def test_init(self):
        """Test provider initialization"""
        self.assertProviderInitialized(self.provider)
        self.assertEqual(self.provider.service, "dnspod")
        self.assertEqual(self.provider.version_date, "2021-03-23")
        self.assertEqual(self.provider.endpoint, "https://dnspod.tencentcloudapi.com")
        self.assertEqual(self.provider.content_type, "application/json")

    def test_validate_success(self):
        """Test successful validation"""
        # Should not raise any exception
        self.provider._validate()

    def test_validate_missing_id(self):
        """Test validation with missing id"""
        with self.assertRaises(ValueError) as context:
            TencentCloudProvider("", self.token, self.logger)
        self.assertIn("id", str(context.exception))

    def test_validate_missing_token(self):
        """Test validation with missing token"""
        with self.assertRaises(ValueError) as context:
            TencentCloudProvider(self.id, "", self.logger)
        self.assertIn("token", str(context.exception))

    @patch.object(TencentCloudProvider, "_http")
    def test_query_zone_id_success(self, mock_http):
        """Test successful zone ID query"""
        domain = "example.com"
        expected_domain_id = 12345678

        mock_http.return_value = {
            "Response": {"DomainInfo": {"Domain": domain, "DomainId": expected_domain_id, "Status": "enable"}}
        }

        zone_id = self.provider._query_zone_id(domain)
        self.assertEqual(zone_id, str(expected_domain_id))

    @patch.object(TencentCloudProvider, "_http")
    def test_query_zone_id_not_found(self, mock_http):
        """Test zone ID query when domain not found"""
        domain = "nonexistent.com"

        mock_http.return_value = {
            "Response": {
                "Error": {"Code": "InvalidParameterValue.DomainNotExists", "Message": "当前域名有误，请返回重新操作。"}
            }
        }

        zone_id = self.provider._query_zone_id(domain)
        self.assertIsNone(zone_id)

    @patch.object(TencentCloudProvider, "_http")
    def test_query_zone_id_invalid_response(self, mock_http):
        """Test zone ID query with invalid response format"""
        domain = "example.com"

        mock_http.return_value = {"Response": {}}

        zone_id = self.provider._query_zone_id(domain)
        self.assertIsNone(zone_id)

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

        record = self.provider._query_record("12345678", "www", "example.com", "A", None, {})

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

        record = self.provider._query_record("12345678", "www", "example.com", "A", None, {})  # type: dict # type: ignore

        self.assertIsNone(record)

    @patch.object(TencentCloudProvider, "_http")
    def test_query_record_root_domain(self, mock_http):
        """Test record query for root domain (@)"""
        mock_http.return_value = {
            "Response": {"RecordList": [{"RecordId": 1234, "Name": "@", "Type": "A", "Value": "1.2.3.4"}]}
        }

        record = self.provider._query_record("1234", "@", "example.com", "A", None, {})  # type: dict # type: ignore

        self.assertIsNotNone(record)
        self.assertEqual(record["Name"], "@")

    @patch.object(TencentCloudProvider, "_http")
    def test_create_record_success(self, mock_http):
        """Test successful record creation"""
        mock_http.return_value = {"Response": {"RecordId": 789012}}

        result = self.provider._create_record("12345678", "www", "example.com", "1.2.3.4", "A", 600, None, {})

        self.assertTrue(result)
        # Verify HTTP call was made
        mock_http.assert_called_once()

    @patch.object(TencentCloudProvider, "_http")
    def test_create_record_root_domain(self, mock_http):
        """Test record creation for root domain"""
        mock_http.return_value = {"Response": {"RecordId": 789012}}

        result = self.provider._create_record("12345678", "@", "example.com", "1.2.3.4", "A", None, None, {})

        self.assertTrue(result)
        # Verify HTTP call was made
        mock_http.assert_called_once()

    @patch.object(TencentCloudProvider, "_http")
    def test_create_record_with_mx(self, mock_http):
        """Test record creation with MX priority"""
        mock_http.return_value = {"Response": {"RecordId": 789012}}

        result = self.provider._create_record(
            "12345678", "mail", "example.com", "mail.example.com", "MX", None, None, {"MX": 10}
        )

        self.assertTrue(result)
        # Verify HTTP call was made
        mock_http.assert_called_once()

    @patch.object(TencentCloudProvider, "_http")
    def test_create_record_failure(self, mock_http):
        """Test record creation failure"""
        mock_http.return_value = {"Response": {}}  # No RecordId in response

        result = self.provider._create_record("12345678", "www", "example.com", "1.2.3.4", "A", None, None, {})

        self.assertFalse(result)

    @patch.object(TencentCloudProvider, "_http")
    def test_update_record_success(self, mock_http):
        """Test successful record update"""
        mock_http.return_value = {"Response": {"RecordId": 123456}}

        old_record = {"RecordId": 123456, "Name": "www", "Type": "A", "Value": "1.2.3.4", "Line": "默认", "TTL": 300}

        result = self.provider._update_record("12345678", old_record, "5.6.7.8", "A", 600, None, {})

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

        result = self.provider._update_record("12345678", old_record, "5.6.7.8", "A", None, None, {})

        self.assertTrue(result)
        # Verify HTTP call was made
        mock_http.assert_called_once()

    @patch.object(TencentCloudProvider, "_http")
    def test_update_record_missing_record_id(self, mock_http):
        """Test record update with missing RecordId"""
        mock_http.return_value = {"Response": {}}  # No RecordId in response
        old_record = {"Name": "www", "Type": "A"}

        result = self.provider._update_record("12345678", old_record, "5.6.7.8", "A", None, None, {})

        self.assertFalse(result)  # Returns False because response doesn't contain RecordId
        mock_http.assert_called_once()  # Request is still made

    @patch.object(TencentCloudProvider, "_http")
    def test_update_record_failure(self, mock_http):
        """Test record update failure"""
        mock_http.return_value = {"Response": {}}  # No RecordId in response

        old_record = {"RecordId": 123456}

        result = self.provider._update_record("12345678", old_record, "5.6.7.8", "A", None, None, {})

        self.assertFalse(result)

    @patch.object(TencentCloudProvider, "_http")
    def test_update_record_extra_priority_over_old_record(self, mock_http):
        """Test that extra parameters take priority over old_record values"""
        import json

        mock_http.return_value = {"Response": {"RecordId": 123456}}

        old_record = {
            "RecordId": 123456,
            "Domain": "example.com",
            "DomainId": 12345678,
            "Name": "www",
            "Line": "默认",
            "Remark": "Old remark",
        }

        # extra should override old_record's Remark
        extra = {"Remark": "New remark from extra", "Status": "ENABLE"}
        result = self.provider._update_record("12345678", old_record, "5.6.7.8", "A", 600, "联通", extra)

        # Verify the call was made with correct parameters
        self.assertTrue(result)
        call_kwargs = mock_http.call_args[1]
        # extra["Remark"] should be set with priority
        body_dict = json.loads(call_kwargs["body"])  # Parse the JSON body
        self.assertEqual(body_dict["Remark"], "New remark from extra")
        self.assertEqual(body_dict["Status"], "ENABLE")

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
        mock_http.return_value = {"Response": {"Error": {"Code": "InvalidParameter", "Message": "Invalid domain name"}}}

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
            # DescribeDomain response (get domain ID)
            {"Response": {"DomainInfo": {"Domain": "example.com", "DomainId": 12345678}}},
            # DescribeRecordList response (no existing records)
            {"Response": {"RecordList": []}},
            # CreateRecord response (record created successfully)
            {"Response": {"RecordId": 123456}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertTrue(result)
        self.assertEqual(mock_http.call_count, 3)

    @patch.object(TencentCloudProvider, "_http")
    def test_set_record_update_existing(self, mock_http):
        """Test set_record updating an existing record"""
        # Mock HTTP responses for the workflow
        responses = [
            # DescribeDomain response (get domain ID)
            {"Response": {"DomainInfo": {"Domain": "example.com", "DomainId": 12345678}}},
            # DescribeRecordList response (existing record found)
            {
                "Response": {
                    "RecordList": [
                        {
                            "RecordId": 123456,
                            "Name": "www",
                            "Type": "A",
                            "Value": "1.2.3.4",
                            "DomainId": 12345678,
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
        self.assertEqual(mock_http.call_count, 3)

    def test_line_configuration_support(self):
        """Test that TencentCloudProvider supports line configuration"""
        with patch.object(self.provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": 123456}

            # Test create record with line parameter
            result = self.provider._create_record(12345678, "www", "example.com", "1.2.3.4", "A", 300, "电信", {})

            self.assertTrue(result)
            mock_request.assert_called_once_with(
                "CreateRecord",
                Domain="example.com",
                DomainId=12345678,
                SubDomain="www",
                RecordType="A",
                Value="1.2.3.4",
                RecordLine="电信",
                TTL=300,
                Remark="Managed by [DDNS](https://ddns.newfuture.cc)",
            )

    def test_update_record_with_line(self):
        """Test _update_record method with line parameter"""
        old_record = {"RecordId": 123456, "Name": "www", "Line": "默认", "Domain": "example.com", "DomainId": 12345678}

        with patch.object(self.provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": 123456}

            # Test with custom line parameter - note that TencentCloud uses old_record.Line when line parameter
            # doesn't override
            result = self.provider._update_record(12345678, old_record, "5.6.7.8", "A", 600, "联通", {})

            self.assertTrue(result)
            mock_request.assert_called_once_with(
                "ModifyRecord",
                Domain="example.com",
                DomainId=12345678,
                SubDomain="www",
                RecordId=123456,
                RecordType="A",
                RecordLine="默认",  # TencentCloud uses old_record line when available
                Value="5.6.7.8",
                TTL=600,
                Remark="Managed by [DDNS](https://ddns.newfuture.cc)",
            )


class TestTencentCloudProviderIntegration(BaseProviderTestCase):
    """Integration tests for TencentCloudProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestTencentCloudProviderIntegration, self).setUp()
        self.provider = TencentCloudProvider(self.id, self.token)
        self.logger = self.mock_logger(self.provider)

    @patch.object(TencentCloudProvider, "_http")
    def test_full_domain_resolution_flow(self, mock_http):
        """Test complete domain resolution flow"""
        # Mock HTTP responses for the workflow
        responses = [
            # DescribeDomain response (get domain ID)
            {"Response": {"DomainInfo": {"Domain": "example.com", "DomainId": 12345678}}},
            # DescribeRecordList response (no existing records)
            {"Response": {"RecordList": []}},
            # CreateRecord response (record created successfully)
            {"Response": {"RecordId": 123456}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("test.example.com", "1.2.3.4", "A", ttl=600)

        self.assertTrue(result)
        self.assertEqual(mock_http.call_count, 3)

        # Verify the CreateRecord call parameters
        create_call = mock_http.call_args_list[2]
        call_body = create_call[1]["body"]
        self.assertIn("DomainId", call_body)
        self.assertIn("CreateRecord", create_call[1]["headers"]["X-TC-Action"])

    @patch.object(TencentCloudProvider, "_http")
    def test_custom_domain_format(self, mock_http):
        """Test custom domain format with ~ separator"""
        # Mock HTTP responses
        responses = [
            # DescribeDomain response (get domain ID)
            {"Response": {"DomainInfo": {"Domain": "example.com", "DomainId": 12345678}}},
            # DescribeRecordList response (no existing records)
            {"Response": {"RecordList": []}},
            # CreateRecord response (record created successfully)
            {"Response": {"RecordId": 123456}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("test~example.com", "1.2.3.4", "A")

        self.assertTrue(result)

        # Verify the CreateRecord action was called
        create_call = mock_http.call_args_list[2]
        headers = create_call[1]["headers"]
        self.assertEqual(headers["X-TC-Action"], "CreateRecord")

        # Verify the body contains the right domain data
        call_body = create_call[1]["body"]
        self.assertIn("12345678", call_body)  # DomainId instead of domain name
        self.assertIn("test", call_body)

    @patch.object(TencentCloudProvider, "_http")
    def test_update_existing_record(self, mock_http):
        """Test updating an existing record"""
        # Mock HTTP responses for the workflow
        responses = [
            # DescribeDomain response (get domain ID)
            {"Response": {"DomainInfo": {"Domain": "example.com", "DomainId": 12345678}}},
            # DescribeRecordList response (existing record found)
            {
                "Response": {
                    "RecordList": [
                        {
                            "RecordId": 12345,
                            "Name": "test",
                            "Type": "A",
                            "Value": "1.2.3.4",
                            "DomainId": 12345678,
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
        self.assertEqual(mock_http.call_count, 3)

        # Verify the ModifyRecord call
        modify_call = mock_http.call_args_list[2]
        self.assertIn("ModifyRecord", modify_call[1]["headers"]["X-TC-Action"])

    @patch.object(TencentCloudProvider, "_http")
    def test_api_error_handling(self, mock_http):
        """Test API error handling"""
        # Mock API error response for DescribeDomain
        mock_http.return_value = {"Response": {"Error": {"Code": "InvalidParameter", "Message": "Invalid domain name"}}}

        # This should return False because zone_id cannot be resolved
        result = self.provider.set_record("test.example.com", "1.2.3.4", "A")
        self.assertFalse(result)
        # Two calls are made: split domain name first, then DescribeDomain for main domain
        self.assertGreater(mock_http.call_count, 0)


class TestTencentCloudProviderRealRequest(BaseProviderTestCase):
    """TencentCloud Provider 真实请求测试类"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestTencentCloudProviderRealRequest, self).setUp()

    def test_auth_failure_real_request(self):
        """Test authentication failure with real API request"""
        # 使用无效的认证信息创建 provider
        invalid_provider = TencentCloudProvider("invalid_id", "invalid_token")

        # Mock logger to capture error logs
        invalid_provider.logger = MagicMock()

        # 尝试查询域名信息，应该返回认证失败
        result = invalid_provider._query_zone_id("example.com")

        # 认证失败时应该返回 None (因为 API 会返回错误)
        self.assertIsNone(result)

        # 验证错误日志被记录
        # 应该有错误日志调用，因为 API 返回认证错误
        self.assertGreaterEqual(invalid_provider.logger.error.call_count, 1)

        # 检查日志内容包含认证相关的错误信息
        error_calls = invalid_provider.logger.error.call_args_list
        logged_messages = [str(call) for call in error_calls]

        # 至少有一个日志应该包含腾讯云 API 错误信息
        has_auth_error = any(
            "tencentcloud api error" in msg.lower() or "authfailure" in msg.lower() or "unauthorized" in msg.lower()
            for msg in logged_messages
        )
        self.assertTrue(
            has_auth_error, "Expected TencentCloud authentication error in logs: {0}".format(logged_messages)
        )


if __name__ == "__main__":
    unittest.main()
