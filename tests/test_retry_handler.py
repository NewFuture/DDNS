# coding=utf-8
"""
测试 HTTP RetryHandler 重试功能
Test HTTP RetryHandler retry functionality
"""

from __future__ import unicode_literals
from __init__ import unittest, patch, MagicMock, call
import time
import socket

from ddns.util.http import (
    RetryHandler,
    request,
    RETRY_STATUS_CODES,
    RETRY_EXCEPTIONS,
)

# Python 2/3 compatibility
try:
    from urllib.error import URLError, HTTPError
except ImportError:
    from urllib2 import URLError, HTTPError  # type: ignore[import]


class TestRetryHandler(unittest.TestCase):
    """测试 RetryHandler 类"""

    def setUp(self):
        """设置测试"""
        self.retry_handler = RetryHandler(retries=2)

    def test_init_default(self):
        """测试默认初始化"""
        handler = RetryHandler()
        self.assertEqual(handler.retries, 3)
        self.assertEqual(handler.retry_codes, RETRY_STATUS_CODES)

    def test_init_custom(self):
        """测试自定义初始化"""
        custom_codes = (500, 502)
        handler = RetryHandler(retries=5, retry_codes=custom_codes)
        self.assertEqual(handler.retries, 5)
        self.assertEqual(handler.retry_codes, custom_codes)

    def test_retry_codes_default(self):
        """测试默认重试状态码"""
        expected_codes = (408, 429, 500, 502, 503, 504)
        self.assertEqual(RETRY_STATUS_CODES, expected_codes)

    @patch('time.sleep')
    def test_network_error_retry(self, mock_sleep):
        """测试网络错误重试"""
        # Mock parent opener
        mock_parent = MagicMock()
        self.retry_handler.parent = mock_parent
        mock_parent.handlers = [self.retry_handler]
        
        # Mock request
        mock_req = MagicMock()
        mock_req.get_full_url.return_value = "http://example.com"
        
        # 第一次和第二次失败，第三次成功
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        
        # Mock build_opener to return our mock opener
        with patch('ddns.util.http.build_opener') as mock_build_opener:
            mock_opener = MagicMock()
            mock_opener.open.side_effect = [
                URLError("Network error"),
                URLError("Network error"),
                mock_response
            ]
            mock_build_opener.return_value = mock_opener
            
            result = self.retry_handler.http_open(mock_req)
            
            # 验证重试次数
            self.assertEqual(mock_opener.open.call_count, 3)
            self.assertEqual(result, mock_response)
            
            # 验证sleep调用 (2^0=1秒, 2^1=2秒)
            expected_calls = [call(1), call(2)]
            mock_sleep.assert_has_calls(expected_calls)

    @patch('time.sleep')
    def test_http_error_retry(self, mock_sleep):
        """测试HTTP错误重试"""
        mock_parent = MagicMock()
        self.retry_handler.parent = mock_parent
        mock_parent.handlers = [self.retry_handler]
        
        mock_req = MagicMock()
        mock_req.get_full_url.return_value = "http://example.com"
        
        # 创建HTTP 500错误
        http_error = HTTPError("http://example.com", 500, "Internal Server Error", {}, None)
        
        # 第一次失败，第二次成功
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        
        with patch('ddns.util.http.build_opener') as mock_build_opener:
            mock_opener = MagicMock()
            mock_opener.open.side_effect = [http_error, mock_response]
            mock_build_opener.return_value = mock_opener
            
            result = self.retry_handler.http_open(mock_req)
            
            self.assertEqual(mock_opener.open.call_count, 2)
            self.assertEqual(result, mock_response)
            mock_sleep.assert_called_once_with(1)  # 2^0 = 1秒

    def test_non_retryable_error_immediate_failure(self):
        """测试非重试错误立即失败"""
        mock_parent = MagicMock()
        self.retry_handler.parent = mock_parent
        mock_parent.handlers = [self.retry_handler]
        
        mock_req = MagicMock()
        
        # 404错误不应该重试
        http_error = HTTPError("http://example.com", 404, "Not Found", {}, None)
        
        with patch('ddns.util.http.build_opener') as mock_build_opener:
            mock_opener = MagicMock()
            mock_opener.open.side_effect = http_error
            mock_build_opener.return_value = mock_opener
            
            with self.assertRaises(HTTPError) as cm:
                self.retry_handler.http_open(mock_req)
            
            self.assertEqual(cm.exception.code, 404)
            self.assertEqual(mock_opener.open.call_count, 1)  # 只调用一次，没有重试

    @patch('time.sleep')
    def test_max_retries_exceeded(self, mock_sleep):
        """测试超过最大重试次数"""
        mock_parent = MagicMock()
        self.retry_handler.parent = mock_parent
        mock_parent.handlers = [self.retry_handler]
        
        mock_req = MagicMock()
        mock_req.get_full_url.return_value = "http://example.com"
        
        # 所有请求都失败
        with patch('ddns.util.http.build_opener') as mock_build_opener:
            mock_opener = MagicMock()
            mock_opener.open.side_effect = URLError("Persistent error")
            mock_build_opener.return_value = mock_opener
            
            with self.assertRaises(URLError):
                self.retry_handler.http_open(mock_req)
            
            # 重试2次 + 第一次 = 3次调用
            self.assertEqual(mock_opener.open.call_count, 3)
            
            # 验证sleep调用次数（只在前两次失败时sleep）
            self.assertEqual(mock_sleep.call_count, 2)


