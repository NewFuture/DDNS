# -*- coding:utf-8 -*-
"""
Task Management for DDNS scheduled tasks.

This module provides cross-platform support for installing and managing
scheduled tasks for DDNS updates.

@author: NewFuture
"""

import sys
import platform
import os
from logging import getLogger

from ..__init__ import __version__

logger = getLogger(__name__)

# Platform detection
SYSTEM = platform.system().lower()
IS_WINDOWS = SYSTEM == 'windows'
IS_MACOS = SYSTEM == 'darwin'
IS_LINUX = SYSTEM == 'linux'

# Task management interface
class TaskManager(object):
    """Base class for task management across platforms."""
    
    def __init__(self, interval=5):
        # type: (int) -> None
        """
        Initialize task manager.
        
        Args:
            interval (int): Task execution interval in minutes (default: 5)
        """
        self.interval = interval
        self.version = __version__
        self.logger = getLogger(self.__class__.__name__)
    
    def install(self, config_path=None):
        # type: (str | None) -> bool
        """
        Install scheduled task.
        
        Args:
            config_path (str, optional): Path to config file
            
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement install method")
    
    def uninstall(self):
        # type: () -> bool
        """
        Uninstall scheduled task.
        
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement uninstall method")
    
    def is_installed(self):
        # type: () -> bool
        """
        Check if scheduled task is installed.
        
        Returns:
            bool: True if installed, False otherwise
        """
        raise NotImplementedError("Subclasses must implement is_installed method")
    
    def status(self):
        # type: () -> dict
        """
        Get task status information.
        
        Returns:
            dict: Status information including installed state, version, etc.
        """
        return {
            'installed': self.is_installed(),
            'interval': self.interval,
            'version': self.version,
            'platform': SYSTEM
        }

def get_task_manager(interval=5):
    # type: (int) -> TaskManager
    """
    Get appropriate task manager for current platform.
    
    Args:
        interval (int): Task execution interval in minutes (default: 5)
        
    Returns:
        TaskManager: Platform-specific task manager instance
        
    Raises:
        NotImplementedError: If platform is not supported
    """
    if IS_WINDOWS:
        from .schtasks import WindowsTaskManager
        return WindowsTaskManager(interval)
    elif IS_MACOS:
        from .launchd import MacOSTaskManager
        return MacOSTaskManager(interval)
    elif IS_LINUX:
        # Try systemd first, fallback to cron
        try:
            from .systemd import SystemdTaskManager
            return SystemdTaskManager(interval)
        except (ImportError, OSError):
            from .cron import CronTaskManager
            return CronTaskManager(interval)
    else:
        # Generic Unix systems - use cron
        from .cron import CronTaskManager
        return CronTaskManager(interval)

__all__ = ['TaskManager', 'get_task_manager', 'IS_WINDOWS', 'IS_MACOS', 'IS_LINUX']