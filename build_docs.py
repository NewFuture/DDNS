#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Static documentation website generator for DDNS project.

This script converts markdown documentation to static HTML with:
- Responsive navigation bar with collapsible directory tree
- In-page table of contents (right sidebar, hidden on small screens)
- Language switcher
- Pure static HTML output
- Footer with GitHub links and edit page link
"""

import os
import re
import json
import shutil
from html import escape

# Configuration
DOC_DIR = "doc"
BUILD_DIR = "build"
GITHUB_REPO = "NewFuture/DDNS"
GITHUB_BRANCH = "master"


def parse_front_matter(content):
    # type: (str) -> tuple
    """
    Parse YAML front matter from markdown content.

    Args:
        content (str): Markdown file content

    Returns:
        tuple: (front_matter_dict, content_without_front_matter)
    """
    front_matter = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            front_matter_text = parts[1].strip()
            content = parts[2].strip()

            # Simple YAML parser for basic key: value pairs
            for line in front_matter_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    front_matter[key.strip()] = value.strip()

    return front_matter, content


def markdown_to_html(content):
    # type: (str) -> str
    """
    Convert markdown to HTML with basic formatting.

    Args:
        content (str): Markdown content

    Returns:
        str: HTML content
    """
    lines = content.split("\n")
    html_lines = []
    in_code_block = False
    code_lang = ""
    in_list = False
    in_blockquote = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code blocks
        if line.startswith("```"):
            if not in_code_block:
                code_lang = line[3:].strip()
                in_code_block = True
                html_lines.append('<pre><code class="language-{}">'.format(escape(code_lang) if code_lang else ""))
            else:
                in_code_block = False
                html_lines.append("</code></pre>")
            i += 1
            continue

        if in_code_block:
            html_lines.append(escape(line))
            i += 1
            continue

        # Headers with IDs for TOC
        header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if header_match:
            level = len(header_match.group(1))
            text = header_match.group(2).strip()
            # Remove markdown links from header text for ID
            clean_text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
            header_id = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", clean_text.lower()).strip("-")
            html_lines.append('<h{} id="{}">{}</h{}>'.format(level, header_id, format_inline(text), level))
            i += 1
            continue

        # Blockquotes
        if line.startswith(">"):
            if not in_blockquote:
                html_lines.append("<blockquote>")
                in_blockquote = True
            content = line[1:].strip()
            html_lines.append("<p>{}</p>".format(format_inline(content)))
            i += 1
            continue
        elif in_blockquote:
            html_lines.append("</blockquote>")
            in_blockquote = False

        # Lists
        if line.strip().startswith(("- ", "* ", "+ ")):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            content = line.strip()[2:]
            html_lines.append("<li>{}</li>".format(format_inline(content)))
            i += 1
            continue
        elif line.strip() and re.match(r"^\d+\.\s+", line.strip()):
            if not in_list:
                html_lines.append("<ol>")
                in_list = True
            content = re.sub(r"^\d+\.\s+", "", line.strip())
            html_lines.append("<li>{}</li>".format(format_inline(content)))
            i += 1
            continue
        elif in_list and not line.strip():
            html_lines.append("</ul>" if lines[i-1].strip().startswith(("- ", "* ", "+ ")) else "</ol>")
            in_list = False

        # Horizontal rule
        if line.strip() in ("---", "***", "___"):
            html_lines.append("<hr>")
            i += 1
            continue

        # Paragraphs
        if line.strip():
            html_lines.append("<p>{}</p>".format(format_inline(line)))
        else:
            html_lines.append("")

        i += 1

    # Close any open tags
    if in_code_block:
        html_lines.append("</code></pre>")
    if in_list:
        html_lines.append("</ul>")
    if in_blockquote:
        html_lines.append("</blockquote>")

    return "\n".join(html_lines)


def format_inline(text):
    # type: (str) -> str
    """
    Format inline markdown elements (bold, italic, code, links, images).

    Args:
        text (str): Text with inline markdown

    Returns:
        str: HTML formatted text
    """
    # Images
    text = re.sub(r"!\[([^\]]*)\]\(([^\)]+)\)", r'<img src="\2" alt="\1">', text)

    # Links
    text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r'<a href="\2">\1</a>', text)

    # Code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # Bold
    text = re.sub(r"\*\*([^\*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)

    # Italic
    text = re.sub(r"\*([^\*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"_([^_]+)_", r"<em>\1</em>", text)

    return text


def extract_toc(content):
    # type: (str) -> list
    """
    Extract table of contents from markdown content.

    Args:
        content (str): Markdown content

    Returns:
        list: List of (level, id, text) tuples
    """
    toc = []
    for line in content.split("\n"):
        header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if header_match:
            level = len(header_match.group(1))
            text = header_match.group(2).strip()
            # Remove markdown links from header text
            clean_text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
            header_id = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", clean_text.lower()).strip("-")
            toc.append((level, header_id, clean_text))
    return toc


def build_nav_tree(doc_dir):
    # type: (str) -> dict
    """
    Build navigation tree from documentation structure.

    Args:
        doc_dir (str): Documentation directory path

    Returns:
        dict: Navigation tree structure
    """
    nav_tree = {"items": [], "dirs": {}}

    # Define directory order and labels
    dir_labels = {
        "config": {"zh": "配置方式", "en": "Configuration"},
        "dev": {"zh": "开发文档", "en": "Development"},
        "providers": {"zh": "DNS 服务商", "en": "DNS Providers"}
    }

    # Get all markdown files
    for root, dirs, files in os.walk(doc_dir):
        rel_path = os.path.relpath(root, doc_dir)

        for filename in sorted(files):
            if not filename.endswith(".md"):
                continue

            file_path = os.path.join(root, filename)
            rel_file_path = os.path.relpath(file_path, doc_dir)

            # Determine language
            is_english = filename.endswith(".en.md")
            base_name = filename[:-6] if is_english else filename[:-3]

            # Read title from front matter
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                front_matter, _ = parse_front_matter(content)
                title = front_matter.get("title", base_name.replace("_", " ").title())

            # Build navigation item
            nav_item = {
                "path": rel_file_path,
                "title": title,
                "base_name": base_name,
                "is_english": is_english
            }

            # Add to appropriate section
            if rel_path == ".":
                nav_tree["items"].append(nav_item)
            else:
                dir_name = rel_path.split(os.sep)[0]
                if dir_name not in nav_tree["dirs"]:
                    nav_tree["dirs"][dir_name] = {
                        "label_zh": dir_labels.get(dir_name, {}).get("zh", dir_name),
                        "label_en": dir_labels.get(dir_name, {}).get("en", dir_name),
                        "items": []
                    }
                nav_tree["dirs"][dir_name]["items"].append(nav_item)

    return nav_tree


def generate_html(doc_path, nav_tree, output_dir):
    # type: (str, dict, str) -> None
    """
    Generate HTML file from markdown documentation.

    Args:
        doc_path (str): Path to markdown file relative to doc/
        nav_tree (dict): Navigation tree structure
        output_dir (str): Output directory for HTML files
    """
    full_path = os.path.join(DOC_DIR, doc_path)

    # Read and parse markdown
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    front_matter, md_content = parse_front_matter(content)
    html_content = markdown_to_html(md_content)
    toc = extract_toc(md_content)

    # Determine if this is an English page
    is_english = doc_path.endswith(".en.md")

    # Get language labels
    lang = "en" if is_english else "zh"
    lang_labels = {
        "zh": {
            "home": "首页",
            "github": "GitHub 仓库",
            "issues": "问题反馈",
            "edit": "编辑此页",
            "toc": "目录",
            "toggle_nav": "切换导航",
            "switch_lang": "Switch to English"
        },
        "en": {
            "home": "Home",
            "github": "GitHub Repository",
            "issues": "Report Issues",
            "edit": "Edit this page",
            "toc": "Table of Contents",
            "toggle_nav": "Toggle Navigation",
            "switch_lang": "切换到中文"
        }
    }
    labels = lang_labels[lang]

    # Get alternate language link
    if is_english:
        alt_path = doc_path.replace(".en.md", ".md")
    else:
        alt_path = doc_path.replace(".md", ".en.md")

    # Check if alternate language file exists
    alt_exists = os.path.exists(os.path.join(DOC_DIR, alt_path))
    alt_url = "/" + alt_path.replace(".md", ".html") if alt_exists else "#"

    # Build navigation HTML
    nav_html = build_navigation_html(nav_tree, doc_path, lang)

    # Build TOC HTML
    toc_html = build_toc_html(toc, labels["toc"]) if toc else ""

    # Get page title
    title = front_matter.get("title", os.path.basename(doc_path).replace(".md", "").replace("_", " ").title())

    # GitHub edit link
    github_edit_url = "https://github.com/{}/edit/{}/{}".format(
        GITHUB_REPO, GITHUB_BRANCH, os.path.join(DOC_DIR, doc_path)
    )

    # Generate full HTML
    html = HTML_TEMPLATE.format(
        title=escape(title),
        navigation=nav_html,
        content=html_content,
        toc=toc_html,
        home_url="/" if lang == "zh" else "/index.en.html",
        github_url="https://github.com/{}".format(GITHUB_REPO),
        issues_url="https://github.com/{}/issues".format(GITHUB_REPO),
        edit_url=github_edit_url,
        alt_lang_url=alt_url,
        labels_json=json.dumps(labels),
        home_label=labels["home"],
        github_label=labels["github"],
        issues_label=labels["issues"],
        edit_label=labels["edit"],
        toggle_nav_label=labels["toggle_nav"],
        switch_lang_label=labels["switch_lang"]
    )

    # Write output file
    output_path = os.path.join(output_dir, doc_path.replace(".md", ".html"))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("Generated: {}".format(output_path))


def build_navigation_html(nav_tree, current_path, lang):
    # type: (dict, str, str) -> str
    """
    Build navigation HTML from tree structure.

    Args:
        nav_tree (dict): Navigation tree
        current_path (str): Current page path
        lang (str): Language code (zh or en)

    Returns:
        str: Navigation HTML
    """
    html_parts = []

    # Root level items
    for item in sorted(nav_tree["items"], key=lambda x: x["base_name"]):
        if (lang == "en" and item["is_english"]) or (lang == "zh" and not item["is_english"]):
            is_active = item["path"] == current_path
            url = item["path"].replace(".md", ".html")
            html_parts.append(
                '<li class="nav-item{}"><a href="/{}">{}</a></li>'.format(
                    " active" if is_active else "",
                    url,
                    escape(item["title"])
                )
            )

    # Directory sections
    dir_order = ["config", "providers", "dev"]
    for dir_name in dir_order:
        if dir_name not in nav_tree["dirs"]:
            continue

        dir_info = nav_tree["dirs"][dir_name]
        label = dir_info["label_en"] if lang == "en" else dir_info["label_zh"]

        # Check if any item in this directory is current
        is_section_active = any(
            item["path"] == current_path
            for item in dir_info["items"]
            if (lang == "en" and item["is_english"]) or (lang == "zh" and not item["is_english"])
        )

        html_parts.append('<li class="nav-section{}">'.format(" active" if is_section_active else ""))
        html_parts.append('<div class="nav-section-title">{}</div>'.format(escape(label)))
        html_parts.append('<ul class="nav-section-items">')

        # Filter items by language
        filtered_items = [
            item for item in dir_info["items"]
            if (lang == "en" and item["is_english"]) or (lang == "zh" and not item["is_english"])
        ]

        for item in sorted(filtered_items, key=lambda x: x["base_name"]):
            is_active = item["path"] == current_path
            url = item["path"].replace(".md", ".html")
            html_parts.append(
                '<li class="nav-item{}"><a href="/{}">{}</a></li>'.format(
                    " active" if is_active else "",
                    url,
                    escape(item["title"])
                )
            )

        html_parts.append("</ul>")
        html_parts.append("</li>")

    return "\n".join(html_parts)


def build_toc_html(toc, title):
    # type: (list, str) -> str
    """
    Build table of contents HTML.

    Args:
        toc (list): List of (level, id, text) tuples
        title (str): TOC section title

    Returns:
        str: TOC HTML
    """
    if not toc:
        return ""

    html_parts = ['<div class="toc-title">{}</div>'.format(escape(title))]
    html_parts.append('<ul class="toc-list">')

    for level, header_id, text in toc:
        if level <= 3:  # Only show h1-h3 in TOC
            indent_class = "toc-level-{}".format(level)
            html_parts.append(
                '<li class="{}"><a href="#{}">{}</a></li>'.format(
                    indent_class,
                    header_id,
                    escape(text)
                )
            )

    html_parts.append("</ul>")
    return "\n".join(html_parts)


# HTML Template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - DDNS Documentation</title>
    <link rel="icon" type="image/svg+xml" href="/doc/img/ddns.svg">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}

        /* Header */
        .header {{
            background: #2c3e50;
            color: white;
            padding: 1rem;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .header-title {{
            font-size: 1.5rem;
            font-weight: bold;
        }}

        .header-nav {{
            display: flex;
            gap: 1rem;
        }}

        .header-nav a {{
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            transition: background 0.3s;
        }}

        .header-nav a:hover {{
            background: rgba(255,255,255,0.1);
        }}

        .mobile-toggle {{
            display: none;
            background: transparent;
            border: 2px solid white;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
        }}

        /* Layout */
        .container {{
            display: flex;
            max-width: 1400px;
            margin: 4rem auto 0;
            min-height: calc(100vh - 4rem);
        }}

        /* Sidebar Navigation */
        .sidebar {{
            width: 280px;
            background: white;
            padding: 2rem 1rem;
            position: fixed;
            top: 4rem;
            left: 0;
            bottom: 0;
            overflow-y: auto;
            border-right: 1px solid #e0e0e0;
            transition: transform 0.3s;
        }}

        .sidebar.hidden {{
            transform: translateX(-100%);
        }}

        .nav-list {{
            list-style: none;
        }}

        .nav-item {{
            margin: 0.25rem 0;
        }}

        .nav-item a {{
            display: block;
            padding: 0.5rem 1rem;
            color: #333;
            text-decoration: none;
            border-radius: 4px;
            transition: background 0.3s;
        }}

        .nav-item a:hover {{
            background: #f0f0f0;
        }}

        .nav-item.active a {{
            background: #3498db;
            color: white;
        }}

        .nav-section {{
            margin: 1rem 0;
        }}

        .nav-section-title {{
            font-weight: bold;
            padding: 0.5rem 1rem;
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .nav-section-items {{
            list-style: none;
            margin-left: 0.5rem;
        }}

        /* Main Content */
        .main-content {{
            flex: 1;
            margin-left: 280px;
            margin-right: 260px;
            padding: 2rem;
            background: white;
            min-height: calc(100vh - 8rem);
        }}

        .content {{
            max-width: 900px;
        }}

        .content h1 {{
            font-size: 2.5rem;
            margin-bottom: 1rem;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.5rem;
        }}

        .content h2 {{
            font-size: 2rem;
            margin: 2rem 0 1rem;
            color: #34495e;
        }}

        .content h3 {{
            font-size: 1.5rem;
            margin: 1.5rem 0 0.75rem;
            color: #34495e;
        }}

        .content h4 {{
            font-size: 1.25rem;
            margin: 1.25rem 0 0.5rem;
            color: #34495e;
        }}

        .content p {{
            margin: 1rem 0;
            line-height: 1.8;
        }}

        .content ul, .content ol {{
            margin: 1rem 0;
            padding-left: 2rem;
        }}

        .content li {{
            margin: 0.5rem 0;
        }}

        .content pre {{
            background: #f7f7f7;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
            margin: 1rem 0;
            border: 1px solid #e0e0e0;
        }}

        .content code {{
            background: #f0f0f0;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: "Courier New", monospace;
            font-size: 0.9em;
        }}

        .content pre code {{
            background: transparent;
            padding: 0;
        }}

        .content blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 1rem;
            margin: 1rem 0;
            color: #666;
            font-style: italic;
        }}

        .content img {{
            max-width: 100%;
            height: auto;
            margin: 1rem 0;
        }}

        .content a {{
            color: #3498db;
            text-decoration: none;
        }}

        .content a:hover {{
            text-decoration: underline;
        }}

        .content hr {{
            border: none;
            border-top: 1px solid #e0e0e0;
            margin: 2rem 0;
        }}

        .content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }}

        .content table th,
        .content table td {{
            border: 1px solid #e0e0e0;
            padding: 0.5rem;
            text-align: left;
        }}

        .content table th {{
            background: #f7f7f7;
            font-weight: bold;
        }}

        /* Table of Contents */
        .toc {{
            width: 260px;
            position: fixed;
            top: 4rem;
            right: 0;
            bottom: 0;
            padding: 2rem 1rem;
            overflow-y: auto;
            background: white;
            border-left: 1px solid #e0e0e0;
        }}

        .toc-title {{
            font-weight: bold;
            margin-bottom: 1rem;
            color: #2c3e50;
            font-size: 1.1rem;
        }}

        .toc-list {{
            list-style: none;
        }}

        .toc-list li {{
            margin: 0.5rem 0;
        }}

        .toc-list a {{
            color: #666;
            text-decoration: none;
            display: block;
            padding: 0.25rem 0;
            transition: color 0.3s;
        }}

        .toc-list a:hover {{
            color: #3498db;
        }}

        .toc-level-1 {{
            font-weight: bold;
        }}

        .toc-level-2 {{
            padding-left: 1rem;
        }}

        .toc-level-3 {{
            padding-left: 2rem;
            font-size: 0.9rem;
        }}

        /* Footer */
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 2rem 1rem;
            text-align: center;
            margin-left: 280px;
            margin-right: 260px;
        }}

        .footer a {{
            color: #3498db;
            text-decoration: none;
            margin: 0 1rem;
        }}

        .footer a:hover {{
            text-decoration: underline;
        }}

        /* Responsive Design */
        @media (max-width: 1200px) {{
            .toc {{
                display: none;
            }}

            .main-content {{
                margin-right: 0;
            }}

            .footer {{
                margin-right: 0;
            }}
        }}

        @media (max-width: 768px) {{
            .mobile-toggle {{
                display: block;
            }}

            .header-nav {{
                display: none;
            }}

            .sidebar {{
                transform: translateX(-100%);
            }}

            .sidebar.show {{
                transform: translateX(0);
                z-index: 999;
            }}

            .main-content {{
                margin-left: 0;
                padding: 1rem;
            }}

            .footer {{
                margin-left: 0;
            }}

            .content h1 {{
                font-size: 2rem;
            }}

            .content h2 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="header-title">
                <a href="{home_url}" style="color: white; text-decoration: none;">DDNS</a>
            </div>
            <button class="mobile-toggle" onclick="toggleNav()">{toggle_nav_label}</button>
            <nav class="header-nav">
                <a href="{home_url}">{home_label}</a>
                <a href="{github_url}" target="_blank">{github_label}</a>
                <a href="{issues_url}" target="_blank">{issues_label}</a>
                <a href="{alt_lang_url}">{switch_lang_label}</a>
            </nav>
        </div>
    </header>

    <div class="container">
        <aside class="sidebar" id="sidebar">
            <ul class="nav-list">
                {navigation}
            </ul>
        </aside>

        <main class="main-content">
            <article class="content">
                {content}
            </article>
        </main>

        <aside class="toc">
            {toc}
        </aside>
    </div>

    <footer class="footer">
        <p>
            <a href="{github_url}" target="_blank">{github_label}</a>
            <a href="{issues_url}" target="_blank">{issues_label}</a>
            <a href="{edit_url}" target="_blank">{edit_label}</a>
        </p>
        <p>&copy; 2024 DDNS Project. Licensed under MIT.</p>
    </footer>

    <script>
        function toggleNav() {{
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('show');
        }}

        // Smooth scroll for TOC links
        document.querySelectorAll('.toc a').forEach(link => {{
            link.addEventListener('click', function(e) {{
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {{
                    targetElement.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
    </script>
</body>
</html>
"""


