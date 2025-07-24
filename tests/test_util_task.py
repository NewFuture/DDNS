# -*- coding:utf-8 -*-
"""
Tests for ddns.util.task module
"""
from __init__ import unittest, patch, MagicMock
import tempfile
import os
import sys
import subprocess

import ddns.util.task as task


class TestTaskFunctions(unittest.TestCase):
    """Test task module functions"""

    @patch("ddns.util.task.platform.system")
    def test_get_scheduler_type_linux_with_systemd(self, mock_system):
        """Test scheduler type detection on Linux with systemd"""
        mock_system.return_value = "Linux"
        with patch("ddns.util.task.subprocess.check_call") as mock_check_call:
            mock_check_call.return_value = None
            result = task.get_scheduler_type()
            self.assertEqual(result, "systemd")
            mock_check_call.assert_called_once_with(
                ["systemctl", "--version"], stdout=unittest.mock.ANY, stderr=unittest.mock.ANY
            )

    @patch("ddns.util.task.platform.system")
    def test_get_scheduler_type_linux_without_systemd(self, mock_system):
        """Test scheduler type detection on Linux without systemd"""
        mock_system.return_value = "Linux"
        with patch("ddns.util.task.subprocess.check_call") as mock_check_call:
            mock_check_call.side_effect = OSError("systemctl not found")
            result = task.get_scheduler_type()
            self.assertEqual(result, "cron")

    @patch("ddns.util.task.platform.system")
    def test_get_scheduler_type_darwin_with_launchd(self, mock_system):
        """Test scheduler type detection on macOS with launchd"""
        mock_system.return_value = "Darwin"
        with patch("ddns.util.task.subprocess.check_call") as mock_check_call:
            mock_check_call.return_value = None
            result = task.get_scheduler_type()
            self.assertEqual(result, "launchd")

    @patch("ddns.util.task.platform.system")
    def test_get_scheduler_type_darwin_without_launchd(self, mock_system):
        """Test scheduler type detection on macOS without launchd"""
        mock_system.return_value = "Darwin"
        with patch("ddns.util.task.subprocess.check_call") as mock_check_call:
            mock_check_call.side_effect = OSError("launchctl not found")
            result = task.get_scheduler_type()
            self.assertEqual(result, "cron")

    @patch("ddns.util.task.platform.system")
    def test_get_scheduler_type_windows(self, mock_system):
        """Test scheduler type detection on Windows"""
        mock_system.return_value = "Windows"
        result = task.get_scheduler_type()
        self.assertEqual(result, "schtasks")

    @patch("ddns.util.task.platform.system")
    def test_get_scheduler_type_unknown(self, mock_system):
        """Test scheduler type detection on unknown system"""
        mock_system.return_value = "Unknown"
        result = task.get_scheduler_type()
        self.assertEqual(result, "cron")

    @patch("ddns.util.task.get_scheduler_type")
    def test_is_installed_systemd_enabled(self, mock_get_scheduler):
        """Test is_installed for systemd when timer is enabled"""
        mock_get_scheduler.return_value = "systemd"
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = b"enabled\n"
            result = task.is_installed()
            self.assertTrue(result)

    @patch("ddns.util.task.get_scheduler_type")
    def test_is_installed_systemd_disabled(self, mock_get_scheduler):
        """Test is_installed for systemd when timer is disabled"""
        mock_get_scheduler.return_value = "systemd"
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = b"disabled\n"
            result = task.is_installed()
            self.assertFalse(result)

    @patch("ddns.util.task.get_scheduler_type")
    def test_is_installed_cron_with_ddns_job(self, mock_get_scheduler):
        """Test is_installed for cron when DDNS job exists"""
        mock_get_scheduler.return_value = "cron"
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = b"*/5 * * * * /usr/bin/ddns\n"
            result = task.is_installed()
            self.assertTrue(result)

    @patch("ddns.util.task.get_scheduler_type")
    def test_is_installed_cron_without_ddns_job(self, mock_get_scheduler):
        """Test is_installed for cron when no DDNS job exists"""
        mock_get_scheduler.return_value = "cron"
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = b"*/5 * * * * /usr/bin/other\n"
            result = task.is_installed()
            self.assertFalse(result)

    @patch("ddns.util.task.get_scheduler_type")
    def test_is_installed_launchd_with_plist(self, mock_get_scheduler):
        """Test is_installed for launchd when plist exists"""
        mock_get_scheduler.return_value = "launchd"
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = task.is_installed()
            self.assertTrue(result)

    @patch("ddns.util.task.get_scheduler_type")
    def test_is_installed_launchd_without_plist(self, mock_get_scheduler):
        """Test is_installed for launchd when plist doesn't exist"""
        mock_get_scheduler.return_value = "launchd"
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            result = task.is_installed()
            self.assertFalse(result)

    @patch("ddns.util.task.get_scheduler_type")
    def test_is_installed_schtasks_with_task(self, mock_get_scheduler):
        """Test is_installed for schtasks when task exists"""
        mock_get_scheduler.return_value = "schtasks"
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = b"DDNS task found\n"
            result = task.is_installed()
            self.assertTrue(result)

    @patch("ddns.util.task.get_scheduler_type")
    def test_is_installed_schtasks_without_task(self, mock_get_scheduler):
        """Test is_installed for schtasks when task doesn't exist"""
        mock_get_scheduler.return_value = "schtasks"
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "schtasks")
            result = task.is_installed()
            self.assertFalse(result)

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task.is_installed")
    @patch("ddns.util.task.platform.system")
    def test_get_status_not_installed(self, mock_system, mock_is_installed, mock_get_scheduler):
        """Test get_status when task is not installed"""
        mock_system.return_value = "Linux"
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = False

        status = task.get_status(config_path="test_config.json", log_path="test_ddns.log", interval=10)

        expected_status = {
            "installed": False,
            "scheduler": "cron",
            "system": "linux",
            "interval": 10,
            "config_path": "test_config.json",
            "log_path": "test_ddns.log",
        }
        self.assertEqual(status, expected_status)

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task.is_installed")
    @patch("ddns.util.task._get_running_status")
    @patch("ddns.util.task.platform.system")
    def test_get_status_installed(self, mock_system, mock_get_running_status, mock_is_installed, mock_get_scheduler):
        """Test get_status when task is installed"""
        mock_system.return_value = "Linux"
        mock_get_scheduler.return_value = "systemd"
        mock_is_installed.return_value = True
        mock_get_running_status.return_value = "active"

        status = task.get_status(config_path="test_config.json", log_path="test_ddns.log", interval=10)

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
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = b"active\n"
            result = task._get_running_status("systemd")
            self.assertEqual(result, "active")

    def test_get_running_status_systemd_inactive(self):
        """Test _get_running_status for systemd when inactive"""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "systemctl")
            result = task._get_running_status("systemd")
            self.assertEqual(result, "inactive")

    def test_get_running_status_cron_active(self):
        """Test _get_running_status for cron when active"""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = b"12345\n"
            result = task._get_running_status("cron")
            self.assertEqual(result, "active")

    def test_get_running_status_cron_inactive(self):
        """Test _get_running_status for cron when inactive"""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "pgrep")
            result = task._get_running_status("cron")
            self.assertEqual(result, "inactive")

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task.is_installed")
    @patch("ddns.util.task._install_cron")
    def test_install_success(self, mock_install_cron, mock_is_installed, mock_get_scheduler):
        """Test successful installation"""
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = False
        mock_install_cron.return_value = True

        result = task.install(config_path="test_config.json", log_path="test_ddns.log", interval=10)

        self.assertTrue(result)
        mock_install_cron.assert_called_once()

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task.is_installed")
    def test_install_already_installed_without_force(self, mock_is_installed, mock_get_scheduler):
        """Test installation when already installed without force"""
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = True

        result = task.install(config_path="test_config.json", log_path="test_ddns.log", interval=10, force=False)

        self.assertTrue(result)

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task.is_installed")
    @patch("ddns.util.task._install_cron")
    def test_install_already_installed_with_force(self, mock_install_cron, mock_is_installed, mock_get_scheduler):
        """Test installation when already installed with force"""
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = True
        mock_install_cron.return_value = True

        result = task.install(config_path="test_config.json", log_path="test_ddns.log", interval=10, force=True)

        self.assertTrue(result)
        mock_install_cron.assert_called_once()

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task.is_installed")
    @patch("ddns.util.task._uninstall_cron")
    def test_uninstall_success(self, mock_uninstall_cron, mock_is_installed, mock_get_scheduler):
        """Test successful uninstallation"""
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = True
        mock_uninstall_cron.return_value = True

        result = task.uninstall()

        self.assertTrue(result)
        mock_uninstall_cron.assert_called_once()

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task.is_installed")
    def test_uninstall_not_installed(self, mock_is_installed, mock_get_scheduler):
        """Test uninstallation when not installed"""
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = False

        result = task.uninstall()

        self.assertTrue(result)

    def test_install_cron_new_crontab(self):
        """Test _install_cron with new crontab"""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "crontab")

            with patch("subprocess.check_call") as mock_check_call:
                with patch("tempfile.NamedTemporaryFile") as mock_temp:
                    mock_temp.return_value.__enter__.return_value.name = "/tmp/test_cron"
                    with patch("os.unlink"):

                        result = task._install_cron("test_config.json", "test_ddns.log", 10)

                        self.assertTrue(result)
                        mock_check_call.assert_called_once_with(["crontab", "/tmp/test_cron"])

    def test_install_cron_existing_crontab(self):
        """Test _install_cron with existing crontab"""
        existing_cron = "0 0 * * * /usr/bin/backup\n"

        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = existing_cron.encode()

            with patch("subprocess.check_call") as mock_check_call:
                with patch("tempfile.NamedTemporaryFile") as mock_temp:
                    mock_temp.return_value.__enter__.return_value.name = "/tmp/test_cron"
                    with patch("os.unlink"):

                        result = task._install_cron("test_config.json", "test_ddns.log", 10)

                        self.assertTrue(result)
                        mock_check_call.assert_called_once_with(["crontab", "/tmp/test_cron"])

    def test_uninstall_cron_with_existing_crontab(self):
        """Test _uninstall_cron with existing crontab containing DDNS"""
        existing_cron = "0 0 * * * /usr/bin/backup\n*/5 * * * * ddns\n"

        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = existing_cron.encode()

            with patch("subprocess.check_call") as mock_check_call:
                with patch("tempfile.NamedTemporaryFile") as mock_temp:
                    mock_temp.return_value.__enter__.return_value.name = "/tmp/test_cron"
                    with patch("os.unlink"):

                        result = task._uninstall_cron()

                        self.assertTrue(result)
                        mock_check_call.assert_called_once_with(["crontab", "/tmp/test_cron"])

    def test_uninstall_cron_no_existing_crontab(self):
        """Test _uninstall_cron with no existing crontab"""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "crontab")

            result = task._uninstall_cron()

            self.assertTrue(result)


