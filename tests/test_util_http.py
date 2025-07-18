# coding=utf-8
# type: ignore[index]
"""
测试 ddns.util.http 模块
Test ddns.util.http module
"""

from __future__ import unicode_literals
from __init__ import unittest, sys, patch, MagicMock, call
import json
import socket
import time

from ddns.util.http import (
    HttpResponse,
    _decode_response_body,
    quote,
    send_http_request,
    RETRY_STATUS_CODES,
    CONNECTION_EXCEPTIONS,
)

# Python 2/3 compatibility
if sys.version_info[0] == 2:  # python 2
    text_type = unicode  # noqa: F821
    binary_type = str
else:
    text_type = str
    binary_type = bytes


def to_bytes(s, encoding="utf-8"):
    if isinstance(s, text_type):
        return s.encode(encoding)
    return s


def to_unicode(s, encoding="utf-8"):
    if isinstance(s, binary_type):
        return s.decode(encoding)
    return s


def byte_string(s):
    if isinstance(s, text_type):
        return s.encode("utf-8")
    return s


class TestHttpResponse(unittest.TestCase):
    """测试 HttpResponse 类"""

    def test_init(self):
        """测试初始化HttpResponse对象"""
        headers = [("Content-Type", "application/json"), ("Content-Length", "100")]
        response = HttpResponse(200, "OK", headers, '{"test": true}')

        self.assertEqual(response.status, 200)
        self.assertEqual(response.reason, "OK")
        self.assertEqual(response.headers, headers)
        self.assertEqual(response.body, '{"test": true}')

    def test_headers_get_case_insensitive(self):
        """测试headers.get方法不区分大小写"""

        # 模拟 response.info() 对象，支持不区分大小写的 get 方法
        class MockHeaders:
            def __init__(self):
                self._headers = {"Content-Type": "application/json", "Content-Length": "100"}

            def get(self, name, default=None):
                # 模拟 HTTPMessage 的不区分大小写查找
                for key, value in self._headers.items():
                    if key.lower() == name.lower():
                        return value
                return default

        headers = MockHeaders()
        response = HttpResponse(200, "OK", headers, "test")

        self.assertEqual(response.headers.get("content-type"), "application/json")
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(response.headers.get("CONTENT-TYPE"), "application/json")
        self.assertEqual(response.headers.get("content-length"), "100")

    def test_headers_get_not_found(self):
        """测试headers.get方法找不到头部时的默认值"""

        class MockHeaders:
            def __init__(self):
                self._headers = {"Content-Type": "application/json"}

            def get(self, name, default=None):
                for key, value in self._headers.items():
                    if key.lower() == name.lower():
                        return value
                return default

        headers = MockHeaders()
        response = HttpResponse(200, "OK", headers, "test")

        self.assertIsNone(response.headers.get("Authorization"))
        self.assertEqual(response.headers.get("Authorization", "default"), "default")

    def test_headers_get_first_match(self):
        """测试headers.get方法返回第一个匹配的头部"""

        class MockHeaders:
            def __init__(self):
                self._headers = {"Set-Cookie": "session=abc"}  # 只保留第一个值

            def get(self, name, default=None):
                for key, value in self._headers.items():
                    if key.lower() == name.lower():
                        return value
                return default

        headers = MockHeaders()
        response = HttpResponse(200, "OK", headers, "test")

        self.assertEqual(response.headers.get("Set-Cookie"), "session=abc")


