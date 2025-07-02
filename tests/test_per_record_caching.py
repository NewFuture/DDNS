#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test per-record caching functionality
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os

from ddns.__main__ import update_ip
from ddns.util.cache import Cache


class TestPerRecordCaching(unittest.TestCase):
    """Test per-record caching improvements"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_cache_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_cache_file.close()
        self.cache = Cache(self.temp_cache_file.name)
        self.mock_dns = Mock()
        self.test_domains = ["example.com", "test.com"]
        self.test_ip = "192.168.1.100"
        self.test_ttl = "300"
        self.proxy_list = ["DIRECT"]
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            os.unlink(self.temp_cache_file.name)
        except OSError:
            pass
    
    @patch('ddns.__main__.get_config')
    @patch('ddns.__main__.get_ip')
    def test_successful_domains_cached_individually(self, mock_get_ip, mock_get_config):
        """Test that successful domain updates are cached individually"""
        mock_get_config.return_value = self.test_domains
        mock_get_ip.return_value = self.test_ip
        
        with patch('ddns.__main__.change_dns_record', return_value=True):
            result = update_ip("4", self.cache, self.mock_dns, self.test_ttl, self.proxy_list)
        
        self.assertTrue(result)
        
        # Verify each domain is cached with correct key format
        for domain in self.test_domains:
            cache_key = f"{domain}:A"
            self.assertIn(cache_key, self.cache)
            self.assertEqual(self.cache[cache_key], self.test_ip)
    
    @patch('ddns.__main__.get_config')
    @patch('ddns.__main__.get_ip')
    def test_partial_failure_only_caches_successful_domains(self, mock_get_ip, mock_get_config):
        """Test that only successful domains are cached when some fail"""
        mock_get_config.return_value = self.test_domains
        mock_get_ip.return_value = self.test_ip
        
        # Mock success for first domain, failure for second
        def mock_change_dns_record(dns, proxy_list, **kwargs):
            return kwargs.get('domain') == self.test_domains[0]
        
        with patch('ddns.__main__.change_dns_record', side_effect=mock_change_dns_record):
            result = update_ip("4", self.cache, self.mock_dns, self.test_ttl, self.proxy_list)
        
        self.assertTrue(result)  # At least one domain succeeded
        
        # Verify only successful domain is cached
        successful_key = f"{self.test_domains[0]}:A"
        failed_key = f"{self.test_domains[1]}:A"
        
        self.assertIn(successful_key, self.cache)
        self.assertEqual(self.cache[successful_key], self.test_ip)
        self.assertNotIn(failed_key, self.cache)
    
    @patch('ddns.__main__.get_config')
    @patch('ddns.__main__.get_ip')
    def test_cached_domains_are_skipped(self, mock_get_ip, mock_get_config):
        """Test that cached domains are skipped on subsequent runs"""
        mock_get_config.return_value = self.test_domains
        mock_get_ip.return_value = self.test_ip
        
        # Pre-populate cache for first domain
        self.cache[f"{self.test_domains[0]}:A"] = self.test_ip
        
        mock_change_dns_record = Mock(return_value=True)
        with patch('ddns.__main__.change_dns_record', mock_change_dns_record):
            result = update_ip("4", self.cache, self.mock_dns, self.test_ttl, self.proxy_list)
        
        self.assertTrue(result)
        
        # Verify DNS update was only called for uncached domain
        self.assertEqual(mock_change_dns_record.call_count, 1)
        call_args = mock_change_dns_record.call_args[1]
        self.assertEqual(call_args['domain'], self.test_domains[1])
    
    @patch('ddns.__main__.get_config')
    @patch('ddns.__main__.get_ip')
    def test_ipv6_uses_aaaa_record_type(self, mock_get_ip, mock_get_config):
        """Test that IPv6 records use AAAA record type in cache keys"""
        mock_get_config.return_value = self.test_domains
        mock_get_ip.return_value = "2001:db8::1"
        
        with patch('ddns.__main__.change_dns_record', return_value=True):
            result = update_ip("6", self.cache, self.mock_dns, self.test_ttl, self.proxy_list)
        
        self.assertTrue(result)
        
        # Verify each domain is cached with AAAA record type
        for domain in self.test_domains:
            cache_key = f"{domain}:AAAA"
            self.assertIn(cache_key, self.cache)
            self.assertEqual(self.cache[cache_key], "2001:db8::1")


if __name__ == '__main__':
    unittest.main()