# -*- coding:utf-8 -*-
"""
Task Management Utility for DDNS scheduled tasks
@author: NewFuture
"""

import os
import platform
import subprocess
import sys
import tempfile
from logging import getLogger

__all__ = ["TaskManager"]

logger = getLogger(__name__)


class TaskManager(object):
    """
    Cross-platform task scheduler manager for DDNS
    """

    def __init__(self, config_path=None, log_path=None, interval=5):
        # type: (str | None, str | None, int) -> None
        """
        Initialize TaskManager
        
        Args:
            config_path (str): Path to DDNS config file
            log_path (str): Path to log file  
            interval (int): Update interval in minutes (default: 5)
        """
        self.config_path = config_path
        self.log_path = log_path
        self.interval = interval
        self.task_name = "DDNS"
        
        # Determine DDNS executable path
        if hasattr(sys, 'frozen'):
            # If running as compiled executable
            self.ddns_cmd = sys.executable
        else:
            # If running as Python script
            self.ddns_cmd = '"{}" -m ddns'.format(sys.executable)

    def get_scheduler_type(self):
        # type: () -> str
        """
        Determine the best task scheduler for current system
        
        Returns:
            str: Scheduler type ("systemd", "cron", "launchd", "schtasks")
        """
        system = platform.system().lower()
        
        if system == "linux":
            # Check if systemd is available
            try:
                subprocess.check_call(["systemctl", "--version"], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL)
                return "systemd"
            except (subprocess.CalledProcessError, OSError):
                return "cron"
        elif system == "darwin":  # macOS
            # Check if launchctl is available
            try:
                subprocess.check_call(["launchctl", "help"],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
                return "launchd"
            except (subprocess.CalledProcessError, OSError):
                return "cron"
        elif system == "windows":
            return "schtasks"
        else:
            # Fallback to cron for other Unix-like systems
            return "cron"

    def is_installed(self):
        # type: () -> bool
        """
        Check if DDNS task is installed
        
        Returns:
            bool: True if task is installed
        """
        scheduler = self.get_scheduler_type()
        
        try:
            if scheduler == "systemd":
                # Check if systemd timer is enabled
                result = subprocess.check_output(["systemctl", "is-enabled", "ddns.timer"],
                                               stderr=subprocess.DEVNULL)
                return result.strip().decode("utf-8") == "enabled"
            elif scheduler == "cron":
                # Check if cron job exists
                try:
                    result = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL)
                    return b"DDNS" in result or b"ddns" in result
                except subprocess.CalledProcessError:
                    return False
            elif scheduler == "launchd":
                # Check if launchd plist exists
                plist_path = os.path.expanduser("~/Library/LaunchAgents/cc.newfuture.ddns.plist")
                return os.path.exists(plist_path)
            elif scheduler == "schtasks":
                # Check if Windows scheduled task exists
                result = subprocess.check_output(["schtasks", "/query", "/tn", self.task_name],
                                               stderr=subprocess.DEVNULL)
                return self.task_name.encode() in result
        except (subprocess.CalledProcessError, OSError):
            pass
        
        return False

    def get_status(self):
        # type: () -> dict
        """
        Get task status information
        
        Returns:
            dict: Status information including installation status, scheduler type, etc.
        """
        scheduler = self.get_scheduler_type()
        installed = self.is_installed()
        status = {
            "installed": installed,
            "scheduler": scheduler,
            "system": platform.system().lower(),
            "interval": self.interval,
            "config_path": self.config_path,
            "log_path": self.log_path,
        }
        
        if installed:
            try:
                status["running_status"] = self._get_running_status(scheduler)
            except Exception as e:
                logger.debug("Failed to get running status: %s", e)
                status["running_status"] = "unknown"
        else:
            # Check fallback scheduler status when not installed with primary
            fallback_scheduler = self._get_fallback_scheduler()
            if fallback_scheduler and fallback_scheduler != scheduler:
                try:
                    fallback_installed = self._check_fallback_installation(fallback_scheduler)
                    if fallback_installed:
                        status["fallback_scheduler"] = fallback_scheduler
                        status["fallback_installed"] = True
                        status["fallback_running_status"] = self._get_running_status(fallback_scheduler)
                except Exception as e:
                    logger.debug("Failed to check fallback scheduler status: %s", e)
        
        return status
    
    def _get_fallback_scheduler(self):
        # type: () -> str | None
        """
        Get fallback scheduler type for current system
        
        Returns:
            str|None: Fallback scheduler type or None if no fallback
        """
        system = platform.system().lower()
        
        if system == "linux":
            # Fallback from systemd to cron
            try:
                subprocess.check_call(["systemctl", "--version"], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL)
                return "cron"  # If systemd exists, cron is fallback
            except (subprocess.CalledProcessError, OSError):
                return None  # Already using cron, no fallback
        elif system == "darwin":  # macOS
            # Fallback from launchd to cron
            try:
                subprocess.check_call(["launchctl", "help"],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
                return "cron"  # If launchd exists, cron is fallback
            except (subprocess.CalledProcessError, OSError):
                return None  # Already using cron, no fallback
        
        return None  # Windows has no fallback
        
    def _check_fallback_installation(self, fallback_scheduler):
        # type: (str) -> bool
        """
        Check if task is installed using fallback scheduler
        
        Args:
            fallback_scheduler (str): Fallback scheduler type
            
        Returns:
            bool: True if installed using fallback scheduler
        """
        if fallback_scheduler == "cron":
            try:
                result = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL)
                return "ddns" in result.decode().lower()
            except (subprocess.CalledProcessError, OSError):
                return False
        
        return False

    def _get_running_status(self, scheduler):
        # type: (str) -> str
        """
        Get running status for specific scheduler
        
        Args:
            scheduler (str): Scheduler type
            
        Returns:
            str: Running status
        """
        if scheduler == "systemd":
            try:
                result = subprocess.check_output(["systemctl", "is-active", "ddns.timer"],
                                               stderr=subprocess.DEVNULL)
                return result.strip().decode("utf-8")
            except subprocess.CalledProcessError:
                return "inactive"
        elif scheduler == "cron":
            try:
                subprocess.check_output(["pgrep", "-f", "cron"], stderr=subprocess.DEVNULL)
                return "active"
            except subprocess.CalledProcessError:
                return "inactive"
        elif scheduler == "launchd":
            try:
                result = subprocess.check_output(["launchctl", "list", "cc.newfuture.ddns"],
                                               stderr=subprocess.DEVNULL)
                return "active" if result else "inactive"
            except subprocess.CalledProcessError:
                return "inactive"
        elif scheduler == "schtasks":
            try:
                result = subprocess.check_output(["schtasks", "/query", "/tn", self.task_name, "/fo", "csv"],
                                               stderr=subprocess.DEVNULL)
                lines = result.decode().strip().split('\n')
                if len(lines) > 1:
                    # Parse CSV output
                    fields = [field.strip('"') for field in lines[1].split('","')]
                    if len(fields) > 2:
                        return fields[2].lower()  # Status field
                return "unknown"
            except subprocess.CalledProcessError:
                return "inactive"
        
        return "unknown"

    def install(self, force=False):
        # type: (bool) -> bool
        """
        Install DDNS scheduled task
        
        Args:
            force (bool): Force reinstall if already exists
            
        Returns:
            bool: True if installation successful
        """
        if self.is_installed() and not force:
            logger.info("DDNS task is already installed. Use --force to reinstall.")
            return True
        
        scheduler = self.get_scheduler_type()
        logger.info("Installing DDNS task using %s scheduler...", scheduler)
        
        try:
            if scheduler == "systemd":
                return self._install_systemd()
            elif scheduler == "cron":
                return self._install_cron()
            elif scheduler == "launchd":
                return self._install_launchd()
            elif scheduler == "schtasks":
                return self._install_schtasks()
        except Exception as e:
            logger.error("Failed to install DDNS task: %s", e)
            return False
        
        return False

    def uninstall(self):
        # type: () -> bool
        """
        Uninstall DDNS scheduled task
        
        Returns:
            bool: True if uninstallation successful
        """
        if not self.is_installed():
            logger.info("DDNS task is not installed.")
            return True
        
        scheduler = self.get_scheduler_type()
        logger.info("Uninstalling DDNS task from %s scheduler...", scheduler)
        
        try:
            if scheduler == "systemd":
                return self._uninstall_systemd()
            elif scheduler == "cron":
                return self._uninstall_cron()
            elif scheduler == "launchd":
                return self._uninstall_launchd()
            elif scheduler == "schtasks":
                return self._uninstall_schtasks()
        except Exception as e:
            logger.error("Failed to uninstall DDNS task: %s", e)
            return False
        
        return False

    def _install_systemd(self):
        # type: () -> bool
        """Install systemd timer and service"""
        service_content = """[Unit]
Description=DDNS automatic IP update service
After=network.target

[Service]
Type=oneshot
WorkingDirectory={work_dir}
ExecStart={ddns_cmd} -c "{config_path}"
""".format(
            work_dir=os.getcwd(),
            ddns_cmd=self.ddns_cmd,
            config_path=os.path.abspath(self.config_path)
        )
        
        timer_content = """[Unit]
Description=DDNS automatic IP update timer

[Timer]
OnUnitActiveSec={interval}m
Unit=ddns.service

[Install]
WantedBy=multi-user.target
""".format(interval=self.interval)
        
        # Check permissions
        if os.geteuid() != 0:
            logger.error("Root permission required for systemd installation.")
            logger.info("Please run with sudo: sudo %s -m ddns task --install", sys.executable)
            return False
        
        # Write service and timer files
        with open("/etc/systemd/system/ddns.service", "w") as f:
            f.write(service_content)
        
        with open("/etc/systemd/system/ddns.timer", "w") as f:
            f.write(timer_content)
        
        # Reload systemd and enable timer
        subprocess.check_call(["systemctl", "daemon-reload"])
        subprocess.check_call(["systemctl", "enable", "ddns.timer"])
        subprocess.check_call(["systemctl", "start", "ddns.timer"])
        
        logger.info("DDNS systemd timer installed successfully")
        logger.info("Use 'systemctl status ddns.timer' to check status")
        logger.info("Use 'journalctl -u ddns.service' to view logs")
        return True

    def _uninstall_systemd(self):
        # type: () -> bool
        """Uninstall systemd timer and service"""
        if os.geteuid() != 0:
            logger.error("Root permission required for systemd uninstallation.")
            logger.info("Please run with sudo: sudo %s -m ddns task --delete", sys.executable)
            return False
        
        # Stop and disable timer
        subprocess.call(["systemctl", "stop", "ddns.timer"], stderr=subprocess.DEVNULL)
        subprocess.call(["systemctl", "disable", "ddns.timer"], stderr=subprocess.DEVNULL)
        
        # Remove files
        for path in ["/etc/systemd/system/ddns.service", "/etc/systemd/system/ddns.timer"]:
            if os.path.exists(path):
                os.remove(path)
        
        subprocess.check_call(["systemctl", "daemon-reload"])
        logger.info("DDNS systemd timer uninstalled successfully")
        return True

    def _install_cron(self):
        # type: () -> bool
        """Install cron job"""
        cron_entry = "*/{} * * * * {} -c {} >> {} 2>&1".format(
            self.interval,
            self.ddns_cmd,
            os.path.abspath(self.config_path),
            os.path.abspath(self.log_path)
        )
        
        # Get existing crontab
        try:
            existing_cron = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL).decode()
        except subprocess.CalledProcessError:
            existing_cron = ""
        
        # Check if DDNS entry already exists
        if "ddns" in existing_cron.lower():
            # Remove existing DDNS entries
            lines = [line for line in existing_cron.split('\n') 
                    if line and "ddns" not in line.lower()]
            existing_cron = '\n'.join(lines)
        
        # Add new DDNS entry
        new_cron = existing_cron.rstrip() + '\n' + cron_entry + '\n'
        
        # Write new crontab
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(new_cron)
            temp_path = f.name
        
        try:
            subprocess.check_call(["crontab", temp_path])
            logger.info("DDNS cron job installed successfully")
            logger.info("Update interval: every %d minutes", self.interval)
            return True
        finally:
            os.unlink(temp_path)

    def _uninstall_cron(self):
        # type: () -> bool
        """Uninstall cron job"""
        try:
            existing_cron = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL).decode()
        except subprocess.CalledProcessError:
            logger.info("No crontab found")
            return True
        
        # Remove DDNS entries
        lines = [line for line in existing_cron.split('\n') 
                if line and "ddns" not in line.lower()]
        new_cron = '\n'.join(lines) + '\n' if lines else ""
        
        # Write new crontab
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(new_cron)
            temp_path = f.name
        
        try:
            subprocess.check_call(["crontab", temp_path])
            logger.info("DDNS cron job uninstalled successfully")
            return True
        finally:
            os.unlink(temp_path)

    def _install_launchd(self):
        # type: () -> bool
        """Install macOS launchd plist"""
        plist_dir = os.path.expanduser("~/Library/LaunchAgents")
        plist_path = os.path.join(plist_dir, "cc.newfuture.ddns.plist")
        
        # Create directory if not exists
        os.makedirs(plist_dir, exist_ok=True)
        
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>cc.newfuture.ddns</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>-m</string>
        <string>ddns</string>
        <string>-c</string>
        <string>{config_path}</string>
    </array>
    <key>StartInterval</key>
    <integer>{interval_seconds}</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_path}</string>
    <key>StandardErrorPath</key>
    <string>{log_path}</string>
    <key>WorkingDirectory</key>
    <string>{work_dir}</string>
