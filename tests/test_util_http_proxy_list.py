# coding=utf-8
"""
测试 ddns.util.http 模块的代理列表功能
Test ddns.util.http module proxy list functionality
"""

from __init__ import unittest, patch, MagicMock
from ddns.util.http import request
import socket


class TestRequestProxyList(unittest.TestCase):
    """测试 request 函数的代理列表功能"""

    @patch('ddns.util.http.build_opener')
    @patch('ddns.util.http.Request')
    def test_request_with_single_proxy_in_list(self, mock_request, mock_build_opener):
        """测试单个代理的列表形式"""
        # 模拟响应
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value = {}
        mock_response.read.return_value = b'{"success": true}'
        mock_response.msg = "OK"

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener

        # 测试单个代理以列表形式传入
        result = request("GET", "http://example.com", proxies=["http://proxy:8080"])

        self.assertEqual(result.status, 200)
        self.assertEqual(result.body, '{"success": true}')
        mock_build_opener.assert_called_once()

    @patch('ddns.util.http.build_opener')
    @patch('ddns.util.http.Request')
    def test_request_with_proxy_list(self, mock_request, mock_build_opener):
        """测试代理列表功能"""
        # 模拟响应
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value = {}
        mock_response.read.return_value = b'{"success": true}'
        mock_response.msg = "OK"

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener

        # 测试代理列表
        proxy_list = ["http://proxy1:8080", "http://proxy2:8080", None]
        result = request("GET", "http://example.com", proxies=proxy_list)

        self.assertEqual(result.status, 200)
        self.assertEqual(result.body, '{"success": true}')
        mock_build_opener.assert_called_once()

    @patch('ddns.util.http.build_opener')
    @patch('ddns.util.http.Request')
    def test_request_with_direct_connection_only(self, mock_request, mock_build_opener):
        """测试仅直连（proxies=[None]）"""
        # 模拟响应
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value = {}
        mock_response.read.return_value = b'{"success": true}'
        mock_response.msg = "OK"

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener

        # 测试直连
        result = request("GET", "http://example.com", proxies=[None])

        self.assertEqual(result.status, 200)
        self.assertEqual(result.body, '{"success": true}')
        mock_build_opener.assert_called_once()

    @patch('ddns.util.http.build_opener')
    @patch('ddns.util.http.Request')
    def test_request_no_proxy_parameters(self, mock_request, mock_build_opener):
        """测试没有代理参数时默认使用直连"""
        # 模拟响应
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value = {}
        mock_response.read.return_value = b'{"success": true}'
        mock_response.msg = "OK"

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener

        # 测试没有代理参数
        result = request("GET", "http://example.com")

        self.assertEqual(result.status, 200)
        self.assertEqual(result.body, '{"success": true}')
        mock_build_opener.assert_called_once()

    @patch('ddns.util.http.build_opener')
    @patch('ddns.util.http.Request')
    def test_request_with_multiple_proxies(self, mock_request, mock_build_opener):
        """测试多个代理列表"""
        # 模拟响应
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value = {}
        mock_response.read.return_value = b'{"success": true}'
        mock_response.msg = "OK"

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener

        # 测试多个代理列表
        result = request("GET", "http://example.com",
                         proxies=["http://list-proxy1:8080", "http://list-proxy2:8080"])

        self.assertEqual(result.status, 200)
        self.assertEqual(result.body, '{"success": true}')
        mock_build_opener.assert_called_once()

    @patch('ddns.util.http.build_opener')
    @patch('ddns.util.http.Request')
    def test_request_with_empty_proxy_list(self, mock_request, mock_build_opener):
        """测试空代理列表时默认使用直连"""
        # 模拟响应
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value = {}
        mock_response.read.return_value = b'{"success": true}'
        mock_response.msg = "OK"

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener

        # 测试空代理列表
        result = request("GET", "http://example.com", proxies=[])

        self.assertEqual(result.status, 200)
        self.assertEqual(result.body, '{"success": true}')
        mock_build_opener.assert_called_once()

    @patch('ddns.util.http.build_opener')
    @patch('ddns.util.http.Request')
    def test_proxy_fallback_first_fails_second_succeeds(self, mock_request, mock_build_opener):
        """测试第一个代理失败，第二个代理成功的情况"""
        # 模拟响应
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value = {}
        mock_response.read.return_value = b'{"success": true}'
        mock_response.msg = "OK"

        # 第一次调用失败，第二次调用成功
        mock_opener_fail = MagicMock()
        mock_opener_fail.open.side_effect = Exception("Proxy connection failed")

        mock_opener_success = MagicMock()
        mock_opener_success.open.return_value = mock_response

        mock_build_opener.side_effect = [mock_opener_fail, mock_opener_success]

        # 测试代理失败回退
        proxy_list = ["http://proxy1:8080", "http://proxy2:8080"]
        result = request("GET", "http://example.com", proxies=proxy_list)

        self.assertEqual(result.status, 200)
        self.assertEqual(result.body, '{"success": true}')
        self.assertEqual(mock_build_opener.call_count, 2)  # 应该调用两次

    @patch('ddns.util.http.build_opener')
    @patch('ddns.util.http.Request')
    def test_proxy_fallback_all_fail(self, mock_request, mock_build_opener):
        """测试所有代理都失败的情况"""
        # 模拟所有请求都失败
        mock_opener = MagicMock()
        mock_opener.open.side_effect = Exception("Connection failed")
        mock_build_opener.return_value = mock_opener

        # 测试所有代理都失败
        proxy_list = ["http://proxy1:8080", "http://proxy2:8080"]

        with self.assertRaises(Exception) as context:
            request("GET", "http://example.com", proxies=proxy_list)

        self.assertIn("Connection failed", str(context.exception))
        self.assertEqual(mock_build_opener.call_count, 2)  # 应该尝试两次

    def test_real_network_proxy_fallback(self):
        """测试真实网络环境下的代理失败回退（如果网络可用）"""
        try:
            # 使用无效代理和直连的组合
            proxy_list = ["http://invalid-proxy:9999", None]

            # 这应该在第一个代理失败后回退到直连
            response = request("GET", "http://httpbin.org/get", proxies=proxy_list, retries=1)

            # 如果成功，应该是通过直连完成的
            self.assertEqual(response.status, 200)
            self.assertIn("httpbin.org", response.body)

        except Exception as e:
            # 网络问题时跳过测试
            error_msg = str(e).lower()
            network_keywords = ["timeout", "connection", "resolution", "unreachable", "network"]
            if any(keyword in error_msg for keyword in network_keywords):
                self.skipTest("Network unavailable for proxy fallback test: {}".format(str(e)))
            else:
                # 其他异常重新抛出
                raise


if __name__ == "__main__":
    unittest.main()