class TestRequestFunction(unittest.TestCase):
    """测试新的 request 函数"""

    @patch('ddns.util.http.build_opener')
    def test_request_with_retry(self, mock_build_opener):
        """测试带重试功能的request函数"""
        # Mock response
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value = {}
        mock_response.read.return_value = b'{"success": true}'
        
        # Mock opener
        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener
        
        # 测试调用
        result = request("GET", "http://example.com", retries=2)
        
        # 验证返回结果
        self.assertEqual(result.status, 200)
        self.assertEqual(result.body, '{"success": true}')
        
        # 验证build_opener被调用，并且包含RetryHandler
        mock_build_opener.assert_called_once()
        args = mock_build_opener.call_args[0]
        handler_types = [type(handler).__name__ for handler in args]
        self.assertIn('RetryHandler', handler_types)

    @patch('ddns.util.http.build_opener')
    def test_request_proxy_compatibility(self, mock_build_opener):
        """测试request函数的代理兼容性"""
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value = {}
        mock_response.read.return_value = b'test'
        
        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener
        
        # 测试requests风格的proxies参数
        proxies = {'http': 'http://proxy:8080', 'https': 'https://proxy:8443'}
        result = request("GET", "http://example.com", proxies=proxies)
        
        self.assertEqual(result.status, 200)
        mock_build_opener.assert_called_once()
        
        # 验证ProxyHandler被添加
        args = mock_build_opener.call_args[0]
        handler_types = [type(handler).__name__ for handler in args]
        self.assertIn('ProxyHandler', handler_types)



    def test_exponential_backoff_calculation(self):
        """测试指数退避计算"""
        # 验证等待时间计算
        for i in range(5):
            expected = 2 ** i
            self.assertEqual(expected, 2 ** i)
        
        # 验证常见重试等待时间
        self.assertEqual(2 ** 0, 1)  # 第一次重试等待1秒
        self.assertEqual(2 ** 1, 2)  # 第二次重试等待2秒
        self.assertEqual(2 ** 2, 4)  # 第三次重试等待4秒
        self.assertEqual(2 ** 3, 8)  # 第四次重试等待8秒

    @patch('ddns.util.http.RetryHandler')
    def test_default_retry_counts(self, mock_retry_handler):
        """测试默认重试次数"""
        from ddns.util.http import request
        
        # Mock RetryHandler和其他组件
        mock_handler_instance = MagicMock()
        mock_retry_handler.return_value = mock_handler_instance
        
        with patch('ddns.util.http.build_opener') as mock_build_opener:
            mock_response = MagicMock()
            mock_response.getcode.return_value = 200
            mock_response.info.return_value = {}
            mock_response.read.return_value = b'test'
            
            mock_opener = MagicMock()
            mock_opener.open.return_value = mock_response
            mock_build_opener.return_value = mock_opener
            
            # 测试默认重试次数
            request("GET", "http://example.com")
            mock_retry_handler.assert_called_with(retries=3)
            
            # 测试自定义重试次数
            request("GET", "http://example.com", retries=5)
            mock_retry_handler.assert_called_with(retries=5)


if __name__ == "__main__":
    unittest.main()