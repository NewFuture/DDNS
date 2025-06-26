# coding=utf-8
"""
Base test utilities and common imports for all provider tests

@author: Github Copilot
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the ddns module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from unittest.mock import patch, MagicMock
except ImportError:
    # Python 2.7 compatibility
    from mock import patch, MagicMock  # type: ignore


class BaseProviderTestCase(unittest.TestCase):
    """Base test case class with common setup for all provider tests"""

    def setUp(self):
        """Set up common test fixtures"""
        self.auth_id = "test_id"
        self.auth_token = "test_token"

    def assertProviderInitialized(self, provider, expected_auth_id=None, expected_auth_token=None):
        """Helper method to assert provider is correctly initialized"""
        self.assertEqual(provider.auth_id, expected_auth_id or self.auth_id)
        self.assertEqual(provider.auth_token, expected_auth_token or self.auth_token)

    def mock_logger(self, provider):
        """Helper method to mock provider logger"""
        provider.logger = MagicMock()
        return provider.logger


# Export commonly used imports for convenience
__all__ = ["BaseProviderTestCase", "unittest", "patch", "MagicMock"]
