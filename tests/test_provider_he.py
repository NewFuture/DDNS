# coding=utf-8
"""
Unit tests for HeProvider (Hurricane Electric)

@author: Github Copilot
"""

from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.he import HeProvider


class TestHeProvider(BaseProviderTestCase):
    """Test cases for HeProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestHeProvider, self).setUp()
        # Override default auth values for HE provider
        self.auth_id = "test_id"
        self.auth_token = "test_password"

    def test_init_with_basic_config(self):
        """Test HeProvider initialization with basic configuration"""
        provider = HeProvider(self.auth_id, self.auth_token)
        self.assertEqual(provider.auth_id, self.auth_id)
        self.assertEqual(provider.auth_token, self.auth_token)
        self.assertEqual(provider.API, "https://dyn.dns.he.net")
        self.assertFalse(provider.decode_response)

    def test_class_constants(self):
        """Test HeProvider class constants"""
        provider = HeProvider(self.auth_id, self.auth_token)
        self.assertEqual(provider.API, "https://dyn.dns.he.net")
        self.assertFalse(provider.decode_response)
        # ContentType should be form-encoded
        from ddns.provider._base import TYPE_FORM

        self.assertEqual(provider.content_type, TYPE_FORM)

    def test_validate_always_passes(self):
        """Test _validate method always passes (no validation required)"""
        provider = HeProvider(self.auth_id, self.auth_token)
        # Should not raise any exception
        provider._validate()

    def test_validate_with_none_values(self):
        """Test _validate method with None values still passes"""
        provider = HeProvider("", None)  # type: ignore
        # Should not raise any exception even with None values
        provider._validate()

    @patch.object(HeProvider, "_http")
    def test_set_record_success_good_response(self, mock_http):
        """Test set_record method with 'good' response"""
        mock_http.return_value = "good 192.168.1.1"

        provider = HeProvider(self.auth_id, self.auth_token)

        result = provider.set_record("example.com", "192.168.1.1", "A")

        # Verify the result
        self.assertEqual(result, "good 192.168.1.1")

        # Verify _http was called with correct parameters
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "POST")  # method
        self.assertEqual(args[1], "/nic/update")  # path

        # Check body parameters
        body = kwargs["body"]
        self.assertEqual(body["hostname"], "example.com")
        self.assertEqual(body["myip"], "192.168.1.1")
        self.assertEqual(body["password"], self.auth_token)

    @patch.object(HeProvider, "_http")
    def test_set_record_success_nochg_response(self, mock_http):
        """Test set_record method with 'nochg' response"""
        mock_http.return_value = "nochg 192.168.1.1"

        provider = HeProvider(self.auth_id, self.auth_token)

        result = provider.set_record("test.example.com", "192.168.1.1", "A")

        # Verify the result
        self.assertEqual(result, "nochg 192.168.1.1")

        # Verify _http was called with correct parameters
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "POST")
        self.assertEqual(args[1], "/nic/update")

        # Check body parameters
        body = kwargs["body"]
        self.assertEqual(body["hostname"], "test.example.com")
        self.assertEqual(body["myip"], "192.168.1.1")
        self.assertEqual(body["password"], self.auth_token)

    @patch.object(HeProvider, "_http")
    def test_set_record_ipv6_address(self, mock_http):
        """Test set_record method with IPv6 address"""
        mock_http.return_value = "good 2001:db8::1"

        provider = HeProvider(self.auth_id, self.auth_token)

        result = provider.set_record("ipv6.example.com", "2001:db8::1", "AAAA")

        # Verify the result
        self.assertEqual(result, "good 2001:db8::1")

        # Check body parameters
        args, kwargs = mock_http.call_args
        body = kwargs["body"]
        self.assertEqual(body["hostname"], "ipv6.example.com")
        self.assertEqual(body["myip"], "2001:db8::1")

    @patch.object(HeProvider, "_http")
    def test_set_record_with_all_parameters(self, mock_http):
        """Test set_record method with all optional parameters"""
        mock_http.return_value = "good 10.0.0.1"

        provider = HeProvider(self.auth_id, self.auth_token)

        result = provider.set_record(
            domain="full.example.com", value="10.0.0.1", record_type="A", ttl=300, line="default", extra_param="test"
        )

        # Verify the result
        self.assertEqual(result, "good 10.0.0.1")

        # Check that core parameters are still correct
        args, kwargs = mock_http.call_args
        body = kwargs["body"]
        self.assertEqual(body["hostname"], "full.example.com")
        self.assertEqual(body["myip"], "10.0.0.1")
        self.assertEqual(body["password"], self.auth_token)

    @patch.object(HeProvider, "_http")
    def test_set_record_empty_response_error(self, mock_http):
        """Test set_record method with empty response (should raise exception)"""
        mock_http.return_value = ""  # Empty response

        provider = HeProvider(self.auth_id, self.auth_token)

        with self.assertRaises(Exception) as cm:
            provider.set_record("example.com", "192.168.1.1")

        self.assertIn("empty response", str(cm.exception))

    @patch.object(HeProvider, "_http")
    def test_set_record_none_response_error(self, mock_http):
        """Test set_record method with None response (should raise exception)"""
        mock_http.return_value = None  # None response

        provider = HeProvider(self.auth_id, self.auth_token)

        with self.assertRaises(Exception) as cm:
            provider.set_record("example.com", "192.168.1.1")

        self.assertIn("empty response", str(cm.exception))

    @patch.object(HeProvider, "_http")
    def test_set_record_error_response(self, mock_http):
        """Test set_record method with error response"""
        mock_http.return_value = "badauth"

        provider = HeProvider(self.auth_id, self.auth_token)

        with self.assertRaises(Exception) as cm:
            provider.set_record("example.com", "192.168.1.1")

        self.assertEqual(str(cm.exception), "badauth")

    @patch.object(HeProvider, "_http")
    def test_set_record_abuse_response(self, mock_http):
        """Test set_record method with abuse response"""
        mock_http.return_value = "abuse"

        provider = HeProvider(self.auth_id, self.auth_token)

        with self.assertRaises(Exception) as cm:
            provider.set_record("example.com", "192.168.1.1")

        self.assertEqual(str(cm.exception), "abuse")

    @patch.object(HeProvider, "_http")
    def test_set_record_notfqdn_response(self, mock_http):
        """Test set_record method with notfqdn response"""
        mock_http.return_value = "notfqdn"

        provider = HeProvider(self.auth_id, self.auth_token)

        with self.assertRaises(Exception) as cm:
            provider.set_record("example.com", "192.168.1.1")

        self.assertEqual(str(cm.exception), "notfqdn")

    @patch.object(HeProvider, "_http")
    def test_set_record_partial_good_response(self, mock_http):
        """Test set_record method with partial 'good' response"""
        mock_http.return_value = "good"  # Just 'good' without IP

        provider = HeProvider(self.auth_id, self.auth_token)

        result = provider.set_record("example.com", "192.168.1.1")

        # Should still return the response as success
        self.assertEqual(result, "good")

    @patch.object(HeProvider, "_http")
    def test_set_record_partial_nochg_response(self, mock_http):
        """Test set_record method with partial 'nochg' response"""
        mock_http.return_value = "nochg"  # Just 'nochg' without IP

        provider = HeProvider(self.auth_id, self.auth_token)

        result = provider.set_record("example.com", "192.168.1.1")

        # Should still return the response as success
        self.assertEqual(result, "nochg")

    def test_set_record_logger_info_called(self):
        """Test that logger.info is called with correct parameters"""
        provider = HeProvider(self.auth_id, self.auth_token)

        # Mock the logger and _http
        provider.logger = MagicMock()

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "good 192.168.1.1"

            provider.set_record("example.com", "192.168.1.1", "A")

        # Verify logger.info was called with correct parameters
        provider.logger.info.assert_called_once_with("%s => %s(%s)", "example.com", "192.168.1.1", "A")

    def test_set_record_logger_debug_called(self):
        """Test that logger.debug is called with parameters"""
        provider = HeProvider(self.auth_id, self.auth_token)

        # Mock the logger and _http
        provider.logger = MagicMock()

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "good 192.168.1.1"

            provider.set_record("example.com", "192.168.1.1", "A")

        # Verify logger.debug was called (we don't check exact params as they include the dict)
        provider.logger.debug.assert_called()

    def test_set_record_logger_error_called(self):
        """Test that logger.error is called on error response"""
        provider = HeProvider(self.auth_id, self.auth_token)

        # Mock the logger and _http
        provider.logger = MagicMock()

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "badauth"

            with self.assertRaises(Exception):
                provider.set_record("example.com", "192.168.1.1", "A")

        # Verify logger.error was called with correct parameters
        provider.logger.error.assert_called_once_with("HE API error: %s", "badauth")


class TestHeProviderIntegration(BaseProviderTestCase):
    """Integration tests for HeProvider"""

    def test_full_workflow_ipv4_success(self):
        """Test complete workflow for IPv4 record with success response"""
        provider = HeProvider("test_auth_id", "test_auth_token")

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "good 1.2.3.4"

            result = provider.set_record("test.com", "1.2.3.4", "A", 300, "default")

            self.assertEqual(result, "good 1.2.3.4")
            mock_http.assert_called_once()
            args, kwargs = mock_http.call_args
            self.assertEqual(args[0], "POST")
            self.assertEqual(args[1], "/nic/update")

            body = kwargs["body"]
            self.assertEqual(body["hostname"], "test.com")
            self.assertEqual(body["myip"], "1.2.3.4")
            self.assertEqual(body["password"], "test_auth_token")

    def test_full_workflow_ipv6_success(self):
        """Test complete workflow for IPv6 record with success response"""
        provider = HeProvider("test_auth_id", "test_auth_token")

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "good ::1"

            result = provider.set_record("test.com", "::1", "AAAA", 600, "telecom")

            self.assertEqual(result, "good ::1")
            mock_http.assert_called_once()

            args, kwargs = mock_http.call_args
            body = kwargs["body"]
            self.assertEqual(body["hostname"], "test.com")
            self.assertEqual(body["myip"], "::1")

    def test_full_workflow_error_handling(self):
        """Test complete workflow with error handling"""
        provider = HeProvider("test_auth_id", "test_auth_token")

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "badauth"

            with self.assertRaises(Exception) as cm:
                provider.set_record("test.com", "1.2.3.4", "A")

            self.assertEqual(str(cm.exception), "badauth")


if __name__ == "__main__":
    unittest.main()
