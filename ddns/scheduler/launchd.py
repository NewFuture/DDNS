# -*- coding:utf-8 -*-
"""
macOS launchd-based task scheduler
@author: NewFuture
"""

import os
import re
import subprocess
from datetime import datetime
from ._base import BaseScheduler
from ..util.fileio import read_file_safely, write_file
from .. import __version__ as version


class LaunchdScheduler(BaseScheduler):
    """macOS launchd-based task scheduler"""
    LABEL = "cc.newfuture.ddns"

    def _get_plist_path(self):
        return os.path.expanduser("~/Library/LaunchAgents/{}.plist".format(self.LABEL))

    def _launchctl(self, *args):  # type: (*str) -> bool
        """Helper to run launchctl commands with consistent error handling"""
        try:
            subprocess.check_call(["launchctl"] + list(args))
            return True
        except subprocess.CalledProcessError:
            return False

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
        program_args_xml = u"\n".join(u"        <string>{}</string>".format(arg.strip('"')) for arg in program_args)
        
        # Create comment with version and install date (consistent with Windows)
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment = "auto-update v{} installed on {}".format(version, date)

        plist_content = (
            u'<?xml version="1.0" encoding="UTF-8"?>\n'
            + u'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            + u'"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            + u'<plist version="1.0">\n<dict>\n'
            + u"    <key>Label</key>\n    <string>{}</string>\n".format(self.LABEL)
            + u"    <key>Description</key>\n    <string>{}</string>\n".format(comment)
            + u"    <key>ProgramArguments</key>\n    <array>\n{}\n    </array>\n".format(program_args_xml)
            + u"    <key>StartInterval</key>\n    <integer>{}</integer>\n".format(interval * 60)
            + u"    <key>RunAtLoad</key>\n    <true/>\n"
            + u"    <key>WorkingDirectory</key>\n    <string>{}</string>\n".format(os.getcwd())
            + u"</dict>\n</plist>\n"
        )

        write_file(plist_path, plist_content)
        if self._launchctl("load", plist_path):
            self.logger.info("DDNS launchd service installed successfully")
            return True
        else:
            self.logger.error("Failed to load launchd service")
            return False

    def uninstall(self):
        plist_path = self._get_plist_path()
        subprocess.call(["launchctl", "unload", plist_path])  # Ignore errors
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

        if self._launchctl("load", plist_path):
            self.logger.info("DDNS launchd service enabled successfully")
            return True
        else:
            self.logger.error("Failed to enable launchd service")
            return False

    def disable(self):
        plist_path = self._get_plist_path()
        if self._launchctl("unload", plist_path):
            self.logger.info("DDNS launchd service disabled successfully")
            return True
        else:
            self.logger.error("Failed to disable launchd service")
            return False
