# -*- coding:utf-8 -*-
"""
Unit tests for ddns.scheduler.launchd module
@author: NewFuture
"""

import os
import platform
import sys

from __init__ import patch, unittest

from ddns.scheduler.launchd import LaunchdScheduler
from ddns.util.try_run import try_run

# Handle builtins import for Python 2/3 compatibility
if sys.version_info[0] >= 3:
    builtins_module = "builtins"
    permission_error = PermissionError
else:
    # Python 2
    builtins_module = "__builtin__"
    permission_error = OSError


class TestLaunchdScheduler(unittest.TestCase):
    """Test cases for LaunchdScheduler class"""

    def setUp(self):
        """Set up test fixtures"""
        self.scheduler = LaunchdScheduler()

    def test_service_name_property(self):
        """Test service name constant"""
        expected_name = "cc.newfuture.ddns"
        self.assertEqual(self.scheduler.LABEL, expected_name)

    def test_plist_path_property(self):
        """Test plist path property"""
        expected_path = os.path.expanduser("~/Library/LaunchAgents/cc.newfuture.ddns.plist")
        self.assertEqual(self.scheduler._get_plist_path(), expected_path)

    def test_get_status_loaded_enabled(self):
        """Test get_status when service is loaded and enabled"""
        # Mock plist file exists and has content
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>cc.newfuture.ddns</string>
    <key>StartInterval</key>
    <integer>300</integer>
