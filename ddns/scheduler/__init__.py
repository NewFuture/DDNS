# -*- coding:utf-8 -*-
"""
Task scheduler management
Provides factory functions and public API for task scheduling
@author: NewFuture
"""

import os
import platform

from ddns.util.fileio import read_file_safely

from ..util.try_run import try_run

# Import all scheduler classes
from ._base import BaseScheduler
from .cron import CronScheduler
from .launchd import LaunchdScheduler
from .schtasks import SchtasksScheduler
from .systemd import SystemdScheduler


def get_scheduler(scheduler=None):
    # type: (str | None) -> BaseScheduler
    """
    Factory function to get appropriate scheduler based on platform or user preference

    Args:
        scheduler: Scheduler type. Can be:
                  - None or "auto": Auto-detect based on platform
                  - "systemd": Use systemd timer (Linux)
                  - "cron": Use cron jobs (Unix/Linux)
                  - "launchd": Use launchd (macOS)
                  - "schtasks": Use Windows Task Scheduler

    Returns:
        Appropriate scheduler instance

    Raises:
        ValueError: If invalid scheduler specified
        NotImplementedError: If scheduler not available on current platform
    """
    # Auto-detect if not specified
    if scheduler is None or scheduler == "auto":
        system = platform.system().lower()
        if system == "windows":
            return SchtasksScheduler()
        elif system == "darwin":  # macOS
            # Check if launchd directories exist
            launchd_dirs = ["/Library/LaunchDaemons", "/System/Library/LaunchDaemons"]
            if any(os.path.isdir(d) for d in launchd_dirs):
                return LaunchdScheduler()
        elif system == "linux" and (
            (read_file_safely("/proc/1/comm", default="").strip().lower() == "systemd")
            or (try_run(["systemctl", "--version"]) is not None)
        ):  # Linux with systemd available
            return SystemdScheduler()
        return CronScheduler()  # Other Unix-like systems, use cron
    elif scheduler == "systemd":
        return SystemdScheduler()
    elif scheduler == "cron":
        return CronScheduler()
    elif scheduler == "launchd" or scheduler == "mac":
        return LaunchdScheduler()
    elif scheduler == "schtasks" or scheduler == "windows":
        return SchtasksScheduler()
    else:
        raise ValueError("Invalid scheduler: {}. ".format(scheduler))


# Export public API
__all__ = ["get_scheduler", "BaseScheduler"]
