# coding=utf-8
"""
DNSPod Provider 单元测试
支持 Python 2.7 和 Python 3
"""

from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.dnspod import DnspodProvider


class TestDnspodProvider(BaseProviderTestCase):
    """DNSPod Provider 测试类"""

    def setUp(self):
        """测试初始化"""
        super(TestDnspodProvider, self).setUp()
        self.provider = DnspodProvider(self.id, self.token)

    def test_init_with_basic_config(self):
        """Test DnspodProvider initialization with basic configuration"""
        provider = DnspodProvider(self.id, self.token)
        self.assertEqual(provider.id, self.id)
        self.assertEqual(provider.token, self.token)
        self.assertEqual(provider.endpoint, "https://dnsapi.cn")
        self.assertEqual(provider.DefaultLine, "默认")

    def test_class_constants(self):
        """Test DnspodProvider class constants"""
        self.assertEqual(DnspodProvider.endpoint, "https://dnsapi.cn")
        self.assertEqual(DnspodProvider.DefaultLine, "默认")
        # ContentType should be TYPE_FORM
        from ddns.provider._base import TYPE_FORM

        self.assertEqual(DnspodProvider.content_type, TYPE_FORM)

    @patch("ddns.provider.dnspod.DnspodProvider._http")
    def test_request_success(self, mock_http):
        """Test _request method with successful response"""
        mock_response = {"status": {"code": "1", "message": "Success"}, "data": {"test": "value"}}
        mock_http.return_value = mock_response

        result = self.provider._request("Test.Action", test_param="test_value")

        self.assertEqual(result, mock_response)
        mock_http.assert_called_once()

        # Verify request parameters
        call_args = mock_http.call_args
        self.assertEqual(call_args[0][0], "POST")  # Method
        self.assertEqual(call_args[0][1], "/Test.Action")  # URL

        # Verify body contains login token and format
        body = call_args[1]["body"]
        self.assertIn("login_token", body)
        expected_token = "{0},{1}".format(self.id, self.token)
        self.assertEqual(body["login_token"], expected_token)
        self.assertEqual(body["format"], "json")
        self.assertEqual(body["test_param"], "test_value")

    @patch("ddns.provider.dnspod.DnspodProvider._http")
    def test_request_failure(self, mock_http):
        """Test _request method with failed response"""
        mock_response = {"status": {"code": "0", "message": "API Error"}}
        mock_http.return_value = mock_response

        # Mock logger to capture warning
        self.provider.logger = MagicMock()

        result = self.provider._request("Test.Action")

        self.assertEqual(result, mock_response)
        self.provider.logger.warning.assert_called_once()

    @patch("ddns.provider.dnspod.DnspodProvider._http")
    def test_request_filters_none_params(self, mock_http):
        """Test _request method filters out None parameters"""
        mock_response = {"status": {"code": "1"}}
        mock_http.return_value = mock_response

        self.provider._request("Test.Action", param1="value1", param2=None, param3="value3")

        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["param1"], "value1")
        self.assertEqual(body["param3"], "value3")
        self.assertNotIn("param2", body)

    @patch("ddns.provider.dnspod.DnspodProvider._http")
    def test_request_with_extra_params(self, mock_http):
        """Test _request method with extra parameters"""
        mock_response = {"status": {"code": "1"}}
        mock_http.return_value = mock_response

        extra = {"extra_param": "extra_value"}
        self.provider._request("Test.Action", extra=extra, normal_param="normal_value")

        # Verify both extra and normal params are included
        body = mock_http.call_args[1]["body"]
        self.assertEqual(body["extra_param"], "extra_value")
        self.assertEqual(body["normal_param"], "normal_value")

    @patch("ddns.provider.dnspod.DnspodProvider._http")
    def test_query_zone_id_success(self, mock_http):
        """Test _query_zone_id method with successful response"""
        mock_http.return_value = {"domain": {"id": "12345", "name": "example.com"}}

        zone_id = self.provider._query_zone_id("example.com")

        self.assertEqual(zone_id, "12345")
        mock_http.assert_called_once()
        # Verify the action was correct
        call_args = mock_http.call_args
        self.assertEqual(call_args[0][1], "/Domain.Info")

    @patch("ddns.provider.dnspod.DnspodProvider._http")
    def test_query_zone_id_not_found(self, mock_http):
        """Test _query_zone_id method when domain is not found"""
        mock_http.return_value = {}

        zone_id = self.provider._query_zone_id("notfound.com")

        self.assertIsNone(zone_id)

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_query_record_success_single(self, mock_request):
        """Test _query_record method with single record found"""
        mock_request.return_value = {"records": [{"id": "123", "name": "www", "value": "192.168.1.1", "type": "A"}]}

        record = self.provider._query_record("zone123", "www", "example.com", "A", None, {})

        self.assertIsNotNone(record)
        if record:
            self.assertEqual(record["id"], "123")
            self.assertEqual(record["name"], "www")
        mock_request.assert_called_once_with(
            "Record.List", domain_id="zone123", sub_domain="www", record_type="A", line=None
        )

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_query_record_success_multiple(self, mock_request):
        """Test _query_record method with multiple records found"""
        mock_request.return_value = {
            "records": [
                {"id": "123", "name": "www", "value": "192.168.1.1", "type": "A"},
                {"id": "124", "name": "ftp", "value": "192.168.1.2", "type": "A"},
            ]
        }

        # Mock logger
        self.provider.logger = MagicMock()

        record = self.provider._query_record("zone123", "www", "example.com", "A", None, {})

        self.assertIsNotNone(record)
        self.assertEqual(record["name"], "www")  # type: ignore[unreachable]
        # Should log warning for multiple records
        self.provider.logger.warning.assert_called_once()

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_query_record_not_found(self, mock_request):
        """Test _query_record method when no records found"""
        mock_request.return_value = {"records": []}

        # Mock logger
        self.provider.logger = MagicMock()

        record = self.provider._query_record("zone123", "notfound", "example.com", "A", None, {})

        self.assertIsNone(record)
        self.provider.logger.warning.assert_called_once()

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_create_record_success(self, mock_request):
        """Test _create_record method with successful creation"""
        mock_request.return_value = {"record": {"id": "12345", "name": "www", "value": "192.168.1.1"}}

        # Mock logger
        self.provider.logger = MagicMock()

        result = self.provider._create_record(
            "zone123", "www", "example.com", "192.168.1.1", "A", ttl=600, line="电信", extra={}
        )

        self.assertTrue(result)
        self.provider.logger.info.assert_called_once()
        mock_request.assert_called_once_with(
            "Record.Create",
            extra={},
            domain_id="zone123",
            sub_domain="www",
            value="192.168.1.1",
            record_type="A",
            record_line="电信",
            ttl=600,
        )

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_create_record_with_default_line(self, mock_request):
        """Test _create_record method with default line"""
        mock_request.return_value = {"record": {"id": "12345", "name": "www", "value": "192.168.1.1"}}

        result = self.provider._create_record("zone123", "www", "example.com", "192.168.1.1", "A", None, None, {})

        self.assertTrue(result)
        # Should use DefaultLine when line is not specified
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args["record_line"], "默认")

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_create_record_failure(self, mock_request):
        """Test _create_record method with failed creation"""
        mock_request.return_value = None

        # Mock logger
        self.provider.logger = MagicMock()

        result = self.provider._create_record("zone123", "www", "example.com", "192.168.1.1", "A", None, None, {})

        self.assertFalse(result)
        self.provider.logger.error.assert_called_once()

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_create_record_with_extra_params(self, mock_request):
        """Test _create_record method with extra parameters"""
        mock_request.return_value = {"record": {"id": "12345", "name": "www", "value": "192.168.1.1"}}

        extra = {"weight": 10}
        result = self.provider._create_record("zone123", "www", "example.com", "192.168.1.1", "A", None, None, extra)

        self.assertTrue(result)
        mock_request.assert_called_once_with(
            "Record.Create",
            extra=extra,
            domain_id="zone123",
            sub_domain="www",
            value="192.168.1.1",
            record_type="A",
            record_line="默认",
            ttl=None,
        )

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_update_record_success(self, mock_request):
        """Test _update_record method with successful update"""
        mock_request.return_value = {"record": {"id": "12345", "name": "www", "value": "192.168.1.2"}}

        old_record = {"id": "12345", "name": "www", "line": "电信"}

        # Mock logger
        self.provider.logger = MagicMock()

        result = self.provider._update_record("zone123", old_record, "192.168.1.2", "A", 300, None, {})

        self.assertTrue(result)
        self.provider.logger.debug.assert_called_once()
        mock_request.assert_called_once_with(
            "Record.Modify",
            domain_id="zone123",
            record_id="12345",
            sub_domain="www",
            record_type="A",
            value="192.168.1.2",
            record_line="电信",
            extra={},
        )

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_update_record_failure(self, mock_request):
        """Test _update_record method with failed update"""
        mock_request.return_value = None

        old_record = {"id": "12345", "name": "www"}

        # Mock logger
        self.provider.logger = MagicMock()

        result = self.provider._update_record("zone123", old_record, "192.168.1.2", "A", None, None, {})

        self.assertFalse(result)
        self.provider.logger.error.assert_called_once()

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_update_record_with_line_conversion(self, mock_request):
        """Test _update_record method with line conversion (Default -> default)"""
        mock_request.return_value = {"record": {"id": "12345", "name": "www", "value": "192.168.1.2"}}

        old_record = {"id": "12345", "name": "www", "line": "Default"}

        result = self.provider._update_record("zone123", old_record, "192.168.1.2", "A", None, None, {})

        self.assertTrue(result)
        # Should convert "Default" to "default"
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args["record_line"], "default")

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_update_record_with_fallback_line(self, mock_request):
        """Test _update_record method with fallback to default line"""
        mock_request.return_value = {"record": {"id": "12345", "name": "www", "value": "192.168.1.2"}}

        old_record = {"id": "12345", "name": "www"}  # No line specified

        result = self.provider._update_record("zone123", old_record, "192.168.1.2", "A", None, None, {})

        self.assertTrue(result)
        # Should use DefaultLine when old record has no line
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args["record_line"], "默认")

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_update_record_with_extra_params(self, mock_request):
        """Test _update_record method with extra parameters"""
        mock_request.return_value = {"record": {"id": "12345", "name": "www", "value": "192.168.1.2"}}

        old_record = {"id": "12345", "name": "www", "line": "电信"}
        extra = {"weight": 20}

        result = self.provider._update_record("zone123", old_record, "192.168.1.2", "A", None, None, extra)

        self.assertTrue(result)
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args["extra"], extra)

    @patch("ddns.provider.dnspod.DnspodProvider._request")
    def test_update_record_extra_priority_over_old_record(self, mock_request):
        """Test that extra parameters take priority over old_record values"""
        mock_request.return_value = {"record": {"id": "12345", "name": "www", "value": "192.168.1.2"}}

        old_record = {"id": "12345", "name": "www", "line": "电信", "weight": 10}
        # extra should override old_record's weight
        extra = {"weight": 20, "mx": 5}

        result = self.provider._update_record("zone123", old_record, "192.168.1.2", "A", None, None, extra)

        self.assertTrue(result)
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args["extra"], extra)
        # Verify extra contains the new weight value
        self.assertEqual(call_args["extra"]["weight"], 20)
        self.assertEqual(call_args["extra"]["mx"], 5)

    def test_request_with_none_response(self):
        """Test _request method when HTTP returns None"""
        with patch("ddns.provider.dnspod.DnspodProvider._http") as mock_http:
            mock_http.return_value = None
            self.provider.logger = MagicMock()

            # Should return None and log a warning
            result = self.provider._request("Test.Action")

            self.assertIsNone(result)
            # Verify warning was logged
            self.provider.logger.warning.assert_called_once()

    def test_create_record_with_no_record_in_response(self):
        """Test _create_record method when response has no record field"""
        with patch("ddns.provider.dnspod.DnspodProvider._request") as mock_request:
            mock_request.return_value = {"status": {"code": "1"}}  # No record field
            self.provider.logger = MagicMock()

            result = self.provider._create_record("zone123", "www", "example.com", "192.168.1.1", "A", None, None, {})

            self.assertFalse(result)
            self.provider.logger.error.assert_called_once()

    def test_update_record_with_no_record_in_response(self):
        """Test _update_record method when response has no record field"""
        with patch("ddns.provider.dnspod.DnspodProvider._request") as mock_request:
            mock_request.return_value = {"status": {"code": "1"}}  # No record field
            old_record = {"id": "12345", "name": "www"}
            self.provider.logger = MagicMock()

            result = self.provider._update_record("zone123", old_record, "192.168.1.2", "A", None, None, {})

            self.assertFalse(result)
            self.provider.logger.error.assert_called_once()

    def test_line_configuration_support(self):
        """Test that DnspodProvider supports line configuration"""
        with patch("ddns.provider.dnspod.DnspodProvider._request") as mock_request:
            mock_request.return_value = {"record": {"id": "12345", "name": "www", "value": "192.168.1.1"}}

            # Test create record with line parameter
            result = self.provider._create_record("zone123", "www", "example.com", "192.168.1.1", "A", 600, "电信", {})

            self.assertTrue(result)
            mock_request.assert_called_once_with(
                "Record.Create",
                extra={},
                domain_id="zone123",
                sub_domain="www",
                value="192.168.1.1",
                record_type="A",
                record_line="电信",
                ttl=600,
            )

    def test_update_record_with_custom_line(self):
        """Test _update_record method with custom line parameter"""
        with patch("ddns.provider.dnspod.DnspodProvider._request") as mock_request:
            mock_request.return_value = {"record": {"id": "12345", "name": "www", "value": "192.168.1.2"}}

            old_record = {"id": "12345", "name": "www", "line": "默认"}

            # Test with custom line parameter
            result = self.provider._update_record("zone123", old_record, "192.168.1.2", "A", 300, "联通", {})

            self.assertTrue(result)
            call_args = mock_request.call_args[1]
            self.assertEqual(call_args["record_line"], "联通")


