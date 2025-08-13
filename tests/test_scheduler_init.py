# -*- coding:utf-8 -*-
"""
Test scheduler initialization and real functionality
@author: NewFuture
"""

import os
import platform
import subprocess

from __init__ import unittest

from ddns.scheduler import get_scheduler


class TestSchedulerInit(unittest.TestCase):
    """Test scheduler initialization and functionality"""

    def test_auto_detection_returns_scheduler(self):
        """Test that auto detection returns a valid scheduler instance"""
        scheduler = get_scheduler("auto")
        self.assertIsNotNone(scheduler)
        # On Windows, should return SchtasksScheduler
        if platform.system().lower() == "windows":
            from ddns.scheduler.schtasks import SchtasksScheduler

            self.assertIsInstance(scheduler, SchtasksScheduler)

    def test_explicit_scheduler_selection(self):
        """Test explicit scheduler selection"""
        test_cases = [
            ("systemd", "SystemdScheduler"),
            ("cron", "CronScheduler"),
            ("launchd", "LaunchdScheduler"),
            ("schtasks", "SchtasksScheduler"),
        ]

        for scheduler_type, expected_class_name in test_cases:
            try:
                scheduler = get_scheduler(scheduler_type)
                self.assertIsNotNone(scheduler, "Failed to get scheduler for type: {}".format(scheduler_type))
                self.assertEqual(
                    scheduler.__class__.__name__,
                    expected_class_name,
                    "Expected {} but got {} for scheduler type: {}".format(
                        expected_class_name, scheduler.__class__.__name__, scheduler_type
                    ),
                )
            except Exception as e:
                self.fail("Failed for scheduler_type {}: {}".format(scheduler_type, e))

    def test_invalid_scheduler_raises_error(self):
        """Test that invalid scheduler raises ValueError"""
        with self.assertRaises(ValueError):
            get_scheduler("invalid_scheduler")

    def test_auto_and_none_equivalent(self):
        """Test that auto and None return the same scheduler type"""
        auto_scheduler = get_scheduler("auto")
        none_scheduler = get_scheduler(None)
        self.assertEqual(type(auto_scheduler), type(none_scheduler))