</dict>
</plist>"""

        with patch("os.path.exists", return_value=True), patch(
            "ddns.scheduler.launchd.read_file_safely", return_value=plist_content
        ), patch("ddns.scheduler.launchd.try_run") as mock_run_command:
            # Mock launchctl list to return service is loaded - need to include the full label
            mock_run_command.return_value = "PID\tStatus\tLabel\n123\t0\tcc.newfuture.ddns\n456\t0\tcom.apple.other"

            status = self.scheduler.get_status()

            expected_status = {
                "scheduler": "launchd",
                "installed": True,
                "enabled": True,
                "interval": 5,  # 300 seconds / 60 = 5 minutes
            }
            self.assertEqual(status["scheduler"], expected_status["scheduler"])
            self.assertEqual(status["installed"], expected_status["installed"])
            self.assertEqual(status["enabled"], expected_status["enabled"])
            self.assertEqual(status["interval"], expected_status["interval"])

    def test_get_status_not_loaded(self):
        """Test get_status when service is not loaded"""
        # Mock plist file doesn't exist
        with patch("os.path.exists", return_value=False), patch(
            "ddns.scheduler.launchd.read_file_safely", return_value=None
        ):
            status = self.scheduler.get_status()

            # When not installed, only basic keys are returned
            self.assertEqual(status["scheduler"], "launchd")
            self.assertEqual(status["installed"], False)
            # enabled and interval keys are not returned when not installed
            self.assertNotIn("enabled", status)
            self.assertNotIn("interval", status)

    @patch("os.path.exists")
    def test_is_installed_true(self, mock_exists):
        """Test is_installed returns True when plist file exists"""
        mock_exists.return_value = True

        result = self.scheduler.is_installed()
        self.assertTrue(result)

    @patch("os.path.exists")
    def test_is_installed_false(self, mock_exists):
        """Test is_installed returns False when plist file doesn't exist"""
        mock_exists.return_value = False

        result = self.scheduler.is_installed()
        self.assertFalse(result)

    @patch("ddns.scheduler.launchd.write_file")
    def test_install_with_sudo_fallback(self, mock_write_file):
        """Test install with sudo fallback for permission issues"""
        mock_write_file.return_value = None  # write_file succeeds

        with patch("ddns.scheduler.launchd.try_run", return_value="loaded successfully"):
            ddns_args = {"dns": "debug", "ipv4": ["test.com"]}
            result = self.scheduler.install(5, ddns_args)
            self.assertTrue(result)

    @unittest.skipUnless(platform.system().lower() == "darwin", "macOS-specific test")
    def test_launchctl_with_sudo_retry(self):
        """Test launchctl command with automatic sudo retry on permission error"""
        with patch("ddns.scheduler.launchd.try_run") as mock_run_cmd:
            # Test that launchctl operations use try_run directly
            mock_run_cmd.return_value = "success"

            # Test enable which uses launchctl load
            plist_path = self.scheduler._get_plist_path()
            with patch("os.path.exists", return_value=True):
                result = self.scheduler.enable()
                self.assertTrue(result)
                # Verify the call was made with the expected command and logger
                mock_run_cmd.assert_called_with(["launchctl", "load", plist_path], logger=self.scheduler.logger)

    @patch("os.path.exists")
    @patch("os.remove")
    def test_uninstall_success(self, mock_remove, mock_exists):
        """Test successful uninstall"""
        mock_exists.return_value = True

        with patch("ddns.scheduler.launchd.try_run", return_value="unloaded successfully"):
            result = self.scheduler.uninstall()
            self.assertTrue(result)
            mock_remove.assert_called_once()

    @patch("os.path.exists")
    @patch("os.remove")
    def test_uninstall_with_permission_handling(self, mock_remove, mock_exists):
        """Test uninstall handles permission errors gracefully"""
        mock_exists.return_value = True

        # Mock file removal failure - use appropriate error type for Python version
        mock_remove.side_effect = permission_error("Permission denied")

        with patch("ddns.scheduler.launchd.try_run", return_value="") as mock_run:
            result = self.scheduler.uninstall()

            # Should handle permission error gracefully and still return True
            self.assertTrue(result)
            # Should attempt to unload the service
            mock_run.assert_called_once()
            # Should attempt to remove the file
            mock_remove.assert_called_once()

    def test_enable_success(self):
        """Test successful enable"""
        with patch("os.path.exists", return_value=True):
            with patch("ddns.scheduler.launchd.try_run", return_value="loaded successfully"):
                result = self.scheduler.enable()
                self.assertTrue(result)

    def test_disable_success(self):
        """Test successful disable"""
        with patch("ddns.scheduler.launchd.try_run", return_value="unloaded successfully"):
            result = self.scheduler.disable()
            self.assertTrue(result)

    def test_build_ddns_command(self):
        """Test _build_ddns_command functionality"""
        ddns_args = {"dns": "debug", "ipv4": ["test.example.com"], "debug": True}

        command = self.scheduler._build_ddns_command(ddns_args)

        self.assertIsInstance(command, list)
        command_str = " ".join(command)
        self.assertIn("debug", command_str)
        self.assertIn("test.example.com", command_str)

    @unittest.skipUnless(platform.system().lower() == "darwin", "macOS-specific test")
    def test_real_launchctl_availability(self):
        """Test if launchctl is available on macOS systems"""
        try:
            # Test launchctl availability by trying to run it
            result = try_run(["launchctl", "version"])
            # launchctl is available if result is not None
            if result is None:
                self.skipTest("launchctl not available")
        except (OSError, Exception):
            self.skipTest("launchctl not found on this system")

    @unittest.skipUnless(platform.system().lower() == "darwin", "macOS-specific test")
    def test_permission_check_methods(self):
        """Test permission checking for launchd operations"""
        # Test if we can write to LaunchAgents directory
        agents_dir = os.path.expanduser("~/Library/LaunchAgents")
        can_write = os.access(agents_dir, os.W_OK) if os.path.exists(agents_dir) else False

        # For system-wide daemons (/Library/LaunchDaemons), we'd typically need sudo
        daemon_dir = "/Library/LaunchDaemons"
        daemon_write = os.access(daemon_dir, os.W_OK) if os.path.exists(daemon_dir) else False

        # If we can't write to system locations, we should be able to use sudo
        if not daemon_write:
            try:
                try_run(["sudo", "--version"])
                sudo_available = True
            except Exception:
                sudo_available = False
            # sudo should be available on macOS systems
            if not sudo_available:
                self.skipTest("sudo not available for elevated permissions")

        # User agents directory should generally be writable or sudo should be available
        if os.path.exists(agents_dir):
            try:
                try_run(["sudo", "--version"])
                sudo_available = True
            except Exception:
                sudo_available = False
            self.assertTrue(
                can_write or sudo_available, "Should be able to write to user LaunchAgents or have sudo access"
            )

    @unittest.skipUnless(platform.system().lower() == "darwin", "macOS-specific test")
    def test_real_launchd_integration(self):
        """Test real launchd integration with actual system calls"""
        # Test launchctl availability by trying to run it directly
        try:
            result = try_run(["launchctl", "version"])
            if result is None:
                self.skipTest("launchctl not available on this system")
        except (OSError, Exception):
            self.skipTest("launchctl not available on this system")

        # Test real launchctl version call
        version_result = try_run(["launchctl", "version"])
        # On a real macOS system, this should work
        self.assertTrue(version_result is None or isinstance(version_result, str))

        # Test real status check
        status = self.scheduler.get_status()
        self.assertIsInstance(status, dict)
        self.assertEqual(status["scheduler"], "launchd")
        self.assertIsInstance(status["installed"], bool)

        # Test launchctl list (read-only operation)
        list_result = try_run(["launchctl", "list"])
        # This might return None or string based on system state
        self.assertTrue(list_result is None or isinstance(list_result, str))

    @unittest.skipUnless(platform.system().lower() == "darwin", "macOS-specific test")
    def test_real_scheduler_methods_safe(self):
        """Test real scheduler methods that don't modify system state"""
        # Test launchctl availability by trying to run it directly
        try:
            result = try_run(["launchctl", "version"])
            if result is None:
                self.skipTest("launchctl not available on this system")
        except (OSError, Exception):
            self.skipTest("launchctl not available on this system")

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
        basic_keys = ["scheduler", "installed"]
        for key in basic_keys:
            self.assertIn(key, status)
        # enabled and interval are only present when service is installed
        if status["installed"]:
            optional_keys = ["enabled", "interval"]
            for key in optional_keys:
                self.assertIn(key, status)

        # Test plist path generation
        plist_path = self.scheduler._get_plist_path()
        self.assertIsInstance(plist_path, str)
        self.assertTrue(plist_path.endswith(".plist"))
        self.assertIn("LaunchAgents", plist_path)

        # Test enable/disable without actual installation (should handle gracefully)
        enable_result = self.scheduler.enable()
        self.assertIsInstance(enable_result, bool)

        disable_result = self.scheduler.disable()
        self.assertIsInstance(disable_result, bool)

    def _setup_real_launchd_test(self):
        """
        Helper method to set up real launchd tests with common functionality
        Returns: (original_label, test_service_label)
        """
        # Check if launchctl is available first
        try:
            result = try_run(["launchctl", "version"])
            if result is None:
                self.skipTest("launchctl not available on this system")
        except (OSError, Exception):
            self.skipTest("launchctl not available on this system")

        # Use a unique test service label to avoid conflicts
        original_label = self.scheduler.LABEL
        import time

        test_service_label = "cc.newfuture.ddns.test.{}".format(int(time.time()))
        self.scheduler.LABEL = test_service_label  # type: ignore

        return original_label, test_service_label

    def _cleanup_real_launchd_test(self, original_label, test_service_label):
        """
        Helper method to clean up real launchd tests
        """
        try:
            # Remove any test services
            if self.scheduler.is_installed():
                self.scheduler.uninstall()
        except Exception:
            pass

        # Restore original service label
        self.scheduler.LABEL = original_label

        # Final cleanup - ensure test service is removed
        try:
            self.scheduler.LABEL = test_service_label
            if self.scheduler.is_installed():
                self.scheduler.uninstall()
        except Exception:
            pass

        # Restore original label
        self.scheduler.LABEL = original_label

    @unittest.skipUnless(platform.system().lower() == "darwin", "macOS-specific integration test")
    def test_real_lifecycle_comprehensive(self):
        """
        Comprehensive real-life integration test covering all lifecycle scenarios
        This combines install/enable/disable/uninstall, error handling, and permission scenarios
        WARNING: This test modifies system state and should only run on test systems
        """
        if platform.system().lower() != "darwin":
            self.skipTest("macOS-specific integration test")

        original_label, test_service_label = self._setup_real_launchd_test()

        try:
            # ===== PHASE 1: Clean state and error handling =====
            if self.scheduler.is_installed():
                self.scheduler.uninstall()

            # Test operations on non-existent service
            self.assertFalse(self.scheduler.enable(), "Enable should fail for non-existent service")

            # Verify initial state
            initial_status = self.scheduler.get_status()
            self.assertEqual(initial_status["scheduler"], "launchd")
            self.assertFalse(initial_status["installed"], "Service should not be installed initially")

            # ===== PHASE 2: Installation and validation =====
            ddns_args = {
                "dns": "debug",
                "ipv4": ["test-comprehensive.example.com"],
                "config": ["config.json"],
                "ttl": 300,
            }
            install_result = self.scheduler.install(interval=5, ddns_args=ddns_args)
            self.assertTrue(install_result, "Installation should succeed")

            # Verify installation
            post_install_status = self.scheduler.get_status()
            self.assertTrue(post_install_status["installed"], "Service should be installed")
            self.assertTrue(post_install_status["enabled"], "Service should be enabled")
            self.assertEqual(post_install_status["interval"], 5, "Interval should match")

            # Verify plist file exists and is readable
            plist_path = self.scheduler._get_plist_path()
            self.assertTrue(os.path.exists(plist_path), "Plist file should exist after installation")
            self.assertTrue(os.access(plist_path, os.R_OK), "Plist file should be readable")

            # Validate plist content
            with open(plist_path, "r") as f:
                content = f.read()
            self.assertIn(test_service_label, content, "Plist should contain correct service label")
            self.assertIn("StartInterval", content, "Plist should contain StartInterval")

            # ===== PHASE 3: Disable/Enable cycle =====
            disable_result = self.scheduler.disable()
            self.assertTrue(disable_result, "Disable should succeed")

            post_disable_status = self.scheduler.get_status()
            self.assertTrue(post_disable_status["installed"], "Should still be installed after disable")
            self.assertFalse(post_disable_status["enabled"], "Should be disabled")

            enable_result = self.scheduler.enable()
            self.assertTrue(enable_result, "Enable should succeed")

            post_enable_status = self.scheduler.get_status()
            self.assertTrue(post_enable_status["installed"], "Should still be installed after enable")
            self.assertTrue(post_enable_status["enabled"], "Should be enabled")

            # ===== PHASE 4: Duplicate installation and permission test =====
            duplicate_install = self.scheduler.install(interval=5, ddns_args=ddns_args)
            self.assertIsInstance(duplicate_install, bool, "Duplicate install should return boolean")

            status_after_duplicate = self.scheduler.get_status()
            self.assertTrue(status_after_duplicate["installed"], "Should remain installed after duplicate")

            # Test LaunchAgents directory accessibility if needed
            agents_dir = os.path.expanduser("~/Library/LaunchAgents")
            if os.path.exists(agents_dir) and os.access(agents_dir, os.W_OK):
                # Test file creation/removal
                test_file = os.path.join(agents_dir, "test_write_access.tmp")
                try:
                    with open(test_file, "w") as f:
                        f.write("test")
                    self.assertTrue(os.path.exists(test_file), "Should be able to create test file")
                    os.remove(test_file)
                    self.assertFalse(os.path.exists(test_file), "Should be able to remove test file")
                except (OSError, IOError):
                    pass  # Permission test failed, but not critical

            # ===== PHASE 5: Uninstall and verification =====
            uninstall_result = self.scheduler.uninstall()
            self.assertTrue(uninstall_result, "Uninstall should succeed")

            final_status = self.scheduler.get_status()
            self.assertFalse(final_status["installed"], "Should not be installed after uninstall")
            self.assertFalse(self.scheduler.is_installed(), "is_installed() should return False")

            # Verify plist file is removed
            self.assertFalse(os.path.exists(plist_path), "Plist file should be removed after uninstall")
        finally:
            self._cleanup_real_launchd_test(original_label, test_service_label)


if __name__ == "__main__":
    unittest.main()
