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

# Constants and helper functions
TASK_NAME = "DDNS"
LAUNCHD_LABEL = "cc.newfuture.ddns"
SYSTEMD_SERVICE = "ddns.service"
SYSTEMD_TIMER = "ddns.timer"
VBS_SCRIPT = "~\\AppData\\Local\\DDNS\\ddns_silent.vbs"


def _get_launchd_plist_path():
    return os.path.expanduser("~/Library/LaunchAgents/{}.plist".format(LAUNCHD_LABEL))


def _get_systemd_path(service):
    return "/etc/systemd/system/{}".format(service)


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


def _run_command(command, **kwargs):
    # type: (list[str], **Any) -> str | None
    """Safely run subprocess command, return decoded string or None if failed"""
    try:
        if sys.version_info[0] >= 3:
            kwargs.setdefault("stderr", subprocess.DEVNULL)
        return subprocess.check_output(command, universal_newlines=True, **kwargs)
    except (subprocess.CalledProcessError, OSError, UnicodeDecodeError):
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
            plist_path = _get_launchd_plist_path()
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

    if scheduler == "systemd":
        result = _run_command(["systemctl", "is-enabled", SYSTEMD_TIMER]) or ""
        return result.strip() == "enabled"
    elif scheduler == "cron":
        result = _run_command(["crontab", "-l"]) or ""
        return "ddns" in result
    elif scheduler == "launchd":
        plist_path = _get_launchd_plist_path()
        return os.path.exists(plist_path)
    elif scheduler == "schtasks":
        result = _run_command(["schtasks", "/query", "/tn", TASK_NAME]) or ""
        return TASK_NAME in result

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
    try:
        if scheduler == "systemd":
            content = read_file_safely(_get_systemd_path(SYSTEMD_TIMER))
            if content:
                match = re.search(r"OnUnitActiveSec=(\d+)m", content)
                return int(match.group(1)) if match else None

        elif scheduler == "cron":
            result = _run_command(["crontab", "-l"])
            if result:
                for line in result.lower().split("\n"):
                    if "ddns" in line and line.strip() and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) >= 5 and parts[0].startswith("*/"):
                            return int(parts[0][2:])

        elif scheduler == "launchd":
            content = read_file_safely(_get_launchd_plist_path())
            if content:
                match = re.search(r"<key>StartInterval</key>\s*<integer>(\d+)</integer>", content)
                return int(match.group(1)) // 60 if match else None

        elif scheduler == "schtasks":
            result = _run_command(["schtasks", "/query", "/tn", TASK_NAME, "/fo", "list", "/v"])
            if result:
                for line in result.split("\n"):
                    if "Repeat: Every:" in line:
                        match = re.search(r"Every:\s*\d*:(\d+):00", line)
                        return int(match.group(1)) if match else None
    except (ValueError, AttributeError):
        pass
    return None


def _get_task_command(scheduler):
    # type: (str) -> str | None
    """Get the actual command from installed task"""
    try:
        if scheduler == "systemd":
            content = read_file_safely(_get_systemd_path(SYSTEMD_SERVICE))
            if content:
                match = re.search(r"ExecStart=(.+)", content)
                return match.group(1).strip() if match else None

        elif scheduler == "cron":
            result = _run_command(["crontab", "-l"])
            if result:
                for line in result.split("\n"):
                    if "ddns" in line.lower() and line.strip() and not line.startswith("#"):
                        parts = line.split()
                        return " ".join(parts[5:]) if len(parts) >= 6 else None

        elif scheduler == "launchd":
            content = read_file_safely(_get_launchd_plist_path())
            if content:
                # Try Program key first
                program_match = re.search(r"<key>Program</key>\s*<string>([^<]+)</string>", content)
                if program_match:
                    return program_match.group(1)
                # Try ProgramArguments array
                args_section = re.search(r"<key>ProgramArguments</key>\s*<array>(.*?)</array>", content, re.DOTALL)
                if args_section:
                    strings = re.findall(r"<string>([^<]+)</string>", args_section.group(1))
                    return " ".join(strings) if strings else None

        elif scheduler == "schtasks":
            result = _run_command(["schtasks", "/query", "/tn", TASK_NAME, "/fo", "list", "/v"])
            if result:
                for line in result.split("\n"):
                    if "Task To Run:" in line:
                        return line.split("Task To Run:", 1)[1].strip()
    except (ValueError, AttributeError, IndexError):
        pass
    return None


