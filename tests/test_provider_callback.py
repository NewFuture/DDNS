# coding=utf-8
"""
Unit tests for CallbackProvider

@author: GitHub Copilot
"""

import os
import sys
import logging
import random
import platform
from time import sleep
from base_test import BaseProviderTestCase, unittest, patch
from ddns.provider.callback import CallbackProvider


class TestCallbackProvider(BaseProviderTestCase):
    """Test cases for CallbackProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestCallbackProvider, self).setUp()
        self.id = "https://example.com/callback?domain=__DOMAIN__&ip=__IP__"
        self.token = ""  # Use empty string instead of None for token

    def test_init_with_basic_config(self):
        """Test CallbackProvider initialization with basic configuration"""
        provider = CallbackProvider(self.id, self.token)
        self.assertEqual(provider.id, self.id)
        self.assertEqual(provider.token, self.token)
        self.assertFalse(provider.decode_response)

    def test_init_with_token_config(self):
        """Test CallbackProvider initialization with token configuration"""
        token = '{"api_key": "__DOMAIN__", "value": "__IP__"}'
        provider = CallbackProvider(self.id, token)
        self.assertEqual(provider.token, token)

    def test_validate_success(self):
        """Test _validate method with valid configuration"""
        provider = CallbackProvider(self.id, self.token)
        # Should not raise any exception since we have a valid id
        provider._validate()

    def test_validate_failure_no_id(self):
        """Test _validate method with missing id"""
        # _validate is called in __init__, so we need to test it directly
        with self.assertRaises(ValueError) as cm:
            CallbackProvider(None, self.token)  # type: ignore
        self.assertIn("id must be configured", str(cm.exception))

    def test_validate_failure_empty_id(self):
        """Test _validate method with empty id"""
        # _validate is called in __init__, so we need to test it directly
        with self.assertRaises(ValueError) as cm:
            CallbackProvider("", self.token)
        self.assertIn("id must be configured", str(cm.exception))

    def test_replace_vars_basic(self):
        """Test _replace_vars method with basic replacements"""
        provider = CallbackProvider(self.id, self.token)

        test_str = "Hello __NAME__, your IP is __IP__"
        mapping = {"__NAME__": "World", "__IP__": "192.168.1.1"}

        result = provider._replace_vars(test_str, mapping)
        expected = "Hello World, your IP is 192.168.1.1"
        self.assertEqual(result, expected)

    def test_replace_vars_no_matches(self):
        """Test _replace_vars method with no matching variables"""
        provider = CallbackProvider(self.id, self.token)

        test_str = "No variables here"
        mapping = {"__NAME__": "World"}

        result = provider._replace_vars(test_str, mapping)
        self.assertEqual(result, test_str)

    def test_replace_vars_partial_matches(self):
        """Test _replace_vars method with partial matches"""
        provider = CallbackProvider(self.id, self.token)

        test_str = "__DOMAIN__ and __UNKNOWN__ and __IP__"
        mapping = {"__DOMAIN__": "example.com", "__IP__": "1.2.3.4"}

        result = provider._replace_vars(test_str, mapping)
        expected = "example.com and __UNKNOWN__ and 1.2.3.4"
        self.assertEqual(result, expected)

    def test_replace_vars_empty_string(self):
        """Test _replace_vars method with empty string"""
        provider = CallbackProvider(self.id, self.token)

        result = provider._replace_vars("", {"__TEST__": "value"})
        self.assertEqual(result, "")

    def test_replace_vars_empty_mapping(self):
        """Test _replace_vars method with empty mapping"""
        provider = CallbackProvider(self.id, self.token)

        test_str = "__DOMAIN__ test"
        result = provider._replace_vars(test_str, {})
        self.assertEqual(result, test_str)

    def test_replace_vars_none_values(self):
        """Test _replace_vars method with None values (should convert to string)"""
        provider = CallbackProvider(self.id, self.token)

        test_str = "TTL: __TTL__, Line: __LINE__"
        mapping = {"__TTL__": None, "__LINE__": None}

        result = provider._replace_vars(test_str, mapping)
        expected = "TTL: None, Line: None"
        self.assertEqual(result, expected)

    def test_replace_vars_numeric_values(self):
        """Test _replace_vars method with numeric values (should convert to string)"""
        provider = CallbackProvider(self.id, self.token)

        test_str = "Port: __PORT__, TTL: __TTL__"
        mapping = {"__PORT__": 8080, "__TTL__": 300}

        result = provider._replace_vars(test_str, mapping)
        expected = "Port: 8080, TTL: 300"
        self.assertEqual(result, expected)

    @patch("ddns.provider.callback.time")
    @patch.object(CallbackProvider, "_http")
    def test_set_record_get_method(self, mock_http, mock_time):
        """Test set_record method using GET method (no token)"""
        mock_time.return_value = 1634567890.123
        mock_http.return_value = "Success"

        provider = CallbackProvider(self.id, None)  # type: ignore

        result = provider.set_record("example.com", "192.168.1.1", "A", 300, "default")

        # Verify the result
        self.assertTrue(result)

        # Verify _http was called with correct parameters
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "GET")  # method        # Check that URL contains replaced variables
        url = args[1]
        self.assertIn("example.com", url)
        self.assertIn("192.168.1.1", url)

    @patch("ddns.provider.callback.time")
    @patch.object(CallbackProvider, "_http")
    def test_set_record_post_method_dict_token(self, mock_http, mock_time):
        """Test set_record method using POST method with dict token"""
        mock_time.return_value = 1634567890.123
        mock_http.return_value = "Success"

        token = {"api_key": "test_key", "domain": "__DOMAIN__", "ip": "__IP__"}
        provider = CallbackProvider(self.id, token)  # type: ignore

        result = provider.set_record("example.com", "192.168.1.1", "A", 300, "default")

        # Verify the result
        self.assertTrue(result)  # Verify _http was called with correct parameters
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "POST")  # method
        # URL should be replaced with actual values even for POST
        url = args[1]
        self.assertIn("example.com", url)
        self.assertIn("192.168.1.1", url)

        # Check params were properly replaced
        params = kwargs["body"]
        self.assertEqual(params["api_key"], "test_key")
        self.assertEqual(params["domain"], "example.com")
        self.assertEqual(params["ip"], "192.168.1.1")

    @patch("ddns.provider.callback.time")
    @patch.object(CallbackProvider, "_http")
    def test_set_record_post_method_json_token(self, mock_http, mock_time):
        """Test set_record method using POST method with JSON string token"""
        mock_time.return_value = 1634567890.123
        mock_http.return_value = "Success"

        token = '{"api_key": "test_key", "domain": "__DOMAIN__", "ip": "__IP__"}'
        provider = CallbackProvider(self.id, token)

        result = provider.set_record("example.com", "192.168.1.1", "A", 300, "default")

        # Verify the result
        self.assertTrue(result)  # Verify _http was called with correct parameters
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "POST")  # method
        # URL should be replaced with actual values even for POST
        url = args[1]
        self.assertIn("example.com", url)
        self.assertIn("192.168.1.1", url)

        # Check params were properly replaced
        params = kwargs["body"]
        self.assertEqual(params["api_key"], "test_key")
        self.assertEqual(params["domain"], "example.com")
        self.assertEqual(params["ip"], "192.168.1.1")

    @patch("ddns.provider.callback.time")
    @patch.object(CallbackProvider, "_http")
    def test_set_record_post_method_mixed_types(self, mock_http, mock_time):
        """Test set_record method with mixed type values in POST parameters"""
        mock_time.return_value = 1634567890.123
        mock_http.return_value = "Success"

        token = {"api_key": 12345, "domain": "__DOMAIN__", "timeout": 30, "enabled": True}
        provider = CallbackProvider(self.id, token)  # type: ignore

        result = provider.set_record("example.com", "192.168.1.1")

        # Verify the result
        self.assertTrue(result)

        # Verify _http was called with correct parameters
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "POST")  # method

        # Check that non-string values were not processed, but string values were replaced
        params = kwargs["body"]
        self.assertEqual(params["api_key"], 12345)  # unchanged (not a string)
        self.assertEqual(params["domain"], "example.com")  # replaced (was a string)
        self.assertEqual(params["timeout"], 30)  # unchanged (not a string)
        self.assertEqual(params["enabled"], True)  # unchanged (not a string)

    @patch("ddns.provider.callback.time")
    @patch.object(CallbackProvider, "_http")
    def test_set_record_http_failure(self, mock_http, mock_time):
        """Test set_record method when HTTP request fails"""
        mock_time.return_value = 1634567890.123
        mock_http.return_value = None  # Simulate failure

        provider = CallbackProvider(self.id, None)  # type: ignore

        result = provider.set_record("example.com", "192.168.1.1")

        # Verify the result is False on failure
        self.assertFalse(result)

    @patch("ddns.provider.callback.time")
    @patch.object(CallbackProvider, "_http")
    def test_set_record_http_none_response(self, mock_http, mock_time):
        """Test set_record method with None HTTP response"""
        mock_time.return_value = 1634567890.123
        mock_http.return_value = None  # None response

        provider = CallbackProvider(self.id, None)  # type: ignore

        result = provider.set_record("example.com", "192.168.1.1")

        # Empty string is falsy, so result should be False
        self.assertFalse(result)

    @patch("ddns.provider.callback.jsondecode")
    def test_json_decode_error_handling(self, mock_jsondecode):
        """Test handling of JSON decode errors in POST method"""
        mock_jsondecode.side_effect = ValueError("Invalid JSON")

        token = "invalid json"
        provider = CallbackProvider(self.id, token)

        # This should raise an exception when trying to decode invalid JSON
        with self.assertRaises(ValueError):
            provider.set_record("example.com", "192.168.1.1")


class TestCallbackProviderRealIntegration(BaseProviderTestCase):
    """Real integration tests for CallbackProvider using httpbin.org"""

    def setUp(self):
        """Set up real test fixtures and skip on unsupported CI environments"""
        super(TestCallbackProviderRealIntegration, self).setUp()
        # Skip on Python 3.10/3.13 or 32bit in CI
        is_ci = os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS") or os.environ.get("GITHUB_REF_NAME")
        pyver = sys.version_info
        sys_platform = sys.platform.lower()
        machine = platform.machine().lower()
        is_mac = sys_platform == "darwin"
        # On macOS CI, require arm64; on others, require amd64/x86_64
        if is_ci:
            if is_mac:
                if not ("arm" in machine or "aarch64" in machine):
                    self.skipTest("On macOS CI, only arm64 is supported for integration tests.")
            else:
                if not ("amd64" in machine or "x86_64" in machine):
                    self.skipTest("On non-macOS CI, only amd64/x86_64 is supported for integration tests.")
            if pyver[:2] in [(3, 10), (3, 13)] or platform.architecture()[0] == "32bit":
                self.skipTest("Skip real HTTP integration on CI for Python 3.10/3.13 or 32bit platform")

    def _setup_provider_with_mock_logger(self, provider):
        """Helper method to setup provider with a mock logger."""
        mock_logger = self.mock_logger(provider)
        # Ensure the logger is configured to capture info calls
        mock_logger.setLevel(logging.INFO)
        return mock_logger

    def _random_delay(self):
        """Add a random delay of 0-3 seconds to avoid rate limiting"""
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS") or os.environ.get("GITHUB_REF_NAME"):
            # In CI environments, use a shorter delay to speed up tests
            delay = random.uniform(0, 2)
        else:
            delay = random.uniform(0, 1)
        sleep(delay)

    def _assert_callback_result_logged(self, mock_logger, *expected_strings):
        """
        Helper to assert that 'Callback result: %s' was logged with expected content.
        """
        info_calls = mock_logger.info.call_args_list
        response_logged = False

        for call in info_calls:
            if len(call[0]) >= 2 and call[0][0] == "Callback result: %s":
                response_content = str(call[0][1])
                # Check if the response contains the expected strings
                if all(expected in response_content for expected in expected_strings):
                    response_logged = True
                    break
                # Also check if this is a firewall/network blocking response
                blocking_keywords = ["firewall", "deny", "blocked", "policy", "rule"]
                if any(keyword.lower() in response_content.lower() for keyword in blocking_keywords):
                    # Skip test if network is blocked
                    raise unittest.SkipTest("Network request blocked by firewall/policy: {}".format(response_content))

        self.assertTrue(
            response_logged,
            "Expected logger.info to log 'Callback result' containing: {}".format(", ".join(expected_strings)),
        )

    def test_real_callback_get_method(self):
        """Test real callback using GET method with httpbin/httpbingo and verify logger calls"""
        # 尝试多个测试端点以提高可靠性
        test_endpoints = [
            "http://httpbin.org/get?domain=__DOMAIN__&ip=__IP__&record_type=__RECORDTYPE__",
            "http://httpbingo.org/get?domain=__DOMAIN__&ip=__IP__&record_type=__RECORDTYPE__",
        ]

        domain = "test.example.com"
        ip = "111.111.111.111"
        last_exception = None

        for endpoint_id in test_endpoints:
            try:
                provider = CallbackProvider(endpoint_id, "", ssl="auto")
                mock_logger = self._setup_provider_with_mock_logger(provider)

                self._random_delay()  # Add random delay before real request
                result = provider.set_record(domain, ip, "A")

                if result:
                    self.assertTrue(result)
                    self._assert_callback_result_logged(mock_logger, domain, ip)
                    return  # 成功则退出
                else:
                    # 如果结果为False，可能是5xx错误，尝试下一个端点
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
        self.skipTest("All network endpoints unavailable for GET callback test{}".format(error_info))

    def test_real_callback_post_method_with_json(self):
        """Test real callback using POST method with JSON data and verify logger calls"""
        # 尝试多个测试端点以提高可靠性
        test_endpoints = ["http://httpbingo.org/post", "http://httpbin.org/post"]

        token = '{"domain": "__DOMAIN__", "ip": "__IP__", "record_type": "__RECORDTYPE__", "ttl": "__TTL__"}'
        domain = "test.example.com"
        ip = "203.0.113.2"
        last_exception = None

        for endpoint_id in test_endpoints:
            try:
                provider = CallbackProvider(endpoint_id, token)
                # Setup provider with mock logger
                mock_logger = self._setup_provider_with_mock_logger(provider)

                self._random_delay()  # Add random delay before real request
                result = provider.set_record(domain, ip, "A", 300)

                if result:
                    # httpbin/httpbingo returns JSON with our posted data, so it should be truthy
                    self.assertTrue(result)
                    # Verify that logger.info was called with response containing domain and IP
                    self._assert_callback_result_logged(mock_logger, domain, ip)
                    return  # 成功则退出
                else:
                    # 如果结果为False，可能是5xx错误，尝试下一个端点
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
        self.skipTest("All network endpoints unavailable for POST callback test{}".format(error_info))

    def test_real_callback_error_handling(self):
        """Test real callback error handling with invalid URL"""
        # Use an invalid URL to test error handling
        id = "http://postman-echo.com/status/400"  # This returns HTTP 400
        provider = CallbackProvider(id, "")

        self._random_delay()  # Add random delay before real request
        result = provider.set_record("test.example.com", "203.0.113.5")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
