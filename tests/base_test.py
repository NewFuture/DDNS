# coding=utf-8
"""
Base test utilities and common imports for all provider tests
@author: NewFuture
"""

from functools import partial

from __init__ import TEST_HTTP_TIMEOUT, unittest, patch, MagicMock  # noqa: F401 # Ensure package initialization


class BaseProviderTestCase(unittest.TestCase):
    """Base test case class with common setup for all provider tests"""

    def setUp(self):
        """Set up common test fixtures"""
        self.id = "test_id"
        self.token = "test_token"

    def assertProviderInitialized(self, provider, expected_id=None, expected_token=None):
        """Helper method to assert provider is correctly initialized"""
        self.assertEqual(provider.id, expected_id or self.id)
        self.assertEqual(provider.token, expected_token or self.token)

    def mock_logger(self, provider):
        """Helper method to mock provider logger"""
        provider.logger = MagicMock()
        return provider.logger

    def configure_test_http(self, provider, timeout=TEST_HTTP_TIMEOUT):
        """Bound real HTTP calls in integration tests."""
        provider._http = partial(provider._http, timeout=timeout, retries=0)
        return provider


# Export commonly used imports for convenience
__all__ = ["BaseProviderTestCase", "unittest", "patch", "MagicMock", "TEST_HTTP_TIMEOUT"]
