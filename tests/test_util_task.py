# -*- coding:utf-8 -*-
"""
Tests for ddns.util.task module
"""
from __init__ import unittest, patch
import subprocess

import ddns.util.task as task


class TestTaskFunctions(unittest.TestCase):
    """Test task module functions"""

    @patch("ddns.util.task.platform.system")
    def test_get_scheduler_type_linux_with_systemd(self, mock_system):
        """Test scheduler type detection on Linux with systemd"""
        mock_system.return_value = "Linux"
        with patch("ddns.util.task.read_file_safely", return_value="systemd\n"):
            result = task.get_scheduler_type()
            self.assertEqual(result, "systemd")

    @patch("ddns.util.task.platform.system")
    def test_get_scheduler_type_linux_without_systemd(self, mock_system):
        """Test scheduler type detection on Linux without systemd"""
        mock_system.return_value = "Linux"
        with patch("ddns.util.task.read_file_safely", return_value="init\n"):
            result = task.get_scheduler_type()
            self.assertEqual(result, "cron")

    @patch("ddns.util.task.platform.system")
    def test_get_scheduler_type_linux_proc_not_accessible(self, mock_system):
        """Test scheduler type detection on Linux when /proc/1/comm is not accessible"""
        mock_system.return_value = "Linux"
        with patch("ddns.util.task.read_file_safely", return_value=None):
            result = task.get_scheduler_type()
            self.assertEqual(result, "cron")

    @patch("ddns.util.task.platform.system")
    def test_get_scheduler_type_darwin_with_launchd(self, mock_system):
        """Test scheduler type detection on macOS with launchd"""
        mock_system.return_value = "Darwin"
        with patch("ddns.util.task.os.path.isdir") as mock_isdir:
            mock_isdir.return_value = True
            result = task.get_scheduler_type()
            self.assertEqual(result, "launchd")

    @patch("ddns.util.task.platform.system")
    def test_get_scheduler_type_darwin_without_launchd(self, mock_system):
        """Test scheduler type detection on macOS without launchd"""
        mock_system.return_value = "Darwin"
        with patch("ddns.util.task.os.path.isdir") as mock_isdir:
            mock_isdir.return_value = False
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
            mock_check_output.return_value = "enabled\n"
            result = task.is_installed()
            self.assertTrue(result)

    @patch("ddns.util.task.get_scheduler_type")
    def test_is_installed_systemd_disabled(self, mock_get_scheduler):
        """Test is_installed for systemd when timer is disabled"""
        mock_get_scheduler.return_value = "systemd"
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = "disabled\n"
            result = task.is_installed()
            self.assertFalse(result)

    @patch("ddns.util.task.get_scheduler_type")
    def test_is_installed_cron_with_ddns_job(self, mock_get_scheduler):
        """Test is_installed for cron when DDNS job exists"""
        mock_get_scheduler.return_value = "cron"
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = "*/5 * * * * /usr/bin/ddns\n"
            result = task.is_installed()
            self.assertTrue(result)

    @patch("ddns.util.task.get_scheduler_type")
    def test_is_installed_cron_without_ddns_job(self, mock_get_scheduler):
        """Test is_installed for cron when no DDNS job exists"""
        mock_get_scheduler.return_value = "cron"
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = "*/5 * * * * /usr/bin/other\n"
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
            mock_check_output.return_value = "DDNS task found\n"
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

        status = task.get_status()

        expected_status = {
            "installed": False,
            "scheduler": "cron",
            "system": "linux",
        }
        self.assertEqual(status, expected_status)

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task.is_installed")
    @patch("ddns.util.task._get_running_status")
    @patch("ddns.util.task._get_task_interval")
    @patch("ddns.util.task._get_task_command")
    @patch("ddns.util.task.platform.system")
    def test_get_status_installed(
        self,
        mock_system,
        mock_get_command,
        mock_get_interval,
        mock_get_running_status,
        mock_is_installed,
        mock_get_scheduler,
    ):
        """Test get_status when task is installed"""
        mock_system.return_value = "Linux"
        mock_get_scheduler.return_value = "systemd"
        mock_is_installed.return_value = True
        mock_get_running_status.return_value = "active"
        mock_get_interval.return_value = 10
        mock_get_command.return_value = "/usr/bin/python3 -m ddns --debug false"

        status = task.get_status()

        expected_status = {
            "installed": True,
            "scheduler": "systemd",
            "system": "linux",
            "interval": 10,
            "running_status": "active",
            "command": "/usr/bin/python3 -m ddns --debug false",
        }
        self.assertEqual(status, expected_status)

    def test_get_task_interval_systemd(self):
        """Test _get_task_interval for systemd"""
        timer_content = """[Unit]
Description=DDNS automatic IP update timer

[Timer]
OnUnitActiveSec=10m
Unit=ddns.service

[Install]
WantedBy=multi-user.target
"""
        with patch("ddns.util.task.read_file_safely") as mock_read_file:
            mock_read_file.return_value = timer_content
            result = task._get_task_interval("systemd")
            self.assertEqual(result, 10)

    def test_get_task_interval_cron(self):
        """Test _get_task_interval for cron"""
        cron_content = "*/15 * * * * cd /path && python -m ddns"
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = cron_content
            result = task._get_task_interval("cron")
            self.assertEqual(result, 15)

    def test_get_task_interval_not_found(self):
        """Test _get_task_interval when interval cannot be determined"""
        result = task._get_task_interval("unsupported")
        self.assertIsNone(result)

    def test_get_task_command_systemd(self):
        """Test _get_task_command for systemd"""
        service_content = """[Unit]
Description=DDNS automatic IP update service

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 -m ddns -c /etc/ddns/config.json

[Install]
WantedBy=multi-user.target
"""
        with patch("ddns.util.task.read_file_safely") as mock_read_file:
            mock_read_file.return_value = service_content
            result = task._get_task_command("systemd")
            self.assertEqual(result, "/usr/bin/python3 -m ddns -c /etc/ddns/config.json")

    def test_get_task_command_cron(self):
        """Test _get_task_command for cron"""
        cron_content = "*/15 * * * * cd /path && python3 -m ddns --config /home/user/ddns.json"
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = cron_content
            result = task._get_task_command("cron")
            self.assertEqual(result, "cd /path && python3 -m ddns --config /home/user/ddns.json")

    def test_get_task_command_not_found(self):
        """Test _get_task_command when command cannot be determined"""
        result = task._get_task_command("unsupported")
        self.assertIsNone(result)

    def test_get_running_status_systemd_active(self):
        """Test _get_running_status for systemd when active"""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = "active\n"
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
            mock_check_output.return_value = "12345\n"
            result = task._get_running_status("cron")
            self.assertEqual(result, "active")

    def test_get_running_status_cron_inactive(self):
        """Test _get_running_status for cron when inactive"""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "pgrep")
            result = task._get_running_status("cron")
            self.assertEqual(result, "inactive")

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task._dispatch_scheduler_operation")
    def test_install_always_proceeds(self, mock_dispatch, mock_get_scheduler):
        """Test successful installation (always proceeds without checking if already installed)"""
        mock_get_scheduler.return_value = "cron"
        mock_dispatch.return_value = True

        result = task.install(interval=10)

        self.assertTrue(result)
        mock_dispatch.assert_called_once_with("install", 10, None)

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task._dispatch_scheduler_operation")
    def test_install_with_ddns_args(self, mock_dispatch, mock_get_scheduler):
        """Test installation with DDNS arguments"""
        mock_get_scheduler.return_value = "systemd"
        mock_dispatch.return_value = True
        ddns_args = {"config": "/path/to/config.json", "debug": True}

        result = task.install(interval=5, ddns_args=ddns_args)

        self.assertTrue(result)
        mock_dispatch.assert_called_once_with("install", 5, ddns_args)

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task.is_installed")
    @patch("ddns.util.task._dispatch_scheduler_operation")
    def test_uninstall_success(self, mock_dispatch, mock_is_installed, mock_get_scheduler):
        """Test successful uninstallation"""
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = True
        mock_dispatch.return_value = True

        result = task.uninstall()

        self.assertTrue(result)
        mock_dispatch.assert_called_once_with("uninstall")

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task.is_installed")
    def test_uninstall_not_installed(self, mock_is_installed, mock_get_scheduler):
        """Test uninstallation when not installed"""
        mock_get_scheduler.return_value = "cron"
        mock_is_installed.return_value = False

        result = task.uninstall()

        self.assertTrue(result)

    @patch("ddns.util.task.get_scheduler_type")
    @patch("ddns.util.task._dispatch_scheduler_operation")
    def test_install_systemd_with_ddns_args(self, mock_dispatch, mock_get_scheduler):
        """Test systemd installation with ddns_args parameter"""
        mock_get_scheduler.return_value = "systemd"
        mock_dispatch.return_value = True

        ddns_args = {"config": ["cloudflare.json"], "debug": True}
        result = task.install(interval=5, ddns_args=ddns_args)

        self.assertTrue(result)
        mock_dispatch.assert_called_once_with("install", 5, ddns_args)


