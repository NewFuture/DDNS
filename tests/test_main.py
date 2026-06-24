# coding=utf-8
"""
Unit tests for ddns.__main__ update workflow
"""

from __init__ import MagicMock, patch, unittest

import os
import tempfile

from ddns.__main__ import update_ip
from ddns.cache import Cache
from ddns.config.config import Config


class TestUpdateIpWithCacheVerifyEvery(unittest.TestCase):
    """Test update_ip behavior with cache_verify_every enabled"""

    def setUp(self):
        self.cache_file = tempfile.mktemp(prefix="ddns_test_main_cache_", suffix=".json")

    def tearDown(self):
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    @patch("ddns.__main__.get_ip", return_value="1.2.3.4")
    def test_force_verify_after_configured_cached_skips(self, mock_get_ip):
        """Test cache hits eventually force an upstream verification"""
        dns = MagicMock()
        dns.set_record.return_value = True
        cache = Cache(self.cache_file)
        cache["example.com:A"] = "1.2.3.4"
        config = Config(cli_config={"dns": "cloudflare", "cache_verify_every": 2})
        counter_key = "cloudflare:example.com:A"

        self.assertTrue(update_ip(dns, cache, ["default"], ["example.com"], "A", config))
        self.assertEqual(cache.get_cache_verify_count(counter_key), 1)
        dns.set_record.assert_not_called()

        self.assertTrue(update_ip(dns, cache, ["default"], ["example.com"], "A", config))
        self.assertEqual(cache.get_cache_verify_count(counter_key), 2)
        dns.set_record.assert_not_called()

        self.assertTrue(update_ip(dns, cache, ["default"], ["example.com"], "A", config))
        dns.set_record.assert_called_once_with(
            "example.com", "1.2.3.4", record_type="A", ttl=None, line=None
        )
        self.assertEqual(cache.get_cache_verify_count(counter_key), 0)
        self.assertEqual(mock_get_ip.call_count, 3)

    @patch("ddns.__main__.get_ip", return_value="1.2.3.4")
    def test_failed_forced_verify_retries_on_next_run(self, mock_get_ip):
        """Test failed forced verification keeps the threshold for the next run"""
        dns = MagicMock()
        dns.set_record.return_value = False
        cache = Cache(self.cache_file)
        cache["example.com:A"] = "1.2.3.4"
        config = Config(cli_config={"dns": "cloudflare", "cache_verify_every": 1})
        counter_key = "cloudflare:example.com:A"

        self.assertTrue(update_ip(dns, cache, ["default"], ["example.com"], "A", config))
        self.assertEqual(cache.get_cache_verify_count(counter_key), 1)

        self.assertFalse(update_ip(dns, cache, ["default"], ["example.com"], "A", config))
        self.assertEqual(dns.set_record.call_count, 1)
        self.assertEqual(cache.get_cache_verify_count(counter_key), 1)

        self.assertFalse(update_ip(dns, cache, ["default"], ["example.com"], "A", config))
        self.assertEqual(dns.set_record.call_count, 2)
        self.assertEqual(cache.get_cache_verify_count(counter_key), 1)
        self.assertEqual(mock_get_ip.call_count, 3)

    @patch("ddns.__main__.get_ip", return_value="5.6.7.8")
    def test_ip_change_resets_verify_counter(self, mock_get_ip):
        """Test updating a changed IP clears persisted verification counters"""
        dns = MagicMock()
        dns.set_record.return_value = True
        cache = Cache(self.cache_file)
        cache["example.com:A"] = "1.2.3.4"
        cache.set_cache_verify_count("cloudflare:example.com:A", 3)
        config = Config(cli_config={"dns": "cloudflare", "cache_verify_every": 2})

        self.assertTrue(update_ip(dns, cache, ["default"], ["example.com"], "A", config))
        dns.set_record.assert_called_once_with(
            "example.com", "5.6.7.8", record_type="A", ttl=None, line=None
        )
        self.assertEqual(cache["example.com:A"], "5.6.7.8")
        self.assertEqual(cache.get_cache_verify_count("cloudflare:example.com:A"), 0)
        self.assertEqual(mock_get_ip.call_count, 1)


if __name__ == "__main__":
    unittest.main()
