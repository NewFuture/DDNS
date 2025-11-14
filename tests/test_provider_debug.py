# coding=utf-8
"""
Unit tests for DebugProvider

@author: GitHub Copilot
"""

import sys
from base_test import BaseProviderTestCase, unittest, patch, MagicMock
from ddns.provider.debug import DebugProvider

if sys.version_info[0] < 3:
    from StringIO import StringIO  # 对应 bytes
else:
    from io import StringIO  # 对应 unicode, py2.7中也存在


class TestDebugProvider(BaseProviderTestCase):
    """Test cases for DebugProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestDebugProvider, self).setUp()

    def test_init_with_basic_config(self):
        """Test DebugProvider initialization with basic configuration"""
        provider = DebugProvider(self.id, self.token)
        self.assertEqual(provider.id, self.id)
        self.assertEqual(provider.token, self.token)

    def test_validate_always_passes(self):
        """Test _validate method always passes (no validation required)"""
        provider = DebugProvider(self.id, self.token)
        # Should not raise any exception
        provider._validate()

    def test_validate_with_none_values(self):
        """Test _validate method with None values still passes"""
        provider = DebugProvider(None, None)  # type: ignore
        # Should not raise any exception even with None values
        provider._validate()

    @patch("sys.stdout", new_callable=StringIO)
    def test_set_record_ipv4(self, mock_stdout):
        """Test set_record method with IPv4 address"""
        provider = DebugProvider(self.id, self.token)

        result = provider.set_record("example.com", "192.168.1.1", "A")

        # Verify the result is True
        self.assertTrue(result)

        # Check that the correct output was printed
        output = mock_stdout.getvalue()
        self.assertIn("[IPv4] 192.168.1.1", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_set_record_ipv6(self, mock_stdout):
        """Test set_record method with IPv6 address"""
        provider = DebugProvider(self.id, self.token)

        result = provider.set_record("example.com", "2001:db8::1", "AAAA")

        # Verify the result is True
        self.assertTrue(result)

        # Check that the correct output was printed
        output = mock_stdout.getvalue()
        self.assertIn("[IPv6] 2001:db8::1", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_set_record_other_type(self, mock_stdout):
        """Test set_record method with other record types (CNAME, etc.)"""
        provider = DebugProvider(self.id, self.token)

        result = provider.set_record("example.com", "target.example.com", "CNAME")

        # Verify the result is True
        self.assertTrue(result)

        # Check that the correct output was printed (empty IP type for non-IP records)
        output = mock_stdout.getvalue()
        self.assertIn("[CNAME] target.example.com", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_set_record_mx_type(self, mock_stdout):
        """Test set_record method with MX record type"""
        provider = DebugProvider(self.id, self.token)

        result = provider.set_record("example.com", "mail.example.com", "MX")

        # Verify the result is True
        self.assertTrue(result)

        # Check that the correct output was printed
        output = mock_stdout.getvalue()
        self.assertIn("[MX] mail.example.com", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_set_record_with_all_parameters(self, mock_stdout):
        """Test set_record method with all optional parameters"""
        provider = DebugProvider(self.id, self.token)

        result = provider.set_record(
            domain="test.example.com", value="10.0.0.1", record_type="A", ttl=300, line="default", extra_param="test"
        )

        # Verify the result is True
        self.assertTrue(result)

        # Check that the correct output was printed
        output = mock_stdout.getvalue()
        self.assertIn("[IPv4] 10.0.0.1", output)

    def test_set_record_logger_debug_called(self):
        """Test that logger.debug is called with correct parameters"""
        provider = DebugProvider(self.id, self.token)

        # Mock the logger
        provider.logger = MagicMock()

        with patch("sys.stdout", new_callable=StringIO):
            result = provider.set_record("example.com", "192.168.1.1", "A", 600, "telecom")

        # Verify the result is True
        self.assertTrue(result)

        # Verify logger.debug was called with correct parameters
        provider.logger.debug.assert_called_once_with("DebugProvider: %s(%s) => %s", "example.com", "A", "192.168.1.1")

    @patch("sys.stdout", new_callable=StringIO)
    def test_set_record_multiple_calls(self, mock_stdout):
        """Test multiple calls to set_record method"""
        provider = DebugProvider(self.id, self.token)

        # Make multiple calls
        result1 = provider.set_record("example1.com", "192.168.1.1", "A")
        result2 = provider.set_record("example2.com", "2001:db8::1", "AAAA")
        result3 = provider.set_record("example3.com", "target.example.com", "CNAME")

        # Verify all results are True
        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertTrue(result3)

        # Check that all outputs were printed
        output = mock_stdout.getvalue()
        self.assertIn("[IPv4] 192.168.1.1", output)
        self.assertIn("[IPv6] 2001:db8::1", output)
        self.assertIn("[CNAME] target.example.com", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_set_record_empty_values(self, mock_stdout):
        """Test set_record method with empty values"""
        provider = DebugProvider(self.id, self.token)

        result = provider.set_record("", "", "")

        # Verify the result is True
        self.assertTrue(result)

        # Check that the correct output was printed
        output = mock_stdout.getvalue()
        self.assertIn("[] ", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_set_record_none_values(self, mock_stdout):
        """Test set_record method with None values"""
        provider = DebugProvider(self.id, self.token)

        result = provider.set_record("example.com", "192.168.1.1", None)  # type: ignore

        # Verify the result is True
        self.assertTrue(result)

        # Check that the correct output was printed (None record_type results in empty IP type)
        output = mock_stdout.getvalue()
        self.assertIn("[None] 192.168.1.1", output)


class TestDebugProviderIntegration(unittest.TestCase):
    """Integration tests for DebugProvider"""

    def test_full_workflow_ipv4(self):
        """Test complete workflow for IPv4 record"""
        provider = DebugProvider("test_auth_id", "test_token")

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = provider.set_record("test.com", "1.2.3.4", "A", 300, "default")

            self.assertTrue(result)
            output = mock_stdout.getvalue()
            self.assertIn("[IPv4] 1.2.3.4", output)

    def test_full_workflow_ipv6(self):
        """Test complete workflow for IPv6 record"""
        provider = DebugProvider("test_auth_id", "test_token")

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = provider.set_record("test.com", "::1", "AAAA", 600, "telecom")

            self.assertTrue(result)
            output = mock_stdout.getvalue()
            self.assertIn("[IPv6] ::1", output)

    def test_full_workflow_cname(self):
        """Test complete workflow for CNAME record"""
        provider = DebugProvider("test_auth_id", "test_token")

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = provider.set_record("www.test.com", "test.com", "CNAME", 3600)

            self.assertTrue(result)
            output = mock_stdout.getvalue()
            self.assertIn("[CNAME] test.com", output)


if __name__ == "__main__":
    unittest.main()
