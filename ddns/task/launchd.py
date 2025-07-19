# -*- coding:utf-8 -*-
"""
macOS launchd implementation for DDNS scheduled tasks.

This module provides macOS-specific task management using launchd.

@author: NewFuture
"""

import os
import sys
import subprocess
import plistlib
from logging import getLogger

from . import TaskManager

logger = getLogger(__name__)

class MacOSTaskManager(TaskManager):
    """macOS launchd implementation."""
    
    PLIST_NAME = "cc.newfuture.ddns.plist"
    
    def __init__(self, interval=5):
        # type: (int) -> None
        super(MacOSTaskManager, self).__init__(interval)
        self.python_exe = sys.executable
        self.user_agents_path = os.path.expanduser("~/Library/LaunchAgents")
        self.system_agents_path = "/Library/LaunchAgents"
        
        # Determine if we should use user or system agents
        self.use_system = os.geteuid() == 0
        self.agents_path = self.system_agents_path if self.use_system else self.user_agents_path
        self.plist_path = os.path.join(self.agents_path, self.PLIST_NAME)
    
    def _run_launchctl(self, args):
        # type: (list) -> tuple[bool, str]
        """
        Run launchctl command and return success status and output.
        
        Args:
            args (list): Command arguments for launchctl
            
        Returns:
            tuple: (success, output)
        """
        try:
            cmd = ['launchctl'] + args
            self.logger.debug("Running command: %s", ' '.join(cmd))
            
            output = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            return True, output
        except subprocess.CalledProcessError as e:
            self.logger.debug("launchctl command failed: %s", e.output)
            return False, e.output
        except Exception as e:
            self.logger.error("Failed to run launchctl: %s", e)
            return False, str(e)
    
    def _create_plist_data(self, config_path=None):
        # type: (str | None) -> dict
        """
        Create plist data for launchd.
        
        Args:
            config_path (str, optional): Path to config file
            
        Returns:
            dict: Plist data
        """
        # Determine script path
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        script_path = os.path.join(current_dir, "run.py")
        
        # Build command arguments
        program_args = [self.python_exe, script_path]
        if config_path:
            program_args.extend(['-c', config_path])
        
        plist_data = {
            'Label': 'cc.newfuture.ddns',
            'ProgramArguments': program_args,
            'StartInterval': self.interval * 60,  # Convert minutes to seconds
            'RunAtLoad': True,
            'KeepAlive': False,
            'StandardOutPath': os.path.expanduser('~/Library/Logs/ddns.log'),
            'StandardErrorPath': os.path.expanduser('~/Library/Logs/ddns.error.log'),
            'UserName': os.environ.get('USER', 'root') if not self.use_system else None
        }
        
        # Remove None values
        plist_data = {k: v for k, v in plist_data.items() if v is not None}
        
        return plist_data
    
    def _write_plist(self, plist_data):
        # type: (dict) -> bool
        """
        Write plist data to file.
        
        Args:
            plist_data (dict): Plist data to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.agents_path, exist_ok=True)
            
            # Write plist file
            with open(self.plist_path, 'wb') as f:
                if sys.version_info[0] >= 3:
                    plistlib.dump(plist_data, f)
                else:
                    # Python 2 compatibility
                    plistlib.writePlist(plist_data, f)
            
            return True
        except Exception as e:
            self.logger.error("Failed to write plist file: %s", e)
            return False
    
    def install(self, config_path=None):
        # type: (str | None) -> bool
        """
        Install launchd job.
        
        Args:
            config_path (str, optional): Path to config file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create plist data
            plist_data = self._create_plist_data(config_path)
            
            # Write plist file
            if not self._write_plist(plist_data):
                return False
            
            # Load the job
            success, output = self._run_launchctl(['load', '-w', self.plist_path])
            
            if success:
                self.logger.info("Successfully installed macOS launchd job")
                self.logger.info("Plist: %s", self.plist_path)
                self.logger.info("Interval: %d minutes", self.interval)
                self.logger.info("Log files:")
                self.logger.info("  Output: %s", plist_data.get('StandardOutPath'))
                self.logger.info("  Error: %s", plist_data.get('StandardErrorPath'))
                return True
            else:
                self.logger.error("Failed to load launchd job: %s", output)
                return False
                
        except Exception as e:
            self.logger.error("Error installing launchd job: %s", e)
            return False
    
    def uninstall(self):
        # type: () -> bool
        """
        Uninstall launchd job.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Unload the job if it exists
            if self.is_installed():
                success, output = self._run_launchctl(['unload', '-w', self.plist_path])
                if not success:
                    self.logger.warning("Failed to unload launchd job: %s", output)
            
            # Remove plist file
            if os.path.exists(self.plist_path):
                os.remove(self.plist_path)
            
            self.logger.info("Successfully uninstalled macOS launchd job")
            return True
            
        except Exception as e:
            self.logger.error("Error uninstalling launchd job: %s", e)
            return False
    
    def is_installed(self):
        # type: () -> bool
        """
        Check if launchd job is installed.
        
        Returns:
            bool: True if installed, False otherwise
        """
        return os.path.exists(self.plist_path)
    
    def status(self):
        # type: () -> dict
        """
        Get detailed status information for launchd job.
        
        Returns:
            dict: Status information
        """
        status = super(MacOSTaskManager, self).status()
        
        if self.is_installed():
            try:
                # Check if job is loaded
                success, output = self._run_launchctl(['list', 'cc.newfuture.ddns'])
                if success:
                    status['loaded'] = True
                    # Parse launchctl list output for details
                    lines = output.strip().split('\n')
                    if len(lines) > 1:
                        parts = lines[1].split('\t')
                        if len(parts) >= 3:
                            status['pid'] = parts[0] if parts[0] != '-' else None
                            status['exit_code'] = parts[1] if parts[1] != '-' else None
                            status['label'] = parts[2]
                else:
                    status['loaded'] = False
                    
                # Try to get more detailed info
                success, output = self._run_launchctl(['print', 'gui/{}/cc.newfuture.ddns'.format(os.getuid())])
                if success:
                    status['detailed_info'] = output
                    
            except Exception as e:
                self.logger.debug("Failed to get detailed status: %s", e)
        
        return status