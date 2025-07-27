# -*- coding:utf-8 -*-
"""
Task Management Utility for DDNS scheduled tasks
@author: NewFuture
"""

import os
import platform
import re
import subprocess
import sys
import tempfile
from logging import getLogger
from .fileio import read_file_safely, write_file

__all__ = ["get_scheduler_type", "is_installed", "get_status", "install", "uninstall", "enable", "disable"]

logger = getLogger(__name__)

# Constants
TASK_NAME = "DDNS"
LAUNCHD_LABEL = "cc.newfuture.ddns"
SYSTEMD_SERVICE = "ddns.service"
SYSTEMD_TIMER = "ddns.timer"
VBS_SCRIPT = "~\\AppData\\Local\\DDNS\\ddns_silent.vbs"

# Scheduler control commands configuration
SCHEDULER_COMMANDS = {
    "systemd": {
        "enable": [
            (["systemctl", "enable", SYSTEMD_TIMER], "enable"),
            (["systemctl", "start", SYSTEMD_TIMER], "start"),
        ],
        "disable": [
            (["systemctl", "stop", SYSTEMD_TIMER], "stop"),
            (["systemctl", "disable", SYSTEMD_TIMER], "disable"),
        ],
        "success_enable": "DDNS systemd timer enabled successfully",
        "success_disable": "DDNS systemd timer disabled successfully",
    },
    "launchd": {
        "enable": [(["launchctl", "load", "PLIST_PATH"], "load")],
        "disable": [(["launchctl", "unload", "PLIST_PATH"], "unload")],
        "success_enable": "DDNS launchd service enabled successfully",
        "success_disable": "DDNS launchd service disabled successfully",
    },
    "schtasks": {
        "enable": [(["schtasks", "/Change", "/TN", TASK_NAME, "/Enable"], "enable")],
        "disable": [(["schtasks", "/Change", "/TN", TASK_NAME, "/Disable"], "disable")],
        "success_enable": "DDNS Windows scheduled task enabled successfully",
        "success_disable": "DDNS Windows scheduled task disabled successfully",
    },
}


def _run_command_safely(command, **kwargs):
    # type: (list, **any) -> bytes | None
    """Safely run subprocess command, return None if failed"""
    try:
        kwargs.setdefault("stderr", subprocess.DEVNULL)
        return subprocess.check_output(command, **kwargs)
    except (subprocess.CalledProcessError, OSError):
        return None


def _dispatch_scheduler_operation(operation, *args, **kwargs):
    """Generic scheduler operation dispatcher"""
    scheduler = get_scheduler_type()

    # Handle enable/disable operations directly
    if operation in ["enable", "disable"]:
        if scheduler == "cron":
            # Special handling for cron
            if operation == "enable":
                logger.info("Cron jobs are automatically enabled when installed")
                return True
            else:
                logger.warning("Cron jobs cannot be disabled without removing them")
                logger.info("To disable, use uninstall command instead")
                return False
        elif scheduler == "launchd":
            # Special handling for launchd - need plist path
            plist_path = os.path.expanduser("~/Library/LaunchAgents/{}.plist".format(LAUNCHD_LABEL))
            if operation == "enable" and not os.path.exists(plist_path):
                logger.error("DDNS launchd service not found")
                return False
            return _control_scheduler(scheduler, operation, plist_path=plist_path)
        else:
            # Use generic control for systemd and schtasks
            return _control_scheduler(scheduler, operation)

    # Handle install/uninstall operations with specific functions
    func_name = "_{}_{}".format(operation, scheduler)
    try:
        func = globals().get(func_name)
        if func:
            return func(*args, **kwargs)
        else:
            logger.error("Unsupported operation %s for scheduler %s", operation, scheduler)
            return False
    except Exception as e:
        logger.error("Failed to %s DDNS task: %s", operation, e)
        return False


def get_scheduler_type():  # type: () -> str
    """Determine the best task scheduler for current system"""
    system = platform.system().lower()

    if system == "linux":
        # Check if systemd is the init system by reading /proc/1/comm
        init_name = read_file_safely("/proc/1/comm")
        if init_name and init_name.strip() == "systemd":
            return "systemd"
        return "cron"
    elif system == "darwin":  # macOS
        # Check if launchd directories exist
        launchd_dirs = ["/Library/LaunchDaemons", "/System/Library/LaunchDaemons"]
        if any(os.path.isdir(d) for d in launchd_dirs):
            return "launchd"
        return "cron"
    elif system == "windows":
        return "schtasks"
    else:
        # Fallback to cron for other Unix-like systems
        return "cron"


