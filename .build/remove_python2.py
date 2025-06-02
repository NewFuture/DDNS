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


def extract_pure_version(version_str):
    """
    提取前4组数字并用点拼接，如 v1.2.3.beta4.5 -> 1.2.3.4
    """
    import re
    nums = re.findall(r'\d+', version_str)
    return '.'.join(nums[:4]) if nums else "0.0.0"


def update_nuitka_version(pyfile):
    """
    读取 __version__ 并替换 nuitka-project 版本号
    """
    with open(pyfile, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取 __version__ 变量
    version_match = re.search(r'__version__\s*=\s*[\'"]([^\'"]+)[\'"]', content)
    if not version_match:
        print(f'No __version__ found in {pyfile}')
        return False

    version_str = version_match.group(1)
    pure_version = extract_pure_version(version_str)

    # 替换 nuitka-project 行
    new_content, n = re.subn(
        r'(# nuitka-project: --product-version=)[^\n]*',
        r'\g<1>' + pure_version,
        content
    )
    if n > 0:
        with open(pyfile, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'update nuitka-project version: {pure_version} in {pyfile}')
        return True
    return False


def main():
    """
    遍历所有py文件并替换兼容导入，同时更新nuitka版本号
    """
    changed_files = 0
    # 先处理 run.py 的 nuitka-project 版本号
    update_nuitka_version(os.path.join(ROOT, "run.py"))
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
