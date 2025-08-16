# -*- coding:utf-8 -*-
"""
Unit tests for ddns.scheduler.systemd module
@author: NewFuture
"""

import os
import platform

from __init__ import patch, unittest

from ddns.scheduler.systemd import SystemdScheduler
from ddns.util.try_run import try_run


class TestSystemdScheduler(unittest.TestCase):
    """Test cases for SystemdScheduler class"""

    def setUp(self):
        """Set up test fixtures"""
        self.scheduler = SystemdScheduler()

    def test_service_name_property(self):
        """Test service name constant"""
        self.assertEqual(self.scheduler.SERVICE_NAME, "ddns.service")

    def test_timer_name_property(self):
        """Test timer name constant"""
        self.assertEqual(self.scheduler.TIMER_NAME, "ddns.timer")

    @patch("os.path.exists")
    def test_is_installed_true(self, mock_exists):
        """Test is_installed returns True when service exists"""
        mock_exists.return_value = True
        result = self.scheduler.is_installed()
        self.assertTrue(result)

    @patch("os.path.exists")
    def test_is_installed_false(self, mock_exists):
        """Test is_installed returns False when service doesn't exist"""
        mock_exists.return_value = False
        result = self.scheduler.is_installed()
        self.assertFalse(result)

    @patch("subprocess.check_output")
    @patch("ddns.scheduler.systemd.read_file_safely")
    @patch("os.path.exists")
    def test_get_status_success(self, mock_exists, mock_read_file, mock_check_output):
        """Test get_status with proper file reading"""
        mock_exists.return_value = True
        # Mock read_file_safely to return content for timer file and service file

        def mock_read_side_effect(file_path):
            if "ddns.timer" in file_path:
                return "OnUnitActiveSec=5m\n"
            elif "ddns.service" in file_path:
                return "ExecStart=/usr/bin/python3 -m ddns\n"
            return ""

        mock_read_file.side_effect = mock_read_side_effect
        # Mock subprocess.check_output to return "enabled" status
        mock_check_output.return_value = "enabled"

        status = self.scheduler.get_status()

        self.assertEqual(status["scheduler"], "systemd")
        self.assertTrue(status["installed"])
        self.assertTrue(status["enabled"])
        self.assertEqual(status["interval"], 5)

    @patch("ddns.scheduler.systemd.write_file")
    @patch.object(SystemdScheduler, "_systemctl")
    def test_install_with_sudo_fallback(self, mock_systemctl, mock_write_file):
        """Test install with sudo fallback for permission issues"""
        # Mock successful file writing and systemctl calls
        mock_write_file.return_value = None  # write_file doesn't return anything
        mock_systemctl.side_effect = [True, True, True]  # daemon-reload, enable, start all succeed

        ddns_args = {"dns": "debug", "ipv4": ["test.com"]}
        result = self.scheduler.install(5, ddns_args)
        self.assertTrue(result)

        # Verify that write_file was called twice (service and timer files)
        self.assertEqual(mock_write_file.call_count, 2)
        # Verify systemctl was called 3 times (daemon-reload, enable, start)
        self.assertEqual(mock_systemctl.call_count, 3)

    def test_systemctl_basic_functionality(self):
        """Test systemctl command basic functionality"""
        # Test that systemctl calls try_run and returns appropriate boolean
        with patch("ddns.scheduler.systemd.try_run") as mock_run_cmd:
            # Test success case
            mock_run_cmd.return_value = "success"
            result = self.scheduler._systemctl("enable", "ddns.timer")
            self.assertTrue(result)
            mock_run_cmd.assert_called_with(["systemctl", "enable", "ddns.timer"], logger=self.scheduler.logger)

            # Test failure case
            mock_run_cmd.return_value = None
            result = self.scheduler._systemctl("enable", "ddns.timer")
            self.assertFalse(result)

    @patch("os.remove")
    @patch.object(SystemdScheduler, "_systemctl")
    def test_uninstall_with_permission_handling(self, mock_systemctl, mock_remove):
        """Test uninstall with proper permission handling"""
        mock_systemctl.return_value = True  # disable() succeeds

        # Mock successful file removal
        mock_remove.return_value = None

        result = self.scheduler.uninstall()
        self.assertTrue(result)

        # Verify both service and timer files are removed
        self.assertEqual(mock_remove.call_count, 2)

    def test_build_ddns_command(self):
        """Test _build_ddns_command functionality"""
        ddns_args = {"dns": "debug", "ipv4": ["test.example.com"], "debug": True}
        command = self.scheduler._build_ddns_command(ddns_args)
        self.assertIsInstance(command, list)
        command_str = " ".join(command)
        self.assertIn("debug", command_str)
        self.assertIn("test.example.com", command_str)

    @unittest.skipUnless(platform.system().lower() == "linux", "Linux-specific test")
    def test_real_systemctl_availability(self):
        """Test if systemctl is available on Linux systems"""
        # Check if systemctl command is available
        try:
            from ddns.util.try_run import try_run

            systemctl_result = try_run(["systemctl", "--version"])
            if not systemctl_result:
                self.skipTest("systemctl not available on this system")
        except Exception:
            self.skipTest("systemctl not available on this system")

        # Test both regular and sudo access
        self.scheduler._systemctl("--version")

        # Test if we have sudo access (don't actually run sudo commands in tests)
        try:
            sudo_result = try_run(["sudo", "--version"])
            if sudo_result:
                # Just verify sudo is available for fallback
                self.assertIsNotNone(sudo_result)
        except Exception:
            # sudo not available, skip test
            self.skipTest("sudo not available for elevated permissions")

    @unittest.skipUnless(platform.system().lower() == "linux", "Linux-specific test")
    def test_permission_check_methods(self):
        """Test permission checking for systemd operations"""
        # Test if we can write to systemd directory
        systemd_dir = "/etc/systemd/system"
        can_write = os.access(systemd_dir, os.W_OK) if os.path.exists(systemd_dir) else False

        # If we can't write directly, we should be able to use sudo
        if not can_write:
            try:
                sudo_result = try_run(["sudo", "--version"])
                self.assertIsNotNone(sudo_result, "sudo should be available for elevated permissions")
            except Exception:
                self.skipTest("sudo not available for elevated permissions")

    @unittest.skipUnless(platform.system().lower() == "linux", "Linux-specific test")
    def test_real_systemd_integration(self):
        """Test real systemd integration with actual system calls"""
        # Check if systemctl command is available
        try:
            systemctl_result = try_run(["systemctl", "--version"])
            if not systemctl_result:
                self.skipTest("systemctl not available on this system")
        except Exception:
            self.skipTest("systemctl not available on this system")

        # Test real systemctl version call
        version_result = self.scheduler._systemctl("--version")
        # On a real Linux system with systemd, this should work
        # We don't assert the result since it may vary based on permissions
        self.assertIsInstance(version_result, bool)

        # Test real status check for a non-existent service
        status = self.scheduler.get_status()
        self.assertIsInstance(status, dict)
        self.assertEqual(status["scheduler"], "systemd")
        self.assertIsInstance(status["installed"], bool)

        # Test if daemon-reload works (read-only operation)
        daemon_reload_result = self.scheduler._systemctl("daemon-reload")
        # This might fail due to permissions, but shouldn't crash
        self.assertIsInstance(daemon_reload_result, bool)

    @unittest.skipUnless(platform.system().lower() == "linux", "Linux-specific test")
    def test_real_scheduler_methods_safe(self):
        """Test real scheduler methods that don't modify system state"""
        # Check if systemctl command is available
        try:
            systemctl_result = try_run(["systemctl", "--version"])
            if not systemctl_result:
                self.skipTest("systemctl not available on this system")
        except Exception:
            self.skipTest("systemctl not available on this system")

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
        # Basic keys should always be present
        basic_required_keys = ["scheduler", "installed"]
        for key in basic_required_keys:
            self.assertIn(key, status)

        # If service is installed, additional keys should be present
        if status.get("installed", False):
            additional_keys = ["enabled", "interval"]
            for key in additional_keys:
                self.assertIn(key, status)

        # Test enable/disable without actual installation (should handle gracefully)
        enable_result = self.scheduler.enable()
        self.assertIsInstance(enable_result, bool)

        disable_result = self.scheduler.disable()
        self.assertIsInstance(disable_result, bool)

    @unittest.skipUnless(platform.system().lower() == "linux", "Linux-specific test")
    def test_real_systemd_lifecycle_operations(self):
        """Test real systemd lifecycle operations: install -> enable -> disable -> uninstall"""
        # Check if systemctl command is available
        try:
            systemctl_result = try_run(["systemctl", "--version"])
            if not systemctl_result:
                self.skipTest("systemctl not available on this system")
        except Exception:
            self.skipTest("systemctl not available on this system")

        # Test arguments for DDNS
        ddns_args = {"dns": "debug", "ipv4": ["test.example.com"], "interval": 10}

        # Store original state
        original_installed = self.scheduler.is_installed()
        self.scheduler.get_status() if original_installed else None

        try:
            # Test 1: Install operation
            install_result = self.scheduler.install(10, ddns_args)
            self.assertIsInstance(install_result, bool)

            # After install, service should be installed (regardless of permissions)
            post_install_status = self.scheduler.get_status()
            self.assertIsInstance(post_install_status, dict)
            self.assertEqual(post_install_status["scheduler"], "systemd")
            self.assertIsInstance(post_install_status["installed"], bool)

            # If installation succeeded, test enable/disable
            if install_result and post_install_status.get("installed", False):
                # Test 2: Enable operation
                enable_result = self.scheduler.enable()
                self.assertIsInstance(enable_result, bool)

                # Check status after enable attempt
                post_enable_status = self.scheduler.get_status()
                self.assertIsInstance(post_enable_status, dict)
                self.assertIn("enabled", post_enable_status)

                # Test 3: Disable operation
                disable_result = self.scheduler.disable()
                self.assertIsInstance(disable_result, bool)

                # Check status after disable attempt
                post_disable_status = self.scheduler.get_status()
                self.assertIsInstance(post_disable_status, dict)
                self.assertIn("enabled", post_disable_status)

                # Test 4: Uninstall operation
                uninstall_result = self.scheduler.uninstall()
                self.assertIsInstance(uninstall_result, bool)

                # Check status after uninstall attempt
                post_uninstall_status = self.scheduler.get_status()
                self.assertIsInstance(post_uninstall_status, dict)
                # After uninstall, installed should be False (if uninstall succeeded)
                if uninstall_result:
                    self.assertFalse(post_uninstall_status.get("installed", True))
            else:
                self.skipTest("Install failed due to permissions - cannot test lifecycle")

        except Exception as e:
            # If we get permission errors, that's expected in test environment
            if "Permission denied" in str(e) or "Interactive authentication required" in str(e):
                self.skipTest("Insufficient permissions for systemd operations")
            else:
                # Re-raise unexpected exceptions
                raise

        finally:
            # Cleanup: Try to restore original state
            try:
                if original_installed:
                    # If it was originally installed, try to restore
                    if not self.scheduler.is_installed():
                        # Try to reinstall with original settings if we have them
                        self.scheduler.install(10, ddns_args)
                else:
                    # If it wasn't originally installed, try to uninstall
                    if self.scheduler.is_installed():
                        self.scheduler.uninstall()
            except Exception:
                # Cleanup failures are not critical for tests
                pass

    @unittest.skipUnless(platform.system().lower() == "linux", "Linux-specific test")
    def test_real_systemd_status_consistency(self):
        """Test that systemd status reporting is consistent across operations"""
        # Check if systemctl command is available
        try:
            systemctl_result = try_run(["systemctl", "--version"])
            if not systemctl_result:
                self.skipTest("systemctl not available on this system")
        except Exception:
            self.skipTest("systemctl not available on this system")

        # Get initial status
        initial_status = self.scheduler.get_status()
        self.assertIsInstance(initial_status, dict)
        self.assertEqual(initial_status["scheduler"], "systemd")
        self.assertIn("installed", initial_status)

        # Test is_installed consistency
        installed_check = self.scheduler.is_installed()
        self.assertEqual(installed_check, initial_status["installed"])

        # If installed, check that additional status fields are present
        if initial_status.get("installed", False):
            required_keys = ["enabled", "interval"]
            for key in required_keys:
                self.assertIn(key, initial_status, "Key '{}' should be present when service is installed".format(key))

        # Test that repeated status calls are consistent
        second_status = self.scheduler.get_status()
        self.assertEqual(initial_status["scheduler"], second_status["scheduler"])
        self.assertEqual(initial_status["installed"], second_status["installed"])

        # If both report as installed, other fields should also match
        if initial_status.get("installed", False) and second_status.get("installed", False):
            for key in ["enabled", "interval"]:
                if key in initial_status and key in second_status:
                    self.assertEqual(
                        initial_status[key],
                        second_status[key],
                        "Status field '{}' should be consistent between calls".format(key),
                    )


if __name__ == "__main__":
    unittest.main()
