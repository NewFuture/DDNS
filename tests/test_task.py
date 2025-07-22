# -*- coding:utf-8 -*-
"""
Tests for ddns.util.task module
"""
from __init__ import unittest, patch, MagicMock
import tempfile
import os
import sys
import subprocess

from ddns.util.task import TaskManager


class TestTaskManager(unittest.TestCase):
    """Test TaskManager functionality"""

    def setUp(self):
        """Set up test cases"""
        self.task_manager = TaskManager(
            config_path="test_config.json",
            log_path="test_ddns.log",
            interval=10
        )

    def test_init(self):
        """Test TaskManager initialization"""
        self.assertEqual(self.task_manager.config_path, "test_config.json")
        self.assertEqual(self.task_manager.log_path, "test_ddns.log")
        self.assertEqual(self.task_manager.interval, 10)
        self.assertEqual(self.task_manager.task_name, "DDNS")

    @patch('ddns.util.task.platform.system')
    def test_get_scheduler_type_linux_with_systemd(self, mock_system):
        """Test scheduler type detection on Linux with systemd"""
        mock_system.return_value = "Linux"
        with patch('ddns.util.task.subprocess.check_call') as mock_check_call:
            mock_check_call.return_value = None
            result = self.task_manager.get_scheduler_type()
            self.assertEqual(result, "systemd")
            mock_check_call.assert_called_once_with(
                ["systemctl", "--version"],
                stdout=unittest.mock.ANY,
                stderr=unittest.mock.ANY
            )

    @patch('ddns.util.task.platform.system')
    def test_get_scheduler_type_linux_without_systemd(self, mock_system):
        """Test scheduler type detection on Linux without systemd"""
        mock_system.return_value = "Linux"
        with patch('ddns.util.task.subprocess.check_call') as mock_check_call:
            mock_check_call.side_effect = OSError("systemctl not found")
            result = self.task_manager.get_scheduler_type()
            self.assertEqual(result, "cron")

    @patch('ddns.util.task.platform.system')
    def test_get_scheduler_type_darwin_with_launchd(self, mock_system):
        """Test scheduler type detection on macOS with launchd"""
        mock_system.return_value = "Darwin"
        with patch('ddns.util.task.subprocess.check_call') as mock_check_call:
            mock_check_call.return_value = None
            result = self.task_manager.get_scheduler_type()
            self.assertEqual(result, "launchd")

    @patch('ddns.util.task.platform.system')
    def test_get_scheduler_type_darwin_without_launchd(self, mock_system):
        """Test scheduler type detection on macOS without launchd"""
        mock_system.return_value = "Darwin"
        with patch('ddns.util.task.subprocess.check_call') as mock_check_call:
            mock_check_call.side_effect = OSError("launchctl not found")
            result = self.task_manager.get_scheduler_type()
            self.assertEqual(result, "cron")

    @patch('ddns.util.task.platform.system')
    def test_get_scheduler_type_windows(self, mock_system):
        """Test scheduler type detection on Windows"""
        mock_system.return_value = "Windows"
        result = self.task_manager.get_scheduler_type()
        self.assertEqual(result, "schtasks")

    @patch('ddns.util.task.platform.system')
    def test_get_scheduler_type_unknown(self, mock_system):
        """Test scheduler type detection on unknown system"""
        mock_system.return_value = "Unknown"
        result = self.task_manager.get_scheduler_type()
        self.assertEqual(result, "cron")

    @patch.object(TaskManager, 'get_scheduler_type')
    def test_is_installed_systemd_enabled(self, mock_get_scheduler):
        """Test is_installed for systemd when timer is enabled"""
        mock_get_scheduler.return_value = "systemd"
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.return_value = b"enabled\n"
            result = self.task_manager.is_installed()
            self.assertTrue(result)

    @patch.object(TaskManager, 'get_scheduler_type')
    def test_is_installed_systemd_disabled(self, mock_get_scheduler):
        """Test is_installed for systemd when timer is disabled"""
        mock_get_scheduler.return_value = "systemd"
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.return_value = b"disabled\n"
            result = self.task_manager.is_installed()
            self.assertFalse(result)

    @patch.object(TaskManager, 'get_scheduler_type')
    def test_is_installed_cron_with_ddns_job(self, mock_get_scheduler):
        """Test is_installed for cron when DDNS job exists"""
        mock_get_scheduler.return_value = "cron"
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.return_value = b"*/5 * * * * /usr/bin/ddns\n"
            result = self.task_manager.is_installed()
            self.assertTrue(result)

    @patch.object(TaskManager, 'get_scheduler_type')
    def test_is_installed_cron_without_ddns_job(self, mock_get_scheduler):
        """Test is_installed for cron when no DDNS job exists"""
        mock_get_scheduler.return_value = "cron"
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.return_value = b"*/5 * * * * /usr/bin/other\n"
            result = self.task_manager.is_installed()
            self.assertFalse(result)

    @patch.object(TaskManager, 'get_scheduler_type')
    def test_is_installed_launchd_with_plist(self, mock_get_scheduler):
        """Test is_installed for launchd when plist exists"""
        mock_get_scheduler.return_value = "launchd"
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            result = self.task_manager.is_installed()
            self.assertTrue(result)

    @patch.object(TaskManager, 'get_scheduler_type')
    def test_is_installed_launchd_without_plist(self, mock_get_scheduler):
        """Test is_installed for launchd when plist doesn't exist"""
        mock_get_scheduler.return_value = "launchd"
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            result = self.task_manager.is_installed()
            self.assertFalse(result)

    @patch.object(TaskManager, 'get_scheduler_type')
    def test_is_installed_schtasks_with_task(self, mock_get_scheduler):
        """Test is_installed for schtasks when task exists"""
        mock_get_scheduler.return_value = "schtasks"
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.return_value = b"DDNS task found\n"
            result = self.task_manager.is_installed()
            self.assertTrue(result)

    @patch.object(TaskManager, 'get_scheduler_type')
    def test_is_installed_schtasks_without_task(self, mock_get_scheduler):
        """Test is_installed for schtasks when task doesn't exist"""
        mock_get_scheduler.return_value = "schtasks"
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "schtasks")
            result = self.task_manager.is_installed()
            self.assertFalse(result)

    @patch.object(TaskManager, 'get_scheduler_type')
    @patch.object(TaskManager, 'is_installed')
    @patch('ddns.util.task.platform.system')
    def test_get_status_not_installed(self, mock_system, mock_is_installed, mock_get_scheduler):
        """Test get_status when task is not installed"""
        mock_system.return_value = "Linux"
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = False
        
        status = self.task_manager.get_status()
        
        expected_status = {
            "installed": False,
            "scheduler": "cron",
            "system": "linux",
            "interval": 10,
            "config_path": "test_config.json",
            "log_path": "test_ddns.log",
        }
        self.assertEqual(status, expected_status)

    @patch.object(TaskManager, 'get_scheduler_type')
    @patch.object(TaskManager, 'is_installed')
    @patch.object(TaskManager, '_get_running_status')
    @patch('ddns.util.task.platform.system')
    def test_get_status_installed(self, mock_system, mock_get_running_status, mock_is_installed, mock_get_scheduler):
        """Test get_status when task is installed"""
        mock_system.return_value = "Linux"
        mock_get_scheduler.return_value = "systemd"
        mock_is_installed.return_value = True
        mock_get_running_status.return_value = "active"
        
        status = self.task_manager.get_status()
        
        expected_status = {
            "installed": True,
            "scheduler": "systemd",
            "system": "linux",
            "interval": 10,
            "config_path": "test_config.json",
            "log_path": "test_ddns.log",
            "running_status": "active",
        }
        self.assertEqual(status, expected_status)

    def test_get_running_status_systemd_active(self):
        """Test _get_running_status for systemd when active"""
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.return_value = b"active\n"
            result = self.task_manager._get_running_status("systemd")
            self.assertEqual(result, "active")

    def test_get_running_status_systemd_inactive(self):
        """Test _get_running_status for systemd when inactive"""
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "systemctl")
            result = self.task_manager._get_running_status("systemd")
            self.assertEqual(result, "inactive")

    def test_get_running_status_cron_active(self):
        """Test _get_running_status for cron when active"""
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.return_value = b"12345\n"
            result = self.task_manager._get_running_status("cron")
            self.assertEqual(result, "active")

    def test_get_running_status_cron_inactive(self):
        """Test _get_running_status for cron when inactive"""
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "pgrep")
            result = self.task_manager._get_running_status("cron")
            self.assertEqual(result, "inactive")

    @patch.object(TaskManager, 'get_scheduler_type')
    @patch.object(TaskManager, 'is_installed')
    @patch.object(TaskManager, '_install_cron')
    def test_install_success(self, mock_install_cron, mock_is_installed, mock_get_scheduler):
        """Test successful installation"""
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = False
        mock_install_cron.return_value = True
        
        result = self.task_manager.install()
        
        self.assertTrue(result)
        mock_install_cron.assert_called_once()

    @patch.object(TaskManager, 'get_scheduler_type')
    @patch.object(TaskManager, 'is_installed')
    def test_install_already_installed_without_force(self, mock_is_installed, mock_get_scheduler):
        """Test installation when already installed without force"""
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = True
        
        result = self.task_manager.install(force=False)
        
        self.assertTrue(result)

    @patch.object(TaskManager, 'get_scheduler_type')
    @patch.object(TaskManager, 'is_installed')
    @patch.object(TaskManager, '_install_cron')
    def test_install_already_installed_with_force(self, mock_install_cron, mock_is_installed, mock_get_scheduler):
        """Test installation when already installed with force"""
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = True
        mock_install_cron.return_value = True
        
        result = self.task_manager.install(force=True)
        
        self.assertTrue(result)
        mock_install_cron.assert_called_once()

    @patch.object(TaskManager, 'get_scheduler_type')
    @patch.object(TaskManager, 'is_installed')
    @patch.object(TaskManager, '_uninstall_cron')
    def test_uninstall_success(self, mock_uninstall_cron, mock_is_installed, mock_get_scheduler):
        """Test successful uninstallation"""
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = True
        mock_uninstall_cron.return_value = True
        
        result = self.task_manager.uninstall()
        
        self.assertTrue(result)
        mock_uninstall_cron.assert_called_once()

    @patch.object(TaskManager, 'get_scheduler_type')
    @patch.object(TaskManager, 'is_installed')
    def test_uninstall_not_installed(self, mock_is_installed, mock_get_scheduler):
        """Test uninstallation when not installed"""
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = False
        
        result = self.task_manager.uninstall()
        
        self.assertTrue(result)

    def test_install_cron_new_crontab(self):
        """Test _install_cron with new crontab"""
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "crontab")
            
            with patch('subprocess.check_call') as mock_check_call:
                with patch('tempfile.NamedTemporaryFile') as mock_temp:
                    mock_temp.return_value.__enter__.return_value.name = "/tmp/test_cron"
                    with patch('os.unlink'):
                        
                        result = self.task_manager._install_cron()
                        
                        self.assertTrue(result)
                        mock_check_call.assert_called_once_with(["crontab", "/tmp/test_cron"])

    def test_install_cron_existing_crontab(self):
        """Test _install_cron with existing crontab"""
        existing_cron = "0 0 * * * /usr/bin/backup\n"
        
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.return_value = existing_cron.encode()
            
            with patch('subprocess.check_call') as mock_check_call:
                with patch('tempfile.NamedTemporaryFile') as mock_temp:
                    mock_temp.return_value.__enter__.return_value.name = "/tmp/test_cron"
                    with patch('os.unlink'):
                        
                        result = self.task_manager._install_cron()
                        
                        self.assertTrue(result)
                        mock_check_call.assert_called_once_with(["crontab", "/tmp/test_cron"])

    def test_uninstall_cron_with_existing_crontab(self):
        """Test _uninstall_cron with existing crontab containing DDNS"""
        existing_cron = "0 0 * * * /usr/bin/backup\n*/5 * * * * ddns\n"
        
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.return_value = existing_cron.encode()
            
            with patch('subprocess.check_call') as mock_check_call:
                with patch('tempfile.NamedTemporaryFile') as mock_temp:
                    mock_temp.return_value.__enter__.return_value.name = "/tmp/test_cron"
                    with patch('os.unlink'):
                        
                        result = self.task_manager._uninstall_cron()
                        
                        self.assertTrue(result)
                        mock_check_call.assert_called_once_with(["crontab", "/tmp/test_cron"])

    def test_uninstall_cron_no_existing_crontab(self):
        """Test _uninstall_cron with no existing crontab"""
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "crontab")
            
            result = self.task_manager._uninstall_cron()
            
            self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()