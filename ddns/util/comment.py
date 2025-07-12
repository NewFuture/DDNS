# -*- coding:utf-8 -*-
"""
Comment removal utility for JSON configuration files.
Supports both # and // style single line comments.
@author: GitHub Copilot
"""


def remove_comment(content):
    # type: (str) -> str
    """
    移除字符串中的单行注释。
    支持 # 和 // 两种注释风格。

    Args:
        content (str): 包含注释的字符串内容

    Returns:
        str: 移除注释后的字符串

    Examples:
        >>> remove_comment('{"key": "value"} // comment')
        '{"key": "value"} '
        >>> remove_comment('# This is a comment\\n{"key": "value"}')
        '\\n{"key": "value"}'
    """
    if not content:
        return content

    lines = content.splitlines()
    cleaned_lines = []

    for line in lines:
        # 移除行内注释，但要小心不要破坏字符串内的内容
        cleaned_line = _remove_line_comment(line)
        cleaned_lines.append(cleaned_line)

    return "\n".join(cleaned_lines)


def _remove_line_comment(line):
    # type: (str) -> str
    """
    移除单行中的注释部分。

    Args:
        line (str): 要处理的行

    Returns:
        str: 移除注释后的行
    """
    # 检查是否是整行注释
    stripped = line.lstrip()
    if stripped.startswith("#") or stripped.startswith("//"):
        return ""

    # 查找行内注释，需要考虑字符串内容
    in_string = False
    quote_char = None
    i = 0

    while i < len(line):
        char = line[i]

        # 处理字符串内的转义序列
        if in_string and char == "\\" and i + 1 < len(line):
            i += 2  # 跳过转义字符
            continue

        # 处理引号字符
        if char in ('"', "'"):
            if not in_string:
                in_string = True
                quote_char = char
            elif char == quote_char:
                in_string = False
                quote_char = None

        # 在字符串外检查注释标记
        elif not in_string:
            if char == "#":
                return line[:i].rstrip()
            elif char == "/" and i + 1 < len(line) and line[i + 1] == "/":
                return line[:i].rstrip()

        i += 1

    return line
