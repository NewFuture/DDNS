# -*- coding:utf-8 -*-
"""
Integration tests for IP module and main functionality
"""
from __init__ import unittest, patch, MagicMock
from ddns.__main__ import get_ip


class TestIpIntegration(unittest.TestCase):
    """测试IP获取集成功能"""

    @patch('ddns.ip.request')
    def test_get_ip_public_mode_fallback(self, mock_request):
        """测试通过get_ip使用public模式的自动fallback功能"""
        # 模拟第一个API失败，第二个成功
        def mock_request_side_effect(method, url, **kwargs):
            if "api.ipify.cn" in url:
                raise Exception("First API failed")
            elif "api.ipify.org" in url:
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

    @patch('ddns.ip.request')
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

    @patch('ddns.ip.request')
    def test_get_ip_multiple_rules_limitation(self, mock_request):
        """测试get_ip的多规则限制 - 当前实现的限制"""
        # 注意：当前get_ip实现有限制 - 如果一个规则返回None，它不会尝试下一个规则
        # 只有当规则抛出异常时才会尝试下一个规则
        # 这是一个已知限制，不在本次功能实现范围内
        
        # 模拟所有public API都失败（返回无效响应）
        mock_response = MagicMock()
        mock_response.body = "invalid response"
        mock_request.return_value = mock_response
        
        # 使用多个规则：先尝试public，失败后应该尝试url:指定的API
        # 但由于当前实现限制，public返回None后不会尝试下一个规则
        result = get_ip("4", ["public", "url:https://backup.api.com/ip"])
        
        # 由于当前实现限制，返回None而不是继续尝试backup API
        self.assertIsNone(result)
        # 只调用了public APIs，没有调用backup API
        self.assertEqual(mock_request.call_count, len(__import__('ddns.ip', fromlist=['PUBLIC_IPV4_APIS']).PUBLIC_IPV4_APIS))


if __name__ == '__main__':
    unittest.main()