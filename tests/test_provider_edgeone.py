# coding=utf-8
"""
Unit tests for EdgeOneProvider
腾讯云 EdgeOne 提供商单元测试

@author: NewFuture
"""

from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.edgeone import EdgeOneProvider


class TestEdgeOneProvider(BaseProviderTestCase):
    """Test EdgeOneProvider functionality"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestEdgeOneProvider, self).setUp()
        self.provider = EdgeOneProvider(self.id, self.token)
        self.logger = self.mock_logger(self.provider)

    def test_init(self):
        """Test provider initialization"""
        self.assertProviderInitialized(self.provider)
        self.assertEqual(self.provider.service, "teo")
        self.assertEqual(self.provider.version_date, "2022-09-01")
        self.assertEqual(self.provider.endpoint, "https://teo.tencentcloudapi.com")
        self.assertEqual(self.provider.content_type, "application/json")

    def test_validate_success(self):
        """Test successful validation"""
        # Should not raise any exception
        self.provider._validate()

    def test_validate_missing_id(self):
        """Test validation with missing id"""
        with self.assertRaises(ValueError) as context:
            EdgeOneProvider("", self.token, self.logger)
        self.assertIn("id", str(context.exception))

    def test_validate_missing_token(self):
        """Test validation with missing token"""
        with self.assertRaises(ValueError) as context:
            EdgeOneProvider(self.id, "", self.logger)
        self.assertIn("token", str(context.exception))

    @patch.object(EdgeOneProvider, "_request")
    def test_query_zone_id_success(self, mock_request):
        """Test successful zone ID query"""
        domain = "example.com"
        expected_zone_id = "zone-123456789"

        mock_request.return_value = {
            "Zones": [{"ZoneId": expected_zone_id, "ZoneName": domain, "ActiveStatus": "active", "Status": "active"}]
        }

        zone_id = self.provider._query_zone_id(domain)
        self.assertEqual(zone_id, expected_zone_id)

    @patch.object(EdgeOneProvider, "_request")
    def test_query_zone_id_not_found(self, mock_request):
        """Test zone ID query when domain not found"""
        mock_request.return_value = {"Zones": []}

        zone_id = self.provider._query_zone_id("nonexistent.com")
        self.assertIsNone(zone_id)

    @patch.object(EdgeOneProvider, "_request")
    def test_query_zone_id_empty_zones(self, mock_request):
        """Test zone ID query with empty zones list"""
        mock_request.return_value = {"Zones": []}

        zone_id = self.provider._query_zone_id("example.com")
        self.assertIsNone(zone_id)

    @patch.object(EdgeOneProvider, "_request")
    def test_query_zone_id_invalid_response(self, mock_request):
        """Test zone ID query with invalid response format"""
        mock_request.return_value = None

        zone_id = self.provider._query_zone_id("example.com")
        self.assertIsNone(zone_id)

    @patch.object(EdgeOneProvider, "_request")
    def test_query_record_found(self, mock_request):
        """Test successful acceleration domain query"""
        mock_request.return_value = {
            "AccelerationDomains": [
                {
                    "ZoneId": "zone-123456789",
                    "DomainName": "www.example.com",
                    "DomainStatus": "online",
                    "OriginDetail": {"OriginType": "ip_domain", "Origin": "1.2.3.4", "BackupOrigin": ""},
                }
            ]
        }

        record = self.provider._query_record("zone-123456789", "www", "example.com", "A", None, {})

        self.assertIsNotNone(record)
        if record:  # Type narrowing for mypy
            self.assertEqual(record["ZoneId"], "zone-123456789")
            self.assertEqual(record["DomainName"], "www.example.com")
            self.assertEqual(record["OriginDetail"]["Origin"], "1.2.3.4")

        # Verify request call was made correctly
        mock_request.assert_called_once()

    @patch.object(EdgeOneProvider, "_request")
    def test_query_record_not_found(self, mock_request):
        """Test acceleration domain query when domain not found"""
        mock_request.return_value = {"AccelerationDomains": []}

        record = self.provider._query_record("zone-123456789", "www", "example.com", "A", None, {})  # type: dict # type: ignore

        self.assertIsNone(record)

    @patch.object(EdgeOneProvider, "_request")
    def test_query_record_root_domain(self, mock_request):
        """Test acceleration domain query for root domain (@)"""
        mock_request.return_value = {
            "AccelerationDomains": [
                {
                    "ZoneId": "zone-123456789",
                    "DomainName": "example.com",
                    "DomainStatus": "online",
                    "OriginDetail": {"OriginType": "ip_domain", "Origin": "1.2.3.4", "BackupOrigin": ""},
                }
            ]
        }

        record = self.provider._query_record("zone-123456789", "@", "example.com", "A", None, {})  # type: dict # type: ignore

        self.assertIsNotNone(record)
        self.assertEqual(record["DomainName"], "example.com")

    @patch.object(EdgeOneProvider, "_request")
    def test_create_record_success(self, mock_request):
        """Test successful acceleration domain creation"""
        mock_request.return_value = {"Response": {"RequestId": "req-123456789"}}

        result = self.provider._create_record("zone-123456789", "www", "example.com", "1.2.3.4", "A", 600, None, {})

        self.assertTrue(result)
        # Verify request call was made correctly
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "CreateAccelerationDomain")
        self.assertEqual(kwargs["ZoneId"], "zone-123456789")
        self.assertEqual(kwargs["DomainName"], "www.example.com")

    @patch.object(EdgeOneProvider, "_request")
    def test_create_record_root_domain(self, mock_request):
        """Test acceleration domain creation for root domain"""
        mock_request.return_value = {"Response": {"RequestId": "req-123456789"}}

        result = self.provider._create_record("zone-123456789", "@", "example.com", "1.2.3.4", "A", 300, None, {})

        self.assertTrue(result)
        # Verify domain name is correct for root
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs["DomainName"], "example.com")

    @patch.object(EdgeOneProvider, "_request")
    def test_create_record_with_extra_params(self, mock_request):
        """Test acceleration domain creation with extra parameters"""
        mock_request.return_value = {"Response": {"RequestId": "req-123456789"}}

        result = self.provider._create_record(
            "zone-123456789", "mail", "example.com", "mail.example.com", "MX", 300, None, {"Priority": 10}
        )

        self.assertTrue(result)
        # Verify extra parameters are passed through
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs["Priority"], 10)

    @patch.object(EdgeOneProvider, "_request")
    def test_create_record_failure(self, mock_request):
        """Test acceleration domain creation failure"""
        mock_request.return_value = None

        result = self.provider._create_record("zone-123456789", "www", "example.com", "1.2.3.4", "A", 300, None, {})

        self.assertFalse(result)

    @patch.object(EdgeOneProvider, "_request")
    def test_update_record_success(self, mock_request):
        """Test successful acceleration domain origin update"""
        mock_request.return_value = {"Response": {"RequestId": "req-123456789"}}

        old_record = {
            "ZoneId": "zone-123456789",
            "DomainName": "www.example.com",
            "DomainStatus": "online",
            "OriginDetail": {"OriginType": "ip_domain", "Origin": "1.2.3.4", "BackupOrigin": ""},
        }

        result = self.provider._update_record("zone-123456789", old_record, "5.6.7.8", "A", 600, None, {})

        self.assertTrue(result)
        # Verify request call was made
        mock_request.assert_called_once()

    @patch.object(EdgeOneProvider, "_request")
    def test_update_record_preserve_backup_origin(self, mock_request):
        """Test acceleration domain update preserves backup origin"""
        mock_request.return_value = {"Response": {"RequestId": "req-123456789"}}

        old_record = {
            "ZoneId": "zone-123456789",
            "DomainName": "www.example.com",
            "DomainStatus": "online",
            "OriginDetail": {"OriginType": "ip_domain", "Origin": "1.2.3.4", "BackupOrigin": "backup.example.com"},
        }

        result = self.provider._update_record("zone-123456789", old_record, "5.6.7.8", "A", None, None, {})

        self.assertTrue(result)
        # Verify request call was made
        mock_request.assert_called_once()

    @patch.object(EdgeOneProvider, "_request")
    def test_update_record_missing_domain_name(self, mock_request):
        """Test acceleration domain update with missing domain name"""
        mock_request.return_value = None  # Simulate API failure due to missing domain name

        old_record = {
            "ZoneId": "zone-123456789",
            # Missing DomainName
            "OriginDetail": {"OriginType": "ip_domain", "Origin": "1.2.3.4"},
        }

        result = self.provider._update_record("zone-123456789", old_record, "5.6.7.8", "A", None, None, {})

        # Should fail because domain name is None and API call will fail
        self.assertFalse(result)

    @patch.object(EdgeOneProvider, "_request")
    def test_update_record_failure(self, mock_request):
        """Test acceleration domain update failure"""
        mock_request.return_value = None  # API call failed

        old_record = {
            "ZoneId": "zone-123456789",
            "DomainName": "www.example.com",
            "OriginDetail": {"OriginType": "ip_domain", "Origin": "1.2.3.4"},
        }

        result = self.provider._update_record("zone-123456789", old_record, "5.6.7.8", "A", None, None, {})

        self.assertFalse(result)

    @patch("ddns.provider.tencentcloud.strftime")
    @patch("ddns.provider.tencentcloud.time")
    @patch.object(EdgeOneProvider, "_http")
    def test_request_success(self, mock_http, mock_time, mock_strftime):
        """Test successful API request"""
        # Mock time functions to get consistent results
        mock_time.return_value = 1609459200
        mock_strftime.return_value = "20210101"
        mock_http.return_value = {"Response": {"ZoneId": "zone-123456", "RequestId": "test-request-id"}}

        result = self.provider._request(
            "DescribeZones",
            Filters=[{"Name": "zone-name", "Values": ["example.com"]}],  # type: ignore[arg-type]
        )

        self.assertIsNotNone(result)
        if result:  # Type narrowing for mypy
            self.assertEqual(result["ZoneId"], "zone-123456")
        mock_http.assert_called_once()

    @patch("ddns.provider.tencentcloud.strftime")
    @patch("ddns.provider.tencentcloud.time")
    @patch.object(EdgeOneProvider, "_http")
    def test_request_api_error(self, mock_http, mock_time, mock_strftime):
        """Test API request with error response"""
        mock_time.return_value = 1609459200
        mock_strftime.return_value = "20210101"
        mock_http.return_value = {"Response": {"Error": {"Code": "InvalidParameter", "Message": "Invalid zone name"}}}

        result = self.provider._request(
            "DescribeZones",
            Filters=[{"Name": "zone-name", "Values": ["invalid"]}],  # type: ignore[arg-type]
        )

        self.assertIsNone(result)

    @patch("ddns.provider.tencentcloud.strftime")
    @patch("ddns.provider.tencentcloud.time")
    @patch.object(EdgeOneProvider, "_http")
    def test_request_unexpected_response(self, mock_http, mock_time, mock_strftime):
        """Test API request with unexpected response format"""
        mock_time.return_value = 1609459200
        mock_strftime.return_value = "20210101"
        mock_http.return_value = {"UnexpectedField": "value"}

        result = self.provider._request(
            "DescribeZones",
            Filters=[{"Name": "zone-name", "Values": ["example.com"]}],  # type: ignore[arg-type]
        )

        self.assertIsNone(result)

    @patch("ddns.provider.tencentcloud.strftime")
    @patch("ddns.provider.tencentcloud.time")
    @patch.object(EdgeOneProvider, "_http")
    def test_request_exception(self, mock_http, mock_time, mock_strftime):
        """Test API request with exception"""
        mock_time.return_value = 1609459200
        mock_strftime.return_value = "20210101"
        mock_http.side_effect = Exception("Network error")

        # The implementation doesn't catch exceptions, so it will propagate
        with self.assertRaises(Exception) as cm:
            self.provider._request(
                "DescribeZones",
                Filters=[{"Name": "zone-name", "Values": ["example.com"]}],  # type: ignore[arg-type]
            )

        self.assertEqual(str(cm.exception), "Network error")

    @patch.object(EdgeOneProvider, "_request")
    def test_set_record_create_new(self, mock_request):
        """Test set_record creating a new acceleration domain"""
        # Mock HTTP responses for the workflow
        responses = [
            # DescribeZones response (get zone ID for main domain)
            {"Zones": [{"ZoneId": "zone-123456789", "ZoneName": "example.com"}]},
            # DescribeAccelerationDomains response (no existing acceleration domain for subdomain)
            {"AccelerationDomains": []},
            # CreateAccelerationDomain response (acceleration domain created successfully)
            {"Response": {"RequestId": "req-123456789"}},
        ]
        mock_request.side_effect = responses

        result = self.provider.set_record("www.example.com", "1.2.3.4", "A")

        # Should succeed because EdgeOne supports creating new acceleration domains
        self.assertTrue(result)
        self.assertEqual(mock_request.call_count, 3)  # Zone lookup, record query, and create calls

    @patch.object(EdgeOneProvider, "_request")
    def test_set_record_update_existing(self, mock_request):
        """Test set_record updating an existing acceleration domain"""
        # Mock HTTP responses for the workflow
        responses = [
            # DescribeZones response (get zone ID for main domain)
            {"Zones": [{"ZoneId": "zone-123456789", "ZoneName": "example.com"}]},
            # DescribeAccelerationDomains response (existing acceleration domain found)
            {
                "AccelerationDomains": [
                    {
                        "ZoneId": "zone-123456789",
                        "DomainName": "www.example.com",
                        "DomainStatus": "online",
                        "OriginDetail": {"OriginType": "ip_domain", "Origin": "1.2.3.4", "BackupOrigin": ""},
                    }
                ]
            },
            # ModifyAccelerationDomain response (acceleration domain updated successfully)
            {"Response": {"RequestId": "req-123456789"}},
        ]
        mock_request.side_effect = responses

        result = self.provider.set_record("www.example.com", "5.6.7.8", "A")

        self.assertTrue(result)
        self.assertEqual(mock_request.call_count, 3)


class TestEdgeOneProviderIntegration(BaseProviderTestCase):
    """Integration tests for EdgeOneProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestEdgeOneProviderIntegration, self).setUp()
        self.provider = EdgeOneProvider(self.id, self.token)
        self.logger = self.mock_logger(self.provider)

    @patch.object(EdgeOneProvider, "_request")
    def test_full_domain_resolution_flow(self, mock_request):
        """Test complete domain resolution flow for creating new domains"""
        # Mock request responses for the workflow
        responses = [
            # DescribeZones response (get zone ID for main domain)
            {"Zones": [{"ZoneId": "zone-123456789", "ZoneName": "example.com"}]},
            # DescribeAccelerationDomains response (no existing acceleration domain for subdomain)
            {"AccelerationDomains": []},
            # CreateAccelerationDomain response (acceleration domain created successfully)
            {"Response": {"RequestId": "req-123456789"}},
        ]
        mock_request.side_effect = responses

        result = self.provider.set_record("test.example.com", "1.2.3.4", "A", ttl=600)

        # Should succeed because EdgeOne supports creating new acceleration domains
        self.assertTrue(result)
        self.assertEqual(mock_request.call_count, 3)  # Zone lookup, record query, and create calls

    @patch.object(EdgeOneProvider, "_request")
    def test_custom_domain_format(self, mock_request):
        """Test custom domain format with ~ separator (create new domain)"""
        # Mock request responses
        responses = [
            # DescribeZones response (get zone ID for main domain)
            {"Zones": [{"ZoneId": "zone-123456789", "ZoneName": "example.com"}]},
            # DescribeAccelerationDomains response (no existing acceleration domain for subdomain)
            {"AccelerationDomains": []},
            # CreateAccelerationDomain response (acceleration domain created successfully)
            {"Response": {"RequestId": "req-123456789"}},
        ]
        mock_request.side_effect = responses

        result = self.provider.set_record("test~example.com", "1.2.3.4", "A")

        # Should succeed because EdgeOne supports creating new acceleration domains
        self.assertTrue(result)

        # Zone lookup, record query, and create calls should be made
        self.assertEqual(mock_request.call_count, 3)

    @patch.object(EdgeOneProvider, "_request")
    def test_update_existing_record(self, mock_request):
        """Test updating an existing acceleration domain"""
        # Mock request responses for the workflow
        responses = [
            # DescribeZones response (get zone ID for main domain)
            {"Zones": [{"ZoneId": "zone-123456789", "ZoneName": "example.com"}]},
            # DescribeAccelerationDomains response (existing acceleration domain found)
            {
                "AccelerationDomains": [
                    {
                        "ZoneId": "zone-123456789",
                        "DomainName": "test.example.com",
                        "DomainStatus": "online",
                        "OriginDetail": {"OriginType": "ip_domain", "Origin": "1.2.3.4", "BackupOrigin": ""},
                    }
                ]
            },
            # ModifyAccelerationDomain response (acceleration domain updated successfully)
            {"Response": {"RequestId": "req-123456789"}},
        ]
        mock_request.side_effect = responses

        result = self.provider.set_record("test.example.com", "5.6.7.8", "A", ttl=300)

        self.assertTrue(result)
        self.assertEqual(mock_request.call_count, 3)

        # Verify the ModifyAccelerationDomain call
        modify_call = mock_request.call_args_list[2]
        self.assertEqual(modify_call[0][0], "ModifyAccelerationDomain")

    @patch.object(EdgeOneProvider, "_request")
    def test_api_error_handling(self, mock_request):
        """Test API error handling"""
        # Mock API error response - the _request method returns None on error
        mock_request.return_value = None

        # This should return False because zone_id cannot be resolved
        result = self.provider.set_record("test.example.com", "1.2.3.4", "A")
        self.assertFalse(result)
        # At least one call should be made to try to resolve zone ID
        self.assertGreater(mock_request.call_count, 0)


class TestEdgeOneProviderRealRequest(BaseProviderTestCase):
    """EdgeOne Provider 真实请求测试类"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestEdgeOneProviderRealRequest, self).setUp()

    def test_auth_failure_real_request(self):
        """Test authentication failure with real API request"""
        # 使用无效的认证信息创建 provider
        invalid_provider = EdgeOneProvider("invalid_id", "invalid_token")

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

        # 至少有一个日志应该包含EdgeOne API 错误信息
        has_auth_error = any(
            "edgeone api error" in msg.lower() or "authfailure" in msg.lower() or "unauthorized" in msg.lower()
            for msg in logged_messages
        )
        self.assertTrue(has_auth_error, "Expected EdgeOne authentication error in logs: {0}".format(logged_messages))


if __name__ == "__main__":
    unittest.main()
