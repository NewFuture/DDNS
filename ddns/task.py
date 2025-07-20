# -*- coding:utf-8 -*-
"""
Task scheduling management for DDNS
Cross-platform support for cron, systemd, launchd, and schtasks
@author: NewFuture
"""

import platform
import os
import sys
import subprocess
import tempfile
from logging import getLogger

# Python 2/3 compatibility
try:
    from shlex import quote
except ImportError:
    from pipes import quote


class TaskManager(object):
    """
    Cross-platform task scheduler manager
    """
    
    def __init__(self, logger=None):
        # type: (getLogger | None) -> None
        self.logger = logger or getLogger(__name__)
        self.system = platform.system().lower()
        self.ddns_version = self._get_ddns_version()
        
    def _get_ddns_version(self):
        # type: () -> str
        """Get DDNS version for task identification"""
        try:
            from . import __version__
            return __version__
        except ImportError:
            return "unknown"
    
    def _get_python_executable(self):
        # type: () -> str
        """Get the current Python executable path"""
        return sys.executable
    
    def _get_ddns_module_path(self):
        # type: () -> str
        """Get the path to run DDNS module"""
        # Use python -m ddns approach for better compatibility
        return "-m ddns"
    
    def _run_command(self, cmd, check_output=False, shell=False):
        # type: (list[str] | str, bool, bool) -> tuple[int, str, str]
        """
        Run system command and return (exit_code, stdout, stderr)
        """
        try:
            if check_output:
                if hasattr(subprocess, 'check_output'):
                    # Python 2.7+
                    stdout = subprocess.check_output(cmd, shell=shell, stderr=subprocess.STDOUT)
                    return 0, stdout.decode('utf-8'), ""
                else:
                    # Fallback for older Python versions
                    proc = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = proc.communicate()
                    return proc.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')
            else:
                exit_code = subprocess.call(cmd, shell=shell)
                return exit_code, "", ""
        except (OSError, subprocess.CalledProcessError) as e:
            self.logger.error("Command failed: %s", e)
            return 1, "", str(e)
        except Exception as e:
            self.logger.error("Unexpected error running command: %s", e)
            return 1, "", str(e)
    
    def detect_available_schedulers(self):
        # type: () -> list[str]
        """
        Detect available task schedulers on current system
        Returns list of available scheduler names
        """
        available = []
        
        if self.system == "linux":
            # Check for systemd
            if self._check_systemd():
                available.append("systemd")
            # Check for cron
            if self._check_cron():
                available.append("cron")
        elif self.system == "darwin":  # macOS
            # Check for launchd
            if self._check_launchd():
                available.append("launchd")
            # Check for cron
            if self._check_cron():
                available.append("cron")
        elif self.system == "windows":
            # Check for schtasks
            if self._check_schtasks():
                available.append("schtasks")
        
        return available
    
    def _check_systemd(self):
        # type: () -> bool
        """Check if systemd is available"""
        exit_code, _, _ = self._run_command(["systemctl", "--version"], check_output=True)
        return exit_code == 0
    
    def _check_cron(self):
        # type: () -> bool
        """Check if cron is available"""
        # Check for crontab command
        exit_code, _, _ = self._run_command(["which", "crontab"], check_output=True)
        if exit_code == 0:
            return True
        # Check for service cron on some systems
        exit_code, _, _ = self._run_command(["service", "cron", "status"], check_output=True)
        return exit_code == 0
    
    def _check_launchd(self):
        # type: () -> bool
        """Check if launchd is available (macOS)"""
        exit_code, _, _ = self._run_command(["launchctl", "version"], check_output=True)
        return exit_code == 0
    
    def _check_schtasks(self):
        # type: () -> bool
        """Check if schtasks is available (Windows)"""
        exit_code, _, _ = self._run_command(["schtasks", "/?"], check_output=True)
        return exit_code == 0
    
    def get_preferred_scheduler(self):
        # type: () -> str | None
        """Get the preferred scheduler for current platform"""
        available = self.detect_available_schedulers()
        if not available:
            return None
        
        # Priority order by platform
        if self.system == "linux":
            preferences = ["systemd", "cron"]
        elif self.system == "darwin":
            preferences = ["launchd", "cron"]
        elif self.system == "windows":
            preferences = ["schtasks"]
        else:
            preferences = available
        
        for scheduler in preferences:
            if scheduler in available:
                return scheduler
        
        return available[0] if available else None
    
    def is_task_installed(self, scheduler=None):
        # type: (str | None) -> tuple[bool, str | None, dict]
        """
        Check if DDNS task is installed
        Returns (is_installed, scheduler_used, task_info)
        """
        if scheduler:
            schedulers = [scheduler]
        else:
            schedulers = self.detect_available_schedulers()
        
        for sched in schedulers:
            if sched == "systemd":
                installed, info = self._check_systemd_task()
                if installed:
                    return True, sched, info
            elif sched == "cron":
                installed, info = self._check_cron_task()
                if installed:
                    return True, sched, info
            elif sched == "launchd":
                installed, info = self._check_launchd_task()
                if installed:
                    return True, sched, info
            elif sched == "schtasks":
                installed, info = self._check_schtasks_task()
                if installed:
                    return True, sched, info
        
        return False, None, {}
    
    def _check_systemd_task(self):
        # type: () -> tuple[bool, dict]
        """Check systemd timer status"""
        # Check if timer exists and is enabled
        exit_code, output, _ = self._run_command(["systemctl", "is-enabled", "ddns.timer"], check_output=True)
        if exit_code != 0:
            return False, {}
        
        # Get timer status
        exit_code, status_output, _ = self._run_command(["systemctl", "status", "ddns.timer"], check_output=True)
        
        info = {
            "enabled": "enabled" in output.lower(),
            "status": status_output.split("\n")[0] if status_output else "unknown",
            "type": "systemd timer",
            "interval": "5 minutes"
        }
        return True, info
    
    def _check_cron_task(self):
        # type: () -> tuple[bool, dict]
        """Check cron job status"""
        exit_code, output, _ = self._run_command(["crontab", "-l"], check_output=True)
        if exit_code != 0:
            return False, {}
        
        # Look for DDNS-related cron entries
        lines = output.strip().split("\n")
        for line in lines:
            if "ddns" in line.lower() and ("run.py" in line or "-m ddns" in line):
                info = {
                    "enabled": True,
                    "status": "active",
                    "type": "cron job",
                    "schedule": line.split()[0:5],
                    "command": " ".join(line.split()[5:])
                }
                return True, info
        
        return False, {}
    
    def _check_launchd_task(self):
        # type: () -> tuple[bool, dict]
        """Check launchd job status"""
        # Check for ddns plist file
        plist_paths = [
            os.path.expanduser("~/Library/LaunchAgents/com.newfuture.ddns.plist"),
            "/Library/LaunchAgents/com.newfuture.ddns.plist",
            "/Library/LaunchDaemons/com.newfuture.ddns.plist"
        ]
        
        for plist_path in plist_paths:
            if os.path.exists(plist_path):
                # Check if loaded
                exit_code, output, _ = self._run_command(["launchctl", "list", "com.newfuture.ddns"], check_output=True)
                loaded = exit_code == 0
                
                info = {
                    "enabled": loaded,
                    "status": "loaded" if loaded else "not loaded",
                    "type": "launchd job",
                    "plist": plist_path,
                    "interval": "5 minutes"
                }
                return True, info
        
        return False, {}
    
    def _check_schtasks_task(self):
        # type: () -> tuple[bool, dict]
        """Check Windows scheduled task status"""
        exit_code, output, _ = self._run_command(['schtasks', '/Query', '/TN', 'DDNS'], check_output=True)
        if exit_code != 0:
            return False, {}
        
        # Parse schtasks output for status information
        lines = output.strip().split("\n")
        status_line = next((line for line in lines if "Status:" in line), "")
        schedule_line = next((line for line in lines if "Schedule Type:" in line), "")
        
        info = {
            "enabled": "Ready" in status_line or "Running" in status_line,
            "status": status_line.split(":")[-1].strip() if status_line else "unknown",
            "type": "scheduled task",
            "schedule": schedule_line.split(":")[-1].strip() if schedule_line else "unknown"
        }
        return True, info
    
    def install_task(self, scheduler=None, interval=5, config_file=None, force=False):
        # type: (str | None, int, str | None, bool) -> bool
        """
        Install DDNS scheduled task
        """
        if not scheduler:
            scheduler = self.get_preferred_scheduler()
            if not scheduler:
                self.logger.error("No supported task scheduler found on this system")
                return False
        
        # Check if already installed
        is_installed, current_scheduler, _ = self.is_task_installed()
        if is_installed and not force:
            if current_scheduler == scheduler:
                self.logger.info("DDNS task already installed with %s", scheduler)
                return True
            else:
                self.logger.warning("DDNS task already installed with %s, use --force to reinstall with %s", 
                                  current_scheduler, scheduler)
                return False
        
        # Uninstall existing task if force reinstall
        if is_installed and force:
            self.logger.info("Removing existing task before reinstall")
            self.uninstall_task()
        
        # Install with selected scheduler
        if scheduler == "systemd":
            return self._install_systemd_task(interval, config_file)
        elif scheduler == "cron":
            return self._install_cron_task(interval, config_file)
        elif scheduler == "launchd":
            return self._install_launchd_task(interval, config_file)
        elif scheduler == "schtasks":
            return self._install_schtasks_task(interval, config_file)
        else:
            self.logger.error("Unsupported scheduler: %s", scheduler)
            return False
    
    def _install_systemd_task(self, interval, config_file):
        # type: (int, str | None) -> bool
        """Install systemd timer"""
        try:
            python_exe = self._get_python_executable()
            ddns_cmd = self._get_ddns_module_path()
            config_arg = " -c " + quote(config_file) if config_file else ""
            
            service_content = """[Unit]
Description=NewFuture DDNS
After=network.target

[Service]
Type=oneshot
ExecStart={python} {ddns_cmd}{config_arg}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
""".format(python=python_exe, ddns_cmd=ddns_cmd, config_arg=config_arg)
            
            timer_content = """[Unit]
Description=NewFuture DDNS Timer

[Timer]
OnUnitActiveSec={interval}m
Unit=ddns.service

[Install]
WantedBy=multi-user.target
""".format(interval=interval)
            
            # Write service file
            with open("/tmp/ddns.service", "w") as f:
                f.write(service_content)
            
            # Write timer file
            with open("/tmp/ddns.timer", "w") as f:
                f.write(timer_content)
            
            # Copy files to systemd directory
            service_path = "/etc/systemd/system/ddns.service"
            timer_path = "/etc/systemd/system/ddns.timer"
            
            exit_code, _, _ = self._run_command(["sudo", "cp", "/tmp/ddns.service", service_path])
            if exit_code != 0:
                self.logger.error("Failed to copy service file")
                return False
                
            exit_code, _, _ = self._run_command(["sudo", "cp", "/tmp/ddns.timer", timer_path])
            if exit_code != 0:
                self.logger.error("Failed to copy timer file")
                return False
            
            # Reload systemd and enable timer
            self._run_command(["sudo", "systemctl", "daemon-reload"])
            exit_code, _, _ = self._run_command(["sudo", "systemctl", "enable", "ddns.timer"])
            if exit_code != 0:
                self.logger.error("Failed to enable systemd timer")
                return False
                
            exit_code, _, _ = self._run_command(["sudo", "systemctl", "start", "ddns.timer"])
            if exit_code != 0:
                self.logger.error("Failed to start systemd timer")
                return False
            
            self.logger.info("Successfully installed DDNS systemd timer (interval: %d minutes)", interval)
            self.logger.info("Use 'systemctl status ddns.timer' to check status")
            self.logger.info("Use 'journalctl -u ddns.service' to view logs")
            
            # Clean up temp files
            os.unlink("/tmp/ddns.service")
            os.unlink("/tmp/ddns.timer")
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to install systemd task: %s", e)
            return False
    
    def _install_cron_task(self, interval, config_file):
        # type: (int, str | None) -> bool
        """Install cron job"""
        try:
            python_exe = self._get_python_executable()
            ddns_cmd = self._get_ddns_module_path()
            config_arg = " -c " + quote(config_file) if config_file else ""
            
            # Create cron schedule (every N minutes)
            cron_schedule = "*/{} * * * *".format(interval)
            cron_command = "{} {} {}".format(python_exe, ddns_cmd, config_arg).strip()
            cron_line = "{} {}".format(cron_schedule, cron_command)
            
            # Get current crontab
            exit_code, current_crontab, _ = self._run_command(["crontab", "-l"], check_output=True)
            if exit_code != 0:
                current_crontab = ""
            
            # Check if DDNS cron already exists
            lines = current_crontab.strip().split("\n") if current_crontab.strip() else []
            ddns_lines = [line for line in lines if "ddns" in line.lower()]
            
            if ddns_lines:
                self.logger.info("Replacing existing DDNS cron job")
                lines = [line for line in lines if "ddns" not in line.lower()]
            
            # Add new DDNS cron job
            lines.append("# DDNS auto-update job (v{})".format(self.ddns_version))
            lines.append(cron_line)
            
            # Write new crontab
            new_crontab = "\n".join(lines) + "\n"
            
            # Use temporary file for crontab input
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                temp_file.write(new_crontab)
                temp_file_path = temp_file.name
            
            try:
                exit_code, _, _ = self._run_command(["crontab", temp_file_path])
                if exit_code != 0:
                    self.logger.error("Failed to install cron job")
                    return False
                
                self.logger.info("Successfully installed DDNS cron job (interval: %d minutes)", interval)
                self.logger.info("Use 'crontab -l' to view installed cron jobs")
                return True
                
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.logger.error("Failed to install cron task: %s", e)
            return False
    
    def _install_launchd_task(self, interval, config_file):
        # type: (int, str | None) -> bool
        """Install launchd job (macOS)"""
        try:
            python_exe = self._get_python_executable()
            ddns_cmd = self._get_ddns_module_path()
            
            # Build command arguments
            args = [python_exe] + ddns_cmd.split()
            if config_file:
                args.extend(["-c", config_file])
            
            plist_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.newfuture.ddns</string>
    <key>ProgramArguments</key>
    <array>
{args}
    </array>
    <key>StartInterval</key>
    <integer>{interval}</integer>
    <key>StandardOutPath</key>
    <string>/tmp/ddns.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ddns.error.log</string>
