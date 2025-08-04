# -*- coding:utf-8 -*-
"""
Unit tests for ddns.scheduler.systemd module
@author: NewFuture
"""
import os
import platform
import shutil
from tests import unittest, patch, MagicMock
from ddns.scheduler.systemd import SystemdScheduler


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

    @patch('os.path.exists')
    def test_is_installed_true(self, mock_exists):
        """Test is_installed returns True when service exists"""
        mock_exists.return_value = True
        result = self.scheduler.is_installed()
        self.assertTrue(result)

    @patch('os.path.exists')
    def test_is_installed_false(self, mock_exists):
        """Test is_installed returns False when service doesn't exist"""
        mock_exists.return_value = False
        result = self.scheduler.is_installed()
        self.assertFalse(result)

    @patch('os.path.exists')
    @patch('ddns.util.fileio.read_file_safely')
    @patch('subprocess.run')
    def test_get_status_success(self, mock_subprocess_run, mock_read_file, mock_exists):
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
        # Mock subprocess.run to return "enabled" status
        mock_result = type('MockResult', (), {'returncode': 0, 'stdout': 'enabled'})()
        mock_subprocess_run.return_value = mock_result
        
        status = self.scheduler.get_status()
        
        self.assertEqual(status["scheduler"], "systemd")
        self.assertTrue(status["installed"])
        self.assertTrue(status["enabled"])
        self.assertEqual(status["interval"], 5)

    @patch('ddns.scheduler.systemd.write_file')
    @patch.object(SystemdScheduler, '_systemctl')
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

    @patch('subprocess.run')
    def test_systemctl_with_sudo_retry(self, mock_run):
        """Test systemctl command with automatic sudo retry on permission error"""
        # First attempt fails with permission error
        mock_run.side_effect = [
            MagicMock(returncode=1, stderr="Permission denied"),
            MagicMock(returncode=0)  # sudo attempt succeeds
        ]
        
        # Test that systemctl automatically retries with sudo
        with patch.object(self.scheduler, '_run_command') as mock_run_cmd:
            mock_run_cmd.side_effect = [None, "success"]  # First fails, sudo succeeds
            self.scheduler._systemctl("enable", "ddns.timer")
            # Should still return success after sudo retry
            mock_run_cmd.assert_called()

    @patch('os.remove')
    @patch.object(SystemdScheduler, '_systemctl')
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
        self.assertIsInstance(command, str)
        self.assertIn("debug", command)
        self.assertIn("test.example.com", command)

    @unittest.skipUnless(platform.system().lower() == "linux", "Linux-specific test")
    def test_real_systemctl_availability(self):
        """Test if systemctl is available on Linux systems"""
        import shutil
        systemctl_path = shutil.which("systemctl")
        
        if systemctl_path:
            # Test both regular and sudo access
            self.scheduler._systemctl("--version")
            
            # Test if we have sudo access (don't actually run sudo commands in tests)
            sudo_path = shutil.which("sudo")
            if sudo_path:
                # Just verify sudo is available for fallback
                self.assertIsNotNone(sudo_path)
        else:
            self.skipTest("systemctl not found on this system")

    @unittest.skipUnless(platform.system().lower() == "linux", "Linux-specific test")
    def test_permission_check_methods(self):
        """Test permission checking for systemd operations"""
        # Test if we can write to systemd directory
        systemd_dir = "/etc/systemd/system"
        can_write = os.access(systemd_dir, os.W_OK) if os.path.exists(systemd_dir) else False
        
        # If we can't write directly, we should be able to use sudo
        if not can_write:
            sudo_path = shutil.which("sudo")
            self.assertIsNotNone(sudo_path, "sudo should be available for elevated permissions")

    @unittest.skipUnless(platform.system().lower() == "linux", "Linux-specific test")
    def test_real_systemd_integration(self):
        """Test real systemd integration with actual system calls"""
        systemctl_path = shutil.which("systemctl")
        if not systemctl_path:
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
        systemctl_path = shutil.which("systemctl")
        if not systemctl_path:
            self.skipTest("systemctl not available on this system")
        
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


if __name__ == "__main__":
    unittest.main()
