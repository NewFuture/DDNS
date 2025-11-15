# coding=utf-8
"""
Unit tests for EdgeOneDnsProvider
腾讯云 EdgeOne DNS 提供商单元测试 - 非加速域名管理

@author: NewFuture
"""

from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.edgeone_dns import EdgeOneDnsProvider


class TestEdgeOneDnsProvider(BaseProviderTestCase):
    """Test EdgeOneDnsProvider functionality"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestEdgeOneDnsProvider, self).setUp()
        self.provider = EdgeOneDnsProvider(self.id, self.token)
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
            EdgeOneDnsProvider("", self.token, self.logger)
        self.assertIn("id", str(context.exception))

    def test_validate_missing_token(self):
        """Test validation with missing token"""
        with self.assertRaises(ValueError) as context:
            EdgeOneDnsProvider(self.id, "", self.logger)
        self.assertIn("token", str(context.exception))

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_query_zone_id_success(self, mock_request):
        """Test successful zone ID query (inherited from EdgeOneProvider)"""
        domain = "example.com"
        expected_zone_id = "zone-123456789"

        mock_request.return_value = {
            "Zones": [{"ZoneId": expected_zone_id, "ZoneName": domain, "ActiveStatus": "active", "Status": "active"}]
        }

        zone_id = self.provider._query_zone_id(domain)
        self.assertEqual(zone_id, expected_zone_id)

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_query_zone_id_not_found(self, mock_request):
        """Test zone ID query when domain not found"""
        mock_request.return_value = {"Zones": []}

        zone_id = self.provider._query_zone_id("nonexistent.com")
        self.assertIsNone(zone_id)

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_query_record_found(self, mock_request):
        """Test successful DNS record query"""
        mock_request.return_value = {
            "DnsRecords": [
                {
                    "RecordId": "record-123456789",
                    "Name": "www.example.com",
                    "Type": "A",
                    "Content": "1.2.3.4",
                    "Status": "active",
                    "TTL": 600,
                }
            ]
        }

        record = self.provider._query_record("zone-123456789", "www", "example.com", "A", None, {})

        self.assertIsNotNone(record)
        if record:  # Type narrowing for mypy
            self.assertEqual(record["RecordId"], "record-123456789")
            self.assertEqual(record["Name"], "www.example.com")
            self.assertEqual(record["Type"], "A")
            self.assertEqual(record["Content"], "1.2.3.4")

        # Verify request call was made correctly
        mock_request.assert_called_once()

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_query_record_not_found(self, mock_request):
        """Test DNS record query when record not found"""
        mock_request.return_value = {"DnsRecords": []}

        record = self.provider._query_record("zone-123456789", "www", "example.com", "A", None, {})

        self.assertIsNone(record)

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_query_record_wrong_type(self, mock_request):
        """Test DNS record query with mismatched record type"""
        mock_request.return_value = {
            "DnsRecords": [
                {
                    "RecordId": "record-123456789",
                    "Name": "www.example.com",
                    "Type": "AAAA",
                    "Content": "::1",
                    "Status": "active",
                }
            ]
        }

        # Query for A record, but only AAAA exists
        record = self.provider._query_record("zone-123456789", "www", "example.com", "A", None, {})

        self.assertIsNone(record)

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_query_record_root_domain(self, mock_request):
        """Test DNS record query for root domain (@)"""
        mock_request.return_value = {
            "DnsRecords": [
                {
                    "RecordId": "record-123456789",
                    "Name": "example.com",
                    "Type": "A",
                    "Content": "1.2.3.4",
                    "Status": "active",
                }
            ]
        }

        record = self.provider._query_record("zone-123456789", "@", "example.com", "A", None, {})

        self.assertIsNotNone(record)
        self.assertEqual(record["Name"], "example.com")

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_create_record_success(self, mock_request):
        """Test successful DNS record creation"""
        mock_request.return_value = {"RequestId": "req-123456789"}

        result = self.provider._create_record("zone-123456789", "www", "example.com", "1.2.3.4", "A", 600, None, {})

        self.assertTrue(result)
        # Verify request call was made correctly
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "CreateDnsRecord")
        self.assertEqual(kwargs["ZoneId"], "zone-123456789")
        self.assertEqual(kwargs["Name"], "www.example.com")
        self.assertEqual(kwargs["Type"], "A")
        self.assertEqual(kwargs["Content"], "1.2.3.4")

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_create_record_root_domain(self, mock_request):
        """Test DNS record creation for root domain"""
        mock_request.return_value = {"RequestId": "req-123456789"}

        result = self.provider._create_record("zone-123456789", "@", "example.com", "1.2.3.4", "A", 300, None, {})

        self.assertTrue(result)
        # Verify domain name is correct for root
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs["Name"], "example.com")

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_create_record_aaaa(self, mock_request):
        """Test DNS record creation with AAAA record"""
        mock_request.return_value = {"RequestId": "req-123456789"}

        result = self.provider._create_record(
            "zone-123456789", "ipv6", "example.com", "2001:db8::1", "AAAA", 300, None, {}
        )

        self.assertTrue(result)
        # Verify parameters
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs["Type"], "AAAA")
        self.assertEqual(kwargs["Content"], "2001:db8::1")

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_create_record_failure(self, mock_request):
        """Test DNS record creation failure"""
        mock_request.return_value = None

        result = self.provider._create_record("zone-123456789", "www", "example.com", "1.2.3.4", "A", 300, None, {})

        self.assertFalse(result)

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_update_record_success(self, mock_request):
        """Test successful DNS record update"""
        mock_request.return_value = {"RequestId": "req-123456789"}

        old_record = {
            "RecordId": "record-123456789",
            "Name": "www.example.com",
            "Type": "A",
            "Content": "1.2.3.4",
            "Status": "active",
        }

        result = self.provider._update_record("zone-123456789", old_record, "5.6.7.8", "A", 600, None, {})

        self.assertTrue(result)
        # Verify request call was made
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "ModifyDnsRecords")
        self.assertEqual(kwargs["ZoneId"], "zone-123456789")
        # Verify the DnsRecords parameter contains the updated record
        self.assertIn("DnsRecords", kwargs)
        self.assertEqual(len(kwargs["DnsRecords"]), 1)
        updated_record = kwargs["DnsRecords"][0]
        self.assertEqual(updated_record["RecordId"], "record-123456789")
        self.assertEqual(updated_record["Content"], "5.6.7.8")

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_update_record_change_type(self, mock_request):
        """Test DNS record update with record type change"""
        mock_request.return_value = {"RequestId": "req-123456789"}

        old_record = {"RecordId": "record-123456789", "Name": "www.example.com", "Type": "A", "Content": "1.2.3.4"}

        result = self.provider._update_record("zone-123456789", old_record, "2001:db8::1", "AAAA", None, None, {})

        self.assertTrue(result)
        # Verify type is changed
        args, kwargs = mock_request.call_args
        updated_record = kwargs["DnsRecords"][0]
        self.assertEqual(updated_record["Type"], "AAAA")
        self.assertEqual(updated_record["Content"], "2001:db8::1")

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_update_record_failure(self, mock_request):
        """Test DNS record update failure"""
        mock_request.return_value = None  # API call failed

        old_record = {"RecordId": "record-123456789", "Name": "www.example.com", "Type": "A", "Content": "1.2.3.4"}

        result = self.provider._update_record("zone-123456789", old_record, "5.6.7.8", "A", None, None, {})

        self.assertFalse(result)

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_set_record_create_new(self, mock_request):
        """Test set_record creating a new DNS record"""
        # Mock HTTP responses for the workflow
        responses = [
            # DescribeZones response (get zone ID for main domain)
            {"Zones": [{"ZoneId": "zone-123456789", "ZoneName": "example.com"}]},
            # DescribeDnsRecords response (no existing DNS record for subdomain)
            {"DnsRecords": []},
            # CreateDnsRecord response (DNS record created successfully)
            {"RequestId": "req-123456789"},
        ]
        mock_request.side_effect = responses

        result = self.provider.set_record("www.example.com", "1.2.3.4", "A")

        self.assertTrue(result)
        self.assertEqual(mock_request.call_count, 3)  # Zone lookup, record query, and create calls

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_set_record_update_existing(self, mock_request):
        """Test set_record updating an existing DNS record"""
        # Mock HTTP responses for the workflow
        responses = [
            # DescribeZones response (get zone ID for main domain)
            {"Zones": [{"ZoneId": "zone-123456789", "ZoneName": "example.com"}]},
            # DescribeDnsRecords response (existing DNS record found)
            {
                "DnsRecords": [
                    {
                        "RecordId": "record-123456789",
                        "Name": "www.example.com",
                        "Type": "A",
                        "Content": "1.2.3.4",
                        "Status": "active",
                    }
                ]
            },
            # ModifyDnsRecords response (DNS record updated successfully)
            {"RequestId": "req-123456789"},
        ]
        mock_request.side_effect = responses

        result = self.provider.set_record("www.example.com", "5.6.7.8", "A")

        self.assertTrue(result)
        self.assertEqual(mock_request.call_count, 3)


class TestEdgeOneDnsProviderIntegration(BaseProviderTestCase):
    """Integration tests for EdgeOneDnsProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestEdgeOneDnsProviderIntegration, self).setUp()
        self.provider = EdgeOneDnsProvider(self.id, self.token)
        self.logger = self.mock_logger(self.provider)

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_full_domain_resolution_flow(self, mock_request):
        """Test complete domain resolution flow for creating new DNS records"""
        # Mock request responses for the workflow
        responses = [
            # DescribeZones response (get zone ID for main domain)
            {"Zones": [{"ZoneId": "zone-123456789", "ZoneName": "example.com"}]},
            # DescribeDnsRecords response (no existing DNS record for subdomain)
            {"DnsRecords": []},
            # CreateDnsRecord response (DNS record created successfully)
            {"RequestId": "req-123456789"},
        ]
        mock_request.side_effect = responses

        result = self.provider.set_record("test.example.com", "1.2.3.4", "A", ttl=600)

        self.assertTrue(result)
        self.assertEqual(mock_request.call_count, 3)  # Zone lookup, record query, and create calls

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_custom_domain_format(self, mock_request):
        """Test custom domain format with ~ separator (create new DNS record)"""
        # Mock request responses
        responses = [
            # DescribeZones response (get zone ID for main domain)
            {"Zones": [{"ZoneId": "zone-123456789", "ZoneName": "example.com"}]},
            # DescribeDnsRecords response (no existing DNS record for subdomain)
            {"DnsRecords": []},
            # CreateDnsRecord response (DNS record created successfully)
            {"RequestId": "req-123456789"},
        ]
        mock_request.side_effect = responses

        result = self.provider.set_record("test~example.com", "1.2.3.4", "A")

        self.assertTrue(result)
        # Zone lookup, record query, and create calls should be made
        self.assertEqual(mock_request.call_count, 3)

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_update_existing_record(self, mock_request):
        """Test updating an existing DNS record"""
        # Mock request responses for the workflow
        responses = [
            # DescribeZones response (get zone ID for main domain)
            {"Zones": [{"ZoneId": "zone-123456789", "ZoneName": "example.com"}]},
            # DescribeDnsRecords response (existing DNS record found)
            {
                "DnsRecords": [
                    {
                        "RecordId": "record-123456789",
                        "Name": "test.example.com",
                        "Type": "A",
                        "Content": "1.2.3.4",
                        "Status": "active",
                    }
                ]
            },
            # ModifyDnsRecords response (DNS record updated successfully)
            {"RequestId": "req-123456789"},
        ]
        mock_request.side_effect = responses

        result = self.provider.set_record("test.example.com", "5.6.7.8", "A", ttl=300)

        self.assertTrue(result)
        self.assertEqual(mock_request.call_count, 3)

        # Verify the ModifyDnsRecords call
        modify_call = mock_request.call_args_list[2]
        self.assertEqual(modify_call[0][0], "ModifyDnsRecords")

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_ipv6_record(self, mock_request):
        """Test creating IPv6 DNS record"""
        # Mock request responses
        responses = [
            # DescribeZones response
            {"Zones": [{"ZoneId": "zone-123456789", "ZoneName": "example.com"}]},
            # DescribeDnsRecords response (no existing record)
            {"DnsRecords": []},
            # CreateDnsRecord response
            {"RequestId": "req-123456789"},
        ]
        mock_request.side_effect = responses

        result = self.provider.set_record("ipv6.example.com", "2001:db8::1", "AAAA")

        self.assertTrue(result)
        # Verify the CreateDnsRecord call includes correct parameters
        create_call = mock_request.call_args_list[2]
        self.assertEqual(create_call[1]["Type"], "AAAA")
        self.assertEqual(create_call[1]["Content"], "2001:db8::1")

    @patch.object(EdgeOneDnsProvider, "_request")
    def test_api_error_handling(self, mock_request):
        """Test API error handling"""
        # Mock API error response - the _request method returns None on error
        mock_request.return_value = None

        # This should return False because zone_id cannot be resolved
        result = self.provider.set_record("test.example.com", "1.2.3.4", "A")
        self.assertFalse(result)
        # At least one call should be made to try to resolve zone ID
        self.assertGreater(mock_request.call_count, 0)


class TestEdgeOneDnsProviderRealRequest(BaseProviderTestCase):
    """EdgeOne DNS Provider 真实请求测试类"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestEdgeOneDnsProviderRealRequest, self).setUp()

    def test_auth_failure_real_request(self):
        """Test authentication failure with real API request"""
        # 使用无效的认证信息创建 provider
        invalid_provider = EdgeOneDnsProvider("invalid_id", "invalid_token")

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
        self.assertTrue(
            has_auth_error,
            "EdgeOne authentication error not found in logs. Logged messages: {0}".format(logged_messages),
        )


if __name__ == "__main__":
    unittest.main()
