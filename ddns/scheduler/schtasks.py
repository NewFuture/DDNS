# -*- coding:utf-8 -*-
"""
schtasks-based task scheduler
@author: NewFuture
"""

import os
import re
import subprocess
from ._base import BaseScheduler
from ..util.fileio import write_file

# Constants
VBS_SCRIPT = "~\\AppData\\Local\\DDNS\\ddns_silent.vbs"


class SchtasksScheduler(BaseScheduler):
    """schtasks-based task scheduler"""

    NAME = "DDNS"

    def _schtasks(self, *args):  # type: (*str) -> bool
        """Helper to run schtasks commands with consistent error handling"""
        subprocess.check_call(["schtasks"] + list(args))
        return True

    def _create_vbs_script(self, ddns_args=None):  # type: (dict | None) -> str
        """Create VBS script for silent execution and return its path"""
        ddns_command = self._build_ddns_command(ddns_args)
        work_dir = os.getcwd()

        # Build VBS content with proper escaping
        vbs_content = (
            u'Set objShell = CreateObject("WScript.Shell")\n'
            u'objShell.CurrentDirectory = "{}"\n'
            u'objShell.Run "{}", 0, False\n'
        ).format(work_dir.replace("\\", "\\\\"), ddns_command.replace('"', '""'))

        # Try locations in order: AppData, then working directory
        vbs_paths = [os.path.expanduser(VBS_SCRIPT), os.path.join(work_dir, ".ddns_silent.vbs")]

        for path in vbs_paths:
            try:
                write_file(path, vbs_content)
                return path
            except Exception as e:
                self.logger.warning("Failed to create VBS in %s: %s", path, e)

        raise Exception("Failed to create VBS script in any location")

    def _extract_xml(self, xml_text, tag_name):  # type: (str, str) -> str | None
        """Extract XML tag content using regex for better performance and flexibility"""
        pattern = r'<{0}[^>]*>(.*?)</{0}>'.format(re.escape(tag_name))
        match = re.search(pattern, xml_text, re.DOTALL)
        return match.group(1).strip() if match else None

    def is_installed(self):
        result = self._run_command(["schtasks", "/query", "/tn", self.NAME]) or ""
        return self.NAME in result

    def get_status(self):
        # Use XML format for language-independent parsing
        task_xml = self._run_command(["schtasks", "/query", "/tn", self.NAME, "/xml"])
        status = {
            "scheduler": "schtasks",
            "installed": bool(task_xml),
        }

        if not task_xml:
            return status  # Task not installed, return minimal status

        status['enabled'] = self._extract_xml(task_xml, 'Enabled') != 'false'
        command = self._extract_xml(task_xml, 'Command')
        arguments = self._extract_xml(task_xml, 'Arguments')
        status["command"] = "{} {}".format(command, arguments) if command and arguments else command

        # Parse interval: PT10M -> 10, fallback to original string
        interval_str = self._extract_xml(task_xml, 'Interval')
        interval_match = re.search(r'PT(\d+)M', interval_str) if interval_str else None
        status["interval"] = int(interval_match.group(1)) if interval_match else interval_str

        # Show description if exists, otherwise show installation date
        description = self._extract_xml(task_xml, 'Description') or self._extract_xml(task_xml, 'Date')
        if description:
            status["description"] = description
        return status

    def install(self, interval, ddns_args=None):
        vbs_path = self._create_vbs_script(ddns_args)
        cmd = 'wscript.exe "{}"'.format(vbs_path)
        return self._schtasks("/Create", "/SC", "MINUTE", "/MO", str(interval), "/TR", cmd, "/TN", self.NAME, "/F")

    def uninstall(self):
        success = self._schtasks("/Delete", "/TN", self.NAME, "/F")
        if success:
            # Clean up VBS script files
            vbs_paths = [os.path.expanduser(VBS_SCRIPT), os.path.join(os.getcwd(), ".ddns_silent.vbs")]
            for vbs_path in vbs_paths:
                if os.path.exists(vbs_path):
                    try:
                        os.remove(vbs_path)
                        self.logger.info("Cleaned up VBS script file: %s", vbs_path)
                    except OSError:
                        self.logger.info("fail to remove %s", vbs_path)
                        pass  # Ignore cleanup failures
        return success

    def enable(self):
        return self._schtasks("/Change", "/TN", self.NAME, "/Enable")

    def disable(self):
        return self._schtasks("/Change", "/TN", self.NAME, "/Disable")
