# -*- coding:utf-8 -*-
"""
Tests for ddns.ip module
"""
from __init__ import unittest, patch, MagicMock
from ddns import ip
from ddns.util.http import HttpResponse


class TestIpModule(unittest.TestCase):
    """测试IP获取模块"""

    def setUp(self):
        """设置测试环境"""
        self.original_ssl_verify = ip.ssl_verify

    def tearDown(self):
        """清理测试环境"""
        ip.ssl_verify = self.original_ssl_verify

    @patch('ddns.ip.request')
    def test_public_v4_single_url_success(self, mock_request):
        """测试公网IPv4获取 - 单个URL成功"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.body = "1.2.3.4"
        mock_request.return_value = mock_response
        
        result = ip.public_v4("https://test.example.com/ip")
        
        self.assertEqual(result, "1.2.3.4")
        mock_request.assert_called_once_with("GET", "https://test.example.com/ip", verify=ip.ssl_verify, retries=2)

    @patch('ddns.ip.request')
    def test_public_v6_single_url_success(self, mock_request):
        """测试公网IPv6获取 - 单个URL成功"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.body = "2001:db8::1"
        mock_request.return_value = mock_response
        
        result = ip.public_v6("https://test.example.com/ipv6")
        
        self.assertEqual(result, "2001:db8::1")
        mock_request.assert_called_once_with("GET", "https://test.example.com/ipv6", verify=ip.ssl_verify, retries=2)

    @patch('ddns.ip.request')
    def test_public_v4_request_failure(self, mock_request):
        """测试公网IPv4获取 - 请求失败"""
        # 模拟请求异常
        mock_request.side_effect = Exception("Network error")
        
        result = ip.public_v4("https://test.example.com/ip")
        
        self.assertIsNone(result)
        mock_request.assert_called_once_with("GET", "https://test.example.com/ip", verify=ip.ssl_verify, retries=2)

    @patch('ddns.ip.request')
    def test_public_v4_invalid_response(self, mock_request):
        """测试公网IPv4获取 - 无效响应"""
        # 模拟无效响应
        mock_response = MagicMock()
        mock_response.body = "invalid response"
        mock_request.return_value = mock_response
        
        result = ip.public_v4("https://test.example.com/ip")
        
        self.assertIsNone(result)
        mock_request.assert_called_once_with("GET", "https://test.example.com/ip", verify=ip.ssl_verify, retries=2)

    @patch('ddns.ip.request')
    def test_public_v4_multiple_apis_first_success(self, mock_request):
        """测试公网IPv4获取 - 多个API第一个成功"""
        # 模拟第一个API成功
        mock_response = MagicMock()
        mock_response.body = "1.2.3.4"
        mock_request.return_value = mock_response
        
        result = ip.public_v4()  # 不提供URL，使用多API模式
        
        self.assertEqual(result, "1.2.3.4")
        # 应该只调用第一个API
        mock_request.assert_called_once_with("GET", ip.PUBLIC_IPV4_APIS[0], verify=ip.ssl_verify, retries=2)

    @patch('ddns.ip.request')
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
        
        result = ip.public_v4()  # 不提供URL，使用多API模式
        
        self.assertEqual(result, "1.2.3.4")
        # 应该调用前两个API
        self.assertEqual(mock_request.call_count, 2)
        mock_request.assert_any_call("GET", ip.PUBLIC_IPV4_APIS[0], verify=ip.ssl_verify, retries=2)
        mock_request.assert_any_call("GET", ip.PUBLIC_IPV4_APIS[1], verify=ip.ssl_verify, retries=2)

    @patch('ddns.ip.request')
    def test_public_v4_multiple_apis_all_fail(self, mock_request):
        """测试公网IPv4获取 - 多个API全部失败"""
        # 模拟所有API都失败
        mock_request.side_effect = Exception("All APIs failed")
        
        result = ip.public_v4()  # 不提供URL，使用多API模式
        
        self.assertIsNone(result)
        # 应该调用所有API
        self.assertEqual(mock_request.call_count, len(ip.PUBLIC_IPV4_APIS))

    @patch('ddns.ip.request')
    def test_public_v6_multiple_apis_first_success(self, mock_request):
        """测试公网IPv6获取 - 多个API第一个成功"""
        # 模拟第一个API成功
        mock_response = MagicMock()
        mock_response.body = "2001:db8::1"
        mock_request.return_value = mock_response
        
        result = ip.public_v6()  # 不提供URL，使用多API模式
        
        self.assertEqual(result, "2001:db8::1")
        # 应该只调用第一个API
        mock_request.assert_called_once_with("GET", ip.PUBLIC_IPV6_APIS[0], verify=ip.ssl_verify, retries=2)

    @patch('ddns.ip.request')
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
        
        result = ip.public_v6()  # 不提供URL，使用多API模式
        
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
            "https://ipv6.icanhazip.com",
        ]
        self.assertEqual(ip.PUBLIC_IPV6_APIS, expected_apis)


if __name__ == '__main__':
    unittest.main()