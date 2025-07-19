# -*- coding:utf-8 -*-
"""
Linux systemd implementation for DDNS scheduled tasks.

This module provides Linux systemd-specific task management.

@author: NewFuture
"""

import os
import sys
import subprocess
import tempfile
from logging import getLogger

from . import TaskManager

logger = getLogger(__name__)

class SystemdTaskManager(TaskManager):
    """Linux systemd implementation."""
    
    SERVICE_NAME = "ddns.service"
    TIMER_NAME = "ddns.timer"
    SYSTEMD_PATH = "/usr/lib/systemd/system"
    CONFIG_PATH = "/etc/DDNS"
    INSTALL_PATH = "/usr/share/DDNS"
    
    def __init__(self, interval=5):
        # type: (int) -> None
        super(SystemdTaskManager, self).__init__(interval)
        self.python_exe = sys.executable
    
    def _run_systemctl(self, args):
        # type: (list) -> tuple[bool, str]
        """
        Run systemctl command and return success status and output.
        
        Args:
            args (list): Command arguments for systemctl
            
        Returns:
            tuple: (success, output)
        """
        try:
            cmd = ['systemctl'] + args
            self.logger.debug("Running command: %s", ' '.join(cmd))
            
            output = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            return True, output
        except subprocess.CalledProcessError as e:
            self.logger.debug("systemctl command failed: %s", e.output)
            return False, e.output
        except Exception as e:
            self.logger.error("Failed to run systemctl: %s", e)
            return False, str(e)
    
    def _create_service_file(self):
        # type: () -> str
        """
        Create systemd service file content.
        
        Returns:
            str: Service file content
        """
        return """[Unit]
Description=NewFuture DDNS (v{version})
After=network.target

[Service]
Type=simple
WorkingDirectory={install_path}
ExecStart={python} {install_path}/run.py -c {config_path}/config.json

[Install]
WantedBy=multi-user.target
""".format(
            version=self.version,
            python=self.python_exe,
            install_path=self.INSTALL_PATH,
            config_path=self.CONFIG_PATH
        )
    
    def _create_timer_file(self):
        # type: () -> str
        """
        Create systemd timer file content.
        
        Returns:
            str: Timer file content
        """
        return """[Unit]
Description=NewFuture DDNS timer (v{version})

[Timer]
OnUnitActiveSec={interval}m
Unit={service}

[Install]
WantedBy=multi-user.target
""".format(
            version=self.version,
            interval=self.interval,
            service=self.SERVICE_NAME
        )
    
    def _check_permissions(self):
        # type: () -> bool
        """
        Check if we have sufficient permissions to install systemd services.
        
        Returns:
            bool: True if we have permissions, False otherwise
        """
        return os.geteuid() == 0 or os.access(self.SYSTEMD_PATH, os.W_OK)
    
    def install(self, config_path=None):
        # type: (str | None) -> bool
        """
        Install systemd service and timer.
        
        Args:
            config_path (str, optional): Path to config file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check permissions
            if not self._check_permissions():
                self.logger.error("Insufficient permissions. Please run as root (sudo).")
                return False
            
            # Create service file
            service_content = self._create_service_file()
            service_path = os.path.join(self.SYSTEMD_PATH, self.SERVICE_NAME)
            
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            # Create timer file
            timer_content = self._create_timer_file()
            timer_path = os.path.join(self.SYSTEMD_PATH, self.TIMER_NAME)
            
            with open(timer_path, 'w') as f:
                f.write(timer_content)
            
            # Copy current directory to install path
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            subprocess.check_call(['cp', '-r', current_dir, self.INSTALL_PATH])
            
            # Create config directory
            os.makedirs(self.CONFIG_PATH, exist_ok=True)
            
            # Copy config file if specified
            if config_path and os.path.exists(config_path):
                import shutil
                shutil.copy2(config_path, os.path.join(self.CONFIG_PATH, 'config.json'))
            elif not os.path.exists(os.path.join(self.CONFIG_PATH, 'config.json')):
                # Create a default config file
                with open(os.path.join(self.CONFIG_PATH, 'config.json'), 'w') as f:
                    f.write('{}')
            
            # Reload systemd and enable timer
            subprocess.check_call(['systemctl', 'daemon-reload'])
            subprocess.check_call(['systemctl', 'enable', self.TIMER_NAME])
            subprocess.check_call(['systemctl', 'start', self.TIMER_NAME])
            
            self.logger.info("Successfully installed systemd service and timer")
            self.logger.info("Service: %s", service_path)
            self.logger.info("Timer: %s", timer_path)
            self.logger.info("Config: %s/config.json", self.CONFIG_PATH)
            self.logger.info("Interval: %d minutes", self.interval)
            
            # Show status commands
            self.logger.info("Useful commands:")
            self.logger.info("  systemctl status %s     # view service status", self.TIMER_NAME)
            self.logger.info("  journalctl -u %s        # view logs", self.TIMER_NAME)
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error("systemctl command failed: %s", e)
            return False
        except Exception as e:
            self.logger.error("Error installing systemd service: %s", e)
            return False
    
    def uninstall(self):
        # type: () -> bool
        """
        Uninstall systemd service and timer.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check permissions
            if not self._check_permissions():
                self.logger.error("Insufficient permissions. Please run as root (sudo).")
                return False
            
            # Stop and disable timer
            subprocess.call(['systemctl', 'stop', self.TIMER_NAME])
            subprocess.call(['systemctl', 'disable', self.TIMER_NAME])
            
            # Remove service and timer files
            service_path = os.path.join(self.SYSTEMD_PATH, self.SERVICE_NAME)
            timer_path = os.path.join(self.SYSTEMD_PATH, self.TIMER_NAME)
            
            if os.path.exists(service_path):
                os.remove(service_path)
            if os.path.exists(timer_path):
                os.remove(timer_path)
            
            # Remove config and install directories
            import shutil
            if os.path.exists(self.CONFIG_PATH):
                shutil.rmtree(self.CONFIG_PATH)
            if os.path.exists(self.INSTALL_PATH):
                shutil.rmtree(self.INSTALL_PATH)
            
            # Reload systemd
            subprocess.call(['systemctl', 'daemon-reload'])
            
            self.logger.info("Successfully uninstalled systemd service and timer")
            return True
            
        except Exception as e:
            self.logger.error("Error uninstalling systemd service: %s", e)
            return False
    
    def is_installed(self):
        # type: () -> bool
        """
        Check if systemd service and timer are installed.
        
        Returns:
            bool: True if installed, False otherwise
        """
        try:
            service_path = os.path.join(self.SYSTEMD_PATH, self.SERVICE_NAME)
            timer_path = os.path.join(self.SYSTEMD_PATH, self.TIMER_NAME)
            return os.path.exists(service_path) and os.path.exists(timer_path)
        except Exception:
            return False
    
    def status(self):
        # type: () -> dict
        """
        Get detailed status information for systemd service.
        
        Returns:
            dict: Status information
        """
        status = super(SystemdTaskManager, self).status()
        
        if self.is_installed():
            try:
                # Get service status
                success, output = self._run_systemctl(['is-active', self.TIMER_NAME])
                status['active'] = success and 'active' in output
                
                # Get enabled status
                success, output = self._run_systemctl(['is-enabled', self.TIMER_NAME])
                status['enabled'] = success and 'enabled' in output
                
                # Get last run info if available
                success, output = self._run_systemctl(['status', self.TIMER_NAME, '--no-pager'])
                if success:
                    status['systemctl_status'] = output
                    
            except Exception as e:
                self.logger.debug("Failed to get detailed status: %s", e)
        
        return status