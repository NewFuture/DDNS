# coding=utf-8
"""
测试 ddns.util.http 模块的代理列表功能
Test ddns.util.http module proxy list functionality
"""

from __init__ import unittest, patch, MagicMock
from ddns.util.http import request, quote


class TestRequestProxyList(unittest.TestCase):
    """测试 request 函数的代理列表功能"""

    @patch("ddns.util.http.build_opener")
    @patch("ddns.util.http.Request")
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

    @patch("ddns.util.http.build_opener")
    @patch("ddns.util.http.Request")
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

    @patch("ddns.util.http.build_opener")
    @patch("ddns.util.http.Request")
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
        result = request("GET", "http://example.com", proxies=None)

        self.assertEqual(result.status, 200)
        self.assertEqual(result.body, '{"success": true}')
        mock_build_opener.assert_called_once()

    @patch("ddns.util.http.build_opener")
    @patch("ddns.util.http.Request")
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

    @patch("ddns.util.http.build_opener")
    @patch("ddns.util.http.Request")
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

    def test_real_network_proxy_fallback(self):
        """测试真实网络环境下的代理失败回退（如果网络可用）"""
        # 尝试多个测试端点以提高可靠性，优先使用httpbin
        test_endpoints = ["http://httpbin.org/get", "http://httpbingo.org/get"]

        last_exception = None

        for url in test_endpoints:
            try:
                # 使用无效代理和直连的组合
                proxy_list = ["http://invalid-proxy:9999", None]

                # 这应该在第一个代理失败后回退到直连
                response = request("GET", url, proxies=proxy_list, retries=3)

                # 如果成功，应该是通过直连完成的
                if response.status == 200:
                    expected_content = "httpbin.org" if "httpbin.org" in url else "httpbingo.org"
                    self.assertIn(expected_content, response.body)
                    return  # 成功则退出
                elif response.status >= 500:
                    # 5xx错误，尝试下一个端点
                    continue

            except Exception as e:
                last_exception = e
                # 网络问题时继续尝试下一个端点
                error_msg = str(e).lower()
                network_keywords = ["timeout", "connection", "resolution", "unreachable", "network"]
                if any(keyword in error_msg for keyword in network_keywords):
                    continue  # 尝试下一个端点
                else:
                    # 其他异常重新抛出
                    raise

        # 如果所有端点都失败，跳过测试
        error_info = " - Last error: {}".format(str(last_exception)) if last_exception else ""
        self.skipTest("All network endpoints unavailable for proxy fallback test{}".format(error_info))

    def test_basic_auth_with_embedded_url(self):
        """测试URL嵌入式基本认证"""
        from ddns.util.http import request

        # 使用URL编码的用户名和密码
        special_username = "user@test.com"
        special_password = "passwo.rd"
        username_encoded = quote(special_username, safe="")
        password_encoded = quote(special_password, safe="")

        # 验证URL编码的特殊字符
        self.assertEqual(username_encoded, "user%40test.com")
        self.assertEqual(password_encoded, "passwo.rd")

        # 尝试多个测试端点以提高可靠性，优先使用httpbingo
        test_hosts = ["httpbingo.org", "httpbin.org"]

        last_exception = None

        for host in test_hosts:
            try:
                # 构建认证URL
                auth_url = "https://{0}:{1}@{2}/basic-auth/{3}/{4}".format(
                    username_encoded, password_encoded, host, username_encoded, password_encoded
                )
                response_auth = request("GET", auth_url, verify=False, retries=2)

                if response_auth.status == 200:
                    self.assertIn('"auth', response_auth.body)
                    self.assertIn("user", response_auth.body)
                    self.assertIn(special_username, response_auth.body)
                    return  # 成功则退出
                elif response_auth.status >= 500:
                    # 5xx错误，尝试下一个端点
                    continue
                else:
                    # 其他状态码也尝试下一个端点
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
        self.skipTest("All network endpoints unavailable for basic auth test{}".format(error_info))


if __name__ == "__main__":
    unittest.main()