def _get_running_status(scheduler):
    # type: (str) -> str
    """Get running status for specific scheduler"""
    try:
        if scheduler == "systemd":
            result = _run_command(["systemctl", "is-active", "ddns.timer"])
            return result.strip() if result else "inactive"
        elif scheduler == "cron":
            result = _run_command(["pgrep", "-f", "cron"])
            return "active" if result else "inactive"
        elif scheduler == "launchd":
            result = _run_command(["launchctl", "list", "cc.newfuture.ddns"])
            return "active" if result else "inactive"
        elif scheduler == "schtasks":
            result = _run_command(["schtasks", "/query", "/tn", "DDNS", "/fo", "csv"])
            if result:
                lines = result.strip().split("\n")
                if len(lines) > 1:
                    fields = [field.strip('"') for field in lines[1].split('","')]
                    return fields[2].lower() if len(fields) > 2 else "unknown"
            return "inactive"
    except (AttributeError, UnicodeDecodeError):
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
    if "debug" in ddns_args and not ddns_args["debug"]:
        del ddns_args["debug"]

    # Process arguments in a unified way
    for key, value in ddns_args.items():
        if isinstance(value, bool):
            # Handle boolean as lowercase string (for cases like --debug true/false)
            cmd_parts.extend(["--{}".format(key), str(value).lower()])
        elif isinstance(value, list):
            for item in value:
                cmd_parts.extend(["--{}".format(key), '"{}"'.format(item)])
        else:
            cmd_parts.extend(["--{}".format(key), '"{}"'.format(value)])

    return " ".join(cmd_parts)


def _install_systemd(interval, ddns_args=None):
    # type: (int, dict | None) -> bool
    """Install systemd timer and service"""
    ddns_command = _build_ddns_command(ddns_args)
    work_dir = os.getcwd()

    # Create service content
    service_content = (
        "[Unit]\nDescription=DDNS automatic IP update service\nAfter=network.target\n\n"
        + "[Service]\nType=oneshot\nWorkingDirectory={}\nExecStart={}\n".format(work_dir, ddns_command)
    )

    # Create timer content
    timer_content = (
        "[Unit]\nDescription=DDNS automatic IP update timer\n\n"
        + "[Timer]\nOnUnitActiveSec={}m\nUnit=ddns.service\n\n".format(interval)
        + "[Install]\nWantedBy=multi-user.target\n"
    )

    try:
        # Write service and timer files
        write_file(_get_systemd_path(SYSTEMD_SERVICE), service_content)
        write_file(_get_systemd_path(SYSTEMD_TIMER), timer_content)

        # Reload systemd and enable timer
        subprocess.check_call(["systemctl", "daemon-reload"])
        subprocess.check_call(["systemctl", "enable", SYSTEMD_TIMER])
        subprocess.check_call(["systemctl", "start", SYSTEMD_TIMER])

        logger.info("DDNS systemd timer installed successfully")
        logger.info("Use 'systemctl status %s' to check status", SYSTEMD_TIMER)
        logger.info("Use 'journalctl -u %s' to view logs", SYSTEMD_SERVICE)
        return True
    except (subprocess.CalledProcessError, OSError, PermissionError) as e:
        logger.error("Failed to install systemd timer: %s", e)
        logger.error("Root permission required for systemd installation.")
        logger.info("Please run with sudo: sudo %s -m ddns task --install", sys.executable)
        return False


def _uninstall_systemd():
    """Uninstall systemd timer and service"""
    try:
        # Stop and disable timer
        subprocess.call(["systemctl", "stop", "ddns.timer"], stderr=subprocess.DEVNULL)
        subprocess.call(["systemctl", "disable", "ddns.timer"], stderr=subprocess.DEVNULL)

        # Remove files
        service_files = [_get_systemd_path(SYSTEMD_SERVICE), _get_systemd_path(SYSTEMD_TIMER)]
        for path in service_files:
            if os.path.exists(path):
                os.remove(path)

        subprocess.check_call(["systemctl", "daemon-reload"])
        logger.info("DDNS systemd timer uninstalled successfully")
        return True
    except (subprocess.CalledProcessError, OSError, PermissionError) as e:
        logger.error("Failed to uninstall systemd timer: %s", e)
        logger.error("Root permission required for systemd uninstallation.")
        logger.info("Please run with sudo: sudo %s -m ddns task --delete", sys.executable)
        return False