class TestDnspodProviderIntegration(BaseProviderTestCase):
    """DNSPod Provider 集成测试类"""

    def setUp(self):
        """测试初始化"""
        super(TestDnspodProviderIntegration, self).setUp()
        self.provider = DnspodProvider(self.id, self.token)
        self.provider.logger = MagicMock()

    @patch("ddns.provider.dnspod.DnspodProvider._http")
    def test_full_workflow_create_record(self, mock_http):
        """Test complete workflow for creating a new record"""
        # Mock HTTP responses for the workflow
        responses = [
            # Domain.Info response
            {"status": {"code": "1"}, "domain": {"id": "zone123"}},
            # Record.List response (no existing records)
            {"status": {"code": "1"}, "records": []},
            # Record.Create response
            {"status": {"code": "1"}, "record": {"id": "rec123", "name": "www", "value": "192.168.1.1"}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("www.example.com", "192.168.1.1")

        self.assertTrue(result)
        self.assertEqual(mock_http.call_count, 3)

    @patch("ddns.provider.dnspod.DnspodProvider._http")
    def test_full_workflow_update_record(self, mock_http):
        """Test complete workflow for updating an existing record"""
        # Mock HTTP responses for the workflow
        responses = [
            # Domain.Info response
            {"status": {"code": "1"}, "domain": {"id": "zone123"}},
            # Record.List response (existing record found)
            {
                "status": {"code": "1"},
                "records": [{"id": "rec123", "name": "www", "value": "192.168.1.100", "line": "默认"}],
            },
            # Record.Modify response
            {"status": {"code": "1"}, "record": {"id": "rec123", "name": "www", "value": "192.168.1.1"}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("www.example.com", "192.168.1.1")

        self.assertTrue(result)
        self.assertEqual(mock_http.call_count, 3)

    @patch("ddns.provider.dnspod.DnspodProvider._http")
    def test_full_workflow_zone_not_found(self, mock_http):
        """Test complete workflow when zone is not found"""
        # Domain.Info response - no domain found
        mock_http.return_value = {"status": {"code": "0", "message": "Domain not found"}}

        # Should return False when zone not found
        result = self.provider.set_record("www.notfound.com", "192.168.1.1")
        self.assertFalse(result)

    @patch("ddns.provider.dnspod.DnspodProvider._http")
    def test_full_workflow_create_failure(self, mock_http):
        """Test complete workflow when record creation fails"""
        responses = [
            # Domain.Info response
            {"status": {"code": "1"}, "domain": {"id": "zone123"}},
            # Record.List response (no existing records)
            {"status": {"code": "1"}, "records": []},
            # Record.Create response (failure)
            {"status": {"code": "0", "message": "Create failed"}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("www.example.com", "192.168.1.1")

        self.assertFalse(result)
        self.assertEqual(mock_http.call_count, 3)

    @patch("ddns.provider.dnspod.DnspodProvider._http")
    def test_full_workflow_update_failure(self, mock_http):
        """Test complete workflow when record update fails"""
        responses = [
            # Domain.Info response
            {"status": {"code": "1"}, "domain": {"id": "zone123"}},
            # Record.List response (existing record found)
            {
                "status": {"code": "1"},
                "records": [{"id": "rec123", "name": "www", "value": "192.168.1.100", "line": "默认"}],
            },
            # Record.Modify response (failure)
            {"status": {"code": "0", "message": "Update failed"}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("www.example.com", "192.168.1.1")

        self.assertFalse(result)
        self.assertEqual(mock_http.call_count, 3)

    @patch("ddns.provider.dnspod.DnspodProvider._http")
    def test_full_workflow_with_options(self, mock_http):
        """Test complete workflow with additional options like ttl and line"""
        responses = [
            # Domain.Info response
            {"status": {"code": "1"}, "domain": {"id": "zone123"}},
            # Record.List response (no existing records)
            {"status": {"code": "1"}, "records": []},
            # Record.Create response
            {"status": {"code": "1"}, "record": {"id": "rec123", "name": "www", "value": "192.168.1.1"}},
        ]
        mock_http.side_effect = responses

        result = self.provider.set_record("www.example.com", "192.168.1.1", record_type="A", ttl=300, line="电信")

        self.assertTrue(result)
        self.assertEqual(mock_http.call_count, 3)

        # Verify the Record.Create call includes the custom options
        create_call = mock_http.call_args_list[2]
        body = create_call[1]["body"]
        self.assertEqual(body["ttl"], 300)
        self.assertEqual(body["record_line"], "电信")


class TestDnspodProviderRealRequest(BaseProviderTestCase):
    """DNSPod Provider 真实请求测试类"""

    def test_auth_failure_real_request(self):
        """Test authentication failure with real API request"""
        # 使用无效的认证信息创建 provider
        invalid_provider = DnspodProvider("invalid_id", "invalid_token")

        # 尝试查询域名信息，应该抛出认证失败异常
        with self.assertRaises(RuntimeError) as cm:
            invalid_provider._query_zone_id("example.com")

        # 验证异常信息包含认证失败 - 更新错误消息格式
        error_message = str(cm.exception)
        self.assertTrue(
            "认证失败" in error_message and "401" in error_message,
            "Expected authentication error message not found in: {}".format(error_message),
        )


if __name__ == "__main__":
    unittest.main()
