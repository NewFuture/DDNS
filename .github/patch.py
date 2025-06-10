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


def remove_windows_textiowrapper(pyfile):
    """
    如果当前系统不是 Windows，则删除 run.py 中的 TextIOWrapper 兼容代码块
    """
    if os.name == 'nt':
        return  # Windows 下不处理

    with open(pyfile, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配并删除 if sys.version_info.major == 3 and os_name == 'nt': ... 代码块
    pattern = re.compile(
        r'(?m)^[ \t]*if sys\.version_info\.major == 3 and os_name == [\'"]nt[\'"]:\n'
        r'(?:[ \t]+from io import TextIOWrapper\n)?'
        r'(?:[ \t]+sys\.stdout = TextIOWrapper\(sys\.stdout\.detach\(\), encoding=[\'"]utf-8[\'"]\)\n)?'
        r'(?:[ \t]+sys\.stderr = TextIOWrapper\(sys\.stderr\.detach\(\), encoding=[\'"]utf-8[\'"]\)\n)?'
    )
    new_content, n = pattern.subn('', content)
    if n > 0:
        with open(pyfile, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Removed Windows TextIOWrapper code from {pyfile}')


def remove_python2_compatibility(pyfile):
    """
    删除指定文件中的 python2 兼容代码，逐行处理
    """
    with open(pyfile, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    changed = False
    while i < len(lines):
        line = lines[i]
        # 匹配 "try: # python3" 或 "try: # python 3"
        if re.match(r'^[ \t]*try:[^\n]*python ?3', line):
            try_block = []
            except_block = []
            i += 1
            # 收集try块内容
            while i < len(lines) and lines[i].startswith((' ', '\t')):
                try_block.append(lines[i].lstrip())
                i += 1
            # 跳过空行
            while i < len(lines) and lines[i].strip() == '':
                i += 1
            # 检查是否存在except块 (不检查具体错误类型，但必须包含python2或python 2)
            if i < len(lines) and re.match(r'^[ \t]*except[^\n]*python ?2', lines[i]):
                i += 1
                # 收集except块内容
                except_block = []
                while i < len(lines) and lines[i].startswith((' ', '\t')):
                    except_block.append(lines[i])
                    i += 1
                # 添加try块内容，except块用空行替代
                new_lines.extend(['\n'] + try_block + ['\n'] * (len(except_block) + 1))
                changed = True
            else:
                # 没有except块，原样保留
                new_lines.append(line)
                new_lines.extend(try_block)
        else:
            new_lines.append(line)
            i += 1

    if changed:
        with open(pyfile, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f'Removed python2 compatibility from {pyfile}')


def main():
    """
    遍历所有py文件并替换兼容导入，同时更新nuitka版本号
    """
    update_nuitka_version(os.path.join(ROOT, "run.py"))

    changed_files = 0
    for dirpath, _, filenames in os.walk(ROOT):
        for fname in filenames:
            if fname.endswith('.py'):
                fpath = os.path.join(dirpath, fname)
                remove_python2_compatibility(fpath)
                changed_files += 1
    print('done')
    print(f'Total processed files: {changed_files}')


if __name__ == '__main__':
    main()
