# coding=utf-8
"""
Unit tests for DnspodComProvider

@author: GitHub Copilot
"""

from base_test import BaseProviderTestCase, unittest
from ddns.provider.dnspod_com import DnspodComProvider


class TestDnspodComProvider(BaseProviderTestCase):
    """Test cases for DnspodComProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestDnspodComProvider, self).setUp()
        self.id = "test_email@example.com"
        self.token = "test_token"

    def test_class_constants(self):
        """Test DnspodComProvider class constants"""
        self.assertEqual(DnspodComProvider.endpoint, "https://api.dnspod.com")
        self.assertEqual(DnspodComProvider.DefaultLine, "default")

    def test_init_with_basic_config(self):
        """Test DnspodComProvider initialization with basic configuration"""
        provider = DnspodComProvider(self.id, self.token)
        self.assertEqual(provider.id, self.id)
        self.assertEqual(provider.token, self.token)
        self.assertEqual(provider.endpoint, "https://api.dnspod.com")

    def test_inheritance_from_dnspod(self):
        """Test that DnspodComProvider properly inherits from DnspodProvider"""
        from ddns.provider.dnspod import DnspodProvider

        provider = DnspodComProvider(self.id, self.token)
        self.assertIsInstance(provider, DnspodProvider)
        # Should have inherited methods from parent
        self.assertTrue(hasattr(provider, "_request"))
        self.assertTrue(hasattr(provider, "_query_zone_id"))
        self.assertTrue(hasattr(provider, "_query_record"))
        self.assertTrue(hasattr(provider, "_create_record"))
        self.assertTrue(hasattr(provider, "_update_record"))


class TestDnspodComProviderIntegration(BaseProviderTestCase):
    """Integration test cases for DnspodComProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestDnspodComProviderIntegration, self).setUp()
        self.id = "test_email@example.com"
        self.token = "test_token"

    def test_api_endpoint_difference(self):
        """Test that DnspodComProvider uses different API endpoint than DnspodProvider"""
        from ddns.provider.dnspod import DnspodProvider

        dnspod_provider = DnspodProvider(self.id, self.token)
        dnspod_com_provider = DnspodComProvider(self.id, self.token)

        # Should use different API endpoints
        self.assertNotEqual(dnspod_provider.endpoint, dnspod_com_provider.endpoint)
        self.assertEqual(dnspod_com_provider.endpoint, "https://api.dnspod.com")

    def test_default_line_setting(self):
        """Test that DnspodComProvider uses correct default line"""
        provider = DnspodComProvider(self.id, self.token)
        self.assertEqual(provider.DefaultLine, "default")


if __name__ == "__main__":
    unittest.main()