class TestDecodeResponseBody(unittest.TestCase):
    """测试 _decode_response_body 函数"""

    def test_utf8_decoding(self):
        """测试UTF-8解码"""
        raw_body = to_bytes("中文测试", "utf-8")
        result = _decode_response_body(raw_body, "text/html; charset=utf-8")
        self.assertEqual(result, "中文测试")

    def test_gbk_decoding(self):
        """测试GBK解码"""
        raw_body = to_bytes("中文测试", "gbk")
        result = _decode_response_body(raw_body, "text/html; charset=gbk")
        self.assertEqual(result, "中文测试")

    def test_gb2312_alias(self):
        """测试GB2312别名映射到GBK"""
        raw_body = to_bytes("中文测试", "gbk")
        result = _decode_response_body(raw_body, "text/html; charset=gb2312")
        self.assertEqual(result, "中文测试")

    def test_iso_8859_1_alias(self):
        """测试ISO-8859-1别名映射到latin-1"""
        raw_body = to_bytes("test", "latin-1")
        result = _decode_response_body(raw_body, "text/html; charset=iso-8859-1")
        self.assertEqual(result, "test")

    def test_no_charset_fallback_to_utf8(self):
        """测试没有charset时默认使用UTF-8"""
        raw_body = to_bytes("test", "utf-8")
        result = _decode_response_body(raw_body, "text/html")
        self.assertEqual(result, "test")

    def test_no_content_type(self):
        """测试没有Content-Type时使用UTF-8"""
        raw_body = to_bytes("test", "utf-8")
        result = _decode_response_body(raw_body, None)
        self.assertEqual(result, "test")

    def test_empty_body(self):
        """测试空响应体"""
        result = _decode_response_body(byte_string(""), "text/html")
        self.assertEqual(result, "")

    def test_invalid_encoding_fallback(self):
        """测试无效编码时的后备机制"""
        raw_body = to_bytes("中文测试", "utf-8")
        # 指定一个无效的编码
        result = _decode_response_body(raw_body, "text/html; charset=invalid-encoding")
        self.assertEqual(result, "中文测试")  # 应该回退到UTF-8

    def test_malformed_charset(self):
        """测试格式错误的charset"""
        raw_body = to_bytes("test", "utf-8")
        result = _decode_response_body(raw_body, "text/html; charset=")
        self.assertEqual(result, "test")


