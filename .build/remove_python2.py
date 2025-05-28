#!/usr/bin/env python3
"""
自动将所有 try-except python2/3 兼容导入替换为 python3 only 导入，并显示处理日志
"""
import os
import re

ROOT = '.'
# 匹配 try-except 块，去除导入前缩进，保证import顶格，删除的行用空行代替
PATTERN = re.compile(
    r'^[ \t]*try:[^\n]*python 3[^\n]*\n'      # try: # python 3
    r'((?:[ \t]+[^\n]*\n)+?)'                 # python3 导入内容
    r'^[ \t]*except ImportError:[^\n]*\n'     # except ImportError: # python 2
    r'((?:[ \t]+from[^\n]*\n|[ \t]+import[^\n]*\n)*)',  # except块内容
    re.MULTILINE
)


def dedent_imports_with_blank(import_block, try_block, except_block):
    """
    保留python3导入并去除缩进,try/except及except内容用空行代替
    """
    try_lines = try_block.count('\n')
    except_lines = except_block.count('\n')
    imports = ''.join(line.lstrip()
                      for line in import_block.splitlines(keepends=True))
    return ('\n' * try_lines) + imports + ('\n' * except_lines)


def main():
    """
    遍历所有py文件并替换兼容导入
    """
    changed_files = 0
    for dirpath, _, filenames in os.walk(ROOT):
        for fname in filenames:
            if fname.endswith('.py'):
                fpath = os.path.join(dirpath, fname)
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()

                def repl(match):
                    try_block = re.match(
                        r'^[ \t]*try:[^\n]*python 3[^\n]*\n', match.group(0)
                    ).group(0)
                    except_block = re.search(
                        r'^[ \t]*except ImportError:[^\n]*\n((?:[ \t]+from[^\n]*\n|[ \t]+import[^\n]*\n)*)',
                        match.group(0), re.MULTILINE
                    )
                    except_block = except_block.group(
                        0) if except_block else ''
                    return dedent_imports_with_blank(match.group(1), try_block, except_block)

                new_content, n = PATTERN.subn(repl, content)
                if n > 0:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f'change: {fpath}')
                    changed_files += 1
    print('done')
    print(f'Total changed files: {changed_files}')


if __name__ == '__main__':
    main()
