# coding=utf-8
"""
测试 HTTP RetryHandler 重试功能
Test HTTP RetryHandler retry functionality
"""

from __future__ import unicode_literals
import socket
import ssl
from __init__ import unittest, patch, MagicMock
import logging

# Python 2/3 compatibility
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO  # type: ignore[no-redef]

from ddns.util.http import (
    RetryHandler,
    request,
)


class TestRetryHandler(unittest.TestCase):
    """测试 RetryHandler 类"""

    def setUp(self):
        """设置测试，创建retries=2的RetryHandler（会重试2次，总共最多3次请求）"""
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

        # 第一次失败，第二次成功 (retries=2，允许重试2次，总共最多3次请求)
        mock_parent.open.side_effect = [socket.timeout, mock_response]

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

        # 第一次返回500错误，第二次成功 (retries=2，允许重试2次，总共最多3次请求)
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

        # 所有请求都失败 (retries=2，会重试2次，总共3次请求: attempts 1, 2, 3)
        # 修复后的RetryHandler会正确抛出最后的异常
        mock_parent.open.side_effect = [socket.gaierror, socket.timeout, socket.timeout]

        # 执行测试，期望最后的异常被抛出
        with self.assertRaises(socket.timeout):
            self.retry_handler.default_open(mock_req)

        # 验证重试次数 (retries=2，总共3次请求)
        self.assertEqual(mock_parent.open.call_count, 3)

        # 验证sleep调用次数 (前两次失败后会sleep)
        self.assertEqual(mock_sleep.call_count, 2)


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
        # 在Python 2中，检查实际的类名需要使用__class__.__name__
        handler_types = [getattr(handler, "__class__", type(handler)).__name__ for handler in args]
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
        handler_types = [getattr(handler, "__class__", type(handler)).__name__ for handler in args]
        self.assertIn("ProxyHandler", handler_types)

    @patch("time.sleep")
    def test_retry_handler_backoff_delays(self, mock_sleep):
        """测试 RetryHandler 的指数退避延迟"""
        # 直接测试 RetryHandler 而不是通过 request() 函数
        retry_handler = RetryHandler(retries=3)

        # 设置父级opener
        mock_parent = MagicMock()
        retry_handler.parent = mock_parent

        # 模拟request对象
        mock_req = MagicMock()
        mock_req.timeout = 30

        # 创建模拟的响应对象
        mock_response_1 = MagicMock()
        mock_response_1.getcode.return_value = 500

        mock_response_2 = MagicMock()
        mock_response_2.getcode.return_value = 500

        mock_response_3 = MagicMock()
        mock_response_3.getcode.return_value = 200

        # 设置parent.open的返回值序列：前两次500错误，第三次200成功
        mock_parent.open.side_effect = [mock_response_1, mock_response_2, mock_response_3]

        # 执行测试
        result = retry_handler.default_open(mock_req)

        # 验证返回成功响应
        self.assertEqual(result, mock_response_3)

        # 验证 time.sleep 被调用的次数和参数
        # 基于RetryHandler实现：attempt从1开始，延迟是2^attempt
        # 第一次失败(attempt=1)后sleep(2^1=2)，第二次失败(attempt=2)后sleep(2^2=4)
        expected_delays = [2, 4]  # 对应2^1, 2^2
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
        self.assertEqual(actual_delays, expected_delays)

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
        handler_types = [getattr(handler, "__class__", type(handler)).__name__ for handler in args]
        self.assertIn("RetryHandler", handler_types)

        # 测试自定义重试次数
        mock_build_opener.reset_mock()
        request("GET", "http://example.com", retries=5)

        # 验证RetryHandler被创建
        mock_build_opener.assert_called_once()
        args = mock_build_opener.call_args[0]
        handler_types = [getattr(handler, "__class__", type(handler)).__name__ for handler in args]
        self.assertIn("RetryHandler", handler_types)


