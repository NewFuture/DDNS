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
