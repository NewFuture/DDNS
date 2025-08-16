# -*- coding:utf-8 -*-
"""
Utility: Safe command execution wrapper used across the project.
Provides a single try_run function with consistent behavior.
"""

import subprocess
import sys


def try_run(command, logger=None, **kwargs):
    # type: (list, object, **object) -> str | None
    """Safely run a subprocess command and return decoded output or None on failure.

    Args:
        command (list): Command array to execute
        logger (object, optional): Logger instance for debug output
        **kwargs: Additional arguments passed to subprocess.check_output

    Returns:
        str or None: Command output as string, or None if command failed

    - Adds a default timeout=60s on Python 3 to avoid hangs
    - Decodes output as text via universal_newlines=True
    - Logs at debug level when logger is provided
    """
    try:
        if sys.version_info[0] >= 3 and "timeout" not in kwargs:
            kwargs["timeout"] = 60
        return subprocess.check_output(command, universal_newlines=True, **kwargs)  # type: ignore
    except Exception as e:  # noqa: BLE001 - broad for subprocess safety
        if logger is not None:
            try:
                logger.debug("Command failed: %s", e)  # type: ignore
            except Exception:
                pass
        return None