class TestTaskDispatcher(unittest.TestCase):
    """Test task dispatcher functionality"""

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task._install_schtasks")
    def test_dispatch_scheduler_operation_install_success(self, mock_install, mock_get_scheduler):
        """Test successful dispatcher operation for install"""
        mock_get_scheduler.return_value = "schtasks"
        mock_install.return_value = True

        result = task._dispatch_scheduler_operation("install", "config.json", "ddns.log", 5)

        self.assertTrue(result)
        mock_install.assert_called_once_with("config.json", "ddns.log", 5)

    @patch("ddns.util.task.get_scheduler_type")
    def test_dispatch_scheduler_operation_unsupported(self, mock_get_scheduler):
        """Test dispatcher with unsupported operation"""
        mock_get_scheduler.return_value = "unsupported_scheduler"

        result = task._dispatch_scheduler_operation("install", "config.json")

        self.assertFalse(result)

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task._enable_systemd")
    def test_dispatch_scheduler_operation_enable_success(self, mock_enable, mock_get_scheduler):
        """Test successful dispatcher operation for enable"""
        mock_get_scheduler.return_value = "systemd"
        mock_enable.return_value = True

        result = task._dispatch_scheduler_operation("enable")

        self.assertTrue(result)
        mock_enable.assert_called_once_with()

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task._enable_systemd")
    def test_dispatch_scheduler_operation_exception(self, mock_enable, mock_get_scheduler):
        """Test dispatcher handling exceptions"""
        mock_get_scheduler.return_value = "systemd"
        mock_enable.side_effect = Exception("Test error")

        result = task._dispatch_scheduler_operation("enable")

        self.assertFalse(result)