class TestTaskDispatcher(unittest.TestCase):
    """Test task dispatcher functionality"""

    @patch("ddns.util.task.get_scheduler_type")
    def test_dispatch_scheduler_operation_install_success(self, mock_get_scheduler):
        """Test successful dispatcher operation for install"""
        mock_get_scheduler.return_value = "systemd"

        # Mock the _install_systemd function that still exists
        with patch("ddns.util.task._install_systemd") as mock_install:
            mock_install.return_value = True

            result = task._dispatch_scheduler_operation("install", 5, None)

            self.assertTrue(result)
            mock_install.assert_called_once_with(5, None)

    @patch("ddns.util.task.subprocess.check_call")
    @patch("ddns.util.task.get_scheduler_type")
    def test_dispatch_scheduler_operation_enable_success(self, mock_get_scheduler, mock_check_call):
        """Test successful dispatcher operation for enable"""
        mock_get_scheduler.return_value = "systemd"
        mock_check_call.return_value = None  # Success

        result = task._dispatch_scheduler_operation("enable")

        self.assertTrue(result)
        # Should call systemctl enable and start
        self.assertEqual(mock_check_call.call_count, 2)

    @patch("ddns.util.task.get_scheduler_type")
    def test_dispatch_scheduler_operation_unsupported(self, mock_get_scheduler):
        """Test dispatcher with unsupported operation"""
        mock_get_scheduler.return_value = "unsupported_scheduler"

        result = task._dispatch_scheduler_operation("install", 5, None)

        self.assertFalse(result)

    @patch("ddns.util.task.get_scheduler_type")
    def test_dispatch_scheduler_operation_exception(self, mock_get_scheduler):
        """Test dispatcher handling exceptions"""
        mock_get_scheduler.return_value = "systemd"

        # Mock _install_systemd to raise an exception
        with patch("ddns.util.task._install_systemd") as mock_install:
            mock_install.side_effect = Exception("Test error")

            result = task._dispatch_scheduler_operation("install", 5, None)

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

    @patch("ddns.util.task.os.makedirs")
    @patch("ddns.util.task.os.getcwd")
    @patch("ddns.util.task._get_ddns_cmd")
    def test_create_vbs_script_success(self, mock_get_cmd, mock_getcwd, mock_makedirs):
        """Test successful VBS script creation"""
        mock_getcwd.return_value = "C:\\test"
        mock_get_cmd.return_value = '"python" -m ddns'

        with patch("ddns.util.task.write_file") as mock_write:
            result = task._create_vbs_script({"config": ["config.json"]})

            self.assertIsInstance(result, str)
            self.assertTrue(result.endswith(".vbs"))
            mock_write.assert_called()

    @patch("ddns.util.task.os.makedirs")
    @patch("ddns.util.task.os.getcwd")
    @patch("ddns.util.task._get_ddns_cmd")
    def test_create_vbs_script_fallback(self, mock_get_cmd, mock_getcwd, mock_makedirs):
        """Test VBS script creation with fallback to working directory"""
        mock_getcwd.return_value = "C:\\test"
        mock_get_cmd.return_value = '"python" -m ddns'

        # First write_file call fails (AppData), second succeeds (working dir)
        with patch("ddns.util.task.write_file", side_effect=[Exception("Permission denied"), None]):
            result = task._create_vbs_script({"config": ["config.json"]})

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