class TestSchedulerRealFunctionality(unittest.TestCase):
    """Test real scheduler functionality when supported on current system"""

    def setUp(self):
        """Set up test environment"""
        self.current_system = platform.system().lower()
        self.scheduler = get_scheduler("auto")
        self.test_ddns_args = {"dns": "debug", "ipv4": ["test.example.com"], "config": []}

    def _is_command_available(self, command):
        """Check if a command is available on the current system"""
        try:
            if self.current_system == "windows":
                result = subprocess.run(["where", command], capture_output=True, check=False, shell=True)
            else:
                result = subprocess.run(["which", command], capture_output=True, check=False)
            return result.returncode == 0
        except Exception:
            return False

    def _is_scheduler_available(self, scheduler_name):
        """Check if a scheduler is available on the current system"""
        try:
            if scheduler_name == "systemd":
                # Check if systemd is running and we have systemctl
                return (
                    self.current_system == "linux"
                    and os.path.exists("/proc/1/comm")
                    and self._is_command_available("systemctl")
                )
            elif scheduler_name == "cron":
                # Check if cron is available
                return self.current_system in ["linux", "darwin"] and self._is_command_available("crontab")
            elif scheduler_name == "launchd":
                # Check if we're on macOS and launchctl is available
                return self.current_system == "darwin" and self._is_command_available("launchctl")
            elif scheduler_name == "schtasks":
                # Check if we're on Windows and schtasks is available
                return self.current_system == "windows" and self._is_command_available("schtasks")
        except Exception:
            return False
        return False

    def test_scheduler_status_call(self):
        """Test that get_status() works on current system"""
        try:
            status = self.scheduler.get_status()
            self.assertIsInstance(status, dict)

            # Basic keys should always be present
            basic_keys = ["installed", "scheduler"]
            for key in basic_keys:
                self.assertIn(key, status, "Status missing basic key: {}".format(key))

            # Scheduler name should be a valid string
            self.assertIsInstance(status["scheduler"], str)
            self.assertGreater(len(status["scheduler"]), 0)

            # Additional keys are only present when installed
            if status.get("installed", False):
                additional_keys = ["enabled"]
                for key in additional_keys:
                    self.assertIn(key, status, "Status missing key for installed scheduler: {}".format(key))
        except Exception as e:
            self.fail("get_status() failed: {}".format(e))

    def test_scheduler_is_installed_call(self):
        """Test that is_installed() works on current system"""
        try:
            installed = self.scheduler.is_installed()
            self.assertIsInstance(installed, bool)
        except Exception as e:
            self.fail("is_installed() failed: {}".format(e))

    def test_scheduler_build_ddns_command(self):
        """Test that _build_ddns_command works correctly"""
        try:
            command = self.scheduler._build_ddns_command(self.test_ddns_args)
            self.assertIsInstance(command, list)
            command_str = " ".join(command)
            self.assertIn("python", command_str.lower())
            self.assertIn("ddns", command_str)
            # Should contain debug provider
            self.assertIn("debug", command_str)
        except Exception as e:
            self.fail("_build_ddns_command() failed: {}".format(e))

    @unittest.skipUnless(platform.system().lower() == "windows", "Windows-specific test")
    def test_windows_scheduler_real_calls(self):
        """Test Windows scheduler real functionality"""
        if not self._is_scheduler_available("schtasks"):
            self.skipTest("schtasks not available")

        from ddns.scheduler.schtasks import SchtasksScheduler

        scheduler = SchtasksScheduler()

        # Test status call
        status = scheduler.get_status()
        self.assertIsInstance(status, dict)
        self.assertEqual(status["scheduler"], "schtasks")

        # Test is_installed call
        installed = scheduler.is_installed()
        self.assertIsInstance(installed, bool)

        # Test command building
        command = scheduler._build_ddns_command(self.test_ddns_args)
        self.assertIsInstance(command, list)
        command_str = " ".join(command)
        self.assertIn("python", command_str.lower())

    @unittest.skipUnless(platform.system().lower() == "linux", "Linux-specific test")
    def test_systemd_scheduler_real_calls(self):
        """Test systemd scheduler real functionality"""
        if not self._is_scheduler_available("systemd"):
            self.skipTest("systemd not available")

        from ddns.scheduler.systemd import SystemdScheduler

        scheduler = SystemdScheduler()

        # Test status call
        status = scheduler.get_status()
        self.assertIsInstance(status, dict)
        self.assertEqual(status["scheduler"], "systemd")

        # Test is_installed call
        installed = scheduler.is_installed()
        self.assertIsInstance(installed, bool)

    @unittest.skipUnless(platform.system().lower() in ["linux", "darwin"], "Unix-specific test")
    def test_cron_scheduler_real_calls(self):
        """Test cron scheduler real functionality"""
        if not self._is_scheduler_available("cron"):
            self.skipTest("cron not available")

        from ddns.scheduler.cron import CronScheduler

        scheduler = CronScheduler()

        # Test status call
        status = scheduler.get_status()
        self.assertIsInstance(status, dict)
        self.assertEqual(status["scheduler"], "cron")

        # Test is_installed call
        installed = scheduler.is_installed()
        self.assertIsInstance(installed, bool)

    @unittest.skipUnless(platform.system().lower() == "darwin", "macOS-specific test")
    def test_launchd_scheduler_real_calls(self):
        """Test launchd scheduler real functionality"""
        if not self._is_scheduler_available("launchd"):
            self.skipTest("launchctl not available")

        from ddns.scheduler.launchd import LaunchdScheduler

        scheduler = LaunchdScheduler()

        # Test status call
        status = scheduler.get_status()
        self.assertIsInstance(status, dict)
        self.assertEqual(status["scheduler"], "launchd")

        # Test is_installed call
        installed = scheduler.is_installed()
        self.assertIsInstance(installed, bool)

    def test_scheduler_methods_exist(self):
        """Test that required scheduler methods exist and are callable"""
        required_methods = ["get_status", "is_installed", "install", "uninstall", "enable", "disable"]

        for method_name in required_methods:
            try:
                self.assertTrue(
                    hasattr(self.scheduler, method_name), "Scheduler missing method: {}".format(method_name)
                )
                method = getattr(self.scheduler, method_name)
                self.assertTrue(callable(method), "Scheduler method not callable: {}".format(method_name))
            except Exception as e:
                self.fail("Failed for method {}: {}".format(method_name, e))

    def test_scheduler_safe_operations(self):
        """Test scheduler operations that are safe to run (won't modify system)"""
        # Test status (safe operation)
        status = self.scheduler.get_status()
        self.assertIsInstance(status, dict)

        # Test is_installed (safe operation)
        installed = self.scheduler.is_installed()
        self.assertIsInstance(installed, bool)

        # Test command building (safe operation)
        command = self.scheduler._build_ddns_command(self.test_ddns_args)
        self.assertIsInstance(command, list)
        self.assertGreater(len(command), 0)

    def test_scheduler_real_integration(self):
        """Test real scheduler integration - comprehensive test for current platform"""
        # Get current platform scheduler
        current_scheduler = get_scheduler("auto")

        # Test basic properties
        self.assertIsNotNone(current_scheduler)
        self.assertTrue(hasattr(current_scheduler, "get_status"))
        self.assertTrue(hasattr(current_scheduler, "is_installed"))

        # Test status method returns valid structure
        status = current_scheduler.get_status()
        self.assertIsInstance(status, dict)
        self.assertIn("scheduler", status)
        self.assertIn("installed", status)

        # Additional keys are only present when installed
        if status.get("installed", False):
            self.assertIn("enabled", status)

        # Test is_installed returns boolean
        installed = current_scheduler.is_installed()
        self.assertIsInstance(installed, bool)

        # Test command building with various args
        test_args = {
            "dns": "debug",
            "ipv4": ["test.domain.com"],
            "ipv6": ["test6.domain.com"],
            "config": ["config.json"],
            "ttl": 600,
        }
        command = current_scheduler._build_ddns_command(test_args)
        self.assertIsInstance(command, list)
        self.assertGreater(len(command), 0)

        # Verify command contains expected elements
        command_str = " ".join(command)
        self.assertIn("python", command_str.lower())
        self.assertIn("debug", command_str)
        self.assertIn("test.domain.com", command_str)


if __name__ == "__main__":
    unittest.main()