class TestSendHttpRequest(unittest.TestCase):
    """测试 send_http_request 函数"""

    def test_get_request_real_api(self):
        """测试真实的GET请求 - 使用postman-echo API服务"""
        from ddns.util.http import send_http_request

        # 使用postman-echo.com提供的GET测试端点
        try:
            response = send_http_request("GET", "http://postman-echo.com/get?test=ddns")
            self.assertEqual(response.status, 200)
            self.assertIsNotNone(response.body)
            # 验证响应内容是JSON格式
            data = json.loads(response.body)
            self.assertIn("args", data)
            self.assertIn("url", data)
            self.assertIn("test", data["args"])
            self.assertEqual(data["args"]["test"], "ddns")
        except (socket.timeout, ConnectionError) as e:
            # 网络不可用时跳过测试
            self.skipTest("Network unavailable: {}".format(str(e)))

    def test_json_api_response(self):
        """测试JSON API响应解析"""
        from ddns.util.http import send_http_request

        try:
            # 使用postman-echo.com的基本GET端点，返回请求信息
            response = send_http_request("GET", "http://postman-echo.com/get?format=json")
            self.assertEqual(response.status, 200)
            self.assertIsNotNone(response.body)

            # 验证返回的是有效的JSON
            data = json.loads(response.body)
            # postman-echo返回请求信息对象
            self.assertIn("args", data)
            self.assertIn("url", data)
            self.assertIsInstance(data, dict)
            self.assertTrue(len(data) > 0)
        except Exception as e:
            self.skipTest("Network unavailable: {}".format(str(e)))

    def test_provider_api_patterns(self):
        """测试常见DNS provider API模式"""
        from ddns.util.http import send_http_request

        try:
            # 测试认证失败场景 - 使用postman-echo模拟401错误
            headers = {
                "Authorization": "Bearer invalid-token",
                "Content-Type": "application/json",
                "User-Agent": "DDNS-Client/4.0",
            }

            # 使用postman-echo模拟401认证失败响应
            response = send_http_request("GET", "http://postman-echo.com/status/401", headers=headers)

            # 应该返回401认证失败
            self.assertEqual(response.status, 401)
            # 401响应可能有空响应体，这是正常的
            self.assertIsNotNone(response.body)

        except Exception as e:
            self.skipTest("Network unavailable: {}".format(str(e)))

    def test_http_400_bad_request_handling(self):
        """测试HTTP 400 Bad Request错误处理"""
        from ddns.util.http import send_http_request

        try:
            # 使用postman-echo模拟400错误
            response = send_http_request("GET", "http://postman-echo.com/status/400")

            # 验证状态码为400
            self.assertEqual(response.status, 400, "应该返回400 Bad Request状态码")

            # 验证响应对象的完整性
            self.assertIsNotNone(response.body, "400响应应该有响应体")
            self.assertIsNotNone(response.headers, "400响应应该有响应头")
            self.assertIsNotNone(response.reason, "400响应应该有状态原因")

        except Exception as e:
            # 网络问题时跳过测试
            error_msg = str(e).lower()
            if any(
                keyword in error_msg for keyword in ["timeout", "connection", "resolution", "unreachable", "network"]
            ):
                self.skipTest("Network unavailable for HTTP 400 test: {}".format(str(e)))
            else:
                # 其他异常重新抛出
                raise

    def test_dns_over_https_simulation(self):
        """测试DNS类型的API响应解析"""
        from ddns.util.http import send_http_request

        try:
            headers = {"Accept": "application/dns-json", "User-Agent": "DDNS-Test/1.0"}

            # 使用postman-echo模拟一个带有特定结构的JSON响应
            response = send_http_request(
                "GET", "http://postman-echo.com/get?domain=example.com&type=A", headers=headers
            )

            self.assertEqual(response.status, 200)

            data = json.loads(response.body)
            # postman-echo返回请求信息，包含args参数
            self.assertIn("args", data)
            self.assertIn("domain", data["args"])
            self.assertEqual(data["args"]["domain"], "example.com")

        except Exception as e:
            self.skipTest("Network unavailable: {}".format(str(e)))

    def test_basic_auth_with_url_embedding(self):
        """测试URL嵌入式基本认证格式"""

        # 测试不同场景的URL嵌入认证格式
        test_cases = [
            {
                "username": "user",
                "password": "pass",
                "domain": "example.com",
                "expected": "https://user:pass@example.com",
            },
            {
                "username": "test@email.com",
                "password": "password!",
                "domain": "api.service.com",
                "expected": "https://test%40email.com:password%21@api.service.com",
            },
            {
                "username": "user+tag",
                "password": "p@ss w0rd",
                "domain": "subdomain.example.org",
                "expected": "https://user%2Btag:p%40ss%20w0rd@subdomain.example.org",
            },
        ]

        for case in test_cases:
            username_encoded = quote(case["username"], safe="")
            password_encoded = quote(case["password"], safe="")

            auth_url = "https://{0}:{1}@{2}".format(username_encoded, password_encoded, case["domain"])

            self.assertEqual(
                auth_url,
                case["expected"],
                "Failed for username={}, password={}".format(case["username"], case["password"]),
            )

    def test_basic_auth_with_httpbin(self):
        """Test basic auth URL format and verification with URL-embedded authentication"""
        from ddns.util.http import send_http_request

        # Test with special credentials containing @ and . characters
        special_username = "user@test.com"
        special_password = "passwo.rd"
        username_encoded = quote(special_username, safe="")
        password_encoded = quote(special_password, safe="")

        # Verify URL encoding of special characters
        self.assertEqual(username_encoded, "user%40test.com")
        self.assertEqual(password_encoded, "passwo.rd")

        # Create auth URL with encoded credentials in URL auth but original in path parameters
        auth_url = "https://{0}:{1}@httpbin.org/basic-auth/{2}/{3}".format(
            username_encoded, password_encoded, username_encoded, password_encoded
        )

        # Try to make actual request
        try:
            response = send_http_request("GET", auth_url)
        except (OSError, IOError) as e:
            # Skip for Network Exceptions (timeout, connection, etc.)
            raise unittest.SkipTest("Network error, skipping httpbin test: {0}".format(e))
            # Verify successful response if we get here
        if response.status > 500:
            # httpbin.org may return 500 if overloaded, skip this test
            raise unittest.SkipTest("httpbin.org returned 500, skipping test")
        self.assertEqual(response.status, 200)
        self.assertIn("authenticated", response.body)
        self.assertIn("user", response.body)

    def test_ssl_auto_fallback_real_network(self):
        """测试SSL auto模式的真实网络自动降级行为"""
        from ddns.util.http import send_http_request

        test_url = "https://postman-echo.com/status/200"  # 使用postman-echo的测试站点

        try:
            # 1. 测试auto模式：应该自动降级成功
            response_auto = send_http_request("GET", test_url, verify_ssl="auto")
            self.assertEqual(response_auto.status, 200, "auto模式自动降级成功访问测试站点")
            self.assertIsNotNone(response_auto.body)

            # 2. 验证禁用SSL验证模式也能成功（作为对照）
            response_false = send_http_request("GET", test_url, verify_ssl=False)
            self.assertEqual(response_false.status, 200, "禁用SSL验证应该成功访问自签名证书站点")

        except Exception as e:
            # 网络问题时跳过测试
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["timeout", "resolution", "unreachable"]):
                self.skipTest("Network unavailable for SSL fallback test: {}".format(str(e)))
            else:
                # 其他异常重新抛出
                raise