def _update_crontab(new_cron):
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
    existing_cron = _run_command(["crontab", "-l"])
    existing_cron = existing_cron if existing_cron else ""

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
    """Uninstall cron job"""
    existing_cron = _run_command(["crontab", "-l"])
    if not existing_cron:
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
    plist_path = _get_launchd_plist_path()
    ddns_command = _build_ddns_command(ddns_args)
    program_args = ddns_command.split()
    program_args_xml = "\n".join("        <string>{}</string>".format(arg.strip('"')) for arg in program_args)

    # Create plist content
    plist_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        + '<plist version="1.0">\n<dict>\n'
        + "    <key>Label</key>\n    <string>{}</string>\n".format(LAUNCHD_LABEL)
        + "    <key>ProgramArguments</key>\n    <array>\n{}\n    </array>\n".format(program_args_xml)
        + "    <key>StartInterval</key>\n    <integer>{}</integer>\n".format(interval * 60)
        + "    <key>RunAtLoad</key>\n    <true/>\n"
        + "    <key>WorkingDirectory</key>\n    <string>{}</string>\n".format(os.getcwd())
        + "</dict>\n</plist>\n"
    )

    write_file(plist_path, plist_content)

    # Load the plist
    subprocess.check_call(["launchctl", "load", plist_path])

    logger.info("DDNS launchd service installed successfully")
    logger.info("Use 'launchctl list %s' to check status", LAUNCHD_LABEL)
    return True


def _uninstall_launchd():
    """Uninstall macOS launchd plist"""
    plist_path = _get_launchd_plist_path()

    # Unload the plist
    subprocess.call(["launchctl", "unload", plist_path], stderr=subprocess.DEVNULL)
    # Remove the plist file
    try:
        os.remove(plist_path)
    except OSError:
        pass  # File doesn't exist

    logger.info("DDNS launchd service uninstalled successfully")
    return True


def _install_schtasks(interval, ddns_args=None):
    # type: (int, dict | None) -> bool
    """Install Windows scheduled task with VBS script"""
    vbs_path = _create_vbs_script(ddns_args)
    cmd = 'wscript.exe "{}"'.format(vbs_path)

    # Check if running as administrator (optional warning)
    admin_result = _run_command(["net", "session"])
    if not admin_result:
        logger.info("Run as administrator is recommended for Windows task installation.")

    # Create scheduled task
    subprocess.check_call(
        ["schtasks", "/Create", "/SC", "MINUTE", "/MO", str(interval), "/TR", cmd, "/TN", TASK_NAME, "/F"]
    )

    logger.info("DDNS Windows scheduled task installed successfully")
    logger.info("Use 'schtasks /query /tn %s' to check status", TASK_NAME)
    return True


def _create_vbs_script(ddns_args=None):
    # type: (dict | None) -> str
    """Create VBS script for silent execution and return its path"""
    ddns_command = _build_ddns_command(ddns_args)
    work_dir = os.getcwd()

    # Create VBS script content
    vbs_content = (
        'Set objShell = CreateObject("WScript.Shell")\n'
        + 'objShell.CurrentDirectory = "{}"\n'.format(work_dir.replace("\\", "\\\\"))
        + 'objShell.Run "{}", 0, False\n'.format(ddns_command.replace('"', '""'))
    )

    # Try user AppData first, fallback to working directory
    vbs_paths = [os.path.expanduser(VBS_SCRIPT), os.path.join(work_dir, ".ddns_silent.vbs")]

    for path in vbs_paths:
        try:
            write_file(path, vbs_content)
            return path
        except Exception as e:
            if path == vbs_paths[0]:  # First attempt failed
                logger.debug("Failed to create VBS in AppData, trying working directory: %s", e)
            continue

    # This should not happen as working directory write should succeed
    raise Exception("Failed to create VBS script in any location")


def _uninstall_schtasks():
    """Uninstall Windows scheduled task and clean up VBS scripts"""
    try:
        subprocess.check_call(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"])
        logger.info("DDNS Windows scheduled task uninstalled successfully")

        # Clean up VBS scripts from both possible locations
        vbs_paths = [os.path.expanduser(VBS_SCRIPT), os.path.join(os.getcwd(), ".ddns_silent.vbs")]

        for vbs_path in vbs_paths:
            try:
                if os.path.exists(vbs_path):
                    os.remove(vbs_path)
                    logger.debug("Cleaned up VBS script file: %s", vbs_path)
            except OSError:
                pass  # File can't be removed, ignore

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
    success_message = config["success_" + operation]

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
