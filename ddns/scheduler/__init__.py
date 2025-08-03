# -*- coding:utf-8 -*-
"""
Task scheduler management
Provides factory functions and public API for task scheduling
@author: NewFuture
"""

import platform
import os

# Import all scheduler classes
from ._base import BaseScheduler
from .systemd import SystemdScheduler
from .cron import CronScheduler
from .launchd import LaunchdScheduler
from .windows import WindowsScheduler


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
    if scheduler is None or scheduler == 'auto':
        system = platform.system().lower()

        if system == "windows":
            return WindowsScheduler()
        elif system == "darwin":  # macOS
            # Check if launchd directories exist
            launchd_dirs = ["/Library/LaunchDaemons", "/System/Library/LaunchDaemons"]
            if any(os.path.isdir(d) for d in launchd_dirs):
                return LaunchdScheduler()
            return CronScheduler()
        elif system == "linux":
            # Check if systemd is the init system by reading /proc/1/comm
            try:
                with open("/proc/1/comm", "r") as f:
                    init_name = f.read().strip()
                if init_name == "systemd":
                    return SystemdScheduler()
            except (OSError, IOError):
                pass  # Fall back to cron if can't read /proc/1/comm
            return CronScheduler()
        else:
            # Other Unix-like systems, use cron
            return CronScheduler()

    # Use specified scheduler
    if scheduler == 'systemd':
        return SystemdScheduler()
    elif scheduler == 'cron':
        return CronScheduler()
    elif scheduler == 'launchd' or scheduler == 'mac':
        return LaunchdScheduler()
    elif scheduler == 'schtasks' or scheduler == 'windows':
        return WindowsScheduler()
    else:
        raise ValueError(
            "Invalid scheduler: {}. Must be one of: auto, systemd, cron, launchd, schtasks".format(scheduler)
        )


# Export public API
__all__ = ["get_scheduler", "BaseScheduler"]
