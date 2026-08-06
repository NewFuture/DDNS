# -*- coding: utf-8 -*-
"""
Unit tests for the DDNS main run path.
"""

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
            cli_config={
                "dns": "debug",
                "cache": True,
                "cache_max_age": 86400,
                "index4": False,
                "index6": False,
            }
        )

        self.assertTrue(__main__.run(config))
        mock_cache_new.assert_called_once_with(True, config.md5(), __main__.logger, 86400)
        self.assertEqual(mock_update_ip.call_count, 2)


if __name__ == "__main__":
    unittest.main()