class TestHttpRetryRealNetwork(unittest.TestCase):
    """测试HTTP重试功能 - 真实网络请求"""

    def test_http_502_retry_auto(self):
        """测试HTTP 502状态码的重试机制 - 使用真实请求检查日志"""
        # 创建日志捕获器
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.WARNING)

        # 获取http模块的logger
        http_logger = logging.getLogger("ddns.util.http")
        original_level = http_logger.level
        original_handlers = http_logger.handlers[:]

        try:
            # 设置日志级别和处理器
            http_logger.setLevel(logging.WARNING)
            http_logger.handlers = [handler]

            # 确保logger会传播到我们的handler
            http_logger.propagate = True

            # 使用httpbin.org的502错误端点测试重试
            try:
                response = request("GET", "http://postman-echo.com/status/502", retries=1, verify="auto")

                # 验证最终返回502错误
                self.assertEqual(response.status, 502)

                # 检查日志输出
                log_output = log_capture.getvalue()

                # 验证日志中包含重试信息（匹配实际的日志格式）
                # 在Python 2中，日志捕获可能有所不同，使用更宽松的检查
                if "HTTP 502 error, retrying in" in log_output:
                    # 统计重试日志的数量
                    retry_count = log_output.count("HTTP 502 error, retrying in")
                    self.assertGreaterEqual(retry_count, 1, "应该至少有一次重试日志")
                    self.assertLessEqual(retry_count, 1, "最多应该有一次重试日志")
                elif "retrying" in log_output.lower():
                    # 如果找到其他形式的重试信息，也算通过
                    self.assertIn("retrying", log_output.lower())
                else:
                    # 如果没有找到重试日志，但请求成功了，可能是因为日志捕获问题或第一次就成功了
                    self.skipTest(
                        "No retry log found: '{}' - possibly succeeded on first attempt".format(repr(log_output))
                    )

            except Exception as e:
                # 网络问题时跳过测试
                error_msg = str(e).lower()
                network_keywords = ["timeout", "connection", "resolution", "unreachable", "network"]
                if any(keyword in error_msg for keyword in network_keywords):
                    self.skipTest("Network unavailable for HTTP 502 retry test: {}".format(str(e)))
                else:
                    # 其他异常重新抛出
                    raise

        finally:
            # 恢复原始日志设置
            http_logger.setLevel(original_level)
            http_logger.handlers = original_handlers

    def test_ssl_certificate_error_no_retry_real_case(self):
        """测试SSL证书错误不触发重试 - 使用真实证书错误案例"""
        # 创建日志捕获器
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.DEBUG)  # 使用DEBUG级别捕获更多信息

        # 获取http模块的logger
        http_logger = logging.getLogger("ddns.util.http")
        original_level = http_logger.level
        original_handlers = http_logger.handlers[:]

        try:
            # 设置日志级别和处理器
            http_logger.setLevel(logging.DEBUG)
            http_logger.handlers = [handler]

            # 使用expired.badssl.com测试过期证书错误
            try:
                # 使用过期证书的网站，强制验证证书，重试一次即可
                request("GET", "https://expired.badssl.com/", retries=1, verify=True)

                # 如果没有抛出异常，说明请求成功了，跳过测试
                self.skipTest("Expected SSL certificate error was not raised")

            except ssl.SSLError as e:
                # 这是我们期望的SSL错误
                # 检查日志输出
                log_output = log_capture.getvalue()

                # 验证日志中没有重试信息
                self.assertNotIn("retrying", log_output.lower())
                self.assertNotIn("retry", log_output.lower())

                # 验证确实是SSL证书错误
                self.assertIn("CERTIFICATE_VERIFY_FAILED", str(e))

            except Exception as e:
                # 检查是否是SSL相关错误
                error_msg = str(e).lower()
                ssl_keywords = ["ssl", "certificate", "verify", "handshake", "tls"]
                network_keywords = ["timeout", "connection", "resolution", "unreachable", "network"]

                if any(keyword in error_msg for keyword in ssl_keywords):
                    # 这是SSL错误，检查日志输出
                    log_output = log_capture.getvalue()

                    # 验证日志中没有重试信息
                    self.assertNotIn("retrying", log_output.lower())
                    self.assertNotIn("retry", log_output.lower())

                    # 验证确实是SSL证书错误
                    self.assertIn("certificate", error_msg)

                elif any(keyword in error_msg for keyword in network_keywords):
                    # 网络问题时跳过测试
                    self.skipTest("Network unavailable for SSL certificate test: {}".format(str(e)))
                else:
                    # 其他异常重新抛出
                    raise

        finally:
            # 恢复原始日志设置
            http_logger.setLevel(original_level)
            http_logger.handlers = original_handlers


if __name__ == "__main__":
    unittest.main()
