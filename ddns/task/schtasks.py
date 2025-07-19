# -*- coding:utf-8 -*-
"""
Windows Task Scheduler implementation for DDNS scheduled tasks.

This module provides Windows-specific task management using schtasks command.

@author: NewFuture
"""

import os
import sys
import subprocess
from logging import getLogger

from . import TaskManager

logger = getLogger(__name__)

class WindowsTaskManager(TaskManager):
    """Windows Task Scheduler implementation."""
    
    TASK_NAME = "DDNS"
    
    def __init__(self, interval=5):
        # type: (int) -> None
        super(WindowsTaskManager, self).__init__(interval)
        self.python_exe = sys.executable
        self.ddns_module = os.path.join(os.path.dirname(sys.executable), "Scripts", "ddns.exe")
        
        # Try to find ddns executable or fallback to python module
        if not os.path.exists(self.ddns_module):
            self.ddns_module = '"{}" -m ddns'.format(self.python_exe)
    
    def _run_schtasks(self, args):
        # type: (list) -> tuple[bool, str]
        """
        Run schtasks command and return success status and output.
        
        Args:
            args (list): Command arguments for schtasks
            
        Returns:
            tuple: (success, output)
        """
        try:
            cmd = ['schtasks'] + args
            self.logger.debug("Running command: %s", ' '.join(cmd))
            
            output = subprocess.check_output(
                cmd, 
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            return True, output
        except subprocess.CalledProcessError as e:
            self.logger.error("schtasks command failed: %s", e.output)
            return False, e.output
        except Exception as e:
            self.logger.error("Failed to run schtasks: %s", e)
            return False, str(e)
    
    def _get_task_user(self):
        # type: () -> str
        """
        Determine the appropriate user for the scheduled task.
        
        Returns:
            str: Username to run the task as
        """
        try:
            # Check if running as administrator
            import ctypes
            if ctypes.windll.shell32.IsUserAnAdmin():
                return "SYSTEM"
            else:
                return os.environ.get('USERNAME', 'SYSTEM')
        except Exception:
            return os.environ.get('USERNAME', 'SYSTEM')
    
    def install(self, config_path=None):
        # type: (str | None) -> bool
        """
        Install Windows scheduled task.
        
        Args:
            config_path (str, optional): Path to config file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Construct command
            if config_path:
                cmd = '{} -c "{}"'.format(self.ddns_module, config_path)
            else:
                cmd = self.ddns_module
            
            user = self._get_task_user()
            
            # Create scheduled task
            args = [
                '/Create',
                '/SC', 'MINUTE',
                '/MO', str(self.interval),
                '/TR', cmd,
                '/TN', self.TASK_NAME,
                '/F',  # Force overwrite existing task
                '/RU', user
            ]
            
            success, output = self._run_schtasks(args)
            
            if success:
                self.logger.info("Successfully installed Windows scheduled task")
                self.logger.info("Task name: %s", self.TASK_NAME)
                self.logger.info("Interval: %d minutes", self.interval)
                self.logger.info("Run as: %s", user)
                return True
            else:
                self.logger.error("Failed to install scheduled task: %s", output)
                if "access is denied" in output.lower():
                    self.logger.error("Permission denied. Please run as administrator.")
                return False
                
        except Exception as e:
            self.logger.error("Error installing scheduled task: %s", e)
            return False
    
    def uninstall(self):
        # type: () -> bool
        """
        Uninstall Windows scheduled task.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            args = ['/Delete', '/TN', self.TASK_NAME, '/F']
            success, output = self._run_schtasks(args)
            
            if success:
                self.logger.info("Successfully uninstalled Windows scheduled task")
                return True
            else:
                # Check if task doesn't exist (which is also success for uninstall)
                if "cannot find the file" in output.lower() or "does not exist" in output.lower():
                    self.logger.info("Scheduled task was not installed")
                    return True
                    
                self.logger.error("Failed to uninstall scheduled task: %s", output)
                if "access is denied" in output.lower():
                    self.logger.error("Permission denied. Please run as administrator.")
                return False
                
        except Exception as e:
            self.logger.error("Error uninstalling scheduled task: %s", e)
            return False
    
    def is_installed(self):
        # type: () -> bool
        """
        Check if Windows scheduled task is installed.
        
        Returns:
            bool: True if installed, False otherwise
        """
        try:
            args = ['/Query', '/TN', self.TASK_NAME]
            success, output = self._run_schtasks(args)
            return success
        except Exception:
            return False
    
    def status(self):
        # type: () -> dict
        """
        Get detailed status information for Windows scheduled task.
        
        Returns:
            dict: Status information
        """
        status = super(WindowsTaskManager, self).status()
        
        if self.is_installed():
            try:
                # Get detailed task information
                args = ['/Query', '/TN', self.TASK_NAME, '/FO', 'LIST']
                success, output = self._run_schtasks(args)
                
                if success:
                    # Parse task details from output
                    details = {}
                    for line in output.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            details[key.strip()] = value.strip()
                    
                    status['details'] = details
                    status['last_run'] = details.get('Last Run Time', 'Unknown')
                    status['next_run'] = details.get('Next Run Time', 'Unknown')
                    status['state'] = details.get('Status', 'Unknown')
                    
            except Exception as e:
                self.logger.debug("Failed to get detailed status: %s", e)
        
        return status