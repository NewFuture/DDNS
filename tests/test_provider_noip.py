# coding=utf-8
"""
Unit tests for NoipProvider (No-IP)

@author: GitHub Copilot
"""

from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.noip import NoipProvider


class TestNoipProvider(BaseProviderTestCase):
    """Test cases for NoipProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestNoipProvider, self).setUp()
        # No-IP uses both id (username) and token (password)
        self.id = "test_username"
        self.token = "test_password"

    def test_init_with_basic_config(self):
        """Test NoipProvider initialization with basic configuration"""
        provider = NoipProvider(self.id, self.token)
        self.assertEqual(provider.id, self.id)
        self.assertEqual(provider.token, self.token)
        # After validation, endpoint should include authentication
        self.assertEqual(provider.endpoint, "https://test_username:test_password@dynupdate.no-ip.com")
        self.assertFalse(provider.decode_response)

    def test_class_constants(self):
        """Test NoipProvider class constants"""
        provider = NoipProvider(self.id, self.token)
        # After validation, endpoint should include authentication
        self.assertEqual(provider.endpoint, "https://test_username:test_password@dynupdate.no-ip.com")
        self.assertFalse(provider.decode_response)
        self.assertIsNone(provider.accept)
        # ContentType should be form-encoded
        from ddns.provider._base import TYPE_FORM

        self.assertEqual(provider.content_type, TYPE_FORM)

    def test_validate_success_with_credentials(self):
        """Test _validate method passes with proper credentials"""
        provider = NoipProvider(self.id, self.token)
        # Should not raise any exception
        provider._validate()

    def test_validate_fails_without_id(self):
        """Test _validate method fails when id is missing"""
        with self.assertRaises(ValueError) as cm:
            NoipProvider("", self.token)
        self.assertIn("No-IP requires username", str(cm.exception))

    def test_validate_fails_without_token(self):
        """Test _validate method fails when token is missing"""
        with self.assertRaises(ValueError) as cm:
            NoipProvider(self.id, "")
        self.assertIn("No-IP requires password", str(cm.exception))

    def test_validate_fails_with_both_missing(self):
        """Test _validate method fails when both credentials are missing"""
        with self.assertRaises(ValueError) as cm:
            NoipProvider("", "")
        self.assertIn("No-IP requires username", str(cm.exception))

    @patch.object(NoipProvider, "_http")
    def test_set_record_success_good_response(self, mock_http):
        """Test set_record method with 'good' response"""
        mock_http.return_value = "good 192.168.1.1"

        provider = NoipProvider(self.id, self.token)

        result = provider.set_record("example.com", "192.168.1.1", "A")

        # Verify the result
        self.assertTrue(result)

        # Verify _http was called with correct parameters
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "GET")  # method
        self.assertEqual(args[1], "/nic/update")  # path

        # Check query parameters
        queries = kwargs["queries"]
        self.assertEqual(queries["hostname"], "example.com")
        self.assertEqual(queries["myip"], "192.168.1.1")

        # Verify that endpoint contains embedded authentication (no Authorization header needed)
        # The endpoint should have been temporarily modified to include auth credentials

    @patch.object(NoipProvider, "_http")
    def test_set_record_success_nochg_response(self, mock_http):
        """Test set_record method with 'nochg' response"""
        mock_http.return_value = "nochg 192.168.1.1"

        provider = NoipProvider(self.id, self.token)

        result = provider.set_record("test.example.com", "192.168.1.1", "A")

        # Verify the result
        self.assertTrue(result)

        # Verify _http was called with correct parameters
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], "/nic/update")

        # Check query parameters
        queries = kwargs["queries"]
        self.assertEqual(queries["hostname"], "test.example.com")
        self.assertEqual(queries["myip"], "192.168.1.1")

    @patch.object(NoipProvider, "_http")
    def test_set_record_ipv6_address(self, mock_http):
        """Test set_record method with IPv6 address"""
        mock_http.return_value = "good 2001:db8::1"

        provider = NoipProvider(self.id, self.token)

        result = provider.set_record("ipv6.example.com", "2001:db8::1", "AAAA")

        # Verify the result
        self.assertTrue(result)

        # Check query parameters
        args, kwargs = mock_http.call_args
        queries = kwargs["queries"]
        self.assertEqual(queries["hostname"], "ipv6.example.com")
        self.assertEqual(queries["myip"], "2001:db8::1")

    @patch.object(NoipProvider, "_http")
    def test_set_record_with_all_parameters(self, mock_http):
        """Test set_record method with all optional parameters"""
        mock_http.return_value = "good 10.0.0.1"

        provider = NoipProvider(self.id, self.token)

        result = provider.set_record(
            domain="full.example.com", value="10.0.0.1", record_type="A", ttl=300, line="default", extra_param="test"
        )

        # Verify the result
        self.assertTrue(result)

        # Check that core parameters are still correct
        args, kwargs = mock_http.call_args
        queries = kwargs["queries"]
        self.assertEqual(queries["hostname"], "full.example.com")
        self.assertEqual(queries["myip"], "10.0.0.1")

    @patch.object(NoipProvider, "_http")
    def test_set_record_nohost_error(self, mock_http):
        """Test set_record method with 'nohost' error response"""
        mock_http.return_value = "nohost"

        provider = NoipProvider(self.id, self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once()
        args = provider.logger.error.call_args[0]
        self.assertIn("does not exist", args[0])

    @patch.object(NoipProvider, "_http")
    def test_set_record_badauth_error(self, mock_http):
        """Test set_record method with 'badauth' error response"""
        mock_http.return_value = "badauth"

        provider = NoipProvider(self.id, self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once()
        args = provider.logger.error.call_args[0]
        self.assertIn("Invalid No-IP username/password", args[0])

    @patch.object(NoipProvider, "_http")
    def test_set_record_badagent_error(self, mock_http):
        """Test set_record method with 'badagent' error response"""
        mock_http.return_value = "badagent"

        provider = NoipProvider(self.id, self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once()
        args = provider.logger.error.call_args[0]
        self.assertIn("client disabled", args[0])

    @patch.object(NoipProvider, "_http")
    def test_set_record_donator_error(self, mock_http):
        """Test set_record method with '!donator' error response"""
        mock_http.return_value = "!donator"

        provider = NoipProvider(self.id, self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once()
        args = provider.logger.error.call_args[0]
        self.assertIn("not available for No-IP free account", args[0])

    @patch.object(NoipProvider, "_http")
    def test_set_record_abuse_error(self, mock_http):
        """Test set_record method with 'abuse' error response"""
        mock_http.return_value = "abuse"

        provider = NoipProvider(self.id, self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once()
        args = provider.logger.error.call_args[0]
        self.assertIn("blocked due to abuse", args[0])

    @patch.object(NoipProvider, "_http")
    def test_set_record_unexpected_response(self, mock_http):
        """Test set_record method with unexpected response"""
        mock_http.return_value = "unknown_response"

        provider = NoipProvider(self.id, self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once()
        args = provider.logger.error.call_args[0]
        self.assertIn("Unexpected No-IP API response", args[0])

    @patch.object(NoipProvider, "_http")
    def test_set_record_empty_response_error(self, mock_http):
        """Test set_record method with empty response"""
        mock_http.return_value = ""

        provider = NoipProvider(self.id, self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged - empty string should be treated as
        # unexpected response
        provider.logger.error.assert_called_once()
        args = provider.logger.error.call_args[0]
        self.assertIn("Unexpected No-IP API response", args[0])

    @patch.object(NoipProvider, "_http")
    def test_set_record_none_response_error(self, mock_http):
        """Test set_record method with None response"""
        mock_http.return_value = None

        provider = NoipProvider(self.id, self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once()
        args = provider.logger.error.call_args[0]
        self.assertIn("Empty response from No-IP API", args[0])

    @patch.object(NoipProvider, "_http")
    def test_set_record_http_exception(self, mock_http):
        """Test set_record method when _http raises an exception"""
        mock_http.side_effect = Exception("Network error")

        provider = NoipProvider(self.id, self.token)
        provider.logger = MagicMock()

        result = provider.set_record("example.com", "192.168.1.1")
        self.assertFalse(result)

        # Verify error was logged
        provider.logger.error.assert_called_once()
        args = provider.logger.error.call_args[0]
        self.assertEqual(args[0], "Error updating No-IP record for %s: %s")
        self.assertEqual(args[1], "example.com")
        self.assertIsInstance(args[2], Exception)

    def test_authentication_url_embedding(self):
        """Test that authentication is embedded in URL correctly"""
        provider = NoipProvider("test_user", "test_pass")

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "good 1.2.3.4"

            # Capture the original endpoint to verify it gets restored
            original_endpoint = provider.endpoint

            provider.set_record("test.com", "1.2.3.4")

            # Check that _http was called
            mock_http.assert_called_once()

            # Verify that endpoint was restored after the call
            self.assertEqual(provider.endpoint, original_endpoint)

            # The actual authentication happens via URL embedding
            # We can't easily test the temporary endpoint change without
            # more complex mocking, but we can verify the method was called

    def test_set_record_logger_info_called(self):
        """Test that logger.info is called with correct parameters"""
        provider = NoipProvider(self.id, self.token)
        provider.logger = MagicMock()

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "good 192.168.1.1"
            provider.set_record("example.com", "192.168.1.1", "A")

        # Verify logger.info was called for initial log
        provider.logger.info.assert_any_call("%s => %s(%s)", "example.com", "192.168.1.1", "A")


class TestNoipProviderIntegration(BaseProviderTestCase):
    """Integration tests for NoipProvider"""

    def test_full_workflow_ipv4_success(self):
        """Test complete workflow for IPv4 record with success response"""
        provider = NoipProvider("test_user", "test_pass")

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "good 1.2.3.4"

            result = provider.set_record("test.com", "1.2.3.4", "A", 300, "default")

            self.assertTrue(result)
            mock_http.assert_called_once()
            args, kwargs = mock_http.call_args
            self.assertEqual(args[0], "GET")
            self.assertEqual(args[1], "/nic/update")

            queries = kwargs["queries"]
            self.assertEqual(queries["hostname"], "test.com")
            self.assertEqual(queries["myip"], "1.2.3.4")

            # No headers needed anymore since authentication is embedded in URL

    def test_full_workflow_ipv6_success(self):
        """Test complete workflow for IPv6 record with success response"""
        provider = NoipProvider("test_user", "test_pass")

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "good ::1"

            result = provider.set_record("test.com", "::1", "AAAA", 600, "telecom")

            self.assertTrue(result)
            mock_http.assert_called_once()

            args, kwargs = mock_http.call_args
            queries = kwargs["queries"]
            self.assertEqual(queries["hostname"], "test.com")
            self.assertEqual(queries["myip"], "::1")

    def test_full_workflow_error_handling(self):
        """Test complete workflow with error handling"""
        provider = NoipProvider("test_user", "test_pass")

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = "badauth"

            result = provider.set_record("test.com", "1.2.3.4", "A")
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
