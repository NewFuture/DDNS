# coding=utf-8
"""
EdgeOne provider 测试用例
@author: GitHub Copilot
"""
from base_test import BaseProviderTestCase, unittest, patch
from ddns.provider.edgeone import EdgeOneProvider


class TestEdgeOneProvider(BaseProviderTestCase):
    def setUp(self):
        super(TestEdgeOneProvider, self).setUp()
        self.provider = EdgeOneProvider(self.authid, self.token)
        self.mock_logger(self.provider)

    def test_init(self):
        """测试初始化"""
        self.assertProviderInitialized(self.provider)
        self.assertEqual(self.provider.endpoint, "https://teo.tencentcloudapi.com")
        self.assertEqual(self.provider.service, "teo")
        self.assertEqual(self.provider.version_date, "2022-09-01")

    @patch.object(EdgeOneProvider, "_http")
    def test_request_success(self, mock_http):
        """测试API请求成功"""
        mock_http.return_value = {"Response": {"test": "data"}}
        result = self.provider._request("TestAction", param1="value1")

        self.assertEqual(result, {"test": "data"})
        mock_http.assert_called_once()

        # 验证请求参数
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "POST")  # method
        self.assertEqual(args[1], "/")  # path
        self.assertIn("body", kwargs)
        self.assertIn("headers", kwargs)

        # 验证请求头
        headers = kwargs["headers"]
        self.assertIn("X-TC-Action", headers)
        self.assertIn("X-TC-Version", headers)
        self.assertIn("X-TC-Timestamp", headers)
        self.assertIn("authorization", headers)
        self.assertEqual(headers["X-TC-Action"], "TestAction")
        self.assertEqual(headers["X-TC-Version"], "2022-09-01")

    @patch.object(EdgeOneProvider, "_http")
    def test_request_error(self, mock_http):
        """测试API请求错误"""
        mock_http.return_value = {"Response": {"Error": {"Code": "InvalidParameter", "Message": "参数错误"}}}
        result = self.provider._request("TestAction")

        self.assertIsNone(result)
        self.provider.logger.error.assert_called_once()  # type: ignore[attr-defined]

    @patch.object(EdgeOneProvider, "_request")
    def test_query_zone_id_success(self, mock_request):
        """测试查询zone_id成功"""
        mock_request.return_value = {"Zones": [{"ZoneId": "zone-123456", "ZoneName": "example.com"}]}

        zone_id = self.provider._query_zone_id("example.com")

        self.assertEqual(zone_id, "zone-123456")
        mock_request.assert_called_once_with(
            "DescribeZones", Filters=[{"Name": "zone-name", "Values": ["example.com"]}]
        )

    @patch.object(EdgeOneProvider, "_request")
    def test_query_zone_id_not_found(self, mock_request):
        """测试查询zone_id失败"""
        mock_request.return_value = {"Zones": []}

        zone_id = self.provider._query_zone_id("notfound.com")

        self.assertIsNone(zone_id)

    @patch.object(EdgeOneProvider, "_request")
    def test_query_zone_id_no_response(self, mock_request):
        """测试查询zone_id无响应"""
        mock_request.return_value = None

        zone_id = self.provider._query_zone_id("example.com")

        self.assertIsNone(zone_id)

    @patch.object(EdgeOneProvider, "_request")
    def test_query_record_success(self, mock_request):
        """测试查询记录成功"""
        mock_request.return_value = {
            "Records": [{"RecordId": "rec-123456", "Name": "test.example.com", "Type": "A", "Content": "1.2.3.4"}]
        }

        record = self.provider._query_record("zone-123456", "test", "example.com", "A", None, {})

        self.assertIsNotNone(record)
        # Type assertion for mypy - we've already checked record is not None
        assert record is not None
        self.assertEqual(record["RecordId"], "rec-123456")
        self.assertEqual(record["Name"], "test.example.com")
        self.assertEqual(record["Type"], "A")

    @patch.object(EdgeOneProvider, "_request")
    def test_query_record_at_subdomain(self, mock_request):
        """测试查询@记录"""
        mock_request.return_value = {
            "Records": [{"RecordId": "rec-123456", "Name": "example.com", "Type": "A", "Content": "1.2.3.4"}]
        }

        record = self.provider._query_record("zone-123456", "@", "example.com", "A", None, {})

        self.assertIsNotNone(record)
        # 验证过滤器参数
        mock_request.assert_called_once_with(
            "DescribeRecords",
            ZoneId="zone-123456",
            Filters=[
                {"Name": "name", "Values": ["example.com"]},  # @ 应该转换为主域名
                {"Name": "type", "Values": ["A"]},
            ],
        )

    @patch.object(EdgeOneProvider, "_request")
    def test_query_record_not_found(self, mock_request):
        """测试查询记录未找到"""
        mock_request.return_value = {"Records": []}

        record = self.provider._query_record("zone-123456", "test", "example.com", "A", None, {})

        self.assertIsNone(record)

    @patch.object(EdgeOneProvider, "_request")
    def test_create_record_success(self, mock_request):
        """测试创建记录成功"""
        mock_request.return_value = {"RecordId": "rec-123456"}

        result = self.provider._create_record("zone-123456", "test", "example.com", "1.2.3.4", "A", 300, None, {})

        self.assertTrue(result)
        self.provider.logger.info.assert_called_with(  # type: ignore[attr-defined]
            "Record created successfully with ID: %s", "rec-123456"
        )

        # 验证请求参数
        mock_request.assert_called_once_with(
            "CreateRecord",
            ZoneId="zone-123456",
            Name="test.example.com",
            Type="A",
            Content="1.2.3.4",
            TTL=300,
            Comment="Managed by [DDNS](https://ddns.newfuture.cc)",
        )

    @patch.object(EdgeOneProvider, "_request")
    def test_create_record_at_subdomain(self, mock_request):
        """测试创建@记录"""
        mock_request.return_value = {"RecordId": "rec-123456"}

        result = self.provider._create_record("zone-123456", "@", "example.com", "1.2.3.4", "A", None, None, {})

        self.assertTrue(result)

        # 验证请求参数 - @ 应该转换为主域名
        mock_request.assert_called_once_with(
            "CreateRecord",
            ZoneId="zone-123456",
            Name="example.com",
            Type="A",
            Content="1.2.3.4",
            TTL=None,
            Comment="Managed by [DDNS](https://ddns.newfuture.cc)",
        )

    @patch.object(EdgeOneProvider, "_request")
    def test_create_record_with_custom_comment(self, mock_request):
        """测试创建记录带自定义备注"""
        mock_request.return_value = {"RecordId": "rec-123456"}

        result = self.provider._create_record(
            "zone-123456", "test", "example.com", "1.2.3.4", "A", None, None, {"Comment": "Custom comment"}
        )

        self.assertTrue(result)

        # 验证自定义备注被保留
        expected_call = mock_request.call_args[1]
        self.assertEqual(expected_call["Comment"], "Custom comment")

    @patch.object(EdgeOneProvider, "_request")
    def test_create_record_failure(self, mock_request):
        """测试创建记录失败"""
        mock_request.return_value = None

        result = self.provider._create_record("zone-123456", "test", "example.com", "1.2.3.4", "A", None, None, {})

        self.assertFalse(result)
        self.provider.logger.error.assert_called_once()  # type: ignore[attr-defined]

    @patch.object(EdgeOneProvider, "_request")
    def test_update_record_success(self, mock_request):
        """测试更新记录成功"""
        mock_request.return_value = {"RecordId": "rec-123456"}

        old_record = {"RecordId": "rec-123456", "Name": "test", "TTL": 600}

        result = self.provider._update_record("zone-123456", old_record, "5.6.7.8", "A", 300, None, {})

        self.assertTrue(result)
        self.provider.logger.info.assert_called_with("Record updated successfully")  # type: ignore[attr-defined]

        # 验证请求参数
        mock_request.assert_called_once_with(
            "ModifyRecord",
            ZoneId="zone-123456",
            RecordId="rec-123456",
            Name="test",
            Type="A",
            Content="5.6.7.8",
            TTL=300,
            Comment="Managed by [DDNS](https://ddns.newfuture.cc)",
        )

    @patch.object(EdgeOneProvider, "_request")
    def test_update_record_preserve_ttl(self, mock_request):
        """测试更新记录时保持原有TTL"""
        mock_request.return_value = {"RecordId": "rec-123456"}

        old_record = {"RecordId": "rec-123456", "Name": "test", "TTL": 600}

        result = self.provider._update_record("zone-123456", old_record, "5.6.7.8", "A", None, None, {})

        self.assertTrue(result)

        # 验证保持原有TTL
        expected_call = mock_request.call_args[1]
        self.assertEqual(expected_call["TTL"], 600)

    @patch.object(EdgeOneProvider, "_request")
    def test_update_record_default_ttl(self, mock_request):
        """测试更新记录时使用默认TTL"""
        mock_request.return_value = {"RecordId": "rec-123456"}

        old_record = {"RecordId": "rec-123456", "Name": "test"}

        result = self.provider._update_record("zone-123456", old_record, "5.6.7.8", "A", None, None, {})

        self.assertTrue(result)

        # 验证使用默认TTL (保持原有TTL = 300)
        expected_call = mock_request.call_args[1]
        self.assertEqual(expected_call["TTL"], 300)

    @patch.object(EdgeOneProvider, "_request")
    def test_update_record_failure(self, mock_request):
        """测试更新记录失败"""
        mock_request.return_value = None

        old_record = {"RecordId": "rec-123456", "Name": "test"}

        result = self.provider._update_record("zone-123456", old_record, "5.6.7.8", "A", None, None, {})

        self.assertFalse(result)
        self.provider.logger.error.assert_called_once()  # type: ignore[attr-defined]

    @patch.object(EdgeOneProvider, "_query_record")
    @patch.object(EdgeOneProvider, "_create_record")
    @patch.object(EdgeOneProvider, "get_zone_id")
    def test_set_record_create_new(self, mock_get_zone_id, mock_create_record, mock_query_record):
        """测试设置记录 - 创建新记录"""
        mock_get_zone_id.return_value = "zone-123456"
        mock_query_record.return_value = None  # 记录不存在
        mock_create_record.return_value = True

        result = self.provider.set_record("test.example.com", "1.2.3.4")

        self.assertTrue(result)
        mock_create_record.assert_called_once()
        mock_query_record.assert_called_once()

    @patch.object(EdgeOneProvider, "_query_record")
    @patch.object(EdgeOneProvider, "_update_record")
    @patch.object(EdgeOneProvider, "get_zone_id")
    def test_set_record_update_existing(self, mock_get_zone_id, mock_update_record, mock_query_record):
        """测试设置记录 - 更新现有记录"""
        mock_get_zone_id.return_value = "zone-123456"
        mock_query_record.return_value = {"RecordId": "rec-123456"}  # 记录存在
        mock_update_record.return_value = True

        result = self.provider.set_record("test.example.com", "1.2.3.4")

        self.assertTrue(result)
        mock_update_record.assert_called_once()
        mock_query_record.assert_called_once()

    @patch.object(EdgeOneProvider, "get_zone_id")
    def test_set_record_no_zone(self, mock_get_zone_id):
        """测试设置记录 - 找不到zone"""
        mock_get_zone_id.return_value = None

        result = self.provider.set_record("test.example.com", "1.2.3.4")

        self.assertFalse(result)

    def test_validate_credentials(self):
        """测试认证信息验证"""
        # 测试缺少ID
        with self.assertRaises(ValueError):
            EdgeOneProvider("", "token")

        # 测试缺少token
        with self.assertRaises(ValueError):
            EdgeOneProvider("id", "")


if __name__ == "__main__":
    unittest.main()
