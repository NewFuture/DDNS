# coding=utf-8
"""
DDNS Tests Package
"""

import sys
import os

try:
    from unittest.mock import patch, MagicMock
except ImportError:  # Python 2
    from mock import patch, MagicMock  # type: ignore

__all__ = ["patch", "MagicMock"]

# 添加当前目录到 Python 路径，这样就可以直接导入 test_base
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 添加上级目录到 Python 路径，这样就可以导入 ddns 模块
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
