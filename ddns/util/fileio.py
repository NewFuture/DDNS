# -*- coding:utf-8 -*-
"""
File I/O utilities for DDNS with Python 2/3 compatibility
@author: NewFuture
"""

import os
from io import open  # Python 2/3 compatible UTF-8 file operations


def _ensure_directory_exists(file_path):  # type: (str) -> None
    """
    Internal helper to ensure directory exists for the given file path

    Args:
        file_path (str): File path whose directory should be created

    Raises:
        OSError: If directory cannot be created
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def read_file_safely(file_path, encoding="utf-8", default=None):  # type: (str, str, str|None) -> str
    """
    Safely read file content with UTF-8 encoding, return None if file doesn't exist or can't be read

    Args:
        file_path (str): Path to the file to read
        encoding (str): File encoding (default: utf-8)

    Returns:
        str | None: File content or None if failed
    """
    try:
        return read_file(file_path, encoding)
    except Exception:
        return default  # type: ignore


def write_file_safely(file_path, content, encoding="utf-8"):  # type: (str, str, str) -> bool
    """
    Safely write content to file with UTF-8 encoding

    Args:
        file_path (str): Path to the file to write
        content (str): Content to write
        encoding (str): File encoding (default: utf-8)

    Returns:
        bool: True if write successful, False otherwise
    """
    try:
        write_file(file_path, content, encoding)
        return True
    except Exception:
        return False


def read_file(file_path, encoding="utf-8"):  # type: (str, str) -> str
    """
    Read file content with UTF-8 encoding, raise exception if failed

    Args:
        file_path (str): Path to the file to read
        encoding (str): File encoding (default: utf-8)

    Returns:
        str: File content

    Raises:
        IOError: If file cannot be read
        UnicodeDecodeError: If file cannot be decoded with specified encoding
    """
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()


def write_file(file_path, content, encoding="utf-8"):  # type: (str, str, str) -> None
    """
    Write content to file with UTF-8 encoding, raise exception if failed

    Args:
        file_path (str): Path to the file to write
        content (str): Content to write
        encoding (str): File encoding (default: utf-8)

    Raises:
        IOError: If file cannot be written
        UnicodeEncodeError: If content cannot be encoded with specified encoding
    """
    _ensure_directory_exists(file_path)
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)


def ensure_directory(file_path):  # type: (str) -> bool
    """
    Ensure the directory for the given file path exists

    Args:
        file_path (str): File path whose directory should be created

    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        _ensure_directory_exists(file_path)
        return True
    except (OSError, IOError):
        return False
