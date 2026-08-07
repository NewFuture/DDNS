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
            "https://api.ipify.org",
            "https://ipv4.ddnsip.cn",
            "https://ipinfo.io/ip",
            "https://api-ipv4.ip.sb/ip",
            "http://checkip.amazonaws.com",
        ]
        self.assertEqual(ip.PUBLIC_IPV4_APIS, expected_apis)

    def test_public_ipv6_apis_list_exists(self):
        """测试IPv6 API列表存在并包含所需的API"""
        expected_apis = [
            "https://api6.ipify.org/",
            "https://ipv6.ddnsip.cn",
            "https://api-ipv6.ip.sb/ip",
            "http://ipv6.icanhazip.com",
        ]
        self.assertEqual(ip.PUBLIC_IPV6_APIS, expected_apis)

    @patch("ddns.ip.request")
    def test_get_ip_public_mode_fallback(self, mock_request):
        """测试通过get_ip使用public模式的自动fallback功能"""

        # 模拟第一个API失败，第二个成功
        def mock_request_side_effect(method, url, **kwargs):
            if url == ip.PUBLIC_IPV4_APIS[0]:
                raise Exception("First API failed")
            elif url == ip.PUBLIC_IPV4_APIS[1]:
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
    def test_get_ip_multiple_url_rules_fallback(self, mock_request):
        """测试get_ip在多个URL规则之间回退"""

        def mock_request_side_effect(method, url, **kwargs):
            mock_response = MagicMock()
            if url == "https://primary.example.com/ip":
                mock_response.body = "invalid response"
            elif url == "https://backup.example.com/ip":
                mock_response.body = "1.2.3.4"
            else:
                raise Exception("Unexpected URL")
            return mock_response

        mock_request.side_effect = mock_request_side_effect

        result = get_ip("4", ["url:https://primary.example.com/ip", "url:https://backup.example.com/ip"])

        self.assertEqual(result, "1.2.3.4")
        self.assertEqual(mock_request.call_count, 2)

    @patch("ddns.ip.request")
    def test_get_ip_multiple_rules_fallback(self, mock_request):
        """测试get_ip在规则返回空结果时继续尝试下一条"""

        def mock_request_side_effect(method, url, **kwargs):
            mock_response = MagicMock()
            if url in ip.PUBLIC_IPV4_APIS:
                mock_response.body = "invalid response"
            elif url == "https://backup.api.com/ip":
                mock_response.body = "1.2.3.4"
            else:
                raise Exception("Unexpected URL")
            return mock_response

        mock_request.side_effect = mock_request_side_effect

        result = get_ip("4", ["public", "url:https://backup.api.com/ip"])

        self.assertEqual(result, "1.2.3.4")
        self.assertEqual(mock_request.call_count, len(ip.PUBLIC_IPV4_APIS) + 1)

    @patch("ddns.ip.os_name", "posix")
    @patch("ddns.ip.try_run")
    def test_regex_v4_uses_ip_address(self, mock_try_run):
        """测试Unix IPv4正则通过参数列表执行ip命令"""
        mock_try_run.return_value = "2: eth0\n    inet 192.0.2.10/24 scope global eth0\n"

        result = ip.regex_v4(r"192\.0\.2\..*")

        self.assertEqual(result, "192.0.2.10")
        mock_try_run.assert_called_once_with(["ip", "address"])

    @patch("ddns.ip.os_name", "posix")
    @patch("ddns.ip.try_run")
    def test_regex_v6_uses_ip_address(self, mock_try_run):
        """测试Unix IPv6正则通过参数列表执行ip命令"""
        mock_try_run.return_value = "2: eth0\n    inet6 2409:8a00::1/64 scope global\n"

        result = ip.regex_v6(r"2409:.*")

        self.assertEqual(result, "2409:8a00::1")
        mock_try_run.assert_called_once_with(["ip", "address"])

    @patch("ddns.ip.os_name", "posix")
    @patch("ddns.ip.try_run")
    def test_regex_falls_back_to_ifconfig_when_ip_fails(self, mock_try_run):
        """测试ip命令失败时直接执行ifconfig"""
        mock_try_run.side_effect = [None, "inet addr:198.51.100.7 Mask:255.255.255.0\n"]

        result = ip.regex_v4(r"198\.51\.100\..*")

        self.assertEqual(result, "198.51.100.7")
        self.assertEqual(mock_try_run.call_args_list[0][0][0], ["ip", "address"])
        self.assertEqual(mock_try_run.call_args_list[1][0][0], ["ifconfig"])

    @patch("ddns.ip.os_name", "posix")
    @patch("ddns.ip.try_run")
    def test_regex_does_not_fallback_after_successful_ip_command(self, mock_try_run):
        """测试ip命令成功但不匹配时不执行ifconfig"""
        mock_try_run.return_value = "2: eth0\n    inet 192.0.2.10/24 scope global eth0\n"

        result = ip.regex_v4(r"172\.16\..*")

        self.assertIsNone(result)
        mock_try_run.assert_called_once_with(["ip", "address"])

    @patch("ddns.ip.os_name", "posix")
    @patch("ddns.ip.try_run")
    def test_regex_returns_none_when_network_commands_fail(self, mock_try_run):
        """测试ip和ifconfig均失败时返回空结果"""
        mock_try_run.side_effect = [None, None]

        result = ip.regex_v4(r".*")

        self.assertIsNone(result)
        self.assertEqual(mock_try_run.call_count, 2)

    @patch("ddns.ip.os_name", "nt")
    @patch("ddns.ip.try_run")
    def test_regex_v4_uses_ipconfig_on_windows(self, mock_try_run):
        """测试Windows IPv4正则直接执行ipconfig"""
        mock_try_run.return_value = "IPv4 Address. . . . . . . . . . . : 203.0.113.9\r\n"

        result = ip.regex_v4(r"203\.0\.113\..*")

        self.assertEqual(result, "203.0.113.9")
        mock_try_run.assert_called_once_with(["ipconfig"])

    @patch("ddns.ip.public_v4")
    @patch("ddns.ip.os_name", "posix")
    @patch("ddns.ip.try_run")
    def test_get_ip_regex_rule_fallback(self, mock_try_run, mock_public_v4):
        """测试regex规则返回空结果时继续回退"""
        mock_try_run.return_value = "inet 192.168.1.10/24\ninet 10.0.0.2/24\n"
        mock_public_v4.return_value = "1.2.3.4"

        result = get_ip("4", ["regex:172\\.16\\..*", "public"])

        self.assertEqual(result, "1.2.3.4")
        mock_public_v4.assert_called_once_with()

    @patch("ddns.ip.public_v4")
    @patch("ddns.__main__.check_output")
    def test_get_ip_cmd_rule_fallback_on_empty_output(self, mock_check_output, mock_public_v4):
        """测试cmd规则输出为空时继续回退"""
        mock_check_output.return_value = b""
        mock_public_v4.return_value = "1.2.3.4"

        result = get_ip("4", ["cmd:test-ip", "public"])

        self.assertEqual(result, "1.2.3.4")
        mock_check_output.assert_called_once_with("test-ip")
        mock_public_v4.assert_called_once_with()

    @patch("ddns.ip.public_v4")
    @patch("ddns.__main__.check_output")
    def test_get_ip_shell_rule_fallback_on_empty_output(self, mock_check_output, mock_public_v4):
        """测试shell规则输出为空时继续回退"""
        mock_check_output.return_value = b""
        mock_public_v4.return_value = "1.2.3.4"

        result = get_ip("4", ["shell:test-ip", "public"])

        self.assertEqual(result, "1.2.3.4")
        mock_check_output.assert_called_once_with("test-ip", shell=True)
        mock_public_v4.assert_called_once_with()

    @patch("ddns.ip.request")
    def test_get_ip_ipv6_rule_fallback(self, mock_request):
        """测试IPv6规则链在空结果时继续回退"""

        def mock_request_side_effect(method, url, **kwargs):
            mock_response = MagicMock()
            if url == "https://primary.example.com/ipv6":
                mock_response.body = "invalid response"
            elif url == "https://backup.example.com/ipv6":
                mock_response.body = "2001:db8::1"
            else:
                raise Exception("Unexpected URL")
            return mock_response

        mock_request.side_effect = mock_request_side_effect

        result = get_ip("6", ["url:https://primary.example.com/ipv6", "url:https://backup.example.com/ipv6"])

        self.assertEqual(result, "2001:db8::1")
        self.assertEqual(mock_request.call_count, 2)


if __name__ == "__main__":
    unittest.main()
