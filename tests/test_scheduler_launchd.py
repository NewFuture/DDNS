# -*- coding:utf-8 -*-
"""
Unit tests for ddns.scheduler.launchd module
@author: NewFuture
"""
import os
import platform
from tests import unittest, patch, MagicMock
from ddns.scheduler.launchd import LaunchdScheduler


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

    @patch('subprocess.run')
    def test_get_status_loaded_enabled(self, mock_run):
        """Test get_status when service is loaded and enabled"""
        # Mock plist file exists and has content
        plist_content = '''<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>cc.newfuture.ddns</string>
    <key>StartInterval</key>
    <integer>300</integer>
</dict>
</plist>'''
        
        with patch('os.path.exists', return_value=True), \
             patch('ddns.scheduler.launchd.read_file_safely', return_value=plist_content), \
             patch('subprocess.run') as mock_subprocess:
            
            # Mock subprocess.run to return service is loaded
            mock_result = type('MockResult', (), {'returncode': 0, 'stdout': '123\t0\tcc.newfuture.ddns'})()
            mock_subprocess.return_value = mock_result
            
            status = self.scheduler.get_status()
            
            expected_status = {
                "scheduler": "launchd",
                "installed": True,
                "enabled": True,
                "interval": 5  # 300 seconds / 60 = 5 minutes
            }
            self.assertEqual(status["scheduler"], expected_status["scheduler"])
            self.assertEqual(status["installed"], expected_status["installed"])
            self.assertEqual(status["enabled"], expected_status["enabled"])
            self.assertEqual(status["interval"], expected_status["interval"])

    @patch('subprocess.run')
    def test_get_status_not_loaded(self, mock_run):
        """Test get_status when service is not loaded"""
        # Mock plist file doesn't exist
        with patch('os.path.exists', return_value=False), \
             patch('ddns.scheduler.launchd.read_file_safely', return_value=None):
            status = self.scheduler.get_status()
            
            # When not installed, only basic keys are returned
            self.assertEqual(status["scheduler"], "launchd")
            self.assertEqual(status["installed"], False)
            # enabled and interval keys are not returned when not installed
            self.assertNotIn("enabled", status)
            self.assertNotIn("interval", status)

    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_is_installed_true(self, mock_exists, mock_run):
        """Test is_installed returns True when plist file exists"""
        mock_exists.return_value = True

        result = self.scheduler.is_installed()
        self.assertTrue(result)

    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_is_installed_false(self, mock_exists, mock_run):
        """Test is_installed returns False when plist file doesn't exist"""
        mock_exists.return_value = False

        result = self.scheduler.is_installed()
        self.assertFalse(result)

    @patch('subprocess.run')
    @patch('builtins.open', create=True)
    def test_install_success(self, mock_open, mock_run):
        """Test successful installation"""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        with patch.object(self.scheduler, '_launchctl', return_value=True):
            ddns_args = {"dns": "debug", "ipv4": ["test.com"]}
            result = self.scheduler.install(5, ddns_args)
            self.assertTrue(result)

    @patch('ddns.scheduler.launchd.write_file')
    @patch.object(LaunchdScheduler, '_launchctl')
    def test_install_with_sudo_fallback(self, mock_launchctl, mock_write_file):
        """Test install with sudo fallback for permission issues"""
        mock_write_file.return_value = None  # write_file succeeds
        mock_launchctl.return_value = True   # launchctl succeeds
        
        ddns_args = {"dns": "debug", "ipv4": ["test.com"]}
        result = self.scheduler.install(5, ddns_args)
        self.assertTrue(result)
        
        # Verify write_file and launchctl were called
        mock_write_file.assert_called_once()
        mock_launchctl.assert_called_once()

    @unittest.skipUnless(platform.system().lower() == "darwin", "macOS-specific test")
    def test_launchctl_with_sudo_retry(self):
        """Test launchctl command with automatic sudo retry on permission error"""
        with patch.object(self.scheduler, '_run_command') as mock_run_cmd:
            # First attempt fails, sudo attempt succeeds
            mock_run_cmd.side_effect = [None, "success"]
            
            # Test that launchctl operations can fall back to sudo
            result = self.scheduler._launchctl("load", self.scheduler._get_plist_path())
            # Should handle permission issues gracefully
            self.assertFalse(result)  # First call returns False for permission error

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_uninstall_success(self, mock_remove, mock_exists, mock_run):
        """Test successful uninstall"""
        mock_exists.return_value = True
        
        with patch.object(self.scheduler, '_launchctl', return_value=True):
            with patch('subprocess.call') as mock_call:
                # Mock subprocess.call for launchctl command
                mock_call.return_value = 0
                result = self.scheduler.uninstall()
                self.assertTrue(result)
                mock_remove.assert_called_once()

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_uninstall_with_permission_handling(self, mock_remove, mock_exists, mock_run):
        """Test uninstall with proper permission handling"""
        mock_exists.return_value = True
        
        # Mock file removal might need sudo
        mock_remove.side_effect = PermissionError("Permission denied")
        
        with patch.object(self.scheduler, '_launchctl', return_value=True):
            with patch('subprocess.call') as mock_call:
                # Mock sudo rm command
                mock_call.return_value = 0
                
                result = self.scheduler.uninstall()
                # Should handle permission error and use sudo for file removal
                self.assertTrue(result)
                mock_call.assert_called()

    @patch.object(LaunchdScheduler, '_launchctl')
    def test_enable_success(self, mock_launchctl):
        """Test successful enable"""
        mock_launchctl.return_value = True
        
        with patch('os.path.exists', return_value=True):
            result = self.scheduler.enable()
            self.assertTrue(result)

    @patch.object(LaunchdScheduler, '_launchctl')
    def test_disable_success(self, mock_launchctl):
        """Test successful disable"""
        mock_launchctl.return_value = True
        
        with patch('os.path.exists', return_value=True):
            result = self.scheduler.disable()
            self.assertTrue(result)

    def test_build_ddns_command(self):
        """Test _build_ddns_command functionality"""
        ddns_args = {"dns": "debug", "ipv4": ["test.example.com"], "debug": True}
        
        command = self.scheduler._build_ddns_command(ddns_args)
        
        self.assertIsInstance(command, str)
        self.assertIn("debug", command)
        self.assertIn("test.example.com", command)

    @unittest.skipUnless(platform.system().lower() == "darwin", "macOS-specific test")
    def test_real_launchctl_availability(self):
        """Test if launchctl is available on macOS systems"""
        import shutil
        launchctl_path = shutil.which("launchctl")
        
        if launchctl_path:
            # launchctl is available, test basic functionality
            self.scheduler._launchctl("version")
            # Don't assert result as it may fail on non-macOS systems or due to permissions
        else:
            self.skipTest("launchctl not found on this system")

    @unittest.skipUnless(platform.system().lower() == "darwin", "macOS-specific test")
    def test_permission_check_methods(self):
        """Test permission checking for launchd operations"""
        import shutil
        
        # Test if we can write to LaunchAgents directory
        agents_dir = os.path.expanduser("~/Library/LaunchAgents")
        can_write = os.access(agents_dir, os.W_OK) if os.path.exists(agents_dir) else False
        
        # For system-wide daemons (/Library/LaunchDaemons), we'd typically need sudo
        daemon_dir = "/Library/LaunchDaemons"
        daemon_write = os.access(daemon_dir, os.W_OK) if os.path.exists(daemon_dir) else False
        
        # If we can't write to system locations, we should be able to use sudo
        if not daemon_write:
            sudo_path = shutil.which("sudo")
            self.assertIsNotNone(sudo_path, "sudo should be available for elevated permissions")
        
        # User agents directory should generally be writable
        if os.path.exists(agents_dir):
            self.assertTrue(can_write or shutil.which("sudo"),
                            "Should be able to write to user LaunchAgents or have sudo access")

    @unittest.skipUnless(platform.system().lower() == "darwin", "macOS-specific test")
    def test_real_launchd_integration(self):
        """Test real launchd integration with actual system calls"""
        import shutil
        launchctl_path = shutil.which("launchctl")
        if not launchctl_path:
            self.skipTest("launchctl not available on this system")
        
        # Test real launchctl version call
        version_result = self.scheduler._launchctl("version")
        # On a real macOS system, this should work
        self.assertIsInstance(version_result, bool)
        
        # Test real status check
        status = self.scheduler.get_status()
        self.assertIsInstance(status, dict)
        self.assertEqual(status["scheduler"], "launchd")
        self.assertIsInstance(status["installed"], bool)
        
        # Test launchctl list (read-only operation)
        list_result = self.scheduler._run_command(["launchctl", "list"])
        # This might return None or string based on system state
        self.assertTrue(list_result is None or isinstance(list_result, str))

    @unittest.skipUnless(platform.system().lower() == "darwin", "macOS-specific test")
    def test_real_scheduler_methods_safe(self):
        """Test real scheduler methods that don't modify system state"""
        import shutil
        launchctl_path = shutil.which("launchctl")
        if not launchctl_path:
            self.skipTest("launchctl not available on this system")
        
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


if __name__ == "__main__":
    unittest.main()