def is_installed():  # type: () -> bool
    """Check if DDNS task is installed"""
    scheduler = get_scheduler_type()

    try:
        if scheduler == "systemd":
            result = subprocess.check_output(["systemctl", "is-enabled", SYSTEMD_TIMER], stderr=subprocess.DEVNULL)
            return result.strip().decode("utf-8") == "enabled"
        elif scheduler == "cron":
            result = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL)
            return b"ddns" in result.lower()
        elif scheduler == "launchd":
            plist_path = os.path.expanduser("~/Library/LaunchAgents/{}.plist".format(LAUNCHD_LABEL))
            return os.path.exists(plist_path)
        elif scheduler == "schtasks":
            result = subprocess.check_output(["schtasks", "/query", "/tn", TASK_NAME], stderr=subprocess.DEVNULL)
            return TASK_NAME.encode() in result
    except (subprocess.CalledProcessError, OSError):
        pass

    return False


def get_status():
    # type: () -> dict
    """Get task status information"""
    scheduler = get_scheduler_type()
    installed = is_installed()
    status = {
        "installed": installed,
        "scheduler": scheduler,
        "system": platform.system().lower(),
    }

    if installed:
        try:
            status["running_status"] = _get_running_status(scheduler)
            # Try to get actual interval from installed task
            interval = _get_task_interval(scheduler)
            if interval:
                status["interval"] = interval
            # Get the command that will be executed
            command = _get_task_command(scheduler)
            if command:
                status["command"] = command
        except Exception as e:
            logger.debug("Failed to get running status: %s", e)
            status["running_status"] = "unknown"

    return status


def install(interval=5, force=False, ddns_args=None):
    # type: (int, bool, dict | None) -> bool
    """Install DDNS scheduled task"""
    if is_installed() and not force:
        logger.info("DDNS task is already installed. Use --force to reinstall.")
        return True

    scheduler = get_scheduler_type()
    logger.info("Installing DDNS task using %s scheduler...", scheduler)
    return _dispatch_scheduler_operation("install", interval, ddns_args)


def uninstall():
    # type: () -> bool
    """Uninstall DDNS scheduled task"""
    if not is_installed():
        logger.info("DDNS task is not installed.")
        return True

    scheduler = get_scheduler_type()
    logger.info("Uninstalling DDNS task from %s scheduler...", scheduler)
    return _dispatch_scheduler_operation("uninstall")


def enable():
    # type: () -> bool
    """Enable DDNS scheduled task"""
    if not is_installed():
        logger.error("DDNS task is not installed. Please install it first.")
        return False

    scheduler = get_scheduler_type()
    logger.info("Enabling DDNS task using %s scheduler...", scheduler)
    return _dispatch_scheduler_operation("enable")


def disable():
    # type: () -> bool
    """Disable DDNS scheduled task"""
    if not is_installed():
        logger.error("DDNS task is not installed.")
        return False

    scheduler = get_scheduler_type()
    logger.info("Disabling DDNS task using %s scheduler...", scheduler)
    return _dispatch_scheduler_operation("disable")


def _get_task_interval(scheduler):
    # type: (str) -> int | None
    """Get the actual interval from installed task"""
    if scheduler == "systemd":
        # Read timer configuration
        timer_path = "/etc/systemd/system/{}".format(SYSTEMD_TIMER)
        content = read_file_safely(timer_path)
        if content:
            # Look for OnUnitActiveSec=XXXm pattern
            match = re.search(r"OnUnitActiveSec=(\d+)m", content)
            if match:
                return int(match.group(1))
    elif scheduler == "cron":
        # Parse crontab to extract interval
        result = _run_command_safely(["crontab", "-l"])
        if result:
            cron_content = result.decode().lower()
            # Look for DDNS entries and parse cron schedule
            for line in cron_content.split("\n"):
                if "ddns" in line and line.strip() and not line.startswith("#"):
                    # Parse cron format: */X * * * * or similar patterns
                    parts = line.split()
                    if len(parts) >= 5:
                        minute_field = parts[0]
                        if minute_field.startswith("*/"):
                            return int(minute_field[2:])
    elif scheduler == "launchd":
        # Read plist file
        plist_path = os.path.expanduser("~/Library/LaunchAgents/{}.plist".format(LAUNCHD_LABEL))
        content = read_file_safely(plist_path)
        if content:
            # Look for StartInterval value (in seconds)
            match = re.search(r"<key>StartInterval</key>\s*<integer>(\d+)</integer>", content)
            if match:
                return int(match.group(1)) // 60  # Convert seconds to minutes
    elif scheduler == "schtasks":
        # Query Windows scheduled task
        result = _run_command_safely(["schtasks", "/query", "/tn", TASK_NAME, "/fo", "list", "/v"])
        if result:
            lines = result.decode().split("\n")
            for line in lines:
                if "Repeat: Every:" in line:
                    # Parse interval from output like "Repeat: Every: 0:05:00"
                    match = re.search(r"Every:\s*\d*:(\d+):00", line)
                    if match:
                        return int(match.group(1))

    return None


