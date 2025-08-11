# -*- coding:utf-8 -*-
"""
schtasks-based task scheduler
@author: NewFuture
"""

import os
import re
import sys

from ._base import BaseScheduler


class SchtasksScheduler(BaseScheduler):
    """schtasks-based task scheduler"""

    NAME = "DDNS"

    def _schtasks(self, *args):  # type: (*str) -> bool
        """Helper to run schtasks commands with consistent error handling"""
        result = self._run_command(["schtasks"] + list(args))
        return result is not None

    def _extract_xml(self, xml_text, tag_name):  # type: (str, str) -> str | None
        """Extract XML tag content using regex for better performance and flexibility"""
        pattern = r"<{0}[^>]*>(.*?)</{0}>".format(re.escape(tag_name))
        match = re.search(pattern, xml_text, re.DOTALL)
        return match.group(1).strip() if match else None

    def is_installed(self):
        result = self._run_command(["schtasks", "/query", "/tn", self.NAME]) or ""
        return self.NAME in result

    def get_status(self):
        # Use XML format for language-independent parsing
        task_xml = self._run_command(["schtasks", "/query", "/tn", self.NAME, "/xml"])
        status = {"scheduler": "schtasks", "installed": bool(task_xml)}

        if not task_xml:
            return status  # Task not installed, return minimal status

        status["enabled"] = self._extract_xml(task_xml, "Enabled") != "false"
        command = self._extract_xml(task_xml, "Command")
        arguments = self._extract_xml(task_xml, "Arguments")
        status["command"] = "{} {}".format(command, arguments) if command and arguments else command

        # Parse interval: PT10M -> 10, fallback to original string
        interval_str = self._extract_xml(task_xml, "Interval")
        interval_match = re.search(r"PT(\d+)M", interval_str) if interval_str else None
        status["interval"] = int(interval_match.group(1)) if interval_match else interval_str

        # Show description if exists, otherwise show installation date
        description = self._extract_xml(task_xml, "Description") or self._extract_xml(task_xml, "Date")
        if description:
            status["description"] = description
        return status

    def install(self, interval, ddns_args=None):
        # Build command line: prefer pythonw for script mode, or compiled exe directly
        cmd = self._build_ddns_command(ddns_args)
        return self._schtasks("/Create", "/SC", "MINUTE", "/MO", str(interval), "/TR", cmd, "/TN", self.NAME, "/F")

    def uninstall(self):
        success = self._schtasks("/Delete", "/TN", self.NAME, "/F")
        return success

    def enable(self):
        return self._schtasks("/Change", "/TN", self.NAME, "/Enable")

    def disable(self):
        return self._schtasks("/Change", "/TN", self.NAME, "/Disable")

    # Override to prefer pythonw when not frozen (Windows scheduler only)
    def _get_ddns_cmd(self):  # type: () -> str
        if hasattr(sys, "frozen"):
            # Compiled binary, call directly (already configured for no window)
            return sys.executable
        # Non-frozen: try pythonw next to the current interpreter; fallback to sys.executable
        exe = sys.executable or "python"
        base_dir = os.path.dirname(exe)
        pythonw_candidate = os.path.join(base_dir, "pythonw.exe")
        py = pythonw_candidate if os.path.exists(pythonw_candidate) else exe
        return '"%s" -m ddns' % (py,)
