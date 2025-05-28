#!/usr/bin/env python3
# 自动将所有 try-except python2/3 兼容导入替换为 python3 only 导入，并显示处理日志
import os
import re

root = '.'
# 匹配 try-except 块，去除导入前缩进，保证import顶格，删除的行用空行代替
pattern = re.compile(
    r'^[ \t]*try:[^\n]*python 3[^\n]*\n'      # try: # python 3
    r'((?:[ \t]+[^\n]*\n)+?)'                 # python3 导入内容
    r'^[ \t]*except ImportError:[^\n]*\n'     # except ImportError: # python 2
    r'((?:[ \t]+from[^\n]*\n|[ \t]+import[^\n]*\n)*)',  # except块内容
    re.MULTILINE
)

def dedent_imports_with_blank(import_block, try_block, except_block):
    # 保留python3导入并去除缩进，try/except及except内容用空行代替
    try_lines = try_block.count('\n')
    except_lines = except_block.count('\n')
    # python3导入内容去除缩进
    imports = ''.join(line.lstrip() for line in import_block.splitlines(keepends=True))
    # 用空行代替try和except块
    return ('\n' * try_lines) + imports + ('\n' * except_lines)

changed_files = 0
for dirpath, _, filenames in os.walk(root):
    for fname in filenames:
        if fname.endswith('.py'):
            fpath = os.path.join(dirpath, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            def repl(m):
                # m.group(0): 全部匹配内容
                # m.group(1): python3导入内容
                # m.group(2): except块内容
                try_block = re.match(r'^[ \t]*try:[^\n]*python 3[^\n]*\n', m.group(0)).group(0)
                except_block = re.search(r'^[ \t]*except ImportError:[^\n]*\n((?:[ \t]+from[^\n]*\n|[ \t]+import[^\n]*\n)*)', m.group(0), re.MULTILINE)
                except_block = except_block.group(0) if except_block else ''
                return dedent_imports_with_blank(m.group(1), try_block, except_block)
            new_content, n = pattern.subn(repl, content)
            if n > 0:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'change: {fpath}')
print('done')

