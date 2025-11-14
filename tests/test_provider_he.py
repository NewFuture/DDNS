# coding=utf-8
"""
Unit tests for HeProvider (Hurricane Electric)

@author: GitHub Copilot
"""

from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.he import HeProvider


class TestHeProvider(BaseProviderTestCase):
    """Test cases for HeProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestHeProvider, self).setUp()
        # Override default auth values for HE provider - HE uses empty id
        self.id = ""
        self.token = "test_password"

    def test_init_with_basic_config(self):
        """Test HeProvider initialization with basic configuration"""
        # HE provider should use empty id and only token
        provider = HeProvider("", self.token)
        self.assertEqual(provider.id, "")
        self.assertEqual(provider.token, self.token)
        self.assertEqual(provider.endpoint, "https://dyn.dns.he.net")
        self.assertFalse(provider.decode_response)

    def test_class_constants(self):
        """Test HeProvider class constants"""
        provider = HeProvider("", self.token)
        self.assertEqual(provider.endpoint, "https://dyn.dns.he.net")
        self.assertFalse(provider.decode_response)
        # ContentType should be form-encoded
        from ddns.provider._base import TYPE_FORM

        self.assertEqual(provider.content_type, TYPE_FORM)

    def test_validate_success_with_token_only(self):
        """Test _validate method passes with token only (correct usage)"""
        provider = HeProvider("", self.token)
        # Should not raise any exception
        provider._validate()

    def test_validate_fails_with_id(self):
        """Test _validate method fails when id is provided"""
        with self.assertRaises(ValueError) as cm:
            HeProvider("some_id", self.token)
        self.assertIn("does not use `id`", str(cm.exception))

    def test_validate_fails_without_token(self):
        """Test _validate method fails when token is missing"""
        with self.assertRaises(ValueError) as cm:
            HeProvider("", "")
        self.assertIn("requires `token(password)`", str(cm.exception))

    @patch.object(HeProvider, "_http")
    def test_set_record_success_good_response(self, mock_http):
        """Test set_record method with 'good' response"""
        mock_http.return_value = "good 192.168.1.1"

        provider = HeProvider("", self.token)

        result = provider.set_record("example.com", "192.168.1.1", "A")

        # Verify the result
        self.assertTrue(result)

        # Verify _http was called with correct parameters
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "POST")  # method
        self.assertEqual(args[1], "/nic/update")  # path

        # Check body parameters
        body = kwargs["body"]
        self.assertEqual(body["hostname"], "example.com")
        self.assertEqual(body["myip"], "192.168.1.1")
        self.assertEqual(body["password"], self.token)

    @patch.object(HeProvider, "_http")
    def test_set_record_success_nochg_response(self, mock_http):
        """Test set_record method with 'nochg' response"""
        mock_http.return_value = "nochg 192.168.1.1"

        provider = HeProvider("", self.token)

        result = provider.set_record("test.example.com", "192.168.1.1", "A")

        # Verify the result
        self.assertTrue(result)

        # Verify _http was called with correct parameters
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "POST")
        self.assertEqual(args[1], "/nic/update")

        # Check body parameters
        body = kwargs["body"]
        self.assertEqual(body["hostname"], "test.example.com")
        self.assertEqual(body["myip"], "192.168.1.1")
        self.assertEqual(body["password"], self.token)

    @patch.object(HeProvider, "_http")
    def test_set_record_ipv6_address(self, mock_http):
        """Test set_record method with IPv6 address"""
        mock_http.return_value = "good 2001:db8::1"

        provider = HeProvider("", self.token)

        result = provider.set_record("ipv6.example.com", "2001:db8::1", "AAAA")

        # Verify the result
        self.assertTrue(result)

        # Check body parameters
        args, kwargs = mock_http.call_args
        body = kwargs["body"]
        self.assertEqual(body["hostname"], "ipv6.example.com")
        self.assertEqual(body["myip"], "2001:db8::1")

    @patch.object(HeProvider, "_http")
    def test_set_record_with_all_parameters(self, mock_http):
        """Test set_record method with all optional parameters"""
        mock_http.return_value = "good 10.0.0.1"

        provider = HeProvider("", self.token)

        result = provider.set_record(
            domain="full.example.com", value="10.0.0.1", record_type="A", ttl=300, line="default", extra_param="test"
        )

        # Verify the result
        self.assertTrue(result)

        # Check that core parameters are still correct
        args, kwargs = mock_http.call_args
        body = kwargs["body"]
        self.assertEqual(body["hostname"], "full.example.com")
        self.assertEqual(body["myip"], "10.0.0.1")
        self.assertEqual(body["password"], self.token)

    @patch.object(HeProvider, "_http")
    def test_set_record_empty_response_error(self, mock_http):
        """Test set_record method with empty response (should return False)"""
        mock_http.return_value = ""  # Empty response

        provider = HeProvider("", self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once_with("HE API error: %s", "")

    @patch.object(HeProvider, "_http")
    def test_set_record_none_response_error(self, mock_http):
        """Test set_record method with None response (should return False)"""
        mock_http.return_value = None  # None response

        provider = HeProvider("", self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged - None causes TypeError when slicing
        provider.logger.error.assert_called_once()
        args = provider.logger.error.call_args[0]
        self.assertEqual(args[0], "Error updating record for %s: %s")
        self.assertEqual(args[1], "example.com")
        self.assertIsInstance(args[2], TypeError)

    @patch.object(HeProvider, "_http")
    def test_set_record_http_exception(self, mock_http):
        """Test set_record method when _http raises an exception"""
        mock_http.side_effect = Exception("Network error")

        provider = HeProvider("", self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once()
        args = provider.logger.error.call_args[0]
        self.assertEqual(args[0], "Error updating record for %s: %s")
        self.assertEqual(args[1], "example.com")
        self.assertIsInstance(args[2], Exception)

    @patch.object(HeProvider, "_http")
    def test_set_record_error_response(self, mock_http):
        """Test set_record method with error response"""
        mock_http.return_value = "badauth"

        provider = HeProvider("", self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once_with("HE API error: %s", "badauth")

    @patch.object(HeProvider, "_http")
    def test_set_record_abuse_response(self, mock_http):
        """Test set_record method with abuse response"""
        mock_http.return_value = "abuse"

        provider = HeProvider("", self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once_with("HE API error: %s", "abuse")

    @patch.object(HeProvider, "_http")
    def test_set_record_notfqdn_response(self, mock_http):
        """Test set_record method with notfqdn response"""
        mock_http.return_value = "notfqdn"

        provider = HeProvider("", self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once_with("HE API error: %s", "notfqdn")

    @patch.object(HeProvider, "_http")
    def test_set_record_partial_good_response(self, mock_http):
        """Test set_record method with partial 'good' response"""
        mock_http.return_value = "good"  # Just 'good' without IP

        provider = HeProvider("", self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")

        # Should return True as success
        self.assertTrue(result)

        # Verify success was logged
        provider.logger.info.assert_any_call("HE API response: %s", "good")

    @patch.object(HeProvider, "_http")
    def test_set_record_partial_nochg_response(self, mock_http):
        """Test set_record method with partial 'nochg' response"""
        mock_http.return_value = "nochg"  # Just 'nochg' without IP

        provider = HeProvider("", self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")

        # Should return True as success
        self.assertTrue(result)

        # Verify success was logged
        provider.logger.info.assert_any_call("HE API response: %s", "nochg")

    def test_set_record_logger_info_called(self):
        """Test that logger.info is called with correct parameters"""
        provider = HeProvider("", self.token)

        # Mock the logger and _http
        provider.logger = MagicMock()

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "good 192.168.1.1"

            provider.set_record("example.com", "192.168.1.1", "A")

        # Verify logger.info was called with correct parameters for the initial log
        provider.logger.info.assert_any_call("%s => %s(%s)", "example.com", "192.168.1.1", "A")

    def test_set_record_logger_info_on_success(self):
        """Test that logger.info is called on success"""
        provider = HeProvider("", self.token)

        # Mock the logger and _http
        provider.logger = MagicMock()

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "good 192.168.1.1"

            provider.set_record("example.com", "192.168.1.1", "A")

        # Verify logger.info was called for successful response
        calls = provider.logger.info.call_args_list
        self.assertEqual(len(calls), 2)  # Initial log and success log

    def test_set_record_logger_error_called(self):
        """Test that logger.error is called on error response"""
        provider = HeProvider("", self.token)

        # Mock the logger and _http
        provider.logger = MagicMock()

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "badauth"

            result = provider.set_record("example.com", "192.168.1.1", "A")
            self.assertFalse(result)

        # Verify logger.error was called with correct parameters
        provider.logger.error.assert_called_once_with("HE API error: %s", "badauth")


class TestHeProviderIntegration(BaseProviderTestCase):
    """Integration tests for HeProvider"""

    def test_full_workflow_ipv4_success(self):
        """Test complete workflow for IPv4 record with success response"""
        provider = HeProvider("", "test_token")

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "good 1.2.3.4"

            result = provider.set_record("test.com", "1.2.3.4", "A", 300, "default")

            self.assertTrue(result)
            mock_http.assert_called_once()
            args, kwargs = mock_http.call_args
            self.assertEqual(args[0], "POST")
            self.assertEqual(args[1], "/nic/update")

            body = kwargs["body"]
            self.assertEqual(body["hostname"], "test.com")
            self.assertEqual(body["myip"], "1.2.3.4")
            self.assertEqual(body["password"], "test_token")

    def test_full_workflow_ipv6_success(self):
        """Test complete workflow for IPv6 record with success response"""
        provider = HeProvider("", "test_token")

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "good ::1"

            result = provider.set_record("test.com", "::1", "AAAA", 600, "telecom")

            self.assertTrue(result)
            mock_http.assert_called_once()

            args, kwargs = mock_http.call_args
            body = kwargs["body"]
            self.assertEqual(body["hostname"], "test.com")
            self.assertEqual(body["myip"], "::1")

    def test_full_workflow_error_handling(self):
        """Test complete workflow with error handling"""
        provider = HeProvider("", "test_token")

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "badauth"

            result = provider.set_record("test.com", "1.2.3.4", "A")
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