def _get_task_command(scheduler):
    # type: (str) -> str | None
    """Get the actual command from installed task"""
    if scheduler == "systemd":
        # Read service configuration
        service_path = "/etc/systemd/system/{}".format(SYSTEMD_SERVICE)
        content = read_file_safely(service_path)
        if content:
            # Look for ExecStart= line
            match = re.search(r"ExecStart=(.+)", content)
            if match:
                return match.group(1).strip()
    elif scheduler == "cron":
        # Parse crontab to extract command
        result = _run_command_safely(["crontab", "-l"])
        if result:
            cron_content = result.decode()
            # Look for DDNS entries and extract command
            for line in cron_content.split("\n"):
                if "ddns" in line.lower() and line.strip() and not line.startswith("#"):
                    # Extract command part (everything after the 5 time fields)
                    parts = line.split()
                    if len(parts) >= 6:
                        return " ".join(parts[5:])
    elif scheduler == "launchd":
        # Read plist file
        plist_path = os.path.expanduser("~/Library/LaunchAgents/{}.plist".format(LAUNCHD_LABEL))
        content = read_file_safely(plist_path)
        if content:
            # Look for ProgramArguments array
            # This is a simplified extraction - real plist parsing would be more complex
            program_match = re.search(r"<key>Program</key>\s*<string>([^<]+)</string>", content)
            if program_match:
                return program_match.group(1)
            # Try to extract from ProgramArguments
            args_section = re.search(r"<key>ProgramArguments</key>\s*<array>(.*?)</array>", content, re.DOTALL)
            if args_section:
                args_content = args_section.group(1)
                strings = re.findall(r"<string>([^<]+)</string>", args_content)
                if strings:
                    return " ".join(strings)
    elif scheduler == "schtasks":
        # Query Windows scheduled task for action details
        result = _run_command_safely(["schtasks", "/query", "/tn", TASK_NAME, "/fo", "list", "/v"])
        if result:
            lines = result.decode().split("\n")
            for line in lines:
                if "Task To Run:" in line:
                    # Extract command after "Task To Run:"
                    command = line.split("Task To Run:", 1)[1].strip()
                    return command

    return None


def _get_running_status(scheduler):
    # type: (str) -> str
    """Get running status for specific scheduler"""
    try:
        if scheduler == "systemd":
            result = subprocess.check_output(["systemctl", "is-active", "ddns.timer"], stderr=subprocess.DEVNULL)
            return result.strip().decode("utf-8")
        elif scheduler == "cron":
            subprocess.check_output(["pgrep", "-f", "cron"], stderr=subprocess.DEVNULL)
            return "active"
        elif scheduler == "launchd":
            result = subprocess.check_output(["launchctl", "list", "cc.newfuture.ddns"], stderr=subprocess.DEVNULL)
            return "active" if result else "inactive"
        elif scheduler == "schtasks":
            result = subprocess.check_output(
                ["schtasks", "/query", "/tn", "DDNS", "/fo", "csv"], stderr=subprocess.DEVNULL
            )
            lines = result.decode().strip().split("\n")
            if len(lines) > 1:
                # Parse CSV output - status is in the 3rd field (index 2)
                fields = [field.strip('"') for field in lines[1].split('","')]
                if len(fields) > 2:
                    return fields[2].lower()
            return "unknown"
    except subprocess.CalledProcessError:
        return "inactive"

    return "unknown"


def _get_ddns_cmd():
    # type: () -> str
    """Get DDNS command for scheduled execution"""
    if hasattr(sys, "frozen"):
        # If running as compiled executable
        return sys.executable
    else:
        # If running as Python script
        return '"{}" -m ddns'.format(sys.executable)


