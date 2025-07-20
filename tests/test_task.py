# -*- coding:utf-8 -*-
"""
Unit tests for DDNS task management functionality
@author: NewFuture
"""

from __init__ import unittest, patch, MagicMock
import tempfile
import os
import platform


class TestTaskManager(unittest.TestCase):
    """Test TaskManager class functionality"""
    
    def setUp(self):
        from ddns.task import TaskManager
        self.logger = MagicMock()
        self.task_manager = TaskManager(self.logger)
    
    def test_init(self):
        """Test TaskManager initialization"""
        self.assertIsNotNone(self.task_manager.logger)
        self.assertIsNotNone(self.task_manager.system)
        self.assertIsNotNone(self.task_manager.ddns_version)
    
    @patch('platform.system')
    def test_system_detection(self, mock_system):
        """Test system detection"""
        from ddns.task import TaskManager
        
        mock_system.return_value = "Linux"
        manager = TaskManager(self.logger)
        self.assertEqual(manager.system, "linux")
        
        mock_system.return_value = "Darwin"
        manager = TaskManager(self.logger)
        self.assertEqual(manager.system, "darwin")
        
        mock_system.return_value = "Windows"
        manager = TaskManager(self.logger)
        self.assertEqual(manager.system, "windows")
    
    @patch.object(platform, 'system', return_value='Linux')
    @patch('ddns.task.TaskManager._run_command')
    def test_detect_available_schedulers_linux(self, mock_run_command, mock_system):
        """Test scheduler detection on Linux"""
        # Mock successful systemd and cron detection
        mock_run_command.side_effect = [
            (0, "systemd 245", ""),  # systemctl --version
            (0, "/usr/bin/crontab", "")  # which crontab
        ]
        
        schedulers = self.task_manager.detect_available_schedulers()
        self.assertIn("systemd", schedulers)
        self.assertIn("cron", schedulers)
    
    @patch('ddns.task.TaskManager._run_command')
    def test_detect_available_schedulers_macos(self, mock_run_command):
        """Test scheduler detection on macOS"""
        # Mock successful launchd and cron detection
        mock_run_command.side_effect = [
            (0, "launchctl version", ""),  # launchctl version
            (0, "/usr/bin/crontab", "")  # which crontab
        ]
        
        # Create a new manager with macOS system
        from ddns.task import TaskManager
        with patch.object(TaskManager, '__init__', lambda self, logger=None: None):
            manager = TaskManager()
            manager.logger = self.logger
            manager.system = "darwin"
            manager.ddns_version = "test"
            
            schedulers = manager.detect_available_schedulers()
            self.assertIn("launchd", schedulers)
            self.assertIn("cron", schedulers)
    
    @patch('ddns.task.TaskManager._run_command')
    def test_detect_available_schedulers_windows(self, mock_run_command):
        """Test scheduler detection on Windows"""
        # Mock successful schtasks detection
        mock_run_command.return_value = (0, "schtasks help", "")
        
        # Create a new manager with Windows system
        from ddns.task import TaskManager
        with patch.object(TaskManager, '__init__', lambda self, logger=None: None):
            manager = TaskManager()
            manager.logger = self.logger
            manager.system = "windows"
            manager.ddns_version = "test"
            
            schedulers = manager.detect_available_schedulers()
            self.assertIn("schtasks", schedulers)
    
    @patch('ddns.task.TaskManager._run_command')
    def test_check_systemd_task_not_installed(self, mock_run_command):
        """Test checking systemd task when not installed"""
        mock_run_command.return_value = (1, "", "Unit ddns.timer could not be found.")
        
        installed, info = self.task_manager._check_systemd_task()
        self.assertFalse(installed)
        self.assertEqual(info, {})
    
    @patch('ddns.task.TaskManager._run_command')
    def test_check_systemd_task_installed(self, mock_run_command):
        """Test checking systemd task when installed"""
        mock_run_command.side_effect = [
            (0, "enabled", ""),  # is-enabled
            (0, "● ddns.timer - NewFuture DDNS Timer\n   Loaded: loaded", "")  # status
        ]
        
        installed, info = self.task_manager._check_systemd_task()
        self.assertTrue(installed)
        self.assertTrue(info["enabled"])
        self.assertEqual(info["type"], "systemd timer")
        self.assertEqual(info["interval"], "5 minutes")
    
    @patch('ddns.task.TaskManager._run_command')
    def test_check_cron_task_not_installed(self, mock_run_command):
        """Test checking cron task when not installed"""
        mock_run_command.return_value = (1, "", "no crontab for user")
        
        installed, info = self.task_manager._check_cron_task()
        self.assertFalse(installed)
        self.assertEqual(info, {})
    
    @patch('ddns.task.TaskManager._run_command')
    def test_check_cron_task_installed(self, mock_run_command):
        """Test checking cron task when installed"""
        crontab_output = "*/5 * * * * /usr/bin/python3 -m ddns -c /etc/ddns/config.json"
        mock_run_command.return_value = (0, crontab_output, "")
        
        installed, info = self.task_manager._check_cron_task()
        self.assertTrue(installed)
        self.assertTrue(info["enabled"])
        self.assertEqual(info["type"], "cron job")
        self.assertEqual(info["schedule"], ["*/5", "*", "*", "*", "*"])
    
    @patch('os.path.exists')
    def test_check_launchd_task_not_installed(self, mock_exists):
        """Test checking launchd task when not installed"""
        mock_exists.return_value = False
        
        installed, info = self.task_manager._check_launchd_task()
        self.assertFalse(installed)
        self.assertEqual(info, {})
    
    @patch('os.path.exists')
    @patch('ddns.task.TaskManager._run_command')
    def test_check_launchd_task_installed(self, mock_run_command, mock_exists):
        """Test checking launchd task when installed"""
        mock_exists.return_value = True
        mock_run_command.return_value = (0, "com.newfuture.ddns", "")  # launchctl list
        
        installed, info = self.task_manager._check_launchd_task()
        self.assertTrue(installed)
        self.assertTrue(info["enabled"])
        self.assertEqual(info["type"], "launchd job")
        self.assertEqual(info["interval"], "5 minutes")
    
    @patch('ddns.task.TaskManager._run_command')
    def test_check_schtasks_task_not_installed(self, mock_run_command):
        """Test checking Windows scheduled task when not installed"""
        mock_run_command.return_value = (1, "", "ERROR: The system cannot find the file specified.")
        
        installed, info = self.task_manager._check_schtasks_task()
        self.assertFalse(installed)
        self.assertEqual(info, {})
    
    @patch('ddns.task.TaskManager._run_command')
    def test_check_schtasks_task_installed(self, mock_run_command):
        """Test checking Windows scheduled task when installed"""
        schtasks_output = """TaskName: DDNS
Status: Ready
Schedule Type: At Logon Time"""
        mock_run_command.return_value = (0, schtasks_output, "")
        
        installed, info = self.task_manager._check_schtasks_task()
        self.assertTrue(installed)
        self.assertTrue(info["enabled"])
        self.assertEqual(info["type"], "scheduled task")
    
    @patch('ddns.task.TaskManager.detect_available_schedulers')
    def test_get_preferred_scheduler_linux(self, mock_detect):
        """Test preferred scheduler selection on Linux"""
        self.task_manager.system = "linux"
        mock_detect.return_value = ["systemd", "cron"]
        
        preferred = self.task_manager.get_preferred_scheduler()
        self.assertEqual(preferred, "systemd")
    
    @patch('ddns.task.TaskManager.detect_available_schedulers')
    def test_get_preferred_scheduler_macos(self, mock_detect):
        """Test preferred scheduler selection on macOS"""
        self.task_manager.system = "darwin"
        mock_detect.return_value = ["launchd", "cron"]
        
        preferred = self.task_manager.get_preferred_scheduler()
        self.assertEqual(preferred, "launchd")
    
    @patch('ddns.task.TaskManager.detect_available_schedulers')
    def test_get_preferred_scheduler_windows(self, mock_detect):
        """Test preferred scheduler selection on Windows"""
        self.task_manager.system = "windows"
        mock_detect.return_value = ["schtasks"]
        
        preferred = self.task_manager.get_preferred_scheduler()
        self.assertEqual(preferred, "schtasks")
    
    @patch('ddns.task.TaskManager.detect_available_schedulers')
    def test_get_preferred_scheduler_no_available(self, mock_detect):
        """Test preferred scheduler when none available"""
        mock_detect.return_value = []
        
        preferred = self.task_manager.get_preferred_scheduler()
        self.assertIsNone(preferred)
    
    @patch('ddns.task.TaskManager._check_systemd_task')
    @patch('ddns.task.TaskManager._check_cron_task')
    @patch('ddns.task.TaskManager.detect_available_schedulers')
    def test_is_task_installed_systemd(self, mock_detect, mock_check_cron, mock_check_systemd):
        """Test task installation check with systemd"""
        mock_detect.return_value = ["systemd", "cron"]
        mock_check_systemd.return_value = (True, {"type": "systemd timer"})
        mock_check_cron.return_value = (False, {})
        
        installed, scheduler, info = self.task_manager.is_task_installed()
        self.assertTrue(installed)
        self.assertEqual(scheduler, "systemd")
        self.assertEqual(info["type"], "systemd timer")
    
    @patch('ddns.task.TaskManager._check_systemd_task')
    @patch('ddns.task.TaskManager._check_cron_task')
    @patch('ddns.task.TaskManager.detect_available_schedulers')
    def test_is_task_installed_none(self, mock_detect, mock_check_cron, mock_check_systemd):
        """Test task installation check when none installed"""
        mock_detect.return_value = ["systemd", "cron"]
        mock_check_systemd.return_value = (False, {})
        mock_check_cron.return_value = (False, {})
        
        installed, scheduler, info = self.task_manager.is_task_installed()
        self.assertFalse(installed)
        self.assertIsNone(scheduler)
        self.assertEqual(info, {})
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    @patch('ddns.task.TaskManager._run_command')
    def test_install_cron_task_success(self, mock_run_command, mock_unlink, mock_temp):
        """Test successful cron task installation"""
        # Mock temporary file
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/test_crontab"
        mock_temp.__enter__ = MagicMock(return_value=mock_temp_file)
        mock_temp.__exit__ = MagicMock(return_value=None)
        
        # Mock crontab commands
        mock_run_command.side_effect = [
            (1, "", "no crontab for user"),  # crontab -l (no existing)
            (0, "", "")  # crontab /tmp/test_crontab
        ]
        
        result = self.task_manager._install_cron_task(5, None)
        self.assertTrue(result)
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    @patch('ddns.task.TaskManager._run_command')
    def test_install_cron_task_failure(self, mock_run_command, mock_unlink, mock_temp):
        """Test failed cron task installation"""
        # Mock temporary file
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/test_crontab"
        mock_temp.__enter__ = MagicMock(return_value=mock_temp_file)
        mock_temp.__exit__ = MagicMock(return_value=None)
        
        # Mock crontab commands
        mock_run_command.side_effect = [
            (1, "", "no crontab for user"),  # crontab -l (no existing)
            (1, "", "permission denied")  # crontab /tmp/test_crontab (failure)
        ]
        
        result = self.task_manager._install_cron_task(5, None)
        self.assertFalse(result)
    
    @patch('ddns.task.TaskManager._run_command')
    def test_uninstall_schtasks_task_success(self, mock_run_command):
        """Test successful Windows scheduled task uninstallation"""
        mock_run_command.return_value = (0, "SUCCESS: The scheduled task \"DDNS\" was successfully deleted.", "")
        
        result = self.task_manager._uninstall_schtasks_task()
        self.assertTrue(result)
    
    @patch('ddns.task.TaskManager._run_command')
    def test_uninstall_schtasks_task_not_found(self, mock_run_command):
        """Test Windows scheduled task uninstallation when task not found"""
        mock_run_command.return_value = (1, "", "ERROR: The system cannot find the file specified.")
        
        result = self.task_manager._uninstall_schtasks_task()
        self.assertFalse(result)
    
    @patch('ddns.task.TaskManager.is_task_installed')
    @patch('ddns.task.TaskManager.get_preferred_scheduler')
    @patch('ddns.task.TaskManager._install_systemd_task')
    def test_install_task_new_installation(self, mock_install_systemd, mock_get_preferred, mock_is_installed):
        """Test installing task when none exists"""
        mock_is_installed.return_value = (False, None, {})
        mock_get_preferred.return_value = "systemd"
        mock_install_systemd.return_value = True
        
        result = self.task_manager.install_task()
        self.assertTrue(result)
        mock_install_systemd.assert_called_once()
    
    @patch('ddns.task.TaskManager.is_task_installed')
    def test_install_task_already_exists_no_force(self, mock_is_installed):
        """Test installing task when one already exists without force"""
        mock_is_installed.return_value = (True, "systemd", {"type": "systemd timer"})
        
        result = self.task_manager.install_task(scheduler="systemd")
        self.assertTrue(result)  # Should return True for already installed
    
    @patch('ddns.task.TaskManager.is_task_installed')
    @patch('ddns.task.TaskManager.uninstall_task')
    @patch('ddns.task.TaskManager._install_systemd_task')
    def test_install_task_force_reinstall(self, mock_install_systemd, mock_uninstall, mock_is_installed):
        """Test force reinstalling existing task"""
        mock_is_installed.return_value = (True, "systemd", {"type": "systemd timer"})
        mock_uninstall.return_value = True
        mock_install_systemd.return_value = True
        
        result = self.task_manager.install_task(scheduler="systemd", force=True)
        self.assertTrue(result)
        mock_uninstall.assert_called_once()
        mock_install_systemd.assert_called_once()
    
    @patch('ddns.task.TaskManager.is_task_installed')
    @patch('ddns.task.TaskManager._uninstall_systemd_task')
    def test_uninstall_task_success(self, mock_uninstall_systemd, mock_is_installed):
        """Test successful task uninstallation"""
        mock_is_installed.return_value = (True, "systemd", {"type": "systemd timer"})
        mock_uninstall_systemd.return_value = True
        
        result = self.task_manager.uninstall_task()
        self.assertTrue(result)
        mock_uninstall_systemd.assert_called_once()
    
    @patch('ddns.task.TaskManager.is_task_installed')
    def test_uninstall_task_not_installed(self, mock_is_installed):
        """Test uninstalling task when none exists"""
        mock_is_installed.return_value = (False, None, {})
        
        result = self.task_manager.uninstall_task()
        self.assertTrue(result)  # Should return True when nothing to uninstall
    
    @patch('ddns.task.TaskManager.is_task_installed')
    @patch('ddns.task.TaskManager.detect_available_schedulers')
    @patch('ddns.task.TaskManager.get_preferred_scheduler')
    def test_get_task_status_complete(self, mock_get_preferred, mock_detect, mock_is_installed):
        """Test getting complete task status"""
        mock_is_installed.return_value = (True, "systemd", {"type": "systemd timer", "enabled": True})
        mock_detect.return_value = ["systemd", "cron"]
        mock_get_preferred.return_value = "systemd"
        
        status = self.task_manager.get_task_status()
        
        self.assertEqual(status["system"], self.task_manager.system)
        self.assertEqual(status["available_schedulers"], ["systemd", "cron"])
        self.assertEqual(status["preferred_scheduler"], "systemd")
        self.assertTrue(status["installed"])
        self.assertEqual(status["current_scheduler"], "systemd")
        self.assertEqual(status["task_info"]["type"], "systemd timer")


