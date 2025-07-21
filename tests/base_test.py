# coding=utf-8
"""
Base test utilities and common imports for all provider tests
@author: NewFuture
"""
from __init__ import unittest, patch, MagicMock  # noqa: F401 # Ensure the package is initialized


class BaseProviderTestCase(unittest.TestCase):
    """Base test case class with common setup for all provider tests"""

    def setUp(self):
        """Set up common test fixtures"""
        self.authid = "test_id"
        self.token = "test_token"

    def assertProviderInitialized(self, provider, expected_id=None, expected_token=None):
        """Helper method to assert provider is correctly initialized"""
        self.assertEqual(provider.id, expected_id or self.authid)
        self.assertEqual(provider.token, expected_token or self.token)

    def mock_logger(self, provider):
        """Helper method to mock provider logger"""
        provider.logger = MagicMock()
        return provider.logger


# Export commonly used imports for convenience
__all__ = ["BaseProviderTestCase", "unittest", "patch", "MagicMock"]