class TestTaskEnableDisable(unittest.TestCase):
    """Test enable/disable functionality"""

    @patch("ddns.util.task.is_installed")
    @patch("ddns.util.task._dispatch_scheduler_operation")
    def test_enable_success(self, mock_dispatch, mock_is_installed):
        """Test successful enable operation"""
        mock_is_installed.return_value = True
        mock_dispatch.return_value = True

        result = task.enable()

        self.assertTrue(result)
        mock_dispatch.assert_called_once_with("enable")

    @patch("ddns.util.task.is_installed")
    def test_enable_not_installed(self, mock_is_installed):
        """Test enable when task is not installed"""
        mock_is_installed.return_value = False

        result = task.enable()

        self.assertFalse(result)

    @patch("ddns.util.task.is_installed")
    @patch("ddns.util.task._dispatch_scheduler_operation")
    def test_disable_success(self, mock_dispatch, mock_is_installed):
        """Test successful disable operation"""
        mock_is_installed.return_value = True
        mock_dispatch.return_value = True

        result = task.disable()

        self.assertTrue(result)
        mock_dispatch.assert_called_once_with("disable")

    @patch("ddns.util.task.is_installed")
    def test_disable_not_installed(self, mock_is_installed):
        """Test disable when task is not installed"""
        mock_is_installed.return_value = False

        result = task.disable()

        self.assertFalse(result)


