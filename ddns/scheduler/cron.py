# -*- coding:utf-8 -*-
"""
Cron-based task scheduler for Unix-like systems
@author: NewFuture
"""

import os
import subprocess
import tempfile

from ..util.fileio import write_file
from ..util.try_run import try_run
from ._base import BaseScheduler


class CronScheduler(BaseScheduler):
    """Cron-based task scheduler for Unix-like systems"""

    SCHEDULER_NAME = "cron"

    KEY = "# DDNS:"

    def _update_crontab(self, lines):  # type: (list[str]) -> bool
        """Update crontab with new content"""
        try:
            temp_path = tempfile.mktemp(suffix=".cron")
            write_file(temp_path, u"\n".join(lines) + u"\n")  # fmt: skip
            subprocess.check_call(["crontab", temp_path])
            os.unlink(temp_path)
            return True
        except Exception as e:
            self.logger.error("Failed to update crontab: %s", e)
            return False

    def is_installed(self, crontab_content=None):  # type: (str | None) -> bool
        result = crontab_content or try_run(["crontab", "-l"], logger=self.logger) or ""
        return self.KEY in result

    def get_status(self):
        status = {"scheduler": "cron", "installed": False}  # type: dict[str, str | bool | int | None]
        # Get crontab content once and reuse it for all checks
        crontab_content = try_run(["crontab", "-l"], logger=self.logger) or ""
        lines = crontab_content.splitlines()
        line = next((i for i in lines if self.KEY in i), "").strip()

        if line:  # Task is installed
            status["installed"] = True
            status["enabled"] = bool(line and not line.startswith("#"))
        else:  # Task not installed
            status["enabled"] = False

        cmd_groups = line.split(self.KEY, 1) if line else ["", ""]
        parts = cmd_groups[0].strip(" #\t").split() if cmd_groups[0] else []
        status["interval"] = int(parts[0][2:]) if len(parts) >= 5 and parts[0].startswith("*/") else None
        status["command"] = " ".join(parts[5:]) if len(parts) >= 6 else None
        status["description"] = cmd_groups[1].strip() if len(cmd_groups) > 1 else None

        return status

    def install(self, interval, ddns_args=None):
        ddns_commands = self._build_ddns_command(ddns_args)
        # Convert array to properly quoted command string for cron
        ddns_command = self._quote_command_array(ddns_commands)
        description = self._get_description()
        cron_entry = '*/{} * * * * cd "{}" && {} # DDNS: {}'.format(interval, os.getcwd(), ddns_command, description)

        crontext = try_run(["crontab", "-l"], logger=self.logger) or ""
        lines = [line for line in crontext.splitlines() if self.KEY not in line]
        lines.append(cron_entry)

        if self._update_crontab(lines):
            return True
        else:
            self.logger.error("Failed to install DDNS cron job")
            return False

    def uninstall(self):
        return self._modify_cron_lines("uninstall")

    def enable(self):
        return self._modify_cron_lines("enable")

    def disable(self):
        return self._modify_cron_lines("disable")

    def _modify_cron_lines(self, action):  # type: (str) -> bool
        """Helper to enable, disable, or uninstall cron lines"""
        crontext = try_run(["crontab", "-l"], logger=self.logger)
        if not crontext or self.KEY not in crontext:
            self.logger.info("No crontab found")
            return False

        modified_lines = []
        for line in crontext.rstrip("\n").splitlines():
            if self.KEY not in line:
                modified_lines.append(line)
            elif action == "uninstall":
                continue  # Skip DDNS lines (remove them)
            elif action == "enable" and line.strip().startswith("#"):
                uncommented = line.lstrip(" #\t").lstrip()  # Enable: uncomment the line
                modified_lines.append(uncommented if uncommented else line)
            elif action == "disable" and not line.strip().startswith("#"):
                modified_lines.append("# " + line)  # Disable: comment the line
            else:
                raise ValueError("Invalid action: {}".format(action))

        if self._update_crontab(modified_lines):
            return True
        else:
            self.logger.error("Failed to %s DDNS cron job", action)
            return False