</dict>
</plist>
""".format(
            python=sys.executable,
            config_path=os.path.abspath(self.config_path),
            interval_seconds=self.interval * 60,
            log_path=os.path.abspath(self.log_path),
            work_dir=os.getcwd()
        )
        
        with open(plist_path, "w") as f:
            f.write(plist_content)
        
        # Load the plist
        subprocess.check_call(["launchctl", "load", plist_path])
        
        logger.info("DDNS launchd service installed successfully")
        logger.info("Use 'launchctl list cc.newfuture.ddns' to check status")
        return True

    def _uninstall_launchd(self):
        # type: () -> bool
        """Uninstall macOS launchd plist"""
        plist_path = os.path.expanduser("~/Library/LaunchAgents/cc.newfuture.ddns.plist")
        
        if os.path.exists(plist_path):
            # Unload the plist
            subprocess.call(["launchctl", "unload", plist_path], stderr=subprocess.DEVNULL)
            # Remove the plist file
            os.remove(plist_path)
        
        logger.info("DDNS launchd service uninstalled successfully")
        return True

    def _install_schtasks(self):
        # type: () -> bool
        """Install Windows scheduled task"""
        # Prepare command
        if hasattr(sys, 'frozen'):
            # If running as compiled executable
            cmd = '"{}" -c "{}"'.format(sys.executable, os.path.abspath(self.config_path))
        else:
            # If running as Python script
            cmd = '"{}" -m ddns -c "{}"'.format(sys.executable, os.path.abspath(self.config_path))
        
        # Check if running as administrator
        try:
            subprocess.check_output(["net", "session"], stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            logger.error("Administrator privileges required for Windows task installation.")
            logger.info("Please run as administrator")
            return False
        
        # Create scheduled task
        subprocess.check_call([
            "schtasks", "/Create", "/SC", "MINUTE", "/MO", str(self.interval),
            "/TR", cmd, "/TN", self.task_name, "/F"
        ])
        
        logger.info("DDNS Windows scheduled task installed successfully")
        logger.info("Use 'schtasks /query /tn %s' to check status", self.task_name)
        return True

    def _uninstall_schtasks(self):
        # type: () -> bool
        """Uninstall Windows scheduled task"""
        try:
            subprocess.check_call(["schtasks", "/Delete", "/TN", self.task_name, "/F"])
            logger.info("DDNS Windows scheduled task uninstalled successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to uninstall Windows scheduled task: %s", e)
            return False