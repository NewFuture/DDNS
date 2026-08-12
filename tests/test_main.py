# -*- coding: utf-8 -*-
"""
Unit tests for the DDNS main run path.
"""

import io
import sys

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
