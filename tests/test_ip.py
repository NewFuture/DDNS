# -*- coding:utf-8 -*-
"""
Tests for ddns.ip module including integration tests
"""

from __init__ import unittest, patch, MagicMock
from ddns import ip
from ddns.__main__ import get_ip
from ddns.util.http import HttpResponse


class TestIpModule(unittest.TestCase):
    """测试IP获取模块"""

    def setUp(self):
        """设置测试环境"""
        self.original_ssl_verify = ip.ssl_verify

    def tearDown(self):
        """清理测试环境"""
        ip.ssl_verify = self.original_ssl_verify

    @patch("ddns.ip.request")
    def test_url_v4_success(self, mock_request):
        """测试自定义URL获取IPv4 - 成功"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.body = "1.2.3.4"
        mock_request.return_value = mock_response

        result = ip.public_v4("https://test.example.com/ip")

        self.assertEqual(result, "1.2.3.4")
        mock_request.assert_called_once_with("GET", "https://test.example.com/ip", verify=ip.ssl_verify, retries=2)

    @patch("ddns.ip.request")
    def test_url_v6_success(self, mock_request):
        """测试自定义URL获取IPv6 - 成功"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.body = "2001:db8::1"
        mock_request.return_value = mock_response

        result = ip.public_v6("https://test.example.com/ipv6")

        self.assertEqual(result, "2001:db8::1")
        mock_request.assert_called_once_with("GET", "https://test.example.com/ipv6", verify=ip.ssl_verify, retries=2)

    @patch("ddns.ip.request")
    def test_url_v4_request_failure(self, mock_request):
        """测试自定义URL获取IPv4 - 请求失败"""
        # 模拟请求异常
        mock_request.side_effect = Exception("Network error")

        result = ip.public_v4("https://test.example.com/ip")

        self.assertIsNone(result)
        mock_request.assert_called_once_with("GET", "https://test.example.com/ip", verify=ip.ssl_verify, retries=2)

    @patch("ddns.ip.request")
    def test_url_v4_invalid_response(self, mock_request):
        """测试自定义URL获取IPv4 - 无效响应"""
        # 模拟无效响应
        mock_response = MagicMock()
        mock_response.body = "invalid response"
        mock_request.return_value = mock_response

        result = ip.public_v4("https://test.example.com/ip")

        self.assertIsNone(result)
        mock_request.assert_called_once_with("GET", "https://test.example.com/ip", verify=ip.ssl_verify, retries=2)

    @patch("ddns.ip.request")
    def test_public_v4_multiple_apis_first_success(self, mock_request):
        """测试公网IPv4获取 - 多个API第一个成功"""
        # 模拟第一个API成功
        mock_response = MagicMock()
        mock_response.body = "1.2.3.4"
        mock_request.return_value = mock_response

        result = ip.public_v4()

        self.assertEqual(result, "1.2.3.4")
        # 应该只调用第一个API
        mock_request.assert_called_once_with("GET", ip.PUBLIC_IPV4_APIS[0], verify=ip.ssl_verify, retries=2)

    @patch("ddns.ip.request")
    def test_public_v4_multiple_apis_fallback_success(self, mock_request):
        """测试公网IPv4获取 - 多个API第一个失败第二个成功"""

        def mock_request_side_effect(method, url, **kwargs):
            if url == ip.PUBLIC_IPV4_APIS[0]:
                raise Exception("First API failed")
            else:
                mock_response = MagicMock()
                mock_response.body = "1.2.3.4"
                return mock_response

        mock_request.side_effect = mock_request_side_effect

        result = ip.public_v4()

        self.assertEqual(result, "1.2.3.4")
        # 应该调用前两个API
        self.assertEqual(mock_request.call_count, 2)
        mock_request.assert_any_call("GET", ip.PUBLIC_IPV4_APIS[0], verify=ip.ssl_verify, retries=2)
        mock_request.assert_any_call("GET", ip.PUBLIC_IPV4_APIS[1], verify=ip.ssl_verify, retries=2)

    @patch("ddns.ip.request")
    def test_public_v4_multiple_apis_all_fail(self, mock_request):
        """测试公网IPv4获取 - 多个API全部失败"""
        # 模拟所有API都失败
        mock_request.side_effect = Exception("All APIs failed")

        result = ip.public_v4()

        self.assertIsNone(result)
        # 应该调用所有API
        self.assertEqual(mock_request.call_count, len(ip.PUBLIC_IPV4_APIS))

    @patch("ddns.ip.request")
    def test_public_v6_multiple_apis_first_success(self, mock_request):
        """测试公网IPv6获取 - 多个API第一个成功"""
        # 模拟第一个API成功
        mock_response = MagicMock()
        mock_response.body = "2001:db8::1"
        mock_request.return_value = mock_response

        result = ip.public_v6()

        self.assertEqual(result, "2001:db8::1")
        # 应该只调用第一个API
        mock_request.assert_called_once_with("GET", ip.PUBLIC_IPV6_APIS[0], verify=ip.ssl_verify, retries=2)

    @patch("ddns.ip.request")
    def test_public_v6_multiple_apis_fallback_success(self, mock_request):
        """测试公网IPv6获取 - 多个API第一个失败第二个成功"""

        def mock_request_side_effect(method, url, **kwargs):
            if url == ip.PUBLIC_IPV6_APIS[0]:
                raise Exception("First API failed")
            else:
                mock_response = MagicMock()
                mock_response.body = "2001:db8::1"
                return mock_response

        mock_request.side_effect = mock_request_side_effect

        result = ip.public_v6()

        self.assertEqual(result, "2001:db8::1")
        # 应该调用前两个API
        self.assertEqual(mock_request.call_count, 2)
        mock_request.assert_any_call("GET", ip.PUBLIC_IPV6_APIS[0], verify=ip.ssl_verify, retries=2)
        mock_request.assert_any_call("GET", ip.PUBLIC_IPV6_APIS[1], verify=ip.ssl_verify, retries=2)

    def test_public_ipv4_apis_list_exists(self):
        """测试IPv4 API列表存在并包含所需的API"""
        expected_apis = [
            "https://api.ipify.cn",
            "https://api.ipify.org",
            "https://4.ipw.cn/",
            "https://ipinfo.io/ip",
            "https://api-ipv4.ip.sb/ip",
            "http://checkip.amazonaws.com",
        ]
        self.assertEqual(ip.PUBLIC_IPV4_APIS, expected_apis)

    def test_public_ipv6_apis_list_exists(self):
        """测试IPv6 API列表存在并包含所需的API"""
        expected_apis = [
            "https://api6.ipify.org/",
            "https://6.ipw.cn/",
            "https://api-ipv6.ip.sb/ip",
            "http://ipv6.icanhazip.com",
        ]
        self.assertEqual(ip.PUBLIC_IPV6_APIS, expected_apis)

    @patch("ddns.ip.request")
    def test_get_ip_public_mode_fallback(self, mock_request):
        """测试通过get_ip使用public模式的自动fallback功能"""

        # 模拟第一个API失败，第二个成功
        def mock_request_side_effect(method, url, **kwargs):
            if "api.ipify.cn" in url:
                raise Exception("First API failed")
            elif "api.ipify.org" in url:
                mock_response = MagicMock()
                mock_response.body = "1.2.3.4"
                return mock_response
            else:
                raise Exception("Unexpected URL")

        mock_request.side_effect = mock_request_side_effect

        # 使用"public"规则获取IPv4地址
        result = get_ip("4", ["public"])

        self.assertEqual(result, "1.2.3.4")
        # 应该调用了前两个API
        self.assertEqual(mock_request.call_count, 2)

    @patch("ddns.ip.request")
    def test_get_ip_url_mode_backward_compatibility(self, mock_request):
        """测试通过get_ip使用url:模式的向后兼容性"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.body = "1.2.3.4"
        mock_request.return_value = mock_response

        # 使用"url:"规则获取IPv4地址
        result = get_ip("4", ["url:https://custom.api.com/ip"])

        self.assertEqual(result, "1.2.3.4")
        # 应该只调用指定的API
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(args[1], "https://custom.api.com/ip")

    @patch("ddns.ip.request")
    def test_get_ip_multiple_rules_limitation(self, mock_request):
        """测试get_ip的多规则限制 - 当前实现的限制"""
        # 注意：当前get_ip实现有限制 - 如果一个规则返回None，它不会尝试下一个规则
        # 只有当规则抛出异常时才会尝试下一个规则
        # 这是一个已知限制，不在本次功能实现范围内

        # 模拟所有public API都失败（返回无效响应）
        mock_response = MagicMock()
        mock_response.body = "invalid response"
        mock_request.return_value = mock_response

        # 使用多个规则：先尝试public，失败后应该尝试url:指定的API
        # 但由于当前实现限制，public返回None后不会尝试下一个规则
        result = get_ip("4", ["public", "url:https://backup.api.com/ip"])

        # 由于当前实现限制，返回None而不是继续尝试backup API
        self.assertIsNone(result)
        # 只调用了public APIs，没有调用backup API
        self.assertEqual(mock_request.call_count, len(ip.PUBLIC_IPV4_APIS))


if __name__ == "__main__":
    unittest.main()
