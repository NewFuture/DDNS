# coding=utf-8
"""
Debug
调试输出
"""
from __future__ import print_function
__all__ = ["ENABLE", "log"]

ENABLE = False


def log(enable=None):
    """
    返回调试函数
    """
    if enable is None:
        enable = ENABLE
    if enable:
        return print
    else:
        def func(*kl, **kw):
            """do nothing"""
            pass
        return func
