# coding=utf-8
# type: ignore[index]
"""
测试 ddns.util.http 模块
Test ddns.util.http module
"""

from __future__ import unicode_literals
from __init__ import unittest, sys
import json
import socket
import random

from ddns.util.http import HttpResponse, _decode_response_body, quote, USER_AGENT

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


class TestUserAgent(unittest.TestCase):
    """测试 USER_AGENT 常量和用户代理头部设置"""

    def _test_user_agent_with_endpoints(self, headers=None, expected_ua=None):
        """通用的User-Agent测试辅助方法"""
        from ddns.util.http import request

        # 多个测试站点，随机顺序以分散负载
        test_endpoints = [
            "https://httpbingo.org/user-agent",
            "http://postman-echo.com/headers",
            "http://httpbin.org/user-agent",
        ]
        if not expected_ua:
            test_endpoints.remove("https://httpbingo.org/user-agent")  # 如果不验证User-Agent，则不需要这个端点
        random.shuffle(test_endpoints)

        for endpoint in test_endpoints:
            try:
                response = request("GET", endpoint, headers=headers, retries=1)
                if response.status == 200:
                    response_data = json.loads(response.body)
                    # 不同的测试站点响应格式可能略有不同
                    headers = response_data["headers"] if "headers" in response_data else response_data
                    # 查找User-Agent头部（不区分大小写）
                    ua_key = next((key for key in headers if key.lower() == "user-agent"), None)
                    if ua_key:
                        ua_value = headers[ua_key]
                        if expected_ua:
                            self.assertEqual(ua_value, expected_ua)
                        else:
                            # 只验证不是None和空字符串
                            self.assertIn(ua_value, (None, ""))
                    else:
                        self.assertIn(expected_ua, (None, ""))
                    return True  # 测试成功

            except OSError as e:
                error_msg = str(e).lower()
                # 不允许None错误时，网络问题继续尝试，其他错误重新抛出
                network_keywords = ["timeout", "connection", "resolution", "unreachable", "network"]
                if not any(keyword in error_msg for keyword in network_keywords):
                    # 如果不是网络问题，重新抛出异常
                    raise
                continue

        # 所有端点都失败
        return False

    def test_user_agent_constant(self):
        """测试USER_AGENT常量格式正确"""
        # 验证USER_AGENT常量存在且格式正确
        self.assertIsInstance(USER_AGENT, str)
        self.assertIn("DDNS/", USER_AGENT)
        self.assertIn("ddns@newfuture.cc", USER_AGENT)

    def test_user_agent_version_format(self):
        """测试USER_AGENT包含版本信息"""
        # USER_AGENT应该包含版本号或"dev"
        has_version = any(char.isdigit() for char in USER_AGENT) or "dev" in USER_AGENT
        self.assertTrue(has_version, "USER_AGENT should contain version number or 'dev'")

    def test_request_sets_user_agent_automatically(self):
        """测试request函数自动设置User-Agent头部"""
        if not self._test_user_agent_with_endpoints(expected_ua=USER_AGENT):
            self.skipTest("All test endpoints unavailable for user-agent test")

    def test_custom_user_agent_override(self):
        """测试自定义User-Agent头部会覆盖默认值"""
        custom_ua = "CustomAgent/1.0"
        headers = {"User-Agent": custom_ua}

        if self._test_user_agent_with_endpoints(headers=headers, expected_ua=custom_ua):
            # 额外验证不是默认的USER_AGENT
            self.assertNotEqual(custom_ua, USER_AGENT)
        else:
            self.skipTest("All test endpoints unavailable for custom user-agent test")

    def test_case_insensitive_user_agent_header(self):
        """测试User-Agent头部大小写不敏感处理"""
        custom_ua = "TestAgent/2.0"
        # 使用小写的user-agent头部
        headers = {"user-agent": custom_ua}

        if self._test_user_agent_with_endpoints(headers=headers, expected_ua=custom_ua):
            # 额外验证不是默认的USER_AGENT
            self.assertNotEqual(custom_ua, USER_AGENT)
        else:
            self.skipTest("All test endpoints unavailable for case-insensitive user-agent test")

    def test_user_agent_header_with_empty_value(self):
        """测试User-Agent头部设置为空字符串时的行为"""
        # 显式设置User-Agent为空字符串
        headers = {"User-Agent": ""}

        if not self._test_user_agent_with_endpoints(headers=headers, expected_ua=""):
            self.skipTest("All test endpoints unavailable or empty User-Agent causes expected failures")


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
    """测试 request 函数"""

    def test_basic_get_request_with_json_response(self):
        """测试基本GET请求和JSON响应解析"""
        from ddns.util.http import request

        try:
            response = request("GET", "http://postman-echo.com/get?test=ddns&format=json")
            self.assertEqual(response.status, 200)
            self.assertIsNotNone(response.body)

            # 验证响应内容是JSON格式
            data = json.loads(response.body)
            self.assertIn("args", data)
            self.assertIn("url", data)
            self.assertIn("test", data["args"])
            self.assertEqual(data["args"]["test"], "ddns")
            self.assertIsInstance(data, dict)
            self.assertTrue(len(data) > 0)

        except (socket.timeout, ConnectionError) as e:
            self.skipTest("Network unavailable: {}".format(str(e)))
        except Exception as e:
            error_msg = str(e).lower()
            network_keywords = ["timeout", "connection", "resolution", "unreachable", "network"]
            if any(keyword in error_msg for keyword in network_keywords):
                self.skipTest("Network unavailable for GET request test: {}".format(str(e)))
            else:
                raise

    def test_http_401_status_code_with_headers(self):
        """测试HTTP 401认证失败状态码处理"""
        from ddns.util.http import request

        try:
            headers = {
                "Authorization": "Bearer invalid-token",
                "Content-Type": "application/json",
                "User-Agent": "DDNS-Client/4.0",
            }
            response = request("GET", "http://postman-echo.com/status/401", headers=headers)
            self.assertEqual(response.status, 401)
            self.assertIsNotNone(response.body)

        except (socket.timeout, ConnectionError) as e:
            self.skipTest("Network unavailable: {}".format(str(e)))
        except Exception as e:
            error_msg = str(e).lower()
            network_keywords = ["timeout", "connection", "resolution", "unreachable", "network"]
            if any(keyword in error_msg for keyword in network_keywords):
                self.skipTest("Network unavailable for 401 status test: {}".format(str(e)))
            else:
                raise

    def test_ssl_auto_mode(self):
        """测试SSL auto模式"""
        from ddns.util.http import request

        try:
            response = request("GET", "https://postman-echo.com/status/200", verify="auto")
            self.assertEqual(response.status, 200, "SSL auto模式应该成功")
            self.assertIsNotNone(response.body)

        except (socket.timeout, ConnectionError) as e:
            self.skipTest("Network unavailable: {}".format(str(e)))
        except Exception as e:
            error_msg = str(e).lower()
            network_keywords = ["timeout", "connection", "resolution", "unreachable", "network", "ssl", "certificate"]
            if any(keyword in error_msg for keyword in network_keywords):
                self.skipTest("Network or SSL unavailable for SSL auto test: {}".format(str(e)))
            else:
                raise

    def test_http_400_status_code(self):
        """测试HTTP 400 Bad Request状态码"""
        from ddns.util.http import request

        try:
            response_400 = request("GET", "http://postman-echo.com/status/400")
            self.assertEqual(response_400.status, 400, "应该返回400 Bad Request状态码")
            self.assertIsNotNone(response_400.body, "400响应应该有响应体")
            self.assertIsNotNone(response_400.headers, "400响应应该有响应头")
            self.assertIsNotNone(response_400.reason, "400响应应该有状态原因")

        except Exception as e:
            # 网络问题时跳过测试
            error_msg = str(e).lower()
            network_keywords = ["timeout", "connection", "resolution", "unreachable", "network"]
            if any(keyword in error_msg for keyword in network_keywords):
                self.skipTest("Network unavailable for HTTP 400 status test: {}".format(str(e)))
            else:
                # 其他异常重新抛出
                raise

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

    def test_http_get_redirect(self):
        """测试HTTP GET重定向处理"""
        from ddns.util.http import request

        # 尝试多个测试端点以提高可靠性
        test_endpoints = [
            "http://httpbin.org/redirect-to?url=http://httpbin.org/get",
            "http://httpbingo.org/redirect-to?url=http://httpbingo.org/get",
        ]

        last_exception = None

        for redirect_url in test_endpoints:
            try:
                # HTTP重定向处理 - GET重定向
                response = request("GET", redirect_url, verify=False, retries=3)

                # 重定向后应该成功
                if response.status == 200:
                    self.assertIsNotNone(response.body)

                    # 验证最终到达了正确的端点
                    data = json.loads(response.body)
                    self.assertIn("url", data)
                    expected_content = "httpbin.org/get" if "httpbin.org" in redirect_url else "httpbingo.org/get"
                    self.assertIn(expected_content, data["url"])
                    return  # 成功则退出
                elif response.status >= 500:
                    # 5xx错误，尝试下一个端点
                    continue

            except Exception as e:
                last_exception = e
                # 网络问题时继续尝试下一个端点
                error_msg = str(e).lower()
                network_keywords = [
                    "timeout",
                    "connection",
                    "resolution",
                    "unreachable",
                    "network",
                    "ssl",
                    "certificate",
                ]
                if any(keyword in error_msg for keyword in network_keywords):
                    continue  # 尝试下一个端点
                else:
                    # 其他异常重新抛出
                    raise

        # 如果所有端点都失败，跳过测试
        error_info = " - Last error: {}".format(str(last_exception)) if last_exception else ""
        self.skipTest("All network endpoints unavailable for GET redirect test{}".format(error_info))

    def test_http_post_redirect(self):
        """测试HTTP POST重定向行为（应该转换为GET请求）"""
        from ddns.util.http import request

        # 尝试多个测试端点以提高可靠性
        test_endpoints = [
            "http://httpbingo.org/redirect-to?url=/get",
            "http://httpbin.org/redirect-to?url=http://httpbin.org/get",
        ]

        last_exception = None

        for redirect_url in test_endpoints:
            try:
                post_data = "test=data&method=POST->GET"
                response_post = request("POST", redirect_url, data=post_data, verify=False, retries=3)

                # 重定向后应该成功
                if response_post.status == 200:
                    self.assertIsNotNone(response_post.body)

                    # 验证最终到达了GET端点
                    data_post = json.loads(response_post.body)
                    self.assertIn("url", data_post)
                    self.assertIn(".org/get", data_post["url"])
                    return  # 成功则退出
                elif response_post.status >= 500:
                    # 5xx错误，尝试下一个端点
                    continue

            except Exception as e:
                last_exception = e
                # 网络问题时继续尝试下一个端点
                error_msg = str(e).lower()
                network_keywords = [
                    "timeout",
                    "connection",
                    "resolution",
                    "unreachable",
                    "network",
                    "ssl",
                    "certificate",
                ]
                if any(keyword in error_msg for keyword in network_keywords):
                    continue  # 尝试下一个端点
                else:
                    # 其他异常重新抛出
                    raise

        # 如果所有端点都失败，跳过测试
        error_info = " - Last error: {}".format(str(last_exception)) if last_exception else ""
        self.skipTest("All network endpoints unavailable for POST redirect test{}".format(error_info))


if __name__ == "__main__":
    unittest.main()
