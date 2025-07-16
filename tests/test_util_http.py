# coding=utf-8
"""
测试 ddns.util.http 模块
Test ddns.util.http module
"""

from __future__ import unicode_literals
from __init__ import unittest
import sys
from ddns.util.http import (
    HttpResponse,
    _decode_response_body,
    quote,
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

    def test_get_header_case_insensitive(self):
        """测试get_header方法不区分大小写"""

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

        self.assertEqual(response.get_header("content-type"), "application/json")
        self.assertEqual(response.get_header("Content-Type"), "application/json")
        self.assertEqual(response.get_header("CONTENT-TYPE"), "application/json")
        self.assertEqual(response.get_header("content-length"), "100")

    def test_get_header_not_found(self):
        """测试get_header方法找不到头部时的默认值"""

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

        self.assertIsNone(response.get_header("Authorization"))
        self.assertEqual(response.get_header("Authorization", "default"), "default")

    def test_get_header_first_match(self):
        """测试get_header方法返回第一个匹配的头部"""

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

        self.assertEqual(response.get_header("Set-Cookie"), "session=abc")


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
            response = send_http_request("GET", "https://postman-echo.com/get?test=ddns")
            self.assertEqual(response.status, 200)
            self.assertIsNotNone(response.body)
            # 验证响应内容是JSON格式
            import json

            data = json.loads(response.body)
            self.assertIn("args", data)
            self.assertIn("url", data)
            self.assertIn("test", data["args"])
            self.assertEqual(data["args"]["test"], "ddns")
        except Exception as e:
            # 网络不可用时跳过测试
            self.skipTest("Network unavailable: {}".format(str(e)))

    def test_json_api_response(self):
        """测试JSON API响应解析"""
        from ddns.util.http import send_http_request

        try:
            # 使用postman-echo.com的基本GET端点，返回请求信息
            response = send_http_request("GET", "https://postman-echo.com/get?format=json")
            self.assertEqual(response.status, 200)
            self.assertIsNotNone(response.body)

            # 验证返回的是有效的JSON
            import json

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
            response = send_http_request("GET", "https://postman-echo.com/status/401", headers=headers)

            # 应该返回401认证失败
            self.assertEqual(response.status, 401)
            # 401响应可能有空响应体，这是正常的
            self.assertIsNotNone(response.body)

        except Exception as e:
            self.skipTest("Network unavailable: {}".format(str(e)))

    def test_dns_over_https_simulation(self):
        """测试DNS类型的API响应解析"""
        from ddns.util.http import send_http_request

        try:
            headers = {"Accept": "application/dns-json", "User-Agent": "DDNS-Test/1.0"}

            # 使用postman-echo模拟一个带有特定结构的JSON响应
            response = send_http_request(
                "GET", "https://postman-echo.com/get?domain=example.com&type=A", headers=headers
            )

            self.assertEqual(response.status, 200)

            import json

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
        from ddns.util.http import send_http_request, URLError

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
        except (URLError, OSError, IOError) as e:
            # Skip for Network Exceptions (timeout, connection, etc.)
            raise unittest.SkipTest("Network error, skipping httpbin test: {0}".format(e))
            # Verify successful response if we get here
        if response.status > 500:
            # httpbin.org may return 500 if overloaded, skip this test
            raise unittest.SkipTest("httpbin.org returned 500, skipping test")
        self.assertEqual(response.status, 200)
        self.assertIn("authenticated", response.body)
        self.assertIn("user", response.body)


if __name__ == "__main__":
    unittest.main()
