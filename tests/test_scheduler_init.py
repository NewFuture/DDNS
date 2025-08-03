# -*- coding:utf-8 -*-
"""
Test scheduler auto detection logic
@author: NewFuture
"""
from tests import unittest
from ddns.scheduler import get_scheduler


class TestSchedulerAutoDetection(unittest.TestCase):
    """Test scheduler auto detection functionality"""

    def test_auto_detection_returns_scheduler(self):
        """Test that auto detection returns a valid scheduler instance"""
        scheduler = get_scheduler("auto")
        self.assertIsNotNone(scheduler)
        # On Windows, should return WindowsScheduler
        import platform
        if platform.system().lower() == "windows":
            from ddns.scheduler.windows import WindowsScheduler
            self.assertIsInstance(scheduler, WindowsScheduler)

    def test_explicit_scheduler_selection(self):
        """Test explicit scheduler selection"""
        test_cases = [
            ("systemd", "SystemdScheduler"),
            ("cron", "CronScheduler"),
            ("launchd", "LaunchdScheduler"),
            ("schtasks", "WindowsScheduler")
        ]
        
        for scheduler_type, expected_class_name in test_cases:
            with self.subTest(scheduler_type=scheduler_type):
                scheduler = get_scheduler(scheduler_type)
                self.assertIsNotNone(scheduler)
                self.assertEqual(scheduler.__class__.__name__, expected_class_name)

    def test_invalid_scheduler_raises_error(self):
        """Test that invalid scheduler raises ValueError"""
        with self.assertRaises(ValueError):
            get_scheduler("invalid_scheduler")

    def test_auto_and_none_equivalent(self):
        """Test that auto and None return the same scheduler type"""
        auto_scheduler = get_scheduler("auto")
        none_scheduler = get_scheduler(None)
        self.assertEqual(type(auto_scheduler), type(none_scheduler))


if __name__ == "__main__":
    unittest.main()
