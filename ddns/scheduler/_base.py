# -*- coding:utf-8 -*-
"""
Base scheduler class for DDNS task management
@author: NewFuture
"""

import sys
from datetime import datetime
from logging import Logger, getLogger  # noqa: F401

from .. import __version__ as version


class BaseScheduler(object):
    """Base class for all task schedulers"""

    def __init__(self, logger=None):  # type: (Logger | None) -> None
        self.logger = (logger or getLogger()).getChild("task")

    def _get_ddns_cmd(self):  # type: () -> list[str]
        """Get DDNS command for scheduled execution as array"""
        if hasattr(sys.modules["__main__"], "__compiled__"):
            return [sys.argv[0]]
        else:
            return [sys.executable, "-m", "ddns"]

    def _build_ddns_command(self, ddns_args=None):  # type: (dict | None) -> list[str]
        """Build DDNS command with arguments as array"""
        # Get base command as array
        cmd_parts = self._get_ddns_cmd()

        if not ddns_args:
            return cmd_parts

        # Filter out debug=False to reduce noise
        args = {k: v for k, v in ddns_args.items() if not (k == "debug" and not v)}

        for key, value in args.items():
            if isinstance(value, bool):
                cmd_parts.extend(["--{}".format(key), str(value).lower()])
            elif isinstance(value, list):
                for item in value:
                    cmd_parts.extend(["--{}".format(key), str(item)])
            else:
                cmd_parts.extend(["--{}".format(key), str(value)])

        return cmd_parts

    def _quote_command_array(self, cmd_array):  # type: (list[str]) -> str
        """Convert command array to properly quoted command string"""
        return " ".join('"{}"'.format(arg) if " " in arg else arg for arg in cmd_array)

    def _get_description(self):  # type: () -> str
        """Generate standard description/comment for DDNS installation"""
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return "auto-update v{} installed on {}".format(version, date)

    def is_installed(self):  # type: () -> bool
        """Check if DDNS task is installed"""
        raise NotImplementedError

    def get_status(self):  # type: () -> dict
        """Get detailed status information"""
        raise NotImplementedError

    def install(self, interval, ddns_args=None):  # type: (int, dict | None) -> bool
        """Install DDNS scheduled task"""
        raise NotImplementedError

    def uninstall(self):  # type: () -> bool
        """Uninstall DDNS scheduled task"""
        raise NotImplementedError

    def enable(self):  # type: () -> bool
        """Enable DDNS scheduled task"""
        raise NotImplementedError

    def disable(self):  # type: () -> bool
        """Disable DDNS scheduled task"""
        raise NotImplementedError
