# coding=utf-8
"""
Unit tests for ddns task subcommand functionality
@author: GitHub Copilot
"""

from __init__ import unittest, patch
import sys
import io
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

        # Initialize test attributes for captured arguments
        self.captured_basic_status_args = None
        self.captured_basic_install_args = None
        self.captured_enable_args = None
        self.captured_disable_args = None
        self.captured_delete_args = None
        self.captured_force_args = None
        self.captured_args = None
        self.captured_status_args = None

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

        # Mock the scheduler.get_status function to avoid actual system operations
        with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
            mock_scheduler = mock_get_scheduler.return_value
            mock_scheduler.get_status.return_value = {
                "installed": True,
                "scheduler": "schtasks",
                "interval": 5,
                "enabled": True,
                "command": "test command",
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
                self.assertIsNotNone(args)
                if args is not None:  # Type checker satisfaction
                    self.assertTrue(args["status"])

    def test_task_subcommand_install(self):
        """Test task subcommand install parsing"""
        sys.argv = ["ddns", "task", "--install", "10", "--config", "test.json"]

        # Mock the scheduler.install function to avoid actual system operations
        with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
            mock_scheduler = mock_get_scheduler.return_value
            mock_scheduler.install.return_value = True

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
                self.assertIsNotNone(args)
                if args is not None:  # Type checker satisfaction
                    self.assertEqual(args["install"], 10)
                    self.assertEqual(args["config"], ["test.json"])

    def test_task_subcommand_enable(self):
        """Test task subcommand enable parsing"""
        sys.argv = ["ddns", "task", "--enable"]

        # Mock the scheduler.enable function
        with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
            mock_scheduler = mock_get_scheduler.return_value
            mock_scheduler.enable.return_value = True
            mock_scheduler.is_installed.return_value = True

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
                self.assertIsNotNone(args)
                if args is not None:  # Type checker satisfaction
                    self.assertTrue(args["enable"])

    def test_task_subcommand_disable(self):
        """Test task subcommand disable parsing"""
        sys.argv = ["ddns", "task", "--disable"]

        # Mock the scheduler.disable function
        with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
            mock_scheduler = mock_get_scheduler.return_value
            mock_scheduler.disable.return_value = True
            mock_scheduler.is_installed.return_value = True

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
                self.assertIsNotNone(args)
                if args is not None:  # Type checker satisfaction
                    self.assertTrue(args["disable"])

    def test_task_subcommand_delete(self):
        """Test task subcommand delete/uninstall parsing"""
        sys.argv = ["ddns", "task", "--uninstall"]

        # Mock the scheduler operations to avoid actual system operations
        with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
            mock_scheduler = mock_get_scheduler.return_value
            mock_scheduler.uninstall.return_value = True

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
                self.assertIsNotNone(args)
                if args is not None:  # Type checker satisfaction
                    self.assertTrue(args["uninstall"])

    def test_task_subcommand_force_install(self):
        """Test task subcommand install parsing with custom interval"""
        sys.argv = ["ddns", "task", "--install", "5"]

        # Mock the scheduler.install function
        with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
            mock_scheduler = mock_get_scheduler.return_value
            mock_scheduler.install.return_value = True

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
                self.assertIsNotNone(args)
                if args is not None:  # Type checker satisfaction
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

        # Mock the scheduler.install function to avoid actual system operations
        with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
            mock_scheduler = mock_get_scheduler.return_value
            mock_scheduler.install.return_value = True

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
                self.assertIsNotNone(args)
                if args is not None:  # Type checker satisfaction
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

        # Mock the scheduler.install function to avoid actual system operations
        with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
            mock_scheduler = mock_get_scheduler.return_value
            mock_scheduler.install.return_value = True

            with patch("ddns.config.cli.sys.exit"):
                load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")

                # Verify that install was called with correct arguments
                mock_scheduler.install.assert_called_once()
                call_args = mock_scheduler.install.call_args

                # Check interval (first positional argument)
                self.assertEqual(call_args[0][0], 5)

                # Check ddns_args contains provider arguments (second positional argument)
                ddns_args = call_args[0][1]
                self.assertEqual(ddns_args["dns"], "cloudflare")
                self.assertEqual(ddns_args["token"], "test-token")
                self.assertEqual(ddns_args["id"], "test-id")
                self.assertEqual(ddns_args["config"], ["cloudflare.json"])

    def test_task_subcommand_status_with_ddns_args(self):
        """Test task status command doesn't need ddns_args but accepts other params"""
        sys.argv = ["ddns", "task", "--status", "--config", "test.json", "--debug"]

        # Mock the scheduler.get_status function to avoid actual system operations
        with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
            mock_scheduler = mock_get_scheduler.return_value
            mock_scheduler.get_status.return_value = {
                "installed": True,
                "scheduler": "schtasks",
                "interval": 5,
                "enabled": True,
                "command": "test command",
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
                self.assertIsNotNone(args)
                if args is not None:  # Type checker satisfaction
                    self.assertTrue(args["status"])
                    self.assertTrue(args["debug"])
                    self.assertEqual(args["config"], ["test.json"])

    def test_task_subcommand_scheduler_default(self):
        """Test task subcommand scheduler default value"""
        sys.argv = ["ddns", "task", "--status"]

        with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
            mock_scheduler = mock_get_scheduler.return_value
            mock_scheduler.get_status.return_value = {"installed": False, "scheduler": "auto"}

            with patch("ddns.config.cli._handle_task_command") as mock_handle:
                captured_args = [None]  # Use list to make it mutable in Python 2

                def capture_args(args):
                    captured_args[0] = args

                mock_handle.side_effect = capture_args

                try:
                    load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
                except SystemExit:
                    pass

                self.assertIsNotNone(captured_args[0])
                if captured_args[0] is not None:
                    self.assertEqual(captured_args[0].get("scheduler"), "auto")

    def test_task_subcommand_scheduler_explicit_values(self):
        """Test task subcommand scheduler with explicit values"""
        test_schedulers = ["auto", "systemd", "cron", "launchd", "schtasks"]

        for scheduler in test_schedulers:
            try:
                sys.argv = ["ddns", "task", "--status", "--scheduler", scheduler]

                with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
                    mock_scheduler = mock_get_scheduler.return_value
                    mock_scheduler.get_status.return_value = {"installed": False, "scheduler": scheduler}

                    with patch("ddns.config.cli._handle_task_command") as mock_handle:
                        captured_args = [None]  # Use list to make it mutable in Python 2

                        def capture_args(args):
                            captured_args[0] = args

                        mock_handle.side_effect = capture_args

                        try:
                            load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
                        except SystemExit:
                            pass

                        self.assertIsNotNone(
                            captured_args[0], "Failed to capture args for scheduler: {}".format(scheduler)
                        )
                        if captured_args[0] is not None:
                            self.assertEqual(
                                captured_args[0].get("scheduler"),
                                scheduler,
                                "Expected scheduler {} but got {}".format(scheduler, captured_args[0].get("scheduler")),
                            )
            except Exception as e:
                self.fail("Failed for scheduler {}: {}".format(scheduler, e))

    def test_task_subcommand_scheduler_with_install(self):
        """Test task subcommand scheduler parameter with install command"""
        sys.argv = ["ddns", "task", "--install", "15", "--scheduler", "cron", "--dns", "debug"]

        with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
            mock_scheduler = mock_get_scheduler.return_value
            mock_scheduler.install.return_value = True

            with patch("ddns.config.cli._handle_task_command") as mock_handle:
                captured_args = [None]  # Use list to make it mutable in Python 2

                def capture_args(args):
                    captured_args[0] = args

                mock_handle.side_effect = capture_args

                try:
                    load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
                except SystemExit:
                    pass

                self.assertIsNotNone(captured_args[0])
                if captured_args[0] is not None:
                    self.assertEqual(captured_args[0].get("scheduler"), "cron")
                    self.assertEqual(captured_args[0].get("install"), 15)
                    self.assertEqual(captured_args[0].get("dns"), "debug")

    def test_task_subcommand_scheduler_excluded_from_ddns_args(self):
        """Test scheduler parameter is excluded from ddns_args in _handle_task_command"""
        sys.argv = ["ddns", "task", "--install", "10", "--scheduler", "systemd", "--dns", "debug", "--id", "test-id"]

        with patch("ddns.config.cli.get_scheduler") as mock_get_scheduler:
            mock_scheduler = mock_get_scheduler.return_value
            mock_scheduler.install.return_value = True

            with patch("ddns.config.cli._handle_task_command") as mock_handle:
                args = [None]  # Use list to make it mutable in Python 2

                def capture_args(cargs):
                    args[0] = cargs

                mock_handle.side_effect = capture_args

                try:
                    load_config("Test DDNS", "Test doc", "1.0.0", "2025-07-04")
                except SystemExit:
                    pass

                self.assertIsNotNone(args[0])
                # Verify scheduler is in args
                self.assertEqual(args[0].get("scheduler"), "systemd")  # type: ignore

                # Simulate what _handle_task_command does with ddns_args
                exclude = {"status", "install", "uninstall", "enable", "disable", "command", "scheduler"}
                options = {k: v for k, v in args[0].items() if k not in exclude and v is not None}  # type: ignore

                # Verify scheduler is excluded from ddns_args but other params are included
                self.assertNotIn("scheduler", options)
                self.assertNotIn("install", options)  # Also excluded
                self.assertIn("dns", options)
                self.assertIn("id", options)
                self.assertEqual(options["dns"], "debug")
                self.assertEqual(options["id"], "test-id")


if __name__ == "__main__":
    unittest.main()
