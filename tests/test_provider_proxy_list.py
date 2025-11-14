# coding=utf-8
"""
测试 provider 基类的代理列表功能
Test provider base class proxy list functionality
"""

from base_test import BaseProviderTestCase, patch, unittest
from ddns.provider._base import SimpleProvider
from ddns.util.http import HttpResponse


class TestSimpleProvider(SimpleProvider):
    """测试用的简单Provider实现"""

    endpoint = "https://api.example.com"

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        # type: (str, str, str, str | int | None, str | None, **object) -> bool
        """简单的set_record实现用于测试"""
        return self._http("POST", "/set", body={"domain": domain, "value": value})


class TestProviderProxyList(BaseProviderTestCase):
    """测试Provider代理列表功能"""

    def setUp(self):
        """设置测试环境"""
        super(TestProviderProxyList, self).setUp()
        # 创建一个包含代理列表的provider
        self.proxy_list = ["http://proxy1:8080", "http://proxy2:8080", None]

    @patch("ddns.provider._base.request")
    def test_provider_http_with_proxy_list(self, mock_request):
        """测试Provider使用代理列表发送HTTP请求"""
        # 模拟成功响应
        mock_response = HttpResponse(200, "OK", {}, '{"status": "success", "data": "test"}')
        mock_request.return_value = mock_response

        # 创建provider并设置代理列表
        provider = TestSimpleProvider(self.id, self.token, proxy=self.proxy_list)

        # 调用_http方法
        result = provider._http("GET", "/test")

        # 验证结果（应该是解析后的JSON）
        self.assertEqual(result["status"], "success")

        # 验证request被正确调用，传递了proxies参数
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["proxies"], self.proxy_list)

    @patch("ddns.provider._base.request")
    def test_provider_http_with_single_proxy_backward_compatibility(self, mock_request):
        """测试Provider单个代理列表"""
        # 模拟成功响应
        mock_response = HttpResponse(200, "OK", {}, '{"status": "success", "data": "test"}')
        mock_request.return_value = mock_response

        # 创建provider并设置单个代理列表
        single_proxy_list = ["http://single-proxy:8080"]
        provider = TestSimpleProvider(self.id, self.token, proxy=single_proxy_list)

        # 调用_http方法
        result = provider._http("GET", "/test")

        # 验证结果
        self.assertEqual(result["status"], "success")

        # 验证request被正确调用
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["proxies"], single_proxy_list)

    @patch("ddns.provider._base.request")
    def test_provider_http_no_proxy(self, mock_request):
        """测试Provider没有代理时的默认行为"""
        # 模拟成功响应
        mock_response = HttpResponse(200, "OK", {}, '{"status": "success", "data": "test"}')
        mock_request.return_value = mock_response

        # 创建provider不设置代理
        provider = TestSimpleProvider(self.id, self.token)

        # 调用_http方法
        result = provider._http("GET", "/test")

        # 验证结果
        self.assertEqual(result["status"], "success")

        # 验证request被正确调用
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["proxies"], None)

    @patch("ddns.provider._base.request")
    def test_provider_http_empty_proxy_list(self, mock_request):
        """测试Provider空代理列表时的默认行为"""
        # 模拟成功响应
        mock_response = HttpResponse(200, "OK", {}, '{"status": "success", "data": "test"}')
        mock_request.return_value = mock_response

        # 创建provider设置空代理列表
        provider = TestSimpleProvider(self.id, self.token, proxy=[])

        # 调用_http方法
        result = provider._http("GET", "/test")

        # 验证结果
        self.assertEqual(result["status"], "success")

        # 验证request被正确调用
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["proxies"], [])

    @patch("ddns.provider._base.request")
    def test_provider_http_request_failure_handling(self, mock_request):
        """测试Provider处理请求失败的情况"""
        # 模拟请求失败
        mock_request.side_effect = RuntimeError("All proxies failed")

        # 创建provider
        provider = TestSimpleProvider(self.id, self.token, proxy=self.proxy_list)

        # 调用_http方法应该抛出异常
        with self.assertRaises(RuntimeError) as context:
            provider._http("GET", "/test")

        self.assertIn("All proxies failed", str(context.exception))

    def test_provider_initialization_with_proxy_types(self):
        """测试Provider初始化时不同代理参数类型的处理"""
        # 测试代理列表
        proxy_list = ["http://proxy1:8080", "http://proxy2:8080", None]
        provider1 = TestSimpleProvider(self.id, self.token, proxy=proxy_list)
        self.assertEqual(provider1._proxy, proxy_list)

        # 测试单项代理列表
        single_proxy_list = ["http://proxy:8080"]
        provider2 = TestSimpleProvider(self.id, self.token, proxy=single_proxy_list)
        self.assertEqual(provider2._proxy, single_proxy_list)

        # 测试None代理
        provider3 = TestSimpleProvider(self.id, self.token, proxy=None)
        self.assertEqual(provider3._proxy, None)

        # 测试空列表代理
        provider4 = TestSimpleProvider(self.id, self.token, proxy=[])
        self.assertEqual(provider4._proxy, [])


if __name__ == "__main__":
    unittest.main()
