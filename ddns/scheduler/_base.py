# -*- coding:utf-8 -*-
"""
Base scheduler class for DDNS task management
@author: NewFuture
"""

import subprocess
import sys
from logging import Logger, getLogger  # noqa: F401


class BaseScheduler(object):
    """Base class for all task schedulers"""

    def __init__(self, logger=None):  # type: (Logger | None) -> None
        self.logger = (logger or getLogger()).getChild("task")

    def _run_command(self, command, **kwargs):  # type: (list[str], **Any) -> str | None
        """Safely run subprocess command, return decoded string or None if failed"""
        try:
            if sys.version_info[0] >= 3:
                kwargs.setdefault("stderr", subprocess.DEVNULL)
            return subprocess.check_output(command, universal_newlines=True, **kwargs)
        except (subprocess.CalledProcessError, OSError, UnicodeDecodeError):
            return None

    def _get_ddns_cmd(self):  # type: () -> str
        """Get DDNS command for scheduled execution"""
        if hasattr(sys, "frozen"):
            return sys.executable
        else:
            return '"{}" -m ddns'.format(sys.executable)

    def _build_ddns_command(self, ddns_args=None):  # type: (dict | None) -> str
        """Build DDNS command with arguments"""
        cmd_parts = [self._get_ddns_cmd()]

        if not ddns_args:
            return " ".join(cmd_parts)

        # Filter out debug=False to reduce noise
        args = {k: v for k, v in ddns_args.items() if not (k == "debug" and not v)}

        for key, value in args.items():
            if isinstance(value, bool):
                cmd_parts.append("--{} {}".format(key, str(value).lower()))
            elif isinstance(value, list):
                for item in value:
                    cmd_parts.append('--{} "{}"'.format(key, item))
            else:
                cmd_parts.append('--{} "{}"'.format(key, value))

        return " ".join(cmd_parts)

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
