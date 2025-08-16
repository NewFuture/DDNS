# -*- coding:utf-8 -*-
"""
Systemd timer-based task scheduler for Linux
@author: NewFuture
"""

import os
import re

from ..util.fileio import read_file_safely, write_file
from ..util.try_run import try_run
from ._base import BaseScheduler

try:  # python 3
    PermissionError  # type: ignore
except NameError:  # python 2 doesn't have PermissionError, use OSError instead
    PermissionError = IOError


class SystemdScheduler(BaseScheduler):
    """Systemd timer-based task scheduler for Linux"""

    SERVICE_NAME = "ddns.service"
    TIMER_NAME = "ddns.timer"
    SERVICE_PATH = "/etc/systemd/system/ddns.service"
    TIMER_PATH = "/etc/systemd/system/ddns.timer"

    def _systemctl(self, *args):
        """Run systemctl command and return success status"""
        result = try_run(["systemctl"] + list(args), logger=self.logger)
        return result is not None

    def is_installed(self):
        """Check if systemd timer files exist"""
        return os.path.exists(self.SERVICE_PATH) and os.path.exists(self.TIMER_PATH)

    def get_status(self):
        """Get comprehensive status information"""
        installed = self.is_installed()
        status = {"scheduler": "systemd", "installed": installed}
        if not installed:
            return status

        # Check if timer is enabled
        result = try_run(["systemctl", "is-enabled", self.TIMER_NAME], logger=self.logger)
        status["enabled"] = bool(result and result.strip() == "enabled")

        # Extract interval from timer file
        timer_content = read_file_safely(self.TIMER_PATH) or ""
        match = re.search(r"OnUnitActiveSec=(\d+)m", timer_content)
        status["interval"] = int(match.group(1)) if match else None

        # Extract command and description from service file
        service_content = read_file_safely(self.SERVICE_PATH) or ""
        match = re.search(r"ExecStart=(.+)", service_content)
        status["command"] = match.group(1).strip() if match else None
        desc_match = re.search(r"Description=(.+)", service_content)
        status["description"] = desc_match.group(1).strip() if desc_match else None

        return status

    def install(self, interval, ddns_args=None):
        """Install systemd timer with specified interval"""
        ddns_commands = self._build_ddns_command(ddns_args)
        # Convert array to properly quoted command string for ExecStart
        ddns_command = self._quote_command_array(ddns_commands)
        work_dir = os.getcwd()
        description = self._get_description()

        # Create service file content
        service_content = u"""[Unit]
Description={}
After=network.target

[Service]
Type=oneshot
WorkingDirectory={}
ExecStart={}
""".format(description, work_dir, ddns_command)  # fmt: skip

        # Create timer file content
        timer_content = u"""[Unit]
Description=DDNS automatic IP update timer
Requires={}

[Timer]
OnUnitActiveSec={}m
Unit={}

[Install]
WantedBy=multi-user.target
""".format(self.SERVICE_NAME, interval, self.SERVICE_NAME)  # fmt: skip

        try:
            # Write service and timer files
            write_file(self.SERVICE_PATH, service_content)
            write_file(self.TIMER_PATH, timer_content)
        except PermissionError as e:
            self.logger.debug("Permission denied when writing systemd files: %s", e)
            print("Permission denied. Please run as root or use sudo.")
            print("or use cron scheduler (with --scheduler=cron) instead.")
            return False
        except Exception as e:
            self.logger.error("Failed to write systemd files: %s", e)
            return False

        if self._systemctl("daemon-reload") and self._systemctl("enable", self.TIMER_NAME):
            self._systemctl("start", self.TIMER_NAME)
            return True
        else:
            self.logger.error("Failed to enable/start systemd timer")
            return False

    def uninstall(self):
        """Uninstall systemd timer and service"""
        self.disable()  # Stop and disable timer
        # Remove systemd files
        try:
            os.remove(self.SERVICE_PATH)
            os.remove(self.TIMER_PATH)
            self._systemctl("daemon-reload")  # Reload systemd configuration
            return True

        except PermissionError as e:
            self.logger.debug("Permission denied when removing systemd files: %s", e)
            print("Permission denied. Please run as root or use sudo.")
            return False
        except Exception as e:
            self.logger.error("Failed to remove systemd files: %s", e)
            return False

    def enable(self):
        """Enable and start systemd timer"""
        return self._systemctl("enable", self.TIMER_NAME) and self._systemctl("start", self.TIMER_NAME)

    def disable(self):
        """Disable and stop systemd timer"""
        self._systemctl("stop", self.TIMER_NAME)
        return self._systemctl("disable", self.TIMER_NAME)