def main():
    """Main build function."""
    print("Building DDNS documentation website...")

    # Create build directory
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

    # Copy static assets
    img_src = os.path.join(DOC_DIR, "img")
    img_dst = os.path.join(BUILD_DIR, "doc", "img")
    if os.path.exists(img_src):
        shutil.copytree(img_src, img_dst)
        print("Copied static assets")

    # Build navigation tree
    nav_tree = build_nav_tree(DOC_DIR)

    # Generate HTML for all markdown files
    for root, dirs, files in os.walk(DOC_DIR):
        for filename in files:
            if filename.endswith(".md"):
                doc_path = os.path.relpath(os.path.join(root, filename), DOC_DIR)
                generate_html(doc_path, nav_tree, BUILD_DIR)

    # Copy index files
    readme_zh = os.path.join("README.md")
    readme_en = os.path.join("README.en.md")

    if os.path.exists(readme_zh):
        # Generate index.html from README.md
        with open(readme_zh, "r", encoding="utf-8") as f:
            content = f.read()

        # Create a temporary doc path for README
        temp_doc_path = "index.md"
        with open(os.path.join(DOC_DIR, temp_doc_path), "w", encoding="utf-8") as f:
            f.write(content)

        generate_html(temp_doc_path, nav_tree, BUILD_DIR)

        # Move to root
        shutil.move(
            os.path.join(BUILD_DIR, "index.html"),
            os.path.join(BUILD_DIR, "index.html")
        )

        # Clean up temp file
        os.remove(os.path.join(DOC_DIR, temp_doc_path))

    if os.path.exists(readme_en):
        # Generate index.en.html from README.en.md
        with open(readme_en, "r", encoding="utf-8") as f:
            content = f.read()

        # Create a temporary doc path for README
        temp_doc_path = "index.en.md"
        with open(os.path.join(DOC_DIR, temp_doc_path), "w", encoding="utf-8") as f:
            f.write(content)

        generate_html(temp_doc_path, nav_tree, BUILD_DIR)

        # Move to root
        shutil.move(
            os.path.join(BUILD_DIR, "index.en.html"),
            os.path.join(BUILD_DIR, "index.en.html")
        )

        # Clean up temp file
        os.remove(os.path.join(DOC_DIR, temp_doc_path))

    # Copy CNAME if exists
    if os.path.exists("CNAME"):
        shutil.copy("CNAME", BUILD_DIR)

    # Copy favicon
    if os.path.exists("favicon.ico"):
        shutil.copy("favicon.ico", BUILD_DIR)

    print("\nBuild complete! Output directory: {}".format(BUILD_DIR))
    print("Open {}/index.html in a browser to view the documentation.".format(BUILD_DIR))


if __name__ == "__main__":
    main()