class TestTaskVBSFunctionality(unittest.TestCase):
    """Test VBS script functionality"""

    def test_get_vbs_locations(self):
        """Test VBS locations list"""
        locations = task._get_vbs_locations()

        self.assertIsInstance(locations, list)
        self.assertTrue(len(locations) > 0)
        # Check that AppData location is first (preferred)
        self.assertIn("AppData", locations[0])

    @patch("ddns.util.task.os.makedirs")
    @patch("ddns.util.task.os.getcwd")
    @patch("ddns.util.task._get_ddns_cmd")
    def test_create_vbs_script_success(self, mock_get_cmd, mock_getcwd, mock_makedirs):
        """Test successful VBS script creation"""
        mock_getcwd.return_value = "C:\\test"
        mock_get_cmd.return_value = '"python" -m ddns'

        with patch("builtins.open", unittest.mock.mock_open()) as mock_open:
            result = task._create_vbs_script("config.json")

            self.assertIsInstance(result, str)
            self.assertTrue(result.endswith(".vbs"))
            mock_open.assert_called()

    @patch("ddns.util.task.os.makedirs")
    @patch("ddns.util.task.os.getcwd")
    @patch("ddns.util.task._get_ddns_cmd")
    def test_create_vbs_script_fallback(self, mock_get_cmd, mock_getcwd, mock_makedirs):
        """Test VBS script creation with fallback to working directory"""
        mock_getcwd.return_value = "C:\\test"
        mock_get_cmd.return_value = '"python" -m ddns'

        # First open call fails (AppData), second succeeds (working dir)
        mock_open = unittest.mock.mock_open()
        mock_open.side_effect = [Exception("Permission denied"), mock_open.return_value]

        with patch("builtins.open", mock_open):
            result = task._create_vbs_script("config.json")

            self.assertIsInstance(result, str)
            self.assertTrue(result.endswith(".vbs"))


class TestTaskConstants(unittest.TestCase):
    """Test task constants"""

    def test_constants_defined(self):
        """Test that all required constants are defined"""
        self.assertEqual(task.TASK_NAME, "DDNS")
        self.assertEqual(task.LAUNCHD_LABEL, "cc.newfuture.ddns")
        self.assertEqual(task.SYSTEMD_SERVICE, "ddns.service")
        self.assertEqual(task.SYSTEMD_TIMER, "ddns.timer")


if __name__ == "__main__":
    unittest.main()
