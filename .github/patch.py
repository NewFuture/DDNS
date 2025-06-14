#!/usr/bin/env python3

import os
import re
import time

ROOT = "."
# 匹配 try-except 块，去除导入前缩进，保证import顶格，删除的行用空行代替
PATTERN = re.compile(
    r"^[ \t]*try:[^\n]*python 3[^\n]*\n"  # try: # python 3
    r"((?:[ \t]+[^\n]*\n)+?)"  # python3 导入内容
    r"^[ \t]*except ImportError:[^\n]*\n"  # except ImportError: # python 2
    r"((?:[ \t]+from[^\n]*\n|[ \t]+import[^\n]*\n)*)",  # except块内容
    re.MULTILINE,
)


def dedent_imports_with_blank(import_block, try_block, except_block):
    """
    保留python3导入并去除缩进,try/except及except内容用空行代替
    """
    try_lines = try_block.count("\n")
    except_lines = except_block.count("\n")
    imports = "".join(line.lstrip() for line in import_block.splitlines(keepends=True))
    return ("\n" * try_lines) + imports + ("\n" * except_lines)


def extract_pure_version(version_str):
    """
    提取前4组数字并用点拼接，如 v1.2.3.beta4.5 -> 1.2.3.4
    """
    nums = re.findall(r"\d+", version_str)
    return ".".join(nums[:4]) if nums else "0.0.0"


def update_nuitka_version(pyfile, version=None):
    """
    读取 __version__ 并替换 nuitka-project 版本号
    """
    pure_version = extract_pure_version(version)

    with open(pyfile, "r", encoding="utf-8") as f:
        content = f.read()
    # 替换 nuitka-project 行
    new_content, n = re.subn(
        r"(# nuitka-project: --product-version=)[^\n]*", r"\g<1>" + pure_version, content
    )
    if n > 0:
        with open(pyfile, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"update nuitka-project version: {pure_version} in {pyfile}")
        return True
    return False


def add_nuitka_file_description(pyfile):
    """
    添加 --file-description 配置，使用 __description__ 变量的值
    """
    with open(pyfile, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取 __description__ 变量的值
    desc_match = re.search(r'__description__\s*=\s*[\'"]([^\'"]+)[\'"]', content)
    if not desc_match:
        print(f"No __description__ found in {pyfile}")
        return False

    description = desc_match.group(1)
    if not content.endswith("\n"):
        content += "\n"
    description_line = f'# nuitka-project: --file-description="{description}"\n'
    if description_line not in content:
        content += description_line

    with open(pyfile, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Added file-description to {pyfile}")
    return True


def add_nuitka_include_modules(pyfile):
    """
    读取 dns 目录下的所有 Python 模块，并添加到 run.py 末尾
    """
    dns_dir = os.path.join(ROOT, "dns")
    if not os.path.exists(dns_dir):
        print(f"DNS directory not found: {dns_dir}")
        return False

    # 获取所有 Python 模块文件
    modules = []
    for filename in os.listdir(dns_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]  # 去掉 .py 扩展名
            modules.append(f"dns.{module_name}")

    if not modules:
        print("No DNS modules found")
        return False

    # 直接在文件末尾追加配置行
    with open(pyfile, "a", encoding="utf-8") as f:
        for module in sorted(modules):
            f.write(f"# nuitka-project: --include-module={module}\n")

    print(f'Added {len(modules)} DNS modules to {pyfile}: {", ".join(modules)}')
    return True


def remove_python2_compatibility(pyfile):
    """
    自动将所有 try-except python2/3 兼容导入替换为 python3 only 导入，并显示处理日志
    删除指定文件中的 python2 兼容代码，逐行处理
    """
    with open(pyfile, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    changed = False
    while i < len(lines):
        line = lines[i]
        # 匹配 "try: # python3" 或 "try: # python 3"
        if re.match(r"^[ \t]*try:[^\n]*python ?3", line):
            try_block = []
            except_block = []
            i += 1
            # 收集try块内容
            while i < len(lines) and lines[i].startswith((" ", "\t")):
                try_block.append(lines[i].lstrip())
                i += 1
            # 跳过空行
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            # 检查是否存在except块 (不检查具体错误类型，但必须包含python2或python 2)
            if i < len(lines) and re.match(r"^[ \t]*except[^\n]*python ?2", lines[i]):
                i += 1
                # 收集except块内容
                except_block = []
                while i < len(lines) and lines[i].startswith((" ", "\t")):
                    except_block.append(lines[i])
                    i += 1
                # 添加try块内容，except块用空行替代
                new_lines.extend(["\n"] + try_block + ["\n"] * (len(except_block) + 1))
                changed = True
            else:
                # 没有except块，原样保留
                new_lines.append(line)
                new_lines.extend(try_block)
        else:
            new_lines.append(line)
            i += 1

    if changed:
        with open(pyfile, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"Removed python2 compatibility from {pyfile}")


def extract_version_from_env():
    """
    从环境变量中提取版本号
    """
    ref = os.environ.get("GITHUB_REF_NAME")
    if not ref:
        return "0.0.0.%s" % (time.strftime("%m%d%H%M"))  # 默认版本号
    if ref and ref.startswith("v"):
        return ref[1:]  # 去掉前缀 'v'
    return ref  # 返回原始版本号


def main():
    """
    遍历所有py文件并替换兼容导入，同时更新nuitka版本号
    """
    run_py_path = os.path.join(ROOT, "run.py")
    version = extract_version_from_env()
    update_nuitka_version(run_py_path, version)
    add_nuitka_file_description(run_py_path)
    add_nuitka_include_modules(run_py_path)

    # 修改__init__.py 中的 __version__
    init_py_path = os.path.join(ROOT, "ddns", "__init__.py")
    replace_version_in_init(version, init_py_path)

    changed_files = 0
    for dirpath, _, filenames in os.walk(ROOT):
        for fname in filenames:
            if fname.endswith(".py"):
                fpath = os.path.join(dirpath, fname)
                remove_python2_compatibility(fpath)
                changed_files += 1
    print("done")
    print(f"Total processed files: {changed_files}")


def replace_version_in_init(version, init_py_path):
    """
    替换 ddns/__init__.py 中的 __version__ 变量
    """
    version_str = f'v{version}@{time.strftime("%Y-%m-%dT%H:%M:%S")}'
    with open(init_py_path, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'__version__\s*=\s*[\'"]([^\'"]+)[\'"]', f'__version__ = "{version_str}"', content
    )
    if new_content != content:
        with open(init_py_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated __version__ in {init_py_path} to {version_str}")


if __name__ == "__main__":
    main()