</dict>
</plist>'''.format(
                args="\n".join("        <string>{}</string>".format(arg) for arg in args),
                interval=interval * 60  # launchd uses seconds
            )
            
            # Determine plist location
            plist_dir = os.path.expanduser("~/Library/LaunchAgents")
            plist_path = os.path.join(plist_dir, "com.newfuture.ddns.plist")
            
            # Create directory if needed
            if not os.path.exists(plist_dir):
                os.makedirs(plist_dir)
            
            # Write plist file
            with open(plist_path, "w") as f:
                f.write(plist_content)
            
            # Load the job
            exit_code, _, _ = self._run_command(["launchctl", "load", plist_path])
            if exit_code != 0:
                self.logger.error("Failed to load launchd job")
                return False
            
            self.logger.info("Successfully installed DDNS launchd job (interval: %d minutes)", interval)
            self.logger.info("Plist file: %s", plist_path)
            self.logger.info("Use 'launchctl list com.newfuture.ddns' to check status")
            return True
            
        except Exception as e:
            self.logger.error("Failed to install launchd task: %s", e)
            return False
    
    def _install_schtasks_task(self, interval, config_file):
        # type: (int, str | None) -> bool
        """Install Windows scheduled task"""
        try:
            python_exe = self._get_python_executable()
            ddns_cmd = self._get_ddns_module_path()
            config_arg = " -c " + quote(config_file) if config_file else ""
            
            task_command = '"{}" {} {}'.format(python_exe, ddns_cmd, config_arg).strip()
            
            # Create scheduled task
            cmd = [
                "schtasks", "/Create",
                "/SC", "MINUTE",
                "/MO", str(interval),
                "/TN", "DDNS",
                "/TR", task_command,
                "/F"  # Force overwrite if exists
            ]
            
            exit_code, output, _ = self._run_command(cmd, check_output=True)
            if exit_code != 0:
                self.logger.error("Failed to create scheduled task")
                return False
            
            self.logger.info("Successfully installed DDNS scheduled task (interval: %d minutes)", interval)
            self.logger.info("Use 'schtasks /Query /TN DDNS' to check status")
            return True
            
        except Exception as e:
            self.logger.error("Failed to install scheduled task: %s", e)
            return False
    
    def uninstall_task(self, scheduler=None):
        # type: (str | None) -> bool
        """
        Uninstall DDNS scheduled task
        """
        is_installed, current_scheduler, _ = self.is_task_installed(scheduler)
        
        if not is_installed:
            self.logger.info("No DDNS task found to uninstall")
            return True
        
        target_scheduler = scheduler or current_scheduler
        
        if target_scheduler == "systemd":
            return self._uninstall_systemd_task()
        elif target_scheduler == "cron":
            return self._uninstall_cron_task()
        elif target_scheduler == "launchd":
            return self._uninstall_launchd_task()
        elif target_scheduler == "schtasks":
            return self._uninstall_schtasks_task()
        else:
            self.logger.error("Unknown scheduler: %s", target_scheduler)
            return False
    
    def _uninstall_systemd_task(self):
        # type: () -> bool
        """Uninstall systemd timer"""
        try:
            # Stop and disable timer
            self._run_command(["sudo", "systemctl", "stop", "ddns.timer"])
            self._run_command(["sudo", "systemctl", "disable", "ddns.timer"])
            
            # Remove files
            self._run_command(["sudo", "rm", "-f", "/etc/systemd/system/ddns.service"])
            self._run_command(["sudo", "rm", "-f", "/etc/systemd/system/ddns.timer"])
            
            # Reload systemd
            self._run_command(["sudo", "systemctl", "daemon-reload"])
            
            self.logger.info("Successfully uninstalled DDNS systemd timer")
            return True
            
        except Exception as e:
            self.logger.error("Failed to uninstall systemd task: %s", e)
            return False
    
    def _uninstall_cron_task(self):
        # type: () -> bool
        """Uninstall cron job"""
        try:
            # Get current crontab
            exit_code, current_crontab, _ = self._run_command(["crontab", "-l"], check_output=True)
            if exit_code != 0:
                self.logger.info("No crontab found")
                return True
            
            # Remove DDNS-related lines
            lines = current_crontab.strip().split("\n")
            filtered_lines = []
            
            for line in lines:
                if "ddns" not in line.lower():
                    filtered_lines.append(line)
            
            # Write new crontab
            if filtered_lines:
                new_crontab = "\n".join(filtered_lines) + "\n"
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                    temp_file.write(new_crontab)
                    temp_file_path = temp_file.name
                
                try:
                    exit_code, _, _ = self._run_command(["crontab", temp_file_path])
                    if exit_code != 0:
                        self.logger.error("Failed to update crontab")
                        return False
                finally:
                    os.unlink(temp_file_path)
            else:
                # Remove entire crontab if it's empty
                self._run_command(["crontab", "-r"])
            
            self.logger.info("Successfully uninstalled DDNS cron job")
            return True
            
        except Exception as e:
            self.logger.error("Failed to uninstall cron task: %s", e)
            return False
    
    def _uninstall_launchd_task(self):
        # type: () -> bool
        """Uninstall launchd job"""
        try:
            # Unload job
            self._run_command(["launchctl", "unload", "com.newfuture.ddns"])
            
            # Remove plist files
            plist_paths = [
                os.path.expanduser("~/Library/LaunchAgents/com.newfuture.ddns.plist"),
                "/Library/LaunchAgents/com.newfuture.ddns.plist",
                "/Library/LaunchDaemons/com.newfuture.ddns.plist"
            ]
            
            removed = False
            for plist_path in plist_paths:
                if os.path.exists(plist_path):
                    os.unlink(plist_path)
                    removed = True
                    self.logger.info("Removed plist file: %s", plist_path)
            
            if removed:
                self.logger.info("Successfully uninstalled DDNS launchd job")
            else:
                self.logger.info("No launchd job found to remove")
            return True
            
        except Exception as e:
            self.logger.error("Failed to uninstall launchd task: %s", e)
            return False
    
    def _uninstall_schtasks_task(self):
        # type: () -> bool
        """Uninstall Windows scheduled task"""
        try:
            exit_code, _, _ = self._run_command(["schtasks", "/Delete", "/TN", "DDNS", "/F"])
            if exit_code == 0:
                self.logger.info("Successfully uninstalled DDNS scheduled task")
                return True
            else:
                self.logger.warning("Scheduled task 'DDNS' not found or failed to delete")
                return False
                
        except Exception as e:
            self.logger.error("Failed to uninstall scheduled task: %s", e)
            return False
    
    def get_task_status(self):
        # type: () -> dict
        """
        Get comprehensive task status information
        """
        is_installed, scheduler, task_info = self.is_task_installed()
        available_schedulers = self.detect_available_schedulers()
        preferred_scheduler = self.get_preferred_scheduler()
        
        status = {
            "system": self.system,
            "available_schedulers": available_schedulers,
            "preferred_scheduler": preferred_scheduler,
            "installed": is_installed,
            "current_scheduler": scheduler,
            "task_info": task_info,
            "ddns_version": self.ddns_version
        }
        
        return status


def print_task_status(status):
    # type: (dict) -> None
    """
    Print formatted task status information
    """
    print("DDNS Task Status")
    print("================")
    print("System: {}".format(status["system"].title()))
    print("DDNS Version: {}".format(status["ddns_version"]))
    print("")
    
    print("Available Schedulers: {}".format(", ".join(status["available_schedulers"]) or "None"))
    print("Preferred Scheduler: {}".format(status["preferred_scheduler"] or "None"))
    print("")
    
    if status["installed"]:
        print("Task Status: INSTALLED")
        print("Current Scheduler: {}".format(status["current_scheduler"]))
        
        task_info = status["task_info"]
        if task_info:
            print("Task Type: {}".format(task_info.get("type", "unknown")))
            print("Status: {}".format(task_info.get("status", "unknown")))
            print("Enabled: {}".format("Yes" if task_info.get("enabled") else "No"))
            
            if "interval" in task_info:
                print("Interval: {}".format(task_info["interval"]))
            elif "schedule" in task_info:
                print("Schedule: {}".format(task_info["schedule"]))
            
            if "command" in task_info:
                print("Command: {}".format(task_info["command"]))
            elif "plist" in task_info:
                print("Plist File: {}".format(task_info["plist"]))
    else:
        print("Task Status: NOT INSTALLED")
        if status["preferred_scheduler"]:
            print("Recommended: Use 'ddns task --install' to install with {}".format(status["preferred_scheduler"]))
        else:
            print("No supported task schedulers found on this system")


def main():
    """
    Main function for task command
    """
    # This will be called from the CLI parser
    pass