class TestTaskCommandBuilder(unittest.TestCase):
    """Test command building functionality"""

    @patch("ddns.util.task._get_ddns_cmd")
    def test_build_ddns_command_without_args(self, mock_get_ddns_cmd):
        """Test building DDNS command without additional arguments"""
        mock_get_ddns_cmd.return_value = '"python3" -m ddns'

        result = task._build_ddns_command(None)

        expected = '"python3" -m ddns'
        self.assertEqual(result, expected)

    @patch("ddns.util.task._get_ddns_cmd")
    def test_build_ddns_command_with_args(self, mock_get_ddns_cmd):
        """Test building DDNS command with additional arguments"""
        mock_get_ddns_cmd.return_value = '"python3" -m ddns'
        ddns_args = {"config": ["config.json"], "proxy": ["http://proxy.example.com:8080"], "debug": True}

        result = task._build_ddns_command(ddns_args)

        # Should contain base command, proxy and debug (config is skipped)
        self.assertIn('"python3" -m ddns', result)
        self.assertIn('--proxy "http://proxy.example.com:8080"', result)
        self.assertIn("--debug", result)
        # config parameter should be skipped, not converted to -c
        self.assertNotIn('-c "config.json"', result)

    @patch("ddns.util.task._get_ddns_cmd")
    def test_build_ddns_command_with_empty_args(self, mock_get_ddns_cmd):
        """Test building DDNS command with empty additional arguments"""
        mock_get_ddns_cmd.return_value = '"python3" -m ddns'

        result = task._build_ddns_command({})

        expected = '"python3" -m ddns'
        self.assertEqual(result, expected)

    @patch("ddns.util.task._get_ddns_cmd")
    def test_build_ddns_command_with_special_chars(self, mock_get_ddns_cmd):
        """Test building DDNS command with arguments containing special characters"""
        mock_get_ddns_cmd.return_value = '"python3" -m ddns'
        ddns_args = {"token": "abc-123_xyz", "domain": "test.example.com"}

        result = task._build_ddns_command(ddns_args)

        # Should contain properly quoted arguments
        self.assertIn('--token "abc-123_xyz"', result)
        self.assertIn('--domain "test.example.com"', result)

    @patch("ddns.util.task._get_ddns_cmd")
    def test_build_ddns_command_with_boolean_flags(self, mock_get_ddns_cmd):
        """Test building DDNS command with boolean flags"""
        mock_get_ddns_cmd.return_value = '"python3" -m ddns'
        ddns_args = {"verbose": True, "ipv6": True, "debug": True}

        result = task._build_ddns_command(ddns_args)

        self.assertIn("--verbose", result)
        self.assertIn("--ipv6", result)
        self.assertIn("--debug", result)

    @patch("ddns.util.task._get_ddns_cmd")
    def test_build_ddns_command_with_false_boolean(self, mock_get_ddns_cmd):
        """Test building DDNS command with False boolean (should be treated as string)"""
        mock_get_ddns_cmd.return_value = '"python3" -m ddns'
        ddns_args = {"cache": False}

        result = task._build_ddns_command(ddns_args)

        # False boolean should be included as string value
        self.assertIn("--cache false", result)

    @patch("ddns.util.task._get_ddns_cmd")
    def test_build_ddns_command_with_list_args(self, mock_get_ddns_cmd):
        """Test building DDNS command with list arguments"""
        mock_get_ddns_cmd.return_value = '"python3" -m ddns'
        ddns_args = {"domains": ["example.com", "test.com"]}

        result = task._build_ddns_command(ddns_args)

        # Should include both domain entries
        self.assertIn('--domains "example.com"', result)
        self.assertIn('--domains "test.com"', result)


if __name__ == "__main__":
    unittest.main()
