# -*- coding:utf-8 -*-
"""
Unit tests for ddns.scheduler.schtasks module
@author: NewFuture
"""
import platform
from __init__ import unittest, patch
from ddns.scheduler.schtasks import SchtasksScheduler


class TestSchtasksScheduler(unittest.TestCase):
    """Test SchtasksScheduler functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.scheduler = SchtasksScheduler()

    def test_task_name_property(self):
        """Test task name property"""
        expected_name = "DDNS"
        self.assertEqual(self.scheduler.NAME, expected_name)

    @patch.object(SchtasksScheduler, '_run_command')
    def test_get_status_installed_enabled(self, mock_run_command):
        """Test get_status when task is installed and enabled"""
        # Mock XML output from schtasks query
        xml_output = """<?xml version="1.0" encoding="UTF-16"?>
        <Task>
            <Settings>
                <Enabled>true</Enabled>
            </Settings>
            <Triggers>
                <TimeTrigger>
                    <Repetition>
                        <Interval>PT5M</Interval>
                    </Repetition>
                </TimeTrigger>
            </Triggers>
            <Actions>
                <Exec>
                    <Command>wscript.exe</Command>
                    <Arguments>"test.vbs"</Arguments>
                </Exec>
            </Actions>
        </Task>"""

        mock_run_command.return_value = xml_output

        status = self.scheduler.get_status()

        expected_status = {
            "scheduler": "schtasks",
            "installed": True,
            "enabled": True,
            "interval": 5,
            "command": 'wscript.exe "test.vbs"',
        }

        # Check main fields
        self.assertEqual(status["scheduler"], expected_status["scheduler"])
        self.assertEqual(status["enabled"], expected_status["enabled"])
        self.assertEqual(status["interval"], expected_status["interval"])

    @patch.object(SchtasksScheduler, '_run_command')
    def test_get_status_not_installed(self, mock_run_command):
        """Test get_status when task is not installed"""
        # Mock _run_command to return None (task not found)
        mock_run_command.return_value = None

        status = self.scheduler.get_status()

        expected_status = {
            "scheduler": "schtasks",
            "installed": False,
        }

        # Check main fields - only scheduler and installed are included when task not found
        self.assertEqual(status["scheduler"], expected_status["scheduler"])
        self.assertEqual(status["installed"], expected_status["installed"])
        # When task is not installed, enabled and interval are not included in status

    @patch.object(SchtasksScheduler, '_run_command')
    def test_is_installed_true(self, mock_run_command):
        """Test is_installed returns True when task exists"""
        mock_run_command.return_value = "TaskName: DDNS\nStatus: Ready"

        result = self.scheduler.is_installed()
        self.assertTrue(result)

    @patch.object(SchtasksScheduler, '_run_command')
    def test_is_installed_false(self, mock_run_command):
        """Test is_installed returns False when task doesn't exist"""
        mock_run_command.return_value = None

        result = self.scheduler.is_installed()
        self.assertFalse(result)

    @patch.object(SchtasksScheduler, '_schtasks')
    @patch.object(SchtasksScheduler, '_create_vbs_script')
    def test_install_success(self, mock_vbs, mock_schtasks):
        """Test successful installation"""
        mock_vbs.return_value = "test.vbs"
        mock_schtasks.return_value = True

        result = self.scheduler.install(5, {"dns": "debug", "ipv4": ["test.com"]})

        self.assertTrue(result)
        mock_schtasks.assert_called_once()
        mock_vbs.assert_called_once()

    @patch.object(SchtasksScheduler, '_schtasks')
    def test_uninstall_success(self, mock_schtasks):
        """Test successful uninstall"""
        mock_schtasks.return_value = True

        result = self.scheduler.uninstall()
        self.assertTrue(result)
        mock_schtasks.assert_called_once()

    @patch.object(SchtasksScheduler, '_schtasks')
    def test_enable_success(self, mock_schtasks):
        """Test successful enable"""
        mock_schtasks.return_value = True

        result = self.scheduler.enable()
        self.assertTrue(result)
        mock_schtasks.assert_called_once()

    @patch.object(SchtasksScheduler, '_schtasks')
    def test_disable_success(self, mock_schtasks):
        """Test successful disable"""
        mock_schtasks.return_value = True

        result = self.scheduler.disable()
        self.assertTrue(result)
        mock_schtasks.assert_called_once()

    def test_build_ddns_command(self):
        """Test _build_ddns_command functionality"""
        ddns_args = {"dns": "debug", "ipv4": ["test.example.com"], "config": ["config.json"], "ttl": 300}

        command = self.scheduler._build_ddns_command(ddns_args)

        self.assertIsInstance(command, str)
        self.assertIn("python", command.lower())
        self.assertIn("ddns", command)
        self.assertIn("debug", command)
        self.assertIn("test.example.com", command)

    def test_xml_extraction(self):
        """Test _extract_xml functionality"""
        xml_text = "<Settings><Enabled>true</Enabled></Settings>"

        result = self.scheduler._extract_xml(xml_text, "Enabled")
        self.assertEqual(result, "true")

        # Test non-existent tag
        result = self.scheduler._extract_xml(xml_text, "NonExistent")
        self.assertIsNone(result)

    @unittest.skipUnless(platform.system().lower() == "windows", "Windows-specific test")
    def test_real_schtasks_availability(self):
        """Test if schtasks is available on Windows systems"""
        if platform.system().lower() == "windows":
            # On Windows, test basic status call
            status = self.scheduler.get_status()
            self.assertIsInstance(status, dict)
            self.assertIn("scheduler", status)
            self.assertEqual(status["scheduler"], "schtasks")
        else:
            self.skipTest("Windows-specific test")

    @unittest.skipUnless(platform.system().lower() == "windows", "Windows-specific test")
    def test_real_schtasks_integration(self):
        """Test real schtasks integration with actual system calls"""
        if platform.system().lower() != "windows":
            self.skipTest("Windows-specific test")

        # Test real schtasks query for non-existent task
        status = self.scheduler.get_status()
        self.assertIsInstance(status, dict)
        self.assertEqual(status["scheduler"], "schtasks")
        self.assertIsInstance(status["installed"], bool)

        # Test schtasks help (safe read-only operation)
        # Note: We rely on the scheduler's _run_command method for actual subprocess calls
        # since it has proper timeout and error handling
        help_result = self.scheduler._run_command(["schtasks", "/?"])
        if help_result:
            self.assertIn("schtasks", help_result.lower())

    @unittest.skipUnless(platform.system().lower() == "windows", "Windows-specific test")
    def test_real_scheduler_methods_safe(self):
        """Test real scheduler methods that don't modify system state"""
        if platform.system().lower() != "windows":
            self.skipTest("Windows-specific test")

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

        # If task is installed, additional keys should be present
        if status.get("installed", False):
            additional_keys = ["enabled", "interval"]
            for key in additional_keys:
                self.assertIn(key, status)

        # Test XML extraction utility
        test_xml = "<Settings><Enabled>true</Enabled></Settings>"
        enabled = self.scheduler._extract_xml(test_xml, "Enabled")
        self.assertEqual(enabled, "true")

        # Test VBS script generation
        ddns_args = {"dns": "debug", "ipv4": ["test.example.com"]}
        vbs_path = self.scheduler._create_vbs_script(ddns_args)
        self.assertIsInstance(vbs_path, str)
        self.assertTrue(vbs_path.endswith(".vbs"))
        self.assertIn("ddns_silent.vbs", vbs_path)

        # Test enable/disable without actual installation (should handle gracefully)
        # These operations will fail if task doesn't exist, but should return boolean
        enable_result = self.scheduler.enable()
        self.assertIsInstance(enable_result, bool)

        disable_result = self.scheduler.disable()
        self.assertIsInstance(disable_result, bool)


if __name__ == "__main__":
    unittest.main()
