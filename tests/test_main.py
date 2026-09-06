# -*- coding: utf-8 -*-
"""
Unit tests for the DDNS main run path.
"""

import io
import sys
import threading

from __init__ import MagicMock, patch, unittest

from ddns import __main__
from ddns.config.config import Config


class TestMain(unittest.TestCase):
    """Test the main DDNS run path."""

    @patch.object(__main__, "update_ip", return_value=True)
    @patch.object(__main__.Cache, "new")
    @patch.object(__main__, "get_provider_class")
    def test_run_passes_cache_max_age_to_cache(self, mock_provider_class, mock_cache_new, mock_update_ip):
        """Test run passes cache_max_age as the fourth Cache.new argument."""
        provider = MagicMock()
        mock_provider_class.return_value = lambda *args, **kwargs: provider
        config = Config(
            cli_config={"dns": "debug", "cache": True, "cache_max_age": 86400, "index4": False, "index6": False}
        )

        self.assertTrue(__main__.run(config))
        mock_cache_new.assert_called_once_with(True, config.md5(), __main__.logger, 86400)
        self.assertEqual(mock_update_ip.call_count, 2)

    @patch.object(__main__, "get_ip", side_effect=[None, "2001:db8::1"])
    @patch.object(__main__.Cache, "new", return_value=None)
    @patch.object(__main__, "get_provider_class")
    def test_run_attempts_ipv6_after_ipv4_failure(self, mock_provider_class, mock_cache_new, mock_get_ip):
        """An unavailable IPv4 address must not prevent an IPv6 update."""
        provider = MagicMock()
        provider.set_record.return_value = True
        mock_provider_class.return_value = lambda *args, **kwargs: provider
        config = Config(
            cli_config={
                "dns": "debug",
                "ipv4": ["v4.example.com"],
                "ipv6": ["v6.example.com"],
                "index4": ["default"],
                "index6": ["default"],
            }
        )

        self.assertFalse(__main__.run(config))

        self.assertEqual([call[0][0] for call in mock_get_ip.call_args_list], ["4", "6"])
        provider.set_record.assert_called_once()
        self.assertEqual(provider.set_record.call_args[0], ("v6.example.com", "2001:db8::1"))
        self.assertEqual(provider.set_record.call_args[1]["record_type"], "AAAA")

    @patch.object(__main__, "_get_ip_from_rule", return_value="2001:db8::1")
    @patch.object(__main__.Cache, "new", return_value=None)
    @patch.object(__main__, "get_provider_class")
    def test_run_disabled_ipv4_does_not_block_ipv6(self, mock_provider_class, mock_cache_new, mock_get_rule):
        """Keeping disabled IPv4 domains must not disable the configured IPv6 family."""
        provider = MagicMock()
        provider.set_record.return_value = True
        mock_provider_class.return_value = lambda *args, **kwargs: provider
        config = Config(
            cli_config={
                "dns": "debug",
                "ipv4": ["v4.example.com"],
                "ipv6": ["v6.example.com"],
                "index4": False,
                "index6": ["default"],
            }
        )

        self.assertTrue(__main__.run(config))

        mock_get_rule.assert_called_once_with("6", "default")
        provider.set_record.assert_called_once()
        self.assertEqual(provider.set_record.call_args[1]["record_type"], "AAAA")

    @patch.object(__main__, "get_ip", return_value=False)
    def test_update_ip_skips_disabled_family(self, mock_get_ip):
        """An explicitly disabled family is skipped without discovery or writes."""
        provider = MagicMock()

        result = __main__.update_ip(
            provider, None, False, ["disabled.example.com"], "AAAA", Config(cli_config={"dns": "debug"})
        )

        self.assertIsNone(result)
        mock_get_ip.assert_not_called()
        provider.set_record.assert_not_called()

    @patch.object(__main__, "get_ip", return_value="192.0.2.1")
    def test_update_ip_reports_partial_failures_and_continues(self, mock_get_ip):
        """Later success must not hide an earlier failure, or stop subsequent domains."""
        config = Config(cli_config={"dns": "debug"})
        for outcomes in (
            [True, False, True],
            [False, True],
            [True, RuntimeError("update rejected"), True],
            [RuntimeError("update rejected"), True],
            [None, True],
        ):
            provider = MagicMock()
            provider.set_record.side_effect = outcomes
            domains = ["record{}.example.com".format(index) for index in range(len(outcomes))]
            cache = {}

            result = __main__.update_ip(provider, cache, ["default"], domains, "A", config)

            self.assertFalse(result, repr(outcomes))
            self.assertEqual(provider.set_record.call_count, len(domains))
            self.assertEqual(
                cache,
                {"{}:A".format(domain): "192.0.2.1" for domain, outcome in zip(domains, outcomes) if outcome is True},
            )

    @patch.object(__main__, "get_ip", return_value="192.0.2.1")
    def test_cached_success_does_not_mask_failed_update(self, mock_get_ip):
        """A cached record remains valid without making a different failed record successful."""
        provider = MagicMock()
        provider.set_record.return_value = False
        cache = {"cached.example.com:A": "192.0.2.1"}

        result = __main__.update_ip(
            provider,
            cache,
            ["default"],
            ["cached.example.com", "failed.example.com"],
            "A",
            Config(cli_config={"dns": "debug"}),
        )

        self.assertFalse(result)
        provider.set_record.assert_called_once()
        self.assertEqual(cache, {"cached.example.com:A": "192.0.2.1"})

    @patch.object(__main__, "get_ip", return_value="192.0.2.1")
    def test_update_ip_all_successes_populate_cache(self, mock_get_ip):
        """All successful records retain the existing cache behavior."""
        provider = MagicMock()
        provider.set_record.return_value = True
        cache = {}
        domains = ["first.example.com", "second.example.com"]

        self.assertTrue(
            __main__.update_ip(provider, cache, ["default"], domains, "A", Config(cli_config={"dns": "debug"}))
        )
        self.assertEqual(provider.set_record.call_count, 2)
        self.assertEqual(cache, {domain + ":A": "192.0.2.1" for domain in domains})

    @patch.object(__main__, "get_ip", return_value="192.0.2.1")
    @patch.object(__main__.Cache, "new", return_value=None)
    @patch.object(__main__, "get_provider_class")
    def test_main_reports_partial_domain_failure(self, mock_provider_class, mock_cache_new, mock_get_ip):
        """The process result must report any rejected domain, not just total failures."""
        provider = MagicMock()
        provider.set_record.side_effect = [True, False]
        mock_provider_class.return_value = lambda *args, **kwargs: provider
        config = Config(cli_config={"dns": "debug", "ipv4": ["first.example.com", "second.example.com"]})

        with patch.object(__main__, "load_configs", return_value=[config]):
            with patch.object(sys, "stdout", io.StringIO()):
                with self.assertRaises(SystemExit) as context:
                    __main__.main()

        self.assertEqual(context.exception.code, 1)
        self.assertEqual(provider.set_record.call_count, 2)

    @patch.object(__main__, "get_ip", return_value="192.0.2.1")
    def test_update_ip_stops_before_next_domain_when_cancelled(self, mock_get_ip):
        """Stop cooperative updates between configured DNS records."""
        cancelled = threading.Event()
        provider = MagicMock()
        provider.set_record.side_effect = lambda *args, **kwargs: cancelled.set() or True
        config = Config(cli_config={"dns": "debug"})

        with self.assertRaises(__main__.UpdateCancelled):
            __main__.update_ip(
                provider,
                None,
                ["public"],
                ["first.example.com", "second.example.com"],
                "A",
                config,
                cancelled=cancelled.is_set,
            )

        provider.set_record.assert_called_once()
        mock_get_ip.assert_called_once()

    @patch.object(__main__, "_get_ip_from_rule")
    def test_get_ip_stops_before_next_rule_when_cancelled(self, mock_get_rule):
        """Stop cooperative address discovery between configured rules."""
        cancelled = threading.Event()
        mock_get_rule.side_effect = lambda *args: cancelled.set()

        with self.assertRaises(__main__.UpdateCancelled):
            __main__.get_ip("4", ["first", "second"], cancelled=cancelled.is_set)

        mock_get_rule.assert_called_once_with("4", "first")

    def test_mcp_mode_does_not_write_windows_leading_line(self):
        """Keep stdout clean before the stdio protocol handler starts."""
        output = io.StringIO()

        with patch.object(sys, "argv", ["ddns", "mcp"]):
            with patch.object(sys, "platform", "win32"):
                with patch.object(sys, "stdout", output):
                    with patch.object(__main__, "load_configs", side_effect=SystemExit(0)):
                        with self.assertRaises(SystemExit):
                            __main__.main()

        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
