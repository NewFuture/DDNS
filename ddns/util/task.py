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

__all__ = ["get_scheduler_type", "is_installed", "get_status", "install", "uninstall", "enable", "disable"]

logger = getLogger(__name__)

# Constants
TASK_NAME = "DDNS"
LAUNCHD_LABEL = "cc.newfuture.ddns"
SYSTEMD_SERVICE = "ddns.service"
SYSTEMD_TIMER = "ddns.timer"


def _dispatch_scheduler_operation(operation, *args, **kwargs):
    """
    Generic scheduler operation dispatcher

    Args:
        operation (str): Operation name (install, uninstall, enable, disable)
        *args: Arguments to pass to the operation function
        **kwargs: Keyword arguments to pass to the operation function

    Returns:
        bool: True if operation successful
    """
    scheduler = get_scheduler_type()
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


def get_scheduler_type():
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
            subprocess.check_call(["systemctl", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "systemd"
        except (subprocess.CalledProcessError, OSError):
            return "cron"
    elif system == "darwin":  # macOS
        # Check if launchctl is available
        try:
            subprocess.check_call(["launchctl", "help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "launchd"
        except (subprocess.CalledProcessError, OSError):
            return "cron"
    elif system == "windows":
        return "schtasks"
    else:
        # Fallback to cron for other Unix-like systems
        return "cron"


def is_installed():
    # type: () -> bool
    """
    Check if DDNS task is installed

    Returns:
        bool: True if task is installed
    """
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


def get_status(config_path=None, interval=5):
    # type: (str | None, int) -> dict
    """
    Get task status information

    Args:
        config_path (str): Path to DDNS config file
        interval (int): Update interval in minutes (default: 5)

    Returns:
        dict: Status information including installation status, scheduler type, etc.
    """
    scheduler = get_scheduler_type()
    installed = is_installed()
    status = {
        "installed": installed,
        "scheduler": scheduler,
        "system": platform.system().lower(),
        "interval": interval,
        "config_path": config_path,
    }

    if installed:
        try:
            status["running_status"] = _get_running_status(scheduler)
        except Exception as e:
            logger.debug("Failed to get running status: %s", e)
            status["running_status"] = "unknown"

    return status


def install(config_path=None, interval=5, force=False):
    # type: (str | None, int, bool) -> bool
    """
    Install DDNS scheduled task

    Args:
        config_path (str): Path to DDNS config file
        interval (int): Update interval in minutes (default: 5)
        force (bool): Force reinstall if already exists

    Returns:
        bool: True if installation successful
    """
    if is_installed() and not force:
        logger.info("DDNS task is already installed. Use --force to reinstall.")
        return True

    scheduler = get_scheduler_type()
    logger.info("Installing DDNS task using %s scheduler...", scheduler)
    return _dispatch_scheduler_operation("install", config_path, interval)


def uninstall():
    # type: () -> bool
    """
    Uninstall DDNS scheduled task

    Returns:
        bool: True if uninstallation successful
    """
    if not is_installed():
        logger.info("DDNS task is not installed.")
        return True

    scheduler = get_scheduler_type()
    logger.info("Uninstalling DDNS task from %s scheduler...", scheduler)
    return _dispatch_scheduler_operation("uninstall")


def enable():
    # type: () -> bool
    """
    Enable DDNS scheduled task

    Returns:
        bool: True if enable successful
    """
    if not is_installed():
        logger.error("DDNS task is not installed. Please install it first.")
        return False

    scheduler = get_scheduler_type()
    logger.info("Enabling DDNS task using %s scheduler...", scheduler)
    return _dispatch_scheduler_operation("enable")


def disable():
    # type: () -> bool
    """
    Disable DDNS scheduled task

    Returns:
        bool: True if disable successful
    """
    if not is_installed():
        logger.error("DDNS task is not installed.")
        return False

    scheduler = get_scheduler_type()
    logger.info("Disabling DDNS task using %s scheduler...", scheduler)
    return _dispatch_scheduler_operation("disable")


def _get_running_status(scheduler):
    # type: (str) -> str
    """
    Get running status for specific scheduler

    Args:
        scheduler (str): Scheduler type

    Returns:
        str: Running status
    """
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
    """
    Get DDNS command for scheduled execution

    Returns:
        str: DDNS command string
    """
    if hasattr(sys, "frozen"):
        # If running as compiled executable
        return sys.executable
    else:
        # If running as Python script
        return '"{}" -m ddns'.format(sys.executable)


def _check_root_permission():
    # type: () -> bool
    """Check if running with root permission (Linux/Unix only)"""
    try:
        # Check if we can access geteuid function
        geteuid = getattr(os, "geteuid", None)
        if geteuid:
            return geteuid() == 0
        else:
            # Windows doesn't have geteuid, assume permission is OK
            return True
    except (AttributeError, OSError):
        return True


def _install_systemd(config_path, interval):
    # type: (str | None, int) -> bool
    """Install systemd timer and service"""
    if not _check_root_permission():
        logger.error("Root permission required for systemd installation.")
        logger.info("Please run with sudo: sudo %s -m ddns task --install", sys.executable)
        return False

    ddns_cmd = _get_ddns_cmd()

    service_content = """[Unit]
Description=DDNS automatic IP update service
After=network.target

[Service]
Type=oneshot
WorkingDirectory={work_dir}
ExecStart={ddns_cmd} -c "{config_path}"
""".format(
        work_dir=os.getcwd(),
        ddns_cmd=ddns_cmd,
        config_path=os.path.abspath(config_path) if config_path else "config.json",
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
    with open("/etc/systemd/system/{}".format(SYSTEMD_SERVICE), "w") as f:
        f.write(service_content)

    with open("/etc/systemd/system/{}".format(SYSTEMD_TIMER), "w") as f:
        f.write(timer_content)

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


def _install_cron(config_path, interval):
    # type: (str | None, int) -> bool
    """Install cron job"""
    ddns_cmd = _get_ddns_cmd()
    work_dir = os.getcwd()

    # Use a more compatible approach that works across different Unix systems
    # Instead of relying on specific shell paths, use the system's default shell behavior
    # This approach works on Linux, macOS, BSD, Alpine, BusyBox, and other Unix variants
    cron_entry = '*/{} * * * * cd "{}" ; {} -c "{}" >> ddns.log 2>&1'.format(
        interval,
        work_dir,
        ddns_cmd,
        os.path.abspath(config_path) if config_path else "config.json",
    )

    # Get existing crontab
    try:
        existing_cron = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL).decode()
    except subprocess.CalledProcessError:
        existing_cron = ""

    # Check if DDNS entry already exists
    if "ddns" in existing_cron.lower():
        # Remove existing DDNS entries
        lines = [line for line in existing_cron.split("\n") if line and "ddns" not in line.lower()]
        existing_cron = "\n".join(lines)

    # Add new DDNS entry
    new_cron = existing_cron.rstrip() + "\n" + cron_entry + "\n"

    # Write new crontab
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(new_cron)
        temp_path = f.name

    try:
        subprocess.check_call(["crontab", temp_path])
        logger.info("DDNS cron job installed successfully")
        logger.info("Update interval: every %d minutes", interval)
        return True
    finally:
        os.unlink(temp_path)


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

    # Write new crontab
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(new_cron)
        temp_path = f.name

    try:
        subprocess.check_call(["crontab", temp_path])
        logger.info("DDNS cron job uninstalled successfully")
        return True
    finally:
        os.unlink(temp_path)


def _install_launchd(config_path, interval):
    # type: (str | None, int) -> bool
    """Install macOS launchd plist"""
    plist_dir = os.path.expanduser("~/Library/LaunchAgents")
    plist_path = os.path.join(plist_dir, "{}.plist".format(LAUNCHD_LABEL))

    # Create directory if not exists
    os.makedirs(plist_dir, exist_ok=True)

    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
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
    <string>ddns.log</string>
    <key>StandardErrorPath</key>
    <string>ddns.log</string>
    <key>WorkingDirectory</key>
    <string>{work_dir}</string>
</dict>
</plist>
""".format(
        label=LAUNCHD_LABEL,
        python=sys.executable,
        config_path=os.path.abspath(config_path) if config_path else "config.json",
        interval_seconds=interval * 60,
        work_dir=os.getcwd(),
    )

    with open(plist_path, "w") as f:
        f.write(plist_content)

    # Load the plist
    subprocess.check_call(["launchctl", "load", plist_path])

    logger.info("DDNS launchd service installed successfully")
    logger.info("Use 'launchctl list %s' to check status", LAUNCHD_LABEL)
    return True


def _uninstall_launchd():
    # type: () -> bool
    """Uninstall macOS launchd plist"""
    plist_path = os.path.expanduser("~/Library/LaunchAgents/{}.plist".format(LAUNCHD_LABEL))

    if os.path.exists(plist_path):
        # Unload the plist
        subprocess.call(["launchctl", "unload", plist_path], stderr=subprocess.DEVNULL)
        # Remove the plist file
        os.remove(plist_path)

    logger.info("DDNS launchd service uninstalled successfully")
    return True


def _get_vbs_locations():
    # type: () -> list
    """Get all possible VBS script locations"""
    return [
        os.path.join(os.path.expanduser("~\\AppData\\Local\\DDNS"), ".ddns_silent.vbs"),  # Current location
        os.path.join(os.path.expanduser("~\\AppData\\Local\\Temp"), ".ddns_silent.vbs"),  # Old temp location
        os.path.join(os.getcwd(), ".ddns_silent.vbs"),  # Working directory (fallback)
        os.path.join(os.getcwd(), "ddns_silent.vbs"),  # Old location (for compatibility)
    ]


def _create_vbs_script(config_path):
    # type: (str | None) -> str
    """Create VBS script for silent execution and return its path"""
    work_dir = os.getcwd()
    vbs_content = '''Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "{work_dir}"
objShell.Run "{ddns_cmd} -c ""{config_path}""", 0, False
'''.format(
        work_dir=work_dir.replace("\\", "\\\\"),
        ddns_cmd=_get_ddns_cmd().replace('"', '""'),
        config_path=os.path.abspath(config_path) if config_path else "config.json",
    )

    # Try to place VBS script in user's AppData\Local directory first
    user_appdata_dir = os.path.expanduser("~\\AppData\\Local\\DDNS")
    os.makedirs(user_appdata_dir, exist_ok=True)
    vbs_path = os.path.join(user_appdata_dir, ".ddns_silent.vbs")

    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        return vbs_path
    except Exception as e:
        logger.warning("Failed to create VBS in user AppData directory, using working directory: %s", e)
        # Fallback to working directory
        vbs_path = os.path.join(work_dir, ".ddns_silent.vbs")
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        return vbs_path


def _install_schtasks(config_path, interval):
    # type: (str | None, int) -> bool
    """Install Windows scheduled task"""
    vbs_path = _create_vbs_script(config_path)
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

        # Clean up VBS script files from all possible locations
        for vbs_path in _get_vbs_locations():
            if os.path.exists(vbs_path):
                try:
                    os.remove(vbs_path)
                    logger.debug("Cleaned up VBS script file: %s", vbs_path)
                except OSError as e:
                    logger.warning("Failed to remove VBS script file %s: %s", vbs_path, e)

        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to uninstall Windows scheduled task: %s", e)
        return False


def _enable_systemd():
    # type: () -> bool
    """Enable systemd timer"""
    try:
        subprocess.check_call(["systemctl", "enable", SYSTEMD_TIMER])
        subprocess.check_call(["systemctl", "start", SYSTEMD_TIMER])
        logger.info("DDNS systemd timer enabled successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to enable systemd timer: %s", e)
        return False


def _disable_systemd():
    # type: () -> bool
    """Disable systemd timer"""
    try:
        subprocess.check_call(["systemctl", "stop", SYSTEMD_TIMER])
        subprocess.check_call(["systemctl", "disable", SYSTEMD_TIMER])
        logger.info("DDNS systemd timer disabled successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to disable systemd timer: %s", e)
        return False


def _enable_cron():
    # type: () -> bool
    """Enable cron job (cron jobs are always enabled when installed)"""
    logger.info("Cron jobs are automatically enabled when installed")
    return True


def _disable_cron():
    # type: () -> bool
    """Disable cron job (effectively removes it)"""
    logger.warning("Cron jobs cannot be disabled without removing them")
    logger.info("To disable, use uninstall command instead")
    return False


def _enable_launchd():
    # type: () -> bool
    """Enable macOS launchd service"""
    plist_path = os.path.expanduser("~/Library/LaunchAgents/{}.plist".format(LAUNCHD_LABEL))

    if not os.path.exists(plist_path):
        logger.error("DDNS launchd service not found")
        return False

    try:
        subprocess.check_call(["launchctl", "load", plist_path])
        logger.info("DDNS launchd service enabled successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to enable launchd service: %s", e)
        return False


def _disable_launchd():
    # type: () -> bool
    """Disable macOS launchd service"""
    plist_path = os.path.expanduser("~/Library/LaunchAgents/{}.plist".format(LAUNCHD_LABEL))

    try:
        subprocess.check_call(["launchctl", "unload", plist_path])
        logger.info("DDNS launchd service disabled successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to disable launchd service: %s", e)
        return False


def _enable_schtasks():
    # type: () -> bool
    """Enable Windows scheduled task"""
    try:
        subprocess.check_call(["schtasks", "/Change", "/TN", TASK_NAME, "/Enable"])
        logger.info("DDNS Windows scheduled task enabled successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to enable Windows scheduled task: %s", e)
        return False


def _disable_schtasks():
    # type: () -> bool
    """Disable Windows scheduled task"""
    try:
        subprocess.check_call(["schtasks", "/Change", "/TN", TASK_NAME, "/Disable"])
        logger.info("DDNS Windows scheduled task disabled successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to disable Windows scheduled task: %s", e)
        return False