class TestTaskCommandIntegration(unittest.TestCase):
    """Test task command integration"""
    
    @patch('sys.argv', ['ddns', 'task', '--help'])
    def test_task_command_help(self):
        """Test task command help output"""
        from ddns.__main__ import handle_task_command_from_args
        
        with self.assertRaises(SystemExit):  # argparse calls sys.exit on --help
            handle_task_command_from_args()
    
    @patch('ddns.task.TaskManager.get_task_status')
    @patch('sys.argv', ['ddns', 'task', '--status'])
    def test_task_command_status(self, mock_get_status):
        """Test task command status action"""
        from ddns.__main__ import handle_task_command_from_args
        
        mock_get_status.return_value = {
            "system": "linux",
            "available_schedulers": ["systemd"],
            "preferred_scheduler": "systemd",
            "installed": False,
            "current_scheduler": None,
            "task_info": {},
            "ddns_version": "test"
        }
        
        handle_task_command_from_args()
        mock_get_status.assert_called_once()
    
    @patch('ddns.task.TaskManager.install_task')
    @patch('sys.argv', ['ddns', 'task', '--install', '--interval', '10'])
    def test_task_command_install(self, mock_install):
        """Test task command install action"""
        from ddns.__main__ import handle_task_command_from_args
        
        mock_install.return_value = True
        
        handle_task_command_from_args()
        mock_install.assert_called_once_with(
            scheduler=None,
            interval=10,
            config_file=None,
            force=False
        )
    
    @patch('ddns.task.TaskManager.uninstall_task')
    @patch('sys.argv', ['ddns', 'task', '--delete'])
    def test_task_command_delete(self, mock_uninstall):
        """Test task command delete action"""
        from ddns.__main__ import handle_task_command_from_args
        
        mock_uninstall.return_value = True
        
        handle_task_command_from_args()
        mock_uninstall.assert_called_once_with(scheduler=None)


