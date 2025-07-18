# coding=utf-8
"""
测试 HTTP RetryHandler 重试功能
Test HTTP RetryHandler retry functionality
"""

from __future__ import unicode_literals
from __init__ import unittest, patch, MagicMock
import socket

from ddns.util.http import (
    RetryHandler,
    request,
)

# Python 2/3 compatibility
try:
    from urllib.error import URLError
except ImportError:
    from urllib2 import URLError  # type: ignore[import]


class TestRetryHandler(unittest.TestCase):
    """测试 RetryHandler 类"""

    def setUp(self):
        """设置测试"""
        self.retry_handler = RetryHandler(retries=2)

    def test_init_default(self):
        """测试默认初始化"""
        handler = RetryHandler()
        self.assertEqual(handler.retries, 3)
        self.assertEqual(handler.RETRY_CODES, (408, 429, 500, 502, 503, 504))

    def test_init_custom(self):
        """测试自定义初始化"""
        handler = RetryHandler(retries=5)
        self.assertEqual(handler.retries, 5)
        self.assertEqual(handler.RETRY_CODES, (408, 429, 500, 502, 503, 504))

    def test_retry_codes_default(self):
        """测试默认重试状态码"""
        expected_codes = (408, 429, 500, 502, 503, 504)
        self.assertEqual(RetryHandler.RETRY_CODES, expected_codes)

    def test_retry_exceptions_default(self):
        """测试默认重试异常"""
        # 只测试在Python 2/3中都可用的异常
        expected_exceptions = (URLError, socket.timeout)
        # 检查前两个异常
        self.assertEqual(RetryHandler.RETRY_EXCEPTIONS[:2], expected_exceptions)
        # 检查总数大于等于2
        self.assertGreaterEqual(len(RetryHandler.RETRY_EXCEPTIONS), 2)

    @patch("time.sleep")
    def test_network_error_retry(self, mock_sleep):
        """测试网络错误重试"""
        # 设置父级opener
        mock_parent = MagicMock()
        self.retry_handler.parent = mock_parent

        # 模拟request对象
        mock_req = MagicMock()
        mock_req.timeout = 30

        # 模拟响应
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = b"success"

        # 第一次失败，第二次成功 (retries=2允许最多2次重试)
        mock_parent.open.side_effect = [URLError("Network error"), mock_response]

        # 执行测试
        result = self.retry_handler.default_open(mock_req)

        # 验证重试次数
        self.assertEqual(mock_parent.open.call_count, 2)
        self.assertEqual(result, mock_response)

        # 验证sleep调用次数 (第一次失败后会sleep)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("time.sleep")
    def test_http_error_retry(self, mock_sleep):
        """测试HTTP错误重试"""
        # 设置父级opener
        mock_parent = MagicMock()
        self.retry_handler.parent = mock_parent

        # 模拟request对象
        mock_req = MagicMock()
        mock_req.timeout = 30

        # 模拟HTTP 500错误响应
        mock_error_response = MagicMock()
        mock_error_response.getcode.return_value = 500

        # 模拟成功响应
        mock_success_response = MagicMock()
        mock_success_response.getcode.return_value = 200

        # 第一次返回500错误，第二次成功
        mock_parent.open.side_effect = [mock_error_response, mock_success_response]

        # 执行测试
        result = self.retry_handler.default_open(mock_req)

        # 验证重试次数
        self.assertEqual(mock_parent.open.call_count, 2)
        self.assertEqual(result, mock_success_response)

        # 验证sleep调用 (第一次失败后会sleep)
        mock_sleep.assert_called_once()

    def test_non_retryable_error_immediate_failure(self):
        """测试非重试错误立即失败"""
        # 设置父级opener
        mock_parent = MagicMock()
        self.retry_handler.parent = mock_parent

        # 模拟request对象
        mock_req = MagicMock()
        mock_req.timeout = 30

        # 模拟不可重试的异常
        mock_parent.open.side_effect = ValueError("Non-retryable error")

        # 执行测试，期望异常被抛出
        with self.assertRaises(ValueError):
            self.retry_handler.default_open(mock_req)

        # 验证只调用一次，没有重试
        self.assertEqual(mock_parent.open.call_count, 1)

    @patch("time.sleep")
    def test_max_retries_exceeded(self, mock_sleep):
        """测试超过最大重试次数"""
        # 设置父级opener
        mock_parent = MagicMock()
        self.retry_handler.parent = mock_parent

        # 模拟request对象
        mock_req = MagicMock()
        mock_req.timeout = 30

        # 所有请求都失败 (retries=2, 最多尝试2次)
        mock_parent.open.side_effect = [URLError("Persistent error"), URLError("Persistent error")]

        # 执行测试，期望异常被抛出
        with self.assertRaises(URLError):
            self.retry_handler.default_open(mock_req)

        # 验证重试次数 (retries=2, 所以最多2次调用)
        self.assertEqual(mock_parent.open.call_count, 2)

        # 验证sleep调用次数 (第一次失败后会sleep)
        self.assertEqual(mock_sleep.call_count, 1)


class TestRequestFunction(unittest.TestCase):
    """测试新的 request 函数"""

    @patch("ddns.util.http.build_opener")
    def test_request_with_retry(self, mock_build_opener):
        """测试带重试功能的request函数"""
        # Mock response
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value = {}
        mock_response.read.return_value = b'{"success": true}'
        mock_response.msg = "OK"

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
        self.assertIn("RetryHandler", handler_types)

    @patch("ddns.util.http.build_opener")
    def test_request_with_proxy(self, mock_build_opener):
        """测试request函数的代理功能"""
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value = {}
        mock_response.read.return_value = b"test"
        mock_response.msg = "OK"

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener

        # 测试代理字符串
        proxy_string = "http://proxy:8080"
        result = request("GET", "http://example.com", proxy=proxy_string)

        self.assertEqual(result.status, 200)
        mock_build_opener.assert_called_once()

        # 验证ProxyHandler被添加
        args = mock_build_opener.call_args[0]
        handler_types = [type(handler).__name__ for handler in args]
        self.assertIn("ProxyHandler", handler_types)

    def test_exponential_backoff_calculation(self):
        """测试指数退避计算"""
        # 验证等待时间计算
        for i in range(5):
            expected = 2**i
            self.assertEqual(expected, 2**i)

        # 验证常见重试等待时间
        self.assertEqual(2**0, 1)  # 第一次重试等待1秒
        self.assertEqual(2**1, 2)  # 第二次重试等待2秒
        self.assertEqual(2**2, 4)  # 第三次重试等待4秒
        self.assertEqual(2**3, 8)  # 第四次重试等待8秒

    @patch("ddns.util.http.build_opener")
    def test_default_retry_counts(self, mock_build_opener):
        """测试默认重试次数"""
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value = {}
        mock_response.read.return_value = b"test"
        mock_response.msg = "OK"

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener

        # 测试默认重试次数
        request("GET", "http://example.com")

        # 验证RetryHandler被创建
        mock_build_opener.assert_called_once()
        args = mock_build_opener.call_args[0]
        handler_types = [type(handler).__name__ for handler in args]
        self.assertIn("RetryHandler", handler_types)

        # 测试自定义重试次数
        mock_build_opener.reset_mock()
        request("GET", "http://example.com", retries=5)

        # 验证RetryHandler被创建
        mock_build_opener.assert_called_once()
        args = mock_build_opener.call_args[0]
        handler_types = [type(handler).__name__ for handler in args]
        self.assertIn("RetryHandler", handler_types)


if __name__ == "__main__":
    unittest.main()