def _build_ddns_command(ddns_args=None):
    # type: (dict | None) -> str
    """Build DDNS command with arguments"""
    cmd_parts = [_get_ddns_cmd()]

    if not ddns_args:
        return " ".join(cmd_parts)

    # Process arguments in a unified way
    for key, value in ddns_args.items():
        if isinstance(value, bool):
            # Handle False boolean as string (for cases like --cache=false)
            cmd_parts.extend(["--{}".format(key), str(value).lower()])
        elif isinstance(value, list):
            for item in value:
                cmd_parts.extend(["--{}".format(key), '"{}"'.format(item)])
        else:
            cmd_parts.extend(["--{}".format(key), '"{}"'.format(value)])

    return " ".join(cmd_parts)


def _check_root_permission():
    # type: () -> bool
    """Check if running with root permission (Linux/Unix only)"""
    geteuid = getattr(os, "geteuid", None)
    if geteuid:
        return geteuid() == 0
    else:
        # Windows doesn't have geteuid, assume permission is OK
        return True


def _install_systemd(interval, ddns_args=None):
    # type: (int, dict | None) -> bool
    """Install systemd timer and service"""
    if not _check_root_permission():
        logger.error("Root permission required for systemd installation.")
        logger.info("Please run with sudo: sudo %s -m ddns task --install", sys.executable)
        return False

    ddns_command = _build_ddns_command(ddns_args)

    service_content = """[Unit]
Description=DDNS automatic IP update service
After=network.target

[Service]
Type=oneshot
WorkingDirectory={work_dir}
ExecStart={ddns_command}
""".format(
        work_dir=os.getcwd(),
        ddns_command=ddns_command,
    )

    timer_content = """[Unit]
Description=DDNS automatic IP update timer

[Timer]
OnUnitActiveSec={interval}m
Unit=ddns.service

[Install]
WantedBy=multi-user.target
""".format(
        interval=interval
    )

    # Write service and timer files
    write_file("/etc/systemd/system/{}".format(SYSTEMD_SERVICE), service_content)
    write_file("/etc/systemd/system/{}".format(SYSTEMD_TIMER), timer_content)

    # Reload systemd and enable timer
    subprocess.check_call(["systemctl", "daemon-reload"])
    subprocess.check_call(["systemctl", "enable", SYSTEMD_TIMER])
    subprocess.check_call(["systemctl", "start", SYSTEMD_TIMER])

    logger.info("DDNS systemd timer installed successfully")
    logger.info("Use 'systemctl status %s' to check status", SYSTEMD_TIMER)
    logger.info("Use 'journalctl -u %s' to view logs", SYSTEMD_SERVICE)
    return True


def _uninstall_systemd():
    # type: () -> bool
    """Uninstall systemd timer and service"""
    if not _check_root_permission():
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


def _update_crontab(new_cron):
    # type: (str) -> bool
    """Update crontab with new content"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(new_cron)
        temp_path = f.name

    try:
        subprocess.check_call(["crontab", temp_path])
        return True
    finally:
        os.unlink(temp_path)


def _install_cron(interval, ddns_args=None):
    # type: (int, dict | None) -> bool
    """Install cron job"""
    ddns_command = _build_ddns_command(ddns_args)

    # Build cron entry with cross-platform compatibility
    cron_entry = '*/{} * * * * cd "{}" && {}'.format(interval, os.getcwd(), ddns_command)

    # Get existing crontab (empty string if none exists)
    existing_cron = _run_command_safely(["crontab", "-l"])
    existing_cron = existing_cron.decode() if existing_cron else ""

    # Remove any existing DDNS entries and build new crontab
    lines = [line for line in existing_cron.split("\n") if line.strip() and "ddns" not in line.lower()]

    # Add new DDNS entry
    lines.append(cron_entry)
    new_cron = "\n".join(lines) + "\n"

    # Update crontab
    if _update_crontab(new_cron):
        logger.info("DDNS cron job installed successfully (interval: %d minutes)", interval)
        return True

    logger.error("Failed to install DDNS cron job")
    return False


def _uninstall_cron():
    # type: () -> bool
    """Uninstall cron job"""
    try:
        existing_cron = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL).decode()
    except subprocess.CalledProcessError:
        logger.info("No crontab found")
        return True

    # Remove DDNS entries
    lines = [line for line in existing_cron.split("\n") if line and "ddns" not in line.lower()]
    new_cron = "\n".join(lines) + "\n" if lines else ""

    # Update crontab
    if _update_crontab(new_cron):
        logger.info("DDNS cron job uninstalled successfully")
        return True
    return False


def _install_launchd(interval, ddns_args=None):
    # type: (int, dict | None) -> bool
    """Install macOS launchd plist"""
    plist_dir = os.path.expanduser("~/Library/LaunchAgents")
    plist_path = os.path.join(plist_dir, "{}.plist".format(LAUNCHD_LABEL))

    # Build program arguments using unified function
    program_args = _build_ddns_command(ddns_args)

    # Build program arguments XML
    program_args_xml = "\n".join(["        <string>{}</string>".format(arg) for arg in program_args])

    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
{program_args}
    </array>
    <key>StartInterval</key>
    <integer>{interval_seconds}</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{work_dir}</string>
</dict>
</plist>
""".format(
        label=LAUNCHD_LABEL,
        program_args=program_args_xml,
        interval_seconds=interval * 60,
        work_dir=os.getcwd(),
    )

    write_file(plist_path, plist_content)

    # Load the plist
    subprocess.check_call(["launchctl", "load", plist_path])

    logger.info("DDNS launchd service installed successfully")
    logger.info("Use 'launchctl list %s' to check status", LAUNCHD_LABEL)
    return True