class TestPrintTaskStatus(unittest.TestCase):
    """Test task status printing functionality"""
    
    @patch('builtins.print')
    def test_print_task_status_not_installed(self, mock_print):
        """Test printing status for not installed task"""
        from ddns.task import print_task_status
        
        status = {
            "system": "linux",
            "ddns_version": "test",
            "available_schedulers": ["systemd", "cron"],
            "preferred_scheduler": "systemd",
            "installed": False,
            "current_scheduler": None,
            "task_info": {}
        }
        
        print_task_status(status)
        
        # Check that print was called multiple times with expected content
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        self.assertIn("DDNS Task Status", print_calls[0])
        self.assertIn("Task Status: NOT INSTALLED", print_calls)
    
    @patch('builtins.print')
    def test_print_task_status_installed(self, mock_print):
        """Test printing status for installed task"""
        from ddns.task import print_task_status
        
        status = {
            "system": "linux",
            "ddns_version": "test",
            "available_schedulers": ["systemd", "cron"],
            "preferred_scheduler": "systemd",
            "installed": True,
            "current_scheduler": "systemd",
            "task_info": {
                "type": "systemd timer",
                "status": "active",
                "enabled": True,
                "interval": "5 minutes"
            }
        }
        
        print_task_status(status)
        
        # Check that print was called multiple times with expected content
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        self.assertIn("Task Status: INSTALLED", print_calls)
        self.assertIn("Current Scheduler: systemd", print_calls)


if __name__ == '__main__':
    unittest.main()