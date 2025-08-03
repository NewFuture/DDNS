# -*- coding:utf-8 -*-
"""
Unit tests for ddns.scheduler.corn module
@author: NewFuture
"""
from __init__ import unittest, patch
from ddns.scheduler.cron import CronScheduler


class TestCronScheduler(unittest.TestCase):
    """Test CronScheduler functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.scheduler = CronScheduler()

    @patch("ddns.scheduler.cron.datetime")
    def test_install_with_version_and_date(self, mock_datetime):
        """Test install method includes version and date in cron entry"""
        mock_datetime.now.return_value.strftime.return_value = "2025-08-01 14:30:00"

        # Mock the methods to avoid actual system calls
        with patch.object(self.scheduler, '_run_command') as mock_run:
            with patch.object(self.scheduler, '_update_crontab') as mock_update:
                with patch.object(self.scheduler, '_build_ddns_command') as mock_build:
                    mock_run.return_value = ""
                    mock_update.return_value = True
                    mock_build.return_value = "python3 -m ddns -c test.json"

                    result = self.scheduler.install(5, {'config': ['test.json']})

                    self.assertTrue(result)
                    mock_update.assert_called_once()

                    # Verify the cron entry contains version and date
                    call_args = mock_update.call_args[0][0]
                    self.assertIn("# DDNS: auto-update v${BUILD_VERSION} installed on 2025-08-01 14:30:00", call_args)

    def test_get_status_extracts_comments(self):
        """Test get_status method extracts comments from cron entry"""
        cron_entry = (
            '*/10 * * * * cd "/home/user" && python3 -m ddns -c test.json '
            '# DDNS: auto-update v4.0 installed on 2025-08-01 14:30:00'
        )

        with patch.object(self.scheduler, '_run_command') as mock_run:

            def mock_command(cmd):
                if cmd == ['crontab', '-l']:
                    return cron_entry
                elif cmd == ['pgrep', '-f', 'cron']:
                    return '12345'
                return None

            mock_run.side_effect = mock_command

            status = self.scheduler.get_status()

            self.assertEqual(status['scheduler'], 'cron')
            self.assertTrue(status['enabled'])
            self.assertEqual(status['interval'], 10)
            self.assertEqual(status['description'], 'auto-update v4.0 installed on 2025-08-01 14:30:00')

    def test_get_status_handles_missing_comment_info(self):
        """Test get_status handles cron entries without full comment info gracefully"""
        cron_entry = '*/5 * * * * cd "/home/user" && python3 -m ddns -c test.json # DDNS: auto-update'

        with patch.object(self.scheduler, '_run_command') as mock_run:

            def mock_command(cmd):
                if cmd == ['crontab', '-l']:
                    return cron_entry
                elif cmd == ['pgrep', '-f', 'cron']:
                    return None
                return None

            mock_run.side_effect = mock_command

            status = self.scheduler.get_status()

            self.assertEqual(status['scheduler'], 'cron')
            self.assertTrue(status['enabled'])
            self.assertEqual(status['interval'], 5)
            self.assertEqual(status['description'], 'auto-update')

    def test_version_fallback_logic(self):
        """Test version fallback logic in install method"""
        with patch("ddns.scheduler.cron.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2025-08-01 14:30:00"

            with patch.object(self.scheduler, '_run_command') as mock_run:
                with patch.object(self.scheduler, '_update_crontab') as mock_update:
                    with patch.object(self.scheduler, '_build_ddns_command') as mock_build:
                        mock_run.return_value = ""
                        mock_update.return_value = True
                        mock_build.return_value = "python3 -m ddns"

                        # Test with import error
                        with patch('builtins.__import__', side_effect=ImportError):
                            result = self.scheduler.install(10)

                            self.assertTrue(result)
                            call_args = mock_update.call_args[0][0]
                            self.assertIn("v${BUILD_VERSION}", call_args)  # Should use the actual version placeholder

    def test_get_status_with_no_comment(self):
        """Test get_status handles cron entries with no DDNS comment"""
        cron_entry = '*/15 * * * * cd "/home/user" && python3 -m ddns -c test.json'

        with patch.object(self.scheduler, '_run_command') as mock_run:

            def mock_command(cmd):
                if cmd == ['crontab', '-l']:
                    return cron_entry
                elif cmd == ['pgrep', '-f', 'cron']:
                    return None
                return None

            mock_run.side_effect = mock_command

            status = self.scheduler.get_status()

            self.assertEqual(status['scheduler'], 'cron')
            self.assertEqual(status['enabled'], False)  # False when no DDNS line found
            # When no DDNS line is found, the method still tries to parse the empty line
            # This results in None values for interval, command, and empty string for comments
            self.assertIsNone(status.get('interval'))
            self.assertIsNone(status.get('command'))
            self.assertEqual(status.get('description'), '')

    def test_modify_cron_lines_enable_disable(self):
        """Test _modify_cron_lines method for enable and disable operations"""
        # Test enable operation on commented line
        with patch.object(self.scheduler, '_run_command') as mock_run:
            with patch.object(self.scheduler, '_update_crontab') as mock_update:
                mock_run.return_value = "# */5 * * * * cd /path && python3 -m ddns # DDNS: auto-update"
                mock_update.return_value = True

                result = self.scheduler.enable()
                self.assertTrue(result)
                mock_update.assert_called_once()
                call_args = mock_update.call_args[0][0]
                self.assertIn("*/5 * * * * cd /path && python3 -m ddns # DDNS: auto-update", call_args)

        # Test disable operation on active line
        with patch.object(self.scheduler, '_run_command') as mock_run:
            with patch.object(self.scheduler, '_update_crontab') as mock_update:
                mock_run.return_value = "*/5 * * * * cd /path && python3 -m ddns # DDNS: auto-update"
                mock_update.return_value = True

                result = self.scheduler.disable()
                self.assertTrue(result)
                mock_update.assert_called_once()
                call_args = mock_update.call_args[0][0]
                self.assertIn("# */5 * * * * cd /path && python3 -m ddns # DDNS: auto-update", call_args)

    def test_modify_cron_lines_uninstall(self):
        """Test _modify_cron_lines method for uninstall operation"""
        with patch.object(self.scheduler, '_run_command') as mock_run:
            with patch.object(self.scheduler, '_update_crontab') as mock_update:
                mock_run.return_value = "*/5 * * * * cd /path && python3 -m ddns # DDNS: auto-update\nother cron job"
                mock_update.return_value = True

                result = self.scheduler.uninstall()
                self.assertTrue(result)
                mock_update.assert_called_once()
                call_args = mock_update.call_args[0][0]
                self.assertNotIn("DDNS", call_args)
                self.assertIn("other cron job", call_args)


if __name__ == '__main__':
    unittest.main()