def _uninstall_launchd():
    # type: () -> bool
    """Uninstall macOS launchd plist"""
    plist_path = os.path.expanduser("~/Library/LaunchAgents/{}.plist".format(LAUNCHD_LABEL))

    # Unload the plist
    subprocess.call(["launchctl", "unload", plist_path], stderr=subprocess.DEVNULL)
    # Remove the plist file
    try:
        os.remove(plist_path)
    except OSError:
        pass  # File doesn't exist

    logger.info("DDNS launchd service uninstalled successfully")
    return True


def _create_vbs_script(ddns_args=None):
    # type: (dict | None) -> str
    """Create VBS script for silent execution and return its path"""
    work_dir = os.getcwd()
    ddns_command = _build_ddns_command(ddns_args)

    vbs_content = """Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "{work_dir}"
objShell.Run "{ddns_command}", 0, False
""".format(
        work_dir=work_dir.replace("\\", "\\\\"),
        ddns_command=ddns_command.replace('"', '""'),
    )

    try:
        vbs_path = os.path.expanduser(VBS_SCRIPT)
        write_file(vbs_path, vbs_content)
        return vbs_path
    except Exception as e:
        logger.warning("Failed to create VBS in user AppData directory, using working directory: %s", e)
        # Fallback to working directory
        vbs_path = os.path.join(work_dir, ".ddns_silent.vbs")
        write_file(vbs_path, vbs_content)
        return vbs_path


def _install_schtasks(interval, ddns_args=None):
    # type: (int, dict | None) -> bool
    """Install Windows scheduled task"""
    vbs_path = _create_vbs_script(ddns_args)
    cmd = 'wscript.exe "{}"'.format(vbs_path)

    # Check if running as administrator (optional warning)
    try:
        subprocess.check_output(["net", "session"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        logger.info("Run as administrator is recommended for Windows task installation.")

    # Create scheduled task
    subprocess.check_call(
        ["schtasks", "/Create", "/SC", "MINUTE", "/MO", str(interval), "/TR", cmd, "/TN", TASK_NAME, "/F"]
    )

    logger.info("DDNS Windows scheduled task installed successfully")
    logger.info("Use 'schtasks /query /tn %s' to check status", TASK_NAME)
    return True


def _uninstall_schtasks():
    # type: () -> bool
    """Uninstall Windows scheduled task"""
    try:
        subprocess.check_call(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"])
        logger.info("DDNS Windows scheduled task uninstalled successfully")

        try:
            vbs_path = os.path.expanduser(VBS_SCRIPT)
            os.remove(vbs_path)
            logger.debug("Cleaned up VBS script file: %s", vbs_path)
        except OSError:
            pass  # File doesn't exist or can't be removed

        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to uninstall Windows scheduled task: %s", e)
        return False


def _control_scheduler(scheduler, operation, **kwargs):
    # type: (str, str, **Any) -> bool
    """Generic function to control scheduler services"""
    if scheduler not in SCHEDULER_COMMANDS:
        logger.error("Unsupported scheduler: %s", scheduler)
        return False

    config = SCHEDULER_COMMANDS[scheduler]
    if operation not in config:
        logger.error("Unsupported operation %s for scheduler %s", operation, scheduler)
        return False

    commands = config[operation]
    success_message = config[f"success_{operation}"]

    try:
        for command_template, action_name in commands:
            # Replace placeholders with actual values
            command = []
            for part in command_template:
                if part == "PLIST_PATH" and "plist_path" in kwargs:
                    command.append(kwargs["plist_path"])
                else:
                    command.append(part)
            subprocess.check_call(command)

        logger.info(success_message)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to %s %s scheduler: %s", operation, scheduler, e)
        return False
