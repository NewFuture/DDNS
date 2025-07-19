# -*- coding:utf-8 -*-
"""
Unix/Linux cron implementation for DDNS scheduled tasks.

This module provides cron-based task management for Unix/Linux systems.

@author: NewFuture
"""

import os
import sys
import subprocess
import tempfile
from logging import getLogger

from . import TaskManager

logger = getLogger(__name__)

class CronTaskManager(TaskManager):
    """Unix/Linux cron implementation."""
    
    CRON_COMMENT = "# DDNS v{version} - NewFuture/DDNS"
    CRON_LINE_PATTERN = "*/{}  *  *  *  *"
    
    def __init__(self, interval=5):
        # type: (int) -> None
        super(CronTaskManager, self).__init__(interval)
        self.python_exe = sys.executable
        self.is_root = os.geteuid() == 0
    
    def _run_crontab(self, args, input_data=None):
        # type: (list, str | None) -> tuple[bool, str]
        """
        Run crontab command and return success status and output.
        
        Args:
            args (list): Command arguments for crontab
            input_data (str, optional): Input data to pass to crontab
            
        Returns:
            tuple: (success, output)
        """
        try:
            cmd = ['crontab'] + args
            self.logger.debug("Running command: %s", ' '.join(cmd))
            
            if input_data is not None:
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                output, _ = proc.communicate(input_data)
                success = proc.returncode == 0
            else:
                output = subprocess.check_output(
                    cmd,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                success = True
            
            return success, output
        except subprocess.CalledProcessError as e:
            self.logger.debug("crontab command failed: %s", e.output)
            return False, e.output
        except Exception as e:
            self.logger.error("Failed to run crontab: %s", e)
            return False, str(e)
    
    def _get_current_crontab(self):
        # type: () -> str
        """
        Get current crontab content.
        
        Returns:
            str: Current crontab content or empty string if none exists
        """
        try:
            success, output = self._run_crontab(['-l'])
            if success:
                return output
            else:
                # No crontab exists yet
                return ""
        except Exception:
            return ""
    
    def _create_cron_command(self, config_path=None):
        # type: (str | None) -> str
        """
        Create cron command line.
        
        Args:
            config_path (str, optional): Path to config file
            
        Returns:
            str: Cron command line
        """
        # Determine script path
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        script_path = os.path.join(current_dir, "run.py")
        
        # Build command
        if config_path:
            cmd = '"{}" "{}" -c "{}"'.format(self.python_exe, script_path, config_path)
        else:
            cmd = '"{}" "{}"'.format(self.python_exe, script_path)
        
        # Add output redirection for logging
        log_file = "/var/log/ddns.log" if self.is_root else os.path.expanduser("~/ddns.log")
        cmd += " >> {} 2>&1".format(log_file)
        
        return cmd
    
    def _create_cron_line(self, config_path=None):
        # type: (str | None) -> str
        """
        Create cron line with timing and command.
        
        Args:
            config_path (str, optional): Path to config file
            
        Returns:
            str: Complete cron line
        """
        timing = self.CRON_LINE_PATTERN.format(self.interval)
        command = self._create_cron_command(config_path)
        return "{} {}".format(timing, command)
    
    def _remove_ddns_lines(self, crontab_content):
        # type: (str) -> str
        """
        Remove existing DDNS cron lines from crontab content.
        
        Args:
            crontab_content (str): Current crontab content
            
        Returns:
            str: Crontab content with DDNS lines removed
        """
        lines = crontab_content.split('\n')
        new_lines = []
        skip_next = False
        
        for line in lines:
            if skip_next:
                skip_next = False
                continue
            
            # Check for DDNS comment line
            if line.strip().startswith("# DDNS"):
                # This is a DDNS comment line, skip it and the next line
                skip_next = True
                continue
            
            # Also check for lines that contain our script but be more specific
            if ('ddns' in line.lower() and 
                ('run.py' in line or '-m ddns' in line) and
                ('*' in line or 'python' in line)):
                continue
            
            new_lines.append(line)
        
        # Remove trailing empty lines
        while new_lines and not new_lines[-1].strip():
            new_lines.pop()
        
        return '\n'.join(new_lines)
    
    def install(self, config_path=None):
        # type: (str | None) -> bool
        """
        Install cron job.
        
        Args:
            config_path (str, optional): Path to config file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get current crontab
            current_crontab = self._get_current_crontab()
            
            # Remove any existing DDNS lines
            clean_crontab = self._remove_ddns_lines(current_crontab)
            
            # Add our new entry
            comment = self.CRON_COMMENT.format(version=self.version)
            cron_line = self._create_cron_line(config_path)
            
            new_crontab = clean_crontab
            if new_crontab and not new_crontab.endswith('\n'):
                new_crontab += '\n'
            new_crontab += comment + '\n'
            new_crontab += cron_line + '\n'
            
            # Install new crontab
            success, output = self._run_crontab(['-'], new_crontab)
            
            if success:
                log_file = "/var/log/ddns.log" if self.is_root else os.path.expanduser("~/ddns.log")
                self.logger.info("Successfully installed cron job")
                self.logger.info("Interval: %d minutes", self.interval)
                self.logger.info("Log file: %s", log_file)
                self.logger.info("View with: crontab -l")
                return True
            else:
                self.logger.error("Failed to install cron job: %s", output)
                return False
                
        except Exception as e:
            self.logger.error("Error installing cron job: %s", e)
            return False
    
    def uninstall(self):
        # type: () -> bool
        """
        Uninstall cron job.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get current crontab
            current_crontab = self._get_current_crontab()
            
            if not current_crontab:
                self.logger.info("No crontab exists or DDNS job not found")
                return True
            
            # Remove DDNS lines
            clean_crontab = self._remove_ddns_lines(current_crontab)
            
            # Install cleaned crontab or remove it completely if empty
            if clean_crontab.strip():
                success, output = self._run_crontab(['-'], clean_crontab)
            else:
                # Remove entire crontab if it's empty
                success, output = self._run_crontab(['-r'])
                # crontab -r may fail if no crontab exists, which is fine
                if not success and "no crontab" in output.lower():
                    success = True
            
            if success:
                self.logger.info("Successfully uninstalled cron job")
                return True
            else:
                self.logger.error("Failed to uninstall cron job: %s", output)
                return False
                
        except Exception as e:
            self.logger.error("Error uninstalling cron job: %s", e)
            return False
    
    def is_installed(self):
        # type: () -> bool
        """
        Check if cron job is installed.
        
        Returns:
            bool: True if installed, False otherwise
        """
        try:
            current_crontab = self._get_current_crontab()
            comment_prefix = self.CRON_COMMENT.split(' ')[0]
            return comment_prefix in current_crontab or 'ddns' in current_crontab
        except Exception:
            return False
    
    def status(self):
        # type: () -> dict
        """
        Get detailed status information for cron job.
        
        Returns:
            dict: Status information
        """
        status = super(CronTaskManager, self).status()
        
        if self.is_installed():
            try:
                current_crontab = self._get_current_crontab()
                status['crontab'] = current_crontab
                
                # Check if cron daemon is running
                try:
                    subprocess.check_output(['pgrep', 'cron'], stderr=subprocess.STDOUT)
                    status['cron_daemon_running'] = True
                except subprocess.CalledProcessError:
                    status['cron_daemon_running'] = False
                
                # Log file location
                log_file = "/var/log/ddns.log" if self.is_root else os.path.expanduser("~/ddns.log")
                status['log_file'] = log_file
                status['log_exists'] = os.path.exists(log_file)
                
            except Exception as e:
                self.logger.debug("Failed to get detailed status: %s", e)
        
        return status