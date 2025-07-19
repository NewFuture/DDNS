# -*- coding:utf-8 -*-
"""
Unit tests for DDNS task management functionality.

@author: NewFuture
"""

from __init__ import unittest, patch, MagicMock

from ddns.task import TaskManager, get_task_manager, IS_WINDOWS, IS_MACOS, IS_LINUX


class TestTaskManager(unittest.TestCase):
    """Test TaskManager base class functionality."""

    def test_task_manager_interface(self):
        """Test TaskManager base class interface."""
        manager = TaskManager(interval=10)
        self.assertEqual(manager.interval, 10)
        self.assertIsNotNone(manager.version)
        
        # Test abstract methods raise NotImplementedError
        with self.assertRaises(NotImplementedError):
            manager.install()
        with self.assertRaises(NotImplementedError):
            manager.uninstall()
        with self.assertRaises(NotImplementedError):
            manager.is_installed()
    
    def test_status_method(self):
        """Test status method returns expected structure."""
        manager = TaskManager(interval=15)
        
        # Mock the is_installed method to avoid NotImplementedError
        with patch.object(manager, 'is_installed', return_value=False):
            status = manager.status()
            
            self.assertIn('installed', status)
            self.assertIn('interval', status)
            self.assertIn('version', status)
            self.assertIn('platform', status)
            self.assertEqual(status['interval'], 15)
            self.assertFalse(status['installed'])


