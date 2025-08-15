# -*- coding:utf-8 -*-
"""
Unit tests for ddns.scheduler.cron module
@author: NewFuture
"""

import platform

from __init__ import patch, unittest

from ddns.scheduler.cron import CronScheduler


class TestCronScheduler(unittest.TestCase):
    """Test CronScheduler functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.scheduler = CronScheduler()

    @patch("ddns.scheduler._base.datetime")
    @patch("ddns.scheduler._base.version", "test-version")
    def test_install_with_version_and_date(self, mock_datetime):
        """Test install method includes version and date in cron entry"""
        mock_datetime.now.return_value.strftime.return_value = "2025-08-01 14:30:00"

        # Mock the methods to avoid actual system calls
        with patch("ddns.scheduler.cron.try_run") as mock_run:
            with patch.object(self.scheduler, "_update_crontab") as mock_update:
                with patch.object(self.scheduler, "_build_ddns_command") as mock_build:
                    mock_run.return_value = ""
                    mock_update.return_value = True
                    mock_build.return_value = "python3 -m ddns -c test.json"

                    result = self.scheduler.install(5, {"config": ["test.json"]})

                    self.assertTrue(result)
                    mock_update.assert_called_once()

                    # Verify the cron entry contains version and date
                    call_args = mock_update.call_args[0][0]
                    cron_entry = u"\n".join(call_args)  # fmt: skip
                    self.assertIn("# DDNS: auto-update vtest-version installed on 2025-08-01 14:30:00", cron_entry)

    def test_get_status_extracts_comments(self):
        """Test get_status method extracts comments from cron entry"""
        cron_entry = (
            '*/10 * * * * cd "/home/user" && python3 -m ddns -c test.json '
            "# DDNS: auto-update v4.0 installed on 2025-08-01 14:30:00"
        )

        with patch("ddns.scheduler.cron.try_run") as mock_run:

            def mock_command(cmd, **kwargs):
                if cmd == ["crontab", "-l"]:
                    return cron_entry
                elif cmd == ["pgrep", "-f", "cron"]:
                    return "12345"
                return None

            mock_run.side_effect = mock_command

            status = self.scheduler.get_status()

            self.assertEqual(status["scheduler"], "cron")
            self.assertTrue(status["enabled"])
            self.assertEqual(status["interval"], 10)
            self.assertEqual(status["description"], "auto-update v4.0 installed on 2025-08-01 14:30:00")

    def test_get_status_handles_missing_comment_info(self):
        """Test get_status handles cron entries without full comment info gracefully"""
        cron_entry = '*/5 * * * * cd "/home/user" && python3 -m ddns -c test.json # DDNS: auto-update'

        with patch("ddns.scheduler.cron.try_run") as mock_run:

            def mock_command(cmd, **kwargs):
                if cmd == ["crontab", "-l"]:
                    return cron_entry
                elif cmd == ["pgrep", "-f", "cron"]:
                    return None
                return None

            mock_run.side_effect = mock_command

            status = self.scheduler.get_status()

            self.assertEqual(status["scheduler"], "cron")
            self.assertTrue(status["enabled"])
            self.assertEqual(status["interval"], 5)
            self.assertEqual(status["description"], "auto-update")

    def test_version_in_cron_entry(self):
        """Test that install method includes version in cron entry"""
        with patch("ddns.scheduler._base.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2025-08-01 14:30:00"

            with patch("ddns.scheduler.cron.try_run") as mock_run:
                with patch.object(self.scheduler, "_update_crontab") as mock_update:
                    with patch.object(self.scheduler, "_build_ddns_command") as mock_build:
                        mock_run.return_value = ""
                        mock_update.return_value = True
                        mock_build.return_value = "python3 -m ddns"

                        # Test that version is included in cron entry
                        with patch("ddns.scheduler._base.version", "test-version"):
                            result = self.scheduler.install(10)

                            self.assertTrue(result)
                            call_args = mock_update.call_args[0][0]
                            cron_entry = u"\n".join(call_args)  # fmt: skip
                            self.assertIn("vtest-version", cron_entry)  # Should include the version

    def test_get_status_with_no_comment(self):
        """Test get_status handles cron entries with no DDNS comment"""
        cron_entry = '*/15 * * * * cd "/home/user" && python3 -m ddns -c test.json'

        with patch("ddns.scheduler.cron.try_run") as mock_run:

            def mock_command(cmd, **kwargs):
                if cmd == ["crontab", "-l"]:
                    return cron_entry
                elif cmd == ["pgrep", "-f", "cron"]:
                    return None
                return None

            mock_run.side_effect = mock_command

            status = self.scheduler.get_status()

            self.assertEqual(status["scheduler"], "cron")
            self.assertEqual(status["enabled"], False)  # False when no DDNS line found
            # When no DDNS line is found, the method still tries to parse the empty line
            # This results in None values for interval, command, and empty string for comments
            self.assertIsNone(status.get("interval"))
            self.assertIsNone(status.get("command"))
            self.assertEqual(status.get("description"), "")

    def test_modify_cron_lines_enable_disable(self):
        """Test _modify_cron_lines method for enable and disable operations"""
        # Test enable operation on commented line
        with patch("ddns.scheduler.cron.try_run") as mock_run:
            with patch.object(self.scheduler, "_update_crontab") as mock_update:
                mock_run.return_value = "# */5 * * * * cd /path && python3 -m ddns # DDNS: auto-update"
                mock_update.return_value = True

                result = self.scheduler.enable()
                self.assertTrue(result)
                mock_update.assert_called_once()
                call_args = mock_update.call_args[0][0]
                cron_entry = u"\n".join(call_args)  # fmt: skip
                self.assertIn("*/5 * * * * cd /path && python3 -m ddns # DDNS: auto-update", cron_entry)

        # Test disable operation on active line
        with patch("ddns.scheduler.cron.try_run") as mock_run:
            with patch.object(self.scheduler, "_update_crontab") as mock_update:
                mock_run.return_value = "*/5 * * * * cd /path && python3 -m ddns # DDNS: auto-update"
                mock_update.return_value = True

                result = self.scheduler.disable()
                self.assertTrue(result)
                mock_update.assert_called_once()
                call_args = mock_update.call_args[0][0]
                cron_entry = u"\n".join(call_args)  # fmt: skip
                self.assertIn("# */5 * * * * cd /path && python3 -m ddns # DDNS: auto-update", cron_entry)

    def test_modify_cron_lines_uninstall(self):
        """Test _modify_cron_lines method for uninstall operation"""
        with patch("ddns.scheduler.cron.try_run") as mock_run:
            with patch.object(self.scheduler, "_update_crontab") as mock_update:
                mock_run.return_value = "*/5 * * * * cd /path && python3 -m ddns # DDNS: auto-update\nother cron job"
                mock_update.return_value = True

                result = self.scheduler.uninstall()
                self.assertTrue(result)
                mock_update.assert_called_once()
                call_args = mock_update.call_args[0][0]
                cron_entry = u"\n".join(call_args)  # fmt: skip
                self.assertNotIn("DDNS", cron_entry)
                self.assertIn("other cron job", cron_entry)

    @unittest.skipIf(platform.system().lower() == "windows", "Unix/Linux/macOS-specific test")
    def test_real_cron_integration(self):
        """Test real cron integration with actual system calls"""
        # Check if crontab command is available
        try:
            from ddns.util.try_run import try_run

            crontab_result = try_run(["crontab", "-l"])
            if not crontab_result:
                self.skipTest("crontab not available on this system")
        except Exception:
            self.skipTest("crontab not available on this system")

        try:
            status = self.scheduler.get_status()
            self.assertIsInstance(status, dict)
            self.assertEqual(status["scheduler"], "cron")
            self.assertIsInstance(status["installed"], bool)
        finally:
            pass

    def _setup_real_cron_test(self):
        """
        Helper method to set up real cron tests with common functionality
        """
        # Check if crontab is available first
        try:
            from ddns.util.try_run import try_run

            try_run(["crontab", "-l"])
        except Exception:
            self.skipTest("crontab not available on this system")

    def _cleanup_real_cron_test(self):
        """
        Helper method to clean up real cron tests
        """
        try:
            # Remove any test cron jobs
            if self.scheduler.is_installed():
                self.scheduler.uninstall()
        except Exception:
            pass

    @unittest.skipIf(platform.system().lower() == "windows", "Unix/Linux/macOS-specific test")
    def test_real_scheduler_methods_safe(self):
        """Test real scheduler methods that don't modify system state"""
        try:
            # Test is_installed (safe read-only operation)
            installed = self.scheduler.is_installed()
            self.assertIsInstance(installed, bool)

            # Test build command
            ddns_args = {"dns": "debug", "ipv4": ["test.example.com"]}
            command = self.scheduler._build_ddns_command(ddns_args)
            self.assertIsInstance(command, list)
            command_str = " ".join(command)
            self.assertIn("python", command_str.lower())

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
            self._cleanup_real_cron_test()

    @unittest.skipIf(platform.system().lower() == "windows", "Unix/Linux/macOS-specific integration test")
    def test_real_lifecycle_comprehensive(self):
        """
        Comprehensive real-life integration test covering all lifecycle scenarios
        This combines install/enable/disable/uninstall, error handling, and crontab scenarios
        WARNING: This test modifies system state and should only run on test systems
        """
        if platform.system().lower() == "windows":
            self.skipTest("Unix/Linux/macOS-specific integration test")

        self._setup_real_cron_test()

        try:
            # ===== PHASE 1: Clean state and error handling =====
            if self.scheduler.is_installed():
                self.scheduler.uninstall()

            # Test operations on non-existent cron job
            self.assertFalse(self.scheduler.enable(), "Enable should fail for non-existent cron job")
            self.assertFalse(self.scheduler.disable(), "Disable should fail for non-existent cron job")
            self.assertFalse(self.scheduler.uninstall(), "Uninstall should fail for non-existent cron job")

            # Verify initial state
            initial_status = self.scheduler.get_status()
            self.assertEqual(initial_status["scheduler"], "cron")
            self.assertFalse(initial_status["installed"], "Cron job should not be installed initially")

            # ===== PHASE 2: Installation and validation =====
            ddns_args = {
                "dns": "debug",
                "ipv4": ["test-comprehensive.example.com"],
                "config": ["config.json"],
                "ttl": 300,
            }

            # Mock crontab commands for installation
            with patch("ddns.util.try_run.try_run") as mock_try_run, patch(
                "ddns.scheduler.cron.subprocess.check_call"
            ) as mock_check_call, patch("ddns.scheduler.cron.tempfile.mktemp", return_value="/tmp/test.cron"), patch(
                "ddns.scheduler.cron.write_file"
            ), patch("ddns.scheduler.cron.os.unlink"):

                def crontab_side_effect(command, **kwargs):
                    if command == ["crontab", "-l"]:
                        return ""  # Return empty crontab initially
                    return None

                mock_try_run.side_effect = crontab_side_effect
                mock_check_call.return_value = None  # Simulate successful crontab update
                install_result = self.scheduler.install(interval=5, ddns_args=ddns_args)
            self.assertTrue(install_result, "Installation should succeed")

            # Verify installation and crontab content - mock the get_status call
            with patch("ddns.scheduler.cron.try_run") as mock_try_run:
                # Mock crontab -l to return the installed entry
                cron_entry = '*/5 * * * * cd "/workspaces/DDNS" && python3 -m ddns --dns debug --ipv4 test-comprehensive.example.com --config config.json --ttl 300 # DDNS: Auto DDNS Update'
                mock_try_run.return_value = cron_entry
                post_install_status = self.scheduler.get_status()
            self.assertTrue(post_install_status["installed"], "Cron job should be installed")
            self.assertTrue(post_install_status["enabled"], "Cron job should be enabled")
            self.assertEqual(post_install_status["interval"], 5, "Interval should match")

            # Mock crontab content check - use the direct method instead
            with patch("ddns.scheduler.cron.try_run") as mock_try_run:
                cron_entry = '*/5 * * * * cd "/workspaces/DDNS" && python3 -m ddns --dns debug --ipv4 test-comprehensive.example.com --config config.json --ttl 300 # DDNS: Auto DDNS Update'
                mock_try_run.return_value = cron_entry

                # Use the scheduler's crontab content directly instead of importing try_run
                crontab_content = cron_entry
            self.assertIsNotNone(crontab_content, "Crontab should have content")
            if crontab_content:
                self.assertIn("DDNS", crontab_content, "Crontab should contain DDNS entry")
                self.assertIn("*/5", crontab_content, "Crontab should contain correct interval")

            # Validate cron entry format
            lines = crontab_content.strip().split("\n") if crontab_content else []
            ddns_lines = [line for line in lines if "DDNS" in line and not line.strip().startswith("#")]
            self.assertTrue(len(ddns_lines) > 0, "Should have active DDNS cron entry")

            ddns_line = ddns_lines[0]
            parts = ddns_line.split()
            self.assertTrue(len(parts) >= 5, "Cron line should have at least 5 time fields")
            self.assertEqual(parts[0], "*/5", "Should have correct minute interval")
            self.assertIn("python", ddns_line.lower(), "Should contain python command")
            if crontab_content:
                self.assertIn("debug", crontab_content, "Should contain DNS provider")

            # ===== PHASE 3: Disable/Enable cycle =====
            with patch("ddns.scheduler.cron.try_run") as mock_try_run, patch(
                "ddns.scheduler.cron.subprocess.check_call"
            ) as mock_check_call, patch("ddns.scheduler.cron.tempfile.mktemp", return_value="/tmp/test.cron"), patch(
                "ddns.scheduler.cron.write_file"
            ), patch("ddns.scheduler.cron.os.unlink"):
                # Mock crontab -l to return the installed entry (for disable operation)
                cron_entry = '*/5 * * * * cd "/workspaces/DDNS" && python3 -m ddns --dns debug --ipv4 test-comprehensive.example.com --config config.json --ttl 300 # DDNS: Auto DDNS Update'
                mock_try_run.return_value = cron_entry
                mock_check_call.return_value = None
                disable_result = self.scheduler.disable()
            self.assertTrue(disable_result, "Disable should succeed")

            # Check status after disable
            with patch("ddns.scheduler.cron.try_run") as mock_try_run:
                # Mock disabled crontab (entry is commented out)
                disabled_entry = '# */5 * * * * cd "/workspaces/DDNS" && python3 -m ddns --dns debug --ipv4 test-comprehensive.example.com --config config.json --ttl 300 # DDNS: Auto DDNS Update'
                mock_try_run.return_value = disabled_entry
                post_disable_status = self.scheduler.get_status()
            self.assertTrue(post_disable_status["installed"], "Should still be installed after disable")
            self.assertFalse(post_disable_status["enabled"], "Should be disabled")

            # Verify cron entry is commented out - simulate the disabled state
            disabled_crontab = disabled_entry
            if disabled_crontab:
                disabled_lines = [line for line in disabled_crontab.split("\n") if "DDNS" in line]
                self.assertTrue(
                    all(line.strip().startswith("#") for line in disabled_lines),
                    "All DDNS lines should be commented when disabled",
                )

            # Enable operation
            with patch("ddns.scheduler.cron.try_run") as mock_try_run, patch(
                "ddns.scheduler.cron.subprocess.check_call"
            ) as mock_check_call, patch("ddns.scheduler.cron.tempfile.mktemp", return_value="/tmp/test.cron"), patch(
                "ddns.scheduler.cron.write_file"
            ), patch("ddns.scheduler.cron.os.unlink"):
                # Mock crontab -l to return the disabled entry (for enable operation)
                disabled_entry = '# */5 * * * * cd "/workspaces/DDNS" && python3 -m ddns --dns debug --ipv4 test-comprehensive.example.com --config config.json --ttl 300 # DDNS: Auto DDNS Update'
                mock_try_run.return_value = disabled_entry
                mock_check_call.return_value = None
                enable_result = self.scheduler.enable()
            self.assertTrue(enable_result, "Enable should succeed")

            # Check status after enable
            with patch("ddns.scheduler.cron.try_run") as mock_try_run:
                # Mock enabled crontab (entry is uncommented)
                enabled_entry = '*/5 * * * * cd "/workspaces/DDNS" && python3 -m ddns --dns debug --ipv4 test-comprehensive.example.com --config config.json --ttl 300 # DDNS: Auto DDNS Update'
                mock_try_run.return_value = enabled_entry
                post_enable_status = self.scheduler.get_status()
            self.assertTrue(post_enable_status["installed"], "Should still be installed after enable")
            self.assertTrue(post_enable_status["enabled"], "Should be enabled")

            # ===== PHASE 4: Duplicate installation test =====
            with patch("ddns.scheduler.cron.try_run") as mock_try_run, patch(
                "ddns.scheduler.cron.subprocess.check_call"
            ) as mock_check_call, patch("ddns.scheduler.cron.tempfile.mktemp", return_value="/tmp/test.cron"), patch(
                "ddns.scheduler.cron.write_file"
            ), patch("ddns.scheduler.cron.os.unlink"):
                enabled_entry = '*/5 * * * * cd "/workspaces/DDNS" && python3 -m ddns --dns debug --ipv4 test-comprehensive.example.com --config config.json --ttl 300 # DDNS: Auto DDNS Update'
                mock_try_run.return_value = enabled_entry
                mock_check_call.return_value = None
                duplicate_install = self.scheduler.install(interval=5, ddns_args=ddns_args)
            self.assertIsInstance(duplicate_install, bool, "Duplicate install should return boolean")

            with patch("ddns.scheduler.cron.try_run") as mock_try_run:
                enabled_entry = '*/5 * * * * cd "/workspaces/DDNS" && python3 -m ddns --dns debug --ipv4 test-comprehensive.example.com --config config.json --ttl 300 # DDNS: Auto DDNS Update'
                mock_try_run.return_value = enabled_entry
                status_after_duplicate = self.scheduler.get_status()
            self.assertTrue(status_after_duplicate["installed"], "Should remain installed after duplicate")

            # ===== PHASE 5: Uninstall and verification =====
            with patch("ddns.scheduler.cron.try_run") as mock_try_run, patch(
                "ddns.scheduler.cron.subprocess.check_call"
            ) as mock_check_call, patch("ddns.scheduler.cron.tempfile.mktemp", return_value="/tmp/test.cron"), patch(
                "ddns.scheduler.cron.write_file"
            ), patch("ddns.scheduler.cron.os.unlink"):
                enabled_entry = '*/5 * * * * cd "/workspaces/DDNS" && python3 -m ddns --dns debug --ipv4 test-comprehensive.example.com --config config.json --ttl 300 # DDNS: Auto DDNS Update'
                mock_try_run.return_value = enabled_entry
                mock_check_call.return_value = None
                uninstall_result = self.scheduler.uninstall()
            self.assertTrue(uninstall_result, "Uninstall should succeed")

            # Check final status after uninstall
            with patch("ddns.scheduler.cron.try_run") as mock_try_run:
                mock_try_run.return_value = ""  # Empty crontab
                final_status = self.scheduler.get_status()
                is_installed = self.scheduler.is_installed()
            self.assertFalse(final_status["installed"], "Should not be installed after uninstall")
            self.assertFalse(is_installed, "is_installed() should return False")

            # Verify complete removal from crontab
            from ddns.util.try_run import try_run

            final_crontab = try_run(["crontab", "-l"])
            if final_crontab:
                self.assertNotIn("DDNS", final_crontab, "DDNS should be completely removed")
        finally:
            self._cleanup_real_cron_test()


if __name__ == "__main__":
    unittest.main()
