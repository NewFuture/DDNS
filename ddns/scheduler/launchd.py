# -*- coding:utf-8 -*-
"""
macOS launchd-based task scheduler
@author: NewFuture
"""

import os
import re
from datetime import datetime

from .. import __version__ as version
from ..util.fileio import read_file_safely, write_file
from ._base import BaseScheduler


class LaunchdScheduler(BaseScheduler):
    """macOS launchd-based task scheduler"""

    LABEL = "cc.newfuture.ddns"

    def _get_plist_path(self):
        return os.path.expanduser("~/Library/LaunchAgents/{}.plist".format(self.LABEL))

    def is_installed(self):
        return os.path.exists(self._get_plist_path())

    def get_status(self):
        # Read plist content once and use it to determine installation status
        content = read_file_safely(self._get_plist_path())
        status = {"scheduler": "launchd", "installed": bool(content)}
        if not content:
            return status

        # For launchd, check if service is actually loaded/enabled
        result = self._run_command(["launchctl", "list"])
        status["enabled"] = bool(result) and self.LABEL in result

        # Get interval
        interval_match = re.search(r"<key>StartInterval</key>\s*<integer>(\d+)</integer>", content)
        status["interval"] = int(interval_match.group(1)) // 60 if interval_match else None

        # Get command
        program_match = re.search(r"<key>Program</key>\s*<string>([^<]+)</string>", content)
        if program_match:
            status["command"] = program_match.group(1)
        else:
            args_section = re.search(r"<key>ProgramArguments</key>\s*<array>(.*?)</array>", content, re.DOTALL)
            if args_section:
                strings = re.findall(r"<string>([^<]+)</string>", args_section.group(1))
                if strings:
                    status["command"] = " ".join(strings)

        # Get comments
        desc_match = re.search(r"<key>Description</key>\s*<string>([^<]+)</string>", content)
        status["description"] = desc_match.group(1) if desc_match else None

        return status

    def install(self, interval, ddns_args=None):
        plist_path = self._get_plist_path()
        ddns_command = self._build_ddns_command(ddns_args)
        program_args = ddns_command.split()
        program_args_xml = "\n".join("        <string>{}</string>".format(arg.strip('"')) for arg in program_args)

        # Create comment with version and install date (consistent with Windows)
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment = "auto-update v{} installed on {}".format(version, date)
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>{label}</string>
        <key>Description</key>
        <string>{comment}</string>
        <key>ProgramArguments</key>
        <array>
    {program_args_xml}
        </array>
        <key>StartInterval</key>
        <integer>{interval}</integer>
        <key>RunAtLoad</key>
        <true/>
        <key>WorkingDirectory</key>
        <string>{cwd}</string>
    </dict>
    </plist>
    """.format(
            label=self.LABEL,
            comment=comment,
            program_args_xml=program_args_xml,
            interval=interval * 60,
            cwd=os.getcwd(),
        )

        write_file(plist_path, plist_content)
        result = self._run_command(["launchctl", "load", plist_path])
        if result is not None:
            self.logger.info("DDNS launchd service installed successfully")
            return True
        else:
            self.logger.error("Failed to load launchd service")
            return False

    def uninstall(self):
        plist_path = self._get_plist_path()
        self._run_command(["launchctl", "unload", plist_path])  # Ignore errors
        try:
            os.remove(plist_path)
        except OSError:
            pass

        self.logger.info("DDNS launchd service uninstalled successfully")
        return True

    def enable(self):
        plist_path = self._get_plist_path()
        if not os.path.exists(plist_path):
            self.logger.error("DDNS launchd service not found")
            return False

        result = self._run_command(["launchctl", "load", plist_path])
        if result is not None:
            self.logger.info("DDNS launchd service enabled successfully")
            return True
        else:
            self.logger.error("Failed to enable launchd service")
            return False

    def disable(self):
        plist_path = self._get_plist_path()
        result = self._run_command(["launchctl", "unload", plist_path])
        if result is not None:
            self.logger.info("DDNS launchd service disabled successfully")
            return True
        else:
            self.logger.error("Failed to disable launchd service")
            return False