class TestGetTaskManager(unittest.TestCase):
    """Test get_task_manager function."""

    @patch('ddns.task.IS_WINDOWS', True)
    @patch('ddns.task.IS_MACOS', False)
    @patch('ddns.task.IS_LINUX', False)
    def test_get_windows_task_manager(self):
        """Test getting Windows task manager."""
        with patch('ddns.task.schtasks.WindowsTaskManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            manager = get_task_manager(interval=7)
            mock_class.assert_called_once_with(7)
            self.assertEqual(manager, mock_instance)

    @patch('ddns.task.IS_WINDOWS', False)
    @patch('ddns.task.IS_MACOS', True)
    @patch('ddns.task.IS_LINUX', False)
    def test_get_macos_task_manager(self):
        """Test getting macOS task manager."""
        with patch('ddns.task.launchd.MacOSTaskManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            manager = get_task_manager(interval=3)
            mock_class.assert_called_once_with(3)
            self.assertEqual(manager, mock_instance)

    @patch('ddns.task.IS_WINDOWS', False)
    @patch('ddns.task.IS_MACOS', False)
    @patch('ddns.task.IS_LINUX', True)
    def test_get_linux_systemd_task_manager(self):
        """Test getting Linux systemd task manager."""
        with patch('ddns.task.systemd.SystemdTaskManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            manager = get_task_manager(interval=12)
            mock_class.assert_called_once_with(12)
            self.assertEqual(manager, mock_instance)

    @patch('ddns.task.IS_WINDOWS', False)
    @patch('ddns.task.IS_MACOS', False)
    @patch('ddns.task.IS_LINUX', True)
    def test_get_linux_cron_fallback(self):
        """Test getting Linux cron task manager as fallback."""
        with patch('ddns.task.systemd.SystemdTaskManager', side_effect=ImportError):
            with patch('ddns.task.cron.CronTaskManager') as mock_class:
                mock_instance = MagicMock()
                mock_class.return_value = mock_instance
                
                manager = get_task_manager(interval=8)
                mock_class.assert_called_once_with(8)
                self.assertEqual(manager, mock_instance)

    @patch('ddns.task.IS_WINDOWS', False)
    @patch('ddns.task.IS_MACOS', False)
    @patch('ddns.task.IS_LINUX', False)
    @patch('ddns.task.SYSTEM', 'freebsd')
    def test_get_generic_unix_task_manager(self):
        """Test getting generic Unix cron task manager."""
        with patch('ddns.task.cron.CronTaskManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            manager = get_task_manager(interval=6)
            mock_class.assert_called_once_with(6)
            self.assertEqual(manager, mock_instance)


class TestWindowsTaskManager(unittest.TestCase):
    """Test Windows task manager functionality."""

    def setUp(self):
        # Only test Windows functionality if we're on Windows or mocking
        with patch('ddns.task.schtasks.subprocess'):
            from ddns.task.schtasks import WindowsTaskManager
            self.manager = WindowsTaskManager(interval=5)

    @patch('ddns.task.schtasks.subprocess.check_output')
    def test_schtasks_success(self, mock_check_output):
        """Test successful schtasks command execution."""
        mock_check_output.return_value = "SUCCESS: The scheduled task was successfully created."
        
        success, output = self.manager._run_schtasks(['/Create', '/TN', 'Test'])
        
        self.assertTrue(success)
        self.assertIn("SUCCESS", output)
        mock_check_output.assert_called_once()

    @patch('ddns.task.schtasks.subprocess.check_output')
    def test_schtasks_failure(self, mock_check_output):
        """Test failed schtasks command execution."""
        from subprocess import CalledProcessError
        mock_check_output.side_effect = CalledProcessError(1, 'schtasks', output="ERROR: Access denied.")
        
        success, output = self.manager._run_schtasks(['/Create', '/TN', 'Test'])
        
        self.assertFalse(success)
        self.assertIn("ERROR", output)

    @patch('ddns.task.schtasks.WindowsTaskManager._run_schtasks')
    def test_install_success(self, mock_run_schtasks):
        """Test successful task installation."""
        mock_run_schtasks.return_value = (True, "SUCCESS: Task created.")
        
        result = self.manager.install()
        
        self.assertTrue(result)
        mock_run_schtasks.assert_called_once()

    @patch('ddns.task.schtasks.WindowsTaskManager._run_schtasks')
    def test_install_failure(self, mock_run_schtasks):
        """Test failed task installation."""
        mock_run_schtasks.return_value = (False, "ERROR: Access denied.")
        
        result = self.manager.install()
        
        self.assertFalse(result)

    @patch('ddns.task.schtasks.WindowsTaskManager._run_schtasks')
    def test_uninstall_success(self, mock_run_schtasks):
        """Test successful task uninstallation."""
        mock_run_schtasks.return_value = (True, "SUCCESS: Task deleted.")
        
        result = self.manager.uninstall()
        
        self.assertTrue(result)

    @patch('ddns.task.schtasks.WindowsTaskManager._run_schtasks')
    def test_uninstall_not_found(self, mock_run_schtasks):
        """Test uninstalling non-existent task (should succeed)."""
        mock_run_schtasks.return_value = (False, "ERROR: The system cannot find the file specified.")
        
        result = self.manager.uninstall()
        
        self.assertTrue(result)  # Not found is considered success for uninstall

    @patch('ddns.task.schtasks.WindowsTaskManager._run_schtasks')
    def test_is_installed_true(self, mock_run_schtasks):
        """Test checking if task is installed (true case)."""
        mock_run_schtasks.return_value = (True, "Task details...")
        
        result = self.manager.is_installed()
        
        self.assertTrue(result)

    @patch('ddns.task.schtasks.WindowsTaskManager._run_schtasks')
    def test_is_installed_false(self, mock_run_schtasks):
        """Test checking if task is installed (false case)."""
        mock_run_schtasks.return_value = (False, "ERROR: Task not found.")
        
        result = self.manager.is_installed()
        
        self.assertFalse(result)


class TestCronTaskManager(unittest.TestCase):
    """Test Cron task manager functionality."""

    def setUp(self):
        with patch('ddns.task.cron.subprocess'):
            from ddns.task.cron import CronTaskManager
            self.manager = CronTaskManager(interval=5)

    @patch('ddns.task.cron.subprocess.check_output')
    def test_get_current_crontab_success(self, mock_check_output):
        """Test getting current crontab successfully."""
        mock_check_output.return_value = "0 */5 * * * /usr/bin/test\n"
        
        crontab = self.manager._get_current_crontab()
        
        self.assertIn("test", crontab)

    @patch('ddns.task.cron.subprocess.check_output')
    def test_get_current_crontab_empty(self, mock_check_output):
        """Test getting empty crontab."""
        from subprocess import CalledProcessError
        mock_check_output.side_effect = CalledProcessError(1, 'crontab', output="no crontab for user")
        
        crontab = self.manager._get_current_crontab()
        
        self.assertEqual(crontab, "")

    def test_create_cron_command(self):
        """Test creating cron command line."""
        cmd = self.manager._create_cron_command("/path/to/config.json")
        
        self.assertIn("run.py", cmd)
        self.assertIn("/path/to/config.json", cmd)
        self.assertIn(">>", cmd)  # Output redirection

    def test_create_cron_line(self):
        """Test creating complete cron line."""
        line = self.manager._create_cron_line()
        
        self.assertIn("*/5", line)  # Default 5-minute interval
        self.assertIn("run.py", line)

    def test_remove_ddns_lines(self):
        """Test removing existing DDNS lines from crontab."""
        existing_crontab = """# Some other job
0 0 * * * /usr/bin/backup
# DDNS v1.0 - NewFuture/DDNS
*/5 * * * * python /path/to/ddns/run.py >> /var/log/ddns.log
# Another job
0 12 * * * /usr/bin/cleanup"""
        
        cleaned = self.manager._remove_ddns_lines(existing_crontab)
        
        self.assertNotIn("DDNS", cleaned)
        self.assertNotIn("ddns", cleaned)
        self.assertIn("backup", cleaned)
        self.assertIn("cleanup", cleaned)

    @patch('ddns.task.cron.CronTaskManager._get_current_crontab')
    @patch('ddns.task.cron.CronTaskManager._run_crontab')
    def test_install_success(self, mock_run_crontab, mock_get_crontab):
        """Test successful cron job installation."""
        mock_get_crontab.return_value = ""
        mock_run_crontab.return_value = (True, "crontab installed")
        
        result = self.manager.install()
        
        self.assertTrue(result)
        mock_run_crontab.assert_called_once()

    @patch('ddns.task.cron.CronTaskManager._get_current_crontab')
    @patch('ddns.task.cron.CronTaskManager._run_crontab')
    def test_uninstall_success(self, mock_run_crontab, mock_get_crontab):
        """Test successful cron job uninstallation."""
        mock_get_crontab.return_value = "# DDNS v1.0\n*/5 * * * * ddns"
        mock_run_crontab.return_value = (True, "crontab updated")
        
        result = self.manager.uninstall()
        
        self.assertTrue(result)

    def test_is_installed_true(self):
        """Test checking if cron job is installed (true case)."""
        with patch.object(self.manager, '_get_current_crontab', return_value="# DDNS v1.0\n*/5 * * * * ddns"):
            result = self.manager.is_installed()
            self.assertTrue(result)

    def test_is_installed_false(self):
        """Test checking if cron job is installed (false case)."""
        with patch.object(self.manager, '_get_current_crontab', return_value="0 0 * * * backup"):
            result = self.manager.is_installed()
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()