# coding=utf-8
"""
DDNS Tests Package
"""

import sys
import os

# 添加当前目录到 Python 路径，这样就可以直接导入 test_base
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