class TestHttpRetry(unittest.TestCase):
    """测试 HTTP 自动重试功能"""

    def setUp(self):
        """设置测试环境"""
        self.mock_time_sleep = patch('ddns.util.http.time.sleep').start()
        self.addCleanup(patch.stopall)

    @patch('ddns.util.http._send_http_request_once')
    def test_retry_on_connection_exceptions(self, mock_send):
        """测试连接异常时的重试"""
        # 模拟前两次请求失败，第三次成功
        mock_send.side_effect = [
            socket.timeout("Connection timed out"),
            OSError("Connection reset"),
            HttpResponse(200, "OK", {}, "success")
        ]
        
        response = send_http_request("GET", "http://example.com", max_retries=2)
        
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, "success")
        self.assertEqual(mock_send.call_count, 3)
        
        # 检查重试间隔：第一次重试等待1秒(2^0)，第二次重试等待2秒(2^1)
        expected_calls = [call(1), call(2)]
        self.mock_time_sleep.assert_has_calls(expected_calls)

    @patch('ddns.util.http._send_http_request_once')
    def test_retry_on_http_status_codes(self, mock_send):
        """测试HTTP错误状态码的重试"""
        # 模拟502错误后成功
        mock_send.side_effect = [
            HttpResponse(502, "Bad Gateway", {}, "error"),
            HttpResponse(200, "OK", {}, "success")
        ]
        
        response = send_http_request("GET", "http://example.com", max_retries=1)
        
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, "success")
        self.assertEqual(mock_send.call_count, 2)
        self.mock_time_sleep.assert_called_once_with(1)

    @patch('ddns.util.http._send_http_request_once')
    def test_no_retry_on_success(self, mock_send):
        """测试成功时不重试"""
        mock_send.return_value = HttpResponse(200, "OK", {}, "success")
        
        response = send_http_request("GET", "http://example.com", max_retries=2)
        
        self.assertEqual(response.status, 200)
        self.assertEqual(mock_send.call_count, 1)
        self.mock_time_sleep.assert_not_called()

    @patch('ddns.util.http._send_http_request_once')
    def test_no_retry_on_non_retryable_status(self, mock_send):
        """测试非重试状态码不重试"""
        mock_send.return_value = HttpResponse(404, "Not Found", {}, "error")
        
        response = send_http_request("GET", "http://example.com", max_retries=2)
        
        self.assertEqual(response.status, 404)
        self.assertEqual(mock_send.call_count, 1)
        self.mock_time_sleep.assert_not_called()

    @patch('ddns.util.http._send_http_request_once')
    def test_max_retries_exhausted_exception(self, mock_send):
        """测试重试次数用尽后抛出异常"""
        mock_send.side_effect = socket.timeout("Connection timed out")
        
        with self.assertRaises(socket.timeout):
            send_http_request("GET", "http://example.com", max_retries=2)
        
        self.assertEqual(mock_send.call_count, 3)  # 原始请求 + 2次重试
        expected_calls = [call(1), call(2)]
        self.mock_time_sleep.assert_has_calls(expected_calls)

    @patch('ddns.util.http._send_http_request_once')
    def test_max_retries_exhausted_status_code(self, mock_send):
        """测试重试次数用尽后返回错误响应"""
        mock_send.return_value = HttpResponse(503, "Service Unavailable", {}, "error")
        
        response = send_http_request("GET", "http://example.com", max_retries=1)
        
        self.assertEqual(response.status, 503)
        self.assertEqual(mock_send.call_count, 2)  # 原始请求 + 1次重试
        self.mock_time_sleep.assert_called_once_with(1)

    @patch('ddns.util.http._send_http_request_once')
    def test_exponential_backoff(self, mock_send):
        """测试指数退避算法"""
        mock_send.side_effect = [
            socket.timeout("timeout 1"),
            socket.timeout("timeout 2"),
            socket.timeout("timeout 3"),
            HttpResponse(200, "OK", {}, "success")
        ]
        
        response = send_http_request("GET", "http://example.com", max_retries=3)
        
        self.assertEqual(response.status, 200)
        # 检查等待时间：1秒(2^0), 2秒(2^1), 4秒(2^2)
        expected_calls = [call(1), call(2), call(4)]
        self.mock_time_sleep.assert_has_calls(expected_calls)

    @patch('ddns.util.http._send_http_request_once')
    def test_retry_status_codes_coverage(self, mock_send):
        """测试所有重试状态码"""
        for status_code in RETRY_STATUS_CODES:
            with self.subTest(status_code=status_code):
                mock_send.side_effect = [
                    HttpResponse(status_code, "Error", {}, "error"),
                    HttpResponse(200, "OK", {}, "success")
                ]
                
                response = send_http_request("GET", "http://example.com", max_retries=1)
                
                self.assertEqual(response.status, 200)
                self.assertEqual(mock_send.call_count, 2)
                
                # 重置mock
                mock_send.reset_mock()
                self.mock_time_sleep.reset_mock()

    @patch('ddns.util.http._send_http_request_once')
    def test_connection_exceptions_coverage(self, mock_send):
        """测试所有连接异常"""
        test_exceptions = [
            socket.timeout("timeout"),
            OSError("OS error"),
        ]
        
        # 添加Python版本特定的异常
        try:
            from urllib.error import URLError
            test_exceptions.append(URLError("URL error"))
        except ImportError:
            from urllib2 import URLError  # type: ignore
            test_exceptions.append(URLError("URL error"))
        
        for exception in test_exceptions:
            with self.subTest(exception=type(exception).__name__):
                mock_send.side_effect = [
                    exception,
                    HttpResponse(200, "OK", {}, "success")
                ]
                
                response = send_http_request("GET", "http://example.com", max_retries=1)
                
                self.assertEqual(response.status, 200)
                self.assertEqual(mock_send.call_count, 2)
                
                # 重置mock
                mock_send.reset_mock()
                self.mock_time_sleep.reset_mock()

    @patch('ddns.util.http._send_http_request_once')
    def test_no_retry_when_max_retries_zero(self, mock_send):
        """测试max_retries=0时不重试"""
        mock_send.side_effect = socket.timeout("timeout")
        
        with self.assertRaises(socket.timeout):
            send_http_request("GET", "http://example.com", max_retries=0)
        
        self.assertEqual(mock_send.call_count, 1)
        self.mock_time_sleep.assert_not_called()

    @patch('ddns.util.http._send_http_request_once')
    def test_non_retryable_exception_immediate_raise(self, mock_send):
        """测试非重试异常立即抛出"""
        mock_send.side_effect = ValueError("invalid value")
        
        with self.assertRaises(ValueError):
            send_http_request("GET", "http://example.com", max_retries=2)
        
        self.assertEqual(mock_send.call_count, 1)
        self.mock_time_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
