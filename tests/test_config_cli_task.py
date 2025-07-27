# coding=utf-8
"""
Unit tests for ddns task subcommand functionality
@author: GitHub Copilot
"""
from __init__ import unittest
import sys
import io
from unittest.mock import patch
from ddns.config.cli import load_config


class TestTaskSubcommand(unittest.TestCase):
    """Test task subcommand functionality"""

    def setUp(self):
        encode = sys.stdout.encoding
        if encode is not None and encode.lower() != "utf-8" and hasattr(sys.stdout, "buffer"):
            # 兼容windows 和部分ASCII编码的老旧系统
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

        self.original_argv = sys.argv[:]

    def tearDown(self):
        sys.argv = self.original_argv

    def test_task_subcommand_help(self):
        """Test task subcommand help parsing"""
        sys.argv = ["ddns", "task", "--help"]

        # Test that SystemExit is raised with help
        with self.assertRaises(SystemExit) as cm:
            load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

        # Help should exit with code 0
        self.assertEqual(cm.exception.code, 0)

    def test_task_subcommand_status(self):
        """Test task subcommand status parsing"""
        sys.argv = ["ddns", "task", "--status"]

        # Mock the task.get_status function to avoid actual system operations
        with patch("ddns.config.cli.task.get_status") as mock_get_status:
            mock_get_status.return_value = {
                "installed": True,
                "scheduler": "schtasks",
                "system": "windows",
                "interval": 5,
                "config_path": None,
                "running_status": "unknown",
            }

            with patch("ddns.config.cli._handle_task_command") as mock_handle:

                def capture_args(args):
                    self.captured_basic_status_args = args

                mock_handle.side_effect = capture_args

                try:
                    load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
                except SystemExit:
                    pass

                # Verify the captured arguments
                args = self.captured_basic_status_args
                self.assertTrue(args["status"])

    def test_task_subcommand_install(self):
        """Test task subcommand install parsing"""
        sys.argv = ["ddns", "task", "--install", "10", "--config", "test.json"]

        # Mock the task.install function to avoid actual system operations
        with patch("ddns.config.cli.task.install") as mock_install:
            mock_install.return_value = True

            with patch("ddns.config.cli._handle_task_command") as mock_handle:

                def capture_args(args):
                    self.captured_basic_install_args = args

                mock_handle.side_effect = capture_args

                try:
                    load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
                except SystemExit:
                    pass

                # Verify the captured arguments
                args = self.captured_basic_install_args
                self.assertEqual(args["install"], 10)
                self.assertEqual(args["config"], ["test.json"])

    def test_task_subcommand_enable(self):
        """Test task subcommand enable parsing"""
        sys.argv = ["ddns", "task", "--enable"]

        # Mock the task.enable function
        with patch("ddns.config.cli.task.enable") as mock_enable:
            mock_enable.return_value = True

            with patch("ddns.config.cli._handle_task_command") as mock_handle:

                def capture_args(args):
                    self.captured_enable_args = args

                mock_handle.side_effect = capture_args

                try:
                    load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
                except SystemExit:
                    pass

                # Verify the captured arguments
                args = self.captured_enable_args
                self.assertTrue(args["enable"])

    def test_task_subcommand_disable(self):
        """Test task subcommand disable parsing"""
        sys.argv = ["ddns", "task", "--disable"]

        # Mock the task.disable function
        with patch("ddns.config.cli.task.disable") as mock_disable:
            mock_disable.return_value = True

            with patch("ddns.config.cli._handle_task_command") as mock_handle:

                def capture_args(args):
                    self.captured_disable_args = args

                mock_handle.side_effect = capture_args

                try:
                    load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
                except SystemExit:
                    pass

                # Verify the captured arguments
                args = self.captured_disable_args
                self.assertTrue(args["disable"])

    def test_task_subcommand_delete(self):
        """Test task subcommand delete/uninstall parsing"""
        sys.argv = ["ddns", "task", "--uninstall"]

        # Mock the task operations to avoid actual system operations
        with patch("ddns.config.cli.task.uninstall") as mock_uninstall:
            mock_uninstall.return_value = True

            with patch("ddns.config.cli._handle_task_command") as mock_handle:

                def capture_args(args):
                    self.captured_delete_args = args

                mock_handle.side_effect = capture_args

                try:
                    load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
                except SystemExit:
                    pass

                # Verify the captured arguments
                args = self.captured_delete_args
                self.assertTrue(args["uninstall"])

    def test_task_subcommand_force_install(self):
        """Test task subcommand install parsing with custom interval"""
        sys.argv = ["ddns", "task", "--install", "5"]

        # Mock the task.install function
        with patch("ddns.config.cli.task.install") as mock_install:
            mock_install.return_value = True

            with patch("ddns.config.cli._handle_task_command") as mock_handle:

                def capture_args(args):
                    self.captured_force_args = args

                mock_handle.side_effect = capture_args

                try:
                    load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
                except SystemExit:
                    pass

                # Verify the captured arguments
                args = self.captured_force_args
                self.assertEqual(args["install"], 5)

    def test_task_subcommand_with_ddns_args(self):
        """Test task subcommand accepts same arguments as main DDNS command"""
        sys.argv = [
            "ddns",
            "task",
            "--install",
            "10",
            "--config",
            "test.json",
            "--proxy",
            "http://proxy.example.com:8080",
            "--debug",
            "--ttl",
            "300",
        ]

        # Mock the task.install function to avoid actual system operations
        with patch("ddns.config.cli.task.install") as mock_install:
            mock_install.return_value = True

            # Mock _handle_task_command directly to capture its behavior
            with patch("ddns.config.cli._handle_task_command") as mock_handle:

                def capture_args(args):
                    # Save the args for verification
                    self.captured_args = args

                mock_handle.side_effect = capture_args

                try:
                    load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
                except SystemExit:
                    # Expected due to task command execution
                    pass

                # Verify that _handle_task_command was called
                mock_handle.assert_called_once()

                # Verify the captured arguments
                args = self.captured_args
                self.assertEqual(args["install"], 10)
                self.assertEqual(args["config"], ["test.json"])
                self.assertEqual(args["proxy"], ["http://proxy.example.com:8080"])
                self.assertTrue(args["debug"])
                self.assertEqual(args["ttl"], 300)

    def test_task_subcommand_with_provider_args(self):
        """Test task subcommand with provider-specific arguments"""
        sys.argv = [
            "ddns",
            "task",
            "--install",
            "5",
            "--config",
            "cloudflare.json",
            "--dns",
            "cloudflare",
            "--token",
            "test-token",
            "--id",
            "test-id",
        ]

        # Mock the task.install function to avoid actual system operations
        with patch("ddns.config.cli.task.install") as mock_install:
            mock_install.return_value = True

            with patch("ddns.config.cli.sys.exit"):
                load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

                # Verify that install was called with correct arguments
                mock_install.assert_called_once()
                call_kwargs = mock_install.call_args[1]

                # Check interval
                self.assertEqual(call_kwargs["interval"], 5)

                # Check ddns_args contains provider arguments
                ddns_args = call_kwargs["ddns_args"]
                self.assertEqual(ddns_args["dns"], "cloudflare")
                self.assertEqual(ddns_args["token"], "test-token")
                self.assertEqual(ddns_args["id"], "test-id")
                self.assertEqual(ddns_args["config"], ["cloudflare.json"])

    def test_task_subcommand_status_with_ddns_args(self):
        """Test task status command doesn't need ddns_args but accepts other params"""
        sys.argv = ["ddns", "task", "--status", "--config", "test.json", "--debug"]

        # Mock the task.get_status function to avoid actual system operations
        with patch("ddns.config.cli.task.get_status") as mock_get_status:
            mock_get_status.return_value = {
                "installed": True,
                "scheduler": "schtasks",
                "system": "windows",
                "interval": 5,
                "config_path": "test.json",
                "running_status": "active",
            }

            with patch("ddns.config.cli._handle_task_command") as mock_handle:

                def capture_args(args):
                    self.captured_status_args = args

                mock_handle.side_effect = capture_args

                try:
                    load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
                except SystemExit:
                    pass

                # Verify the captured arguments include debug flag
                args = self.captured_status_args
                self.assertTrue(args["status"])
                self.assertTrue(args["debug"])
                self.assertEqual(args["config"], ["test.json"])


if __name__ == "__main__":
    unittest.main()
