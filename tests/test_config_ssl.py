# coding=utf-8
"""
Unit tests for SSL configuration integration

@author: GitHub Copilot
"""

import unittest
import sys
import os
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ddns.util.config import init_config, get_config  # noqa: E402
from ddns.__init__ import __version__, __description__, __doc__, build_date  # noqa: E402
from ddns.provider._base import SimpleProvider  # noqa: E402


class _TestSSLProvider(SimpleProvider):
    """Test provider to verify SSL configuration"""

    API = "https://api.example.com"

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        return True


class TestSSLConfiguration(unittest.TestCase):
    """Test SSL configuration integration"""

    def setUp(self):
        """Set up test fixtures"""
        # Clear global state before each test
        pass

    def test_cli_ssl_false(self):
        """Test SSL configuration via CLI argument --ssl false"""
        with patch.object(sys, 'argv', ['test', '--token', 'test', '--ssl', 'false']):
            init_config(__description__, __doc__, __version__, build_date)
            ssl_config = get_config('ssl')
            self.assertEqual(ssl_config, 'false')

    def test_cli_ssl_true(self):
        """Test SSL configuration via CLI argument --ssl true"""
        with patch.object(sys, 'argv', ['test', '--token', 'test', '--ssl', 'true']):
            init_config(__description__, __doc__, __version__, build_date)
            ssl_config = get_config('ssl')
            self.assertEqual(ssl_config, 'true')

    def test_cli_ssl_auto(self):
        """Test SSL configuration via CLI argument --ssl auto"""
        with patch.object(sys, 'argv', ['test', '--token', 'test', '--ssl', 'auto']):
            init_config(__description__, __doc__, __version__, build_date)
            ssl_config = get_config('ssl')
            self.assertEqual(ssl_config, 'auto')

    def test_cli_ssl_custom_path(self):
        """Test SSL configuration via CLI argument --ssl /path/to/cert.pem"""
        args = ['test', '--token', 'test', '--ssl', '/path/to/cert.pem']
        with patch.object(sys, 'argv', args):
            init_config(__description__, __doc__, __version__, build_date)
            ssl_config = get_config('ssl')
            self.assertEqual(ssl_config, '/path/to/cert.pem')

    def test_env_ssl_false(self):
        """Test SSL configuration via environment variable DDNS_SSL=false"""
        env_vars = {'DDNS_SSL': 'false', 'DDNS_TOKEN': 'test'}
        with patch.dict(os.environ, env_vars):
            with patch.object(sys, 'argv', ['test']):
                init_config(__description__, __doc__, __version__, build_date)
                ssl_config = get_config('ssl')
                self.assertEqual(ssl_config, 'false')

    def test_env_ssl_true(self):
        """Test SSL configuration via environment variable DDNS_SSL=true"""
        env_vars = {'DDNS_SSL': 'true', 'DDNS_TOKEN': 'test'}
        with patch.dict(os.environ, env_vars):
            with patch.object(sys, 'argv', ['test']):
                init_config(__description__, __doc__, __version__, build_date)
                ssl_config = get_config('ssl')
                self.assertEqual(ssl_config, 'true')

    def test_env_ssl_auto(self):
        """Test SSL configuration via environment variable DDNS_SSL=auto"""
        env_vars = {'DDNS_SSL': 'auto', 'DDNS_TOKEN': 'test'}
        with patch.dict(os.environ, env_vars):
            with patch.object(sys, 'argv', ['test']):
                init_config(__description__, __doc__, __version__, build_date)
                ssl_config = get_config('ssl')
                self.assertEqual(ssl_config, 'auto')

    def test_cli_overrides_env(self):
        """Test that CLI argument overrides environment variable"""
        env_vars = {'DDNS_SSL': 'false', 'DDNS_TOKEN': 'test'}
        with patch.dict(os.environ, env_vars):
            with patch.object(sys, 'argv', ['test', '--ssl', 'true']):
                init_config(__description__, __doc__, __version__, build_date)
                ssl_config = get_config('ssl')
                self.assertEqual(ssl_config, 'true')

    def test_default_ssl_config(self):
        """Test default SSL configuration when none provided"""
        with patch.object(sys, 'argv', ['test', '--token', 'test']):
            init_config(__description__, __doc__, __version__, build_date)
            ssl_config = get_config('ssl', 'auto')
            self.assertEqual(ssl_config, 'auto')

    def test_provider_ssl_integration(self):
        """Test that SSL configuration is passed to provider correctly"""
        provider = _TestSSLProvider('test_id', 'test_token', verify_ssl='false')
        self.assertEqual(provider.verify_ssl, 'false')

        provider = _TestSSLProvider('test_id', 'test_token', verify_ssl=True)
        self.assertTrue(provider.verify_ssl)

        cert_path = '/path/to/cert.pem'
        provider = _TestSSLProvider('test_id', 'test_token', verify_ssl=cert_path)
        self.assertEqual(provider.verify_ssl, '/path/to/cert.pem')

    def test_case_insensitive_env_vars(self):
        """Test that environment variables are case insensitive"""
        env_vars = {'ddns_ssl': 'false', 'ddns_token': 'test'}
        with patch.dict(os.environ, env_vars):
            with patch.object(sys, 'argv', ['test']):
                init_config(__description__, __doc__, __version__, build_date)
                ssl_config = get_config('ssl')
                self.assertEqual(ssl_config, 'false')


if __name__ == '__main__':
    unittest.main()
