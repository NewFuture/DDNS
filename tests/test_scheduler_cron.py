# -*- coding:utf-8 -*-
"""
Unit tests for ddns.scheduler.corn module
@author: NewFuture
"""
import platform
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

    def test_version_in_cron_entry(self):
        """Test that install method includes version in cron entry"""
        with patch("ddns.scheduler.cron.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2025-08-01 14:30:00"

            with patch.object(self.scheduler, '_run_command') as mock_run:
                with patch.object(self.scheduler, '_update_crontab') as mock_update:
                    with patch.object(self.scheduler, '_build_ddns_command') as mock_build:
                        mock_run.return_value = ""
                        mock_update.return_value = True
                        mock_build.return_value = "python3 -m ddns"

                        # Test that version is included in cron entry
                        with patch('ddns.scheduler.cron.version', 'test-version'):
                            result = self.scheduler.install(10)

                            self.assertTrue(result)
                            call_args = mock_update.call_args[0][0]
                            self.assertIn("vtest-version", call_args)  # Should include the version

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

    @unittest.skipIf(platform.system().lower() == "windows", "Unix/Linux/macOS-specific test")
    def test_real_cron_integration(self):
        """Test real cron integration with actual system calls"""
        # Check if crontab command is available
        try:
            crontab_result = self.scheduler._run_command(["crontab", "-l"])
            if not crontab_result:
                self.skipTest("crontab not available on this system")
        except Exception:
            self.skipTest("crontab not available on this system")

        # Test real crontab list with shorter timeout to prevent hanging
        # Save original method and override with shorter timeout
        original_run_command = self.scheduler._run_command

        def fast_run_command(command, **kwargs):
            kwargs.setdefault('timeout', 5)  # 5 second timeout for tests
            return original_run_command(command, **kwargs)

        self.scheduler._run_command = fast_run_command

        try:
            status = self.scheduler.get_status()
            self.assertIsInstance(status, dict)
            self.assertEqual(status["scheduler"], "cron")
            self.assertIsInstance(status["installed"], bool)
        finally:
            # Restore original method
            self.scheduler._run_command = original_run_command

    @unittest.skipIf(platform.system().lower() == "windows", "Unix/Linux/macOS-specific test")
    def test_real_scheduler_methods_safe(self):
        """Test real scheduler methods that don't modify system state"""
        # Check if crontab command is available
        try:
            crontab_result = self.scheduler._run_command(["crontab", "-l"])
            if not crontab_result:
                self.skipTest("crontab not available on this system")
        except Exception:
            self.skipTest("crontab not available on this system")

        # Save original method and override with shorter timeout
        original_run_command = self.scheduler._run_command

        def fast_run_command(command, **kwargs):
            kwargs.setdefault('timeout', 5)  # 5 second timeout for tests
            return original_run_command(command, **kwargs)

        self.scheduler._run_command = fast_run_command

        try:
            # Test is_installed (safe read-only operation)
            installed = self.scheduler.is_installed()
            self.assertIsInstance(installed, bool)

            # Test build command
            ddns_args = {"dns": "debug", "ipv4": ["test.example.com"]}
            command = self.scheduler._build_ddns_command(ddns_args)
            self.assertIsInstance(command, str)
            self.assertIn("python", command.lower())

            # Test get status (safe read-only operation)
            status = self.scheduler.get_status()
            required_keys = ["scheduler", "installed", "enabled", "interval"]
            for key in required_keys:
                self.assertIn(key, status)

            # Test enable/disable without actual installation (should handle gracefully)
            enable_result = self.scheduler.enable()
            self.assertIsInstance(enable_result, bool)

            disable_result = self.scheduler.disable()
            self.assertIsInstance(disable_result, bool)
        finally:
            # Restore original method
            self.scheduler._run_command = original_run_command


if __name__ == '__main__':
    unittest.main()
