# coding=utf-8
"""
Unit tests for CallbackProvider

@author: Testing Suite
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the ddns module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from unittest.mock import patch
except ImportError:
    # Python 2.7 compatibility
    from mock import patch

from ddns.provider.callback import CallbackProvider


class TestCallbackProvider(unittest.TestCase):
    """Test cases for CallbackProvider"""

    def setUp(self):
        """Set up test fixtures"""
        self.auth_id = "https://example.com/callback?domain=__DOMAIN__&ip=__IP__"
        self.auth_token = ""  # Use empty string instead of None for auth_token

    def test_init_with_basic_config(self):
        """Test CallbackProvider initialization with basic configuration"""
        provider = CallbackProvider(self.auth_id, self.auth_token)
        self.assertEqual(provider.auth_id, self.auth_id)
        self.assertEqual(provider.auth_token, self.auth_token)
        self.assertFalse(provider.DecodeResponse)

    def test_init_with_token_config(self):
        """Test CallbackProvider initialization with token configuration"""
        auth_token = '{"api_key": "__DOMAIN__", "value": "__IP__"}'
        provider = CallbackProvider(self.auth_id, auth_token)
        self.assertEqual(provider.auth_token, auth_token)

    def test_validate_success(self):
        """Test _validate method with valid configuration"""
        provider = CallbackProvider(self.auth_id, self.auth_token)
        # Should not raise any exception since we have a valid auth_id
        provider._validate()

    def test_validate_failure_no_id(self):
        """Test _validate method with missing id"""
        # _validate is called in __init__, so we need to test it directly
        with self.assertRaises(ValueError) as cm:
            CallbackProvider(None, self.auth_token)  # type: ignore
        self.assertIn("id must be configured", str(cm.exception))

    def test_validate_failure_empty_id(self):
        """Test _validate method with empty id"""
        # _validate is called in __init__, so we need to test it directly
        with self.assertRaises(ValueError) as cm:
            CallbackProvider("", self.auth_token)
        self.assertIn("id must be configured", str(cm.exception))

    def test_replace_vars_basic(self):
        """Test _replace_vars method with basic replacements"""
        provider = CallbackProvider(self.auth_id, self.auth_token)

        test_str = "Hello __NAME__, your IP is __IP__"
        mapping = {"__NAME__": "World", "__IP__": "192.168.1.1"}

        result = provider._replace_vars(test_str, mapping)
        expected = "Hello World, your IP is 192.168.1.1"
        self.assertEqual(result, expected)

    def test_replace_vars_no_matches(self):
        """Test _replace_vars method with no matching variables"""
        provider = CallbackProvider(self.auth_id, self.auth_token)

        test_str = "No variables here"
        mapping = {"__NAME__": "World"}

        result = provider._replace_vars(test_str, mapping)
        self.assertEqual(result, test_str)

    def test_replace_vars_partial_matches(self):
        """Test _replace_vars method with partial matches"""
        provider = CallbackProvider(self.auth_id, self.auth_token)

        test_str = "__DOMAIN__ and __UNKNOWN__ and __IP__"
        mapping = {"__DOMAIN__": "example.com", "__IP__": "1.2.3.4"}

        result = provider._replace_vars(test_str, mapping)
        expected = "example.com and __UNKNOWN__ and 1.2.3.4"
        self.assertEqual(result, expected)

    def test_replace_vars_empty_string(self):
        """Test _replace_vars method with empty string"""
        provider = CallbackProvider(self.auth_id, self.auth_token)

        result = provider._replace_vars("", {"__TEST__": "value"})
        self.assertEqual(result, "")

    def test_replace_vars_empty_mapping(self):
        """Test _replace_vars method with empty mapping"""
        provider = CallbackProvider(self.auth_id, self.auth_token)

        test_str = "__DOMAIN__ test"
        result = provider._replace_vars(test_str, {})
        self.assertEqual(result, test_str)

    def test_replace_vars_none_values(self):
        """Test _replace_vars method with None values (should convert to string)"""
        provider = CallbackProvider(self.auth_id, self.auth_token)

        test_str = "TTL: __TTL__, Line: __LINE__"
        mapping = {"__TTL__": None, "__LINE__": None}

        result = provider._replace_vars(test_str, mapping)
        expected = "TTL: None, Line: None"
        self.assertEqual(result, expected)

    def test_replace_vars_numeric_values(self):
        """Test _replace_vars method with numeric values (should convert to string)"""
        provider = CallbackProvider(self.auth_id, self.auth_token)

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

        provider = CallbackProvider(self.auth_id, None)  # type: ignore

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

        auth_token = {"api_key": "test_key", "domain": "__DOMAIN__", "ip": "__IP__"}
        provider = CallbackProvider(self.auth_id, auth_token)  # type: ignore

        result = provider.set_record("example.com", "192.168.1.1", "A", 300, "default")

        # Verify the result
        self.assertTrue(result)        # Verify _http was called with correct parameters
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

        auth_token = '{"api_key": "test_key", "domain": "__DOMAIN__", "ip": "__IP__"}'
        provider = CallbackProvider(self.auth_id, auth_token)

        result = provider.set_record("example.com", "192.168.1.1", "A", 300, "default")

        # Verify the result
        self.assertTrue(result)        # Verify _http was called with correct parameters
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
        
        auth_token = {"api_key": 12345, "domain": "__DOMAIN__", "timeout": 30, "enabled": True}
        provider = CallbackProvider(self.auth_id, auth_token)  # type: ignore
        
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

        provider = CallbackProvider(self.auth_id, None)  # type: ignore

        result = provider.set_record("example.com", "192.168.1.1")

        # Verify the result is False on failure
        self.assertFalse(result)

    @patch("ddns.provider.callback.time")
    @patch.object(CallbackProvider, "_http")
    def test_set_record_http_empty_response(self, mock_http, mock_time):
        """Test set_record method with empty HTTP response"""
        mock_time.return_value = 1634567890.123
        mock_http.return_value = ""  # Empty response

        provider = CallbackProvider(self.auth_id, None)  # type: ignore

        result = provider.set_record("example.com", "192.168.1.1")

        # Empty string is falsy, so result should be False
        self.assertFalse(result)

    @patch("ddns.provider.callback.jsondecode")
    def test_json_decode_error_handling(self, mock_jsondecode):
        """Test handling of JSON decode errors in POST method"""
        mock_jsondecode.side_effect = ValueError("Invalid JSON")

        auth_token = "invalid json"
        provider = CallbackProvider(self.auth_id, auth_token)

        # This should raise an exception when trying to decode invalid JSON
        with self.assertRaises(ValueError):
            provider.set_record("example.com", "192.168.1.1")


if __name__ == "__main__":
    unittest.main()
