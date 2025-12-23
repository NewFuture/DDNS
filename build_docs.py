#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Documentation website builder using MkDocs with Material theme.

This script sets up and builds the DDNS documentation website using mature
tools instead of custom markdown parsing:
- MkDocs: Popular static site generator for project documentation
- Material for MkDocs: Modern, responsive theme with built-in features
"""

import os
import sys
import subprocess
import json
import shutil


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import mkdocs
        import material
        return True
    except ImportError:
        return False


def install_dependencies():
    """Install MkDocs and Material theme."""
    print("Installing dependencies (MkDocs and Material theme)...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "mkdocs-material"]
        )
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print("Error installing dependencies: {}".format(e))
        return False


def generate_mkdocs_config():
    """Generate mkdocs.yml configuration file."""
    # Scan documentation structure
    doc_structure = scan_docs()

    config = {
        "site_name": "DDNS Documentation",
        "site_url": "https://ddns.newfuture.cc",
        "site_description": "Dynamic DNS client with support for multiple DNS providers",
        "repo_url": "https://github.com/NewFuture/DDNS",
        "repo_name": "NewFuture/DDNS",
        "edit_uri": "edit/master/",
        "theme": {
            "name": "material",
            "language": "zh",
            "favicon": "doc/img/ddns.svg",
            "logo": "doc/img/ddns.svg",
            "palette": [
                {
                    "scheme": "default",
                    "primary": "blue",
                    "accent": "light-blue",
                    "toggle": {
                        "icon": "material/brightness-7",
                        "name": "Switch to dark mode",
                    },
                },
                {
                    "scheme": "slate",
                    "primary": "blue",
                    "accent": "light-blue",
                    "toggle": {
                        "icon": "material/brightness-4",
                        "name": "Switch to light mode",
                    },
                },
            ],
            "features": [
                "navigation.instant",
                "navigation.tracking",
                "navigation.tabs",
                "navigation.sections",
                "navigation.expand",
                "navigation.top",
                "navigation.footer",
                "toc.follow",
                "toc.integrate",
                "search.suggest",
                "search.highlight",
                "content.code.copy",
                "content.action.edit",
            ],
        },
        "plugins": ["search"],
        "markdown_extensions": [
            "admonition",
            "attr_list",
            "def_list",
            "footnotes",
            "meta",
            "md_in_html",
            "toc",
            "pymdownx.arithmatex",
            "pymdownx.betterem",
            "pymdownx.caret",
            "pymdownx.mark",
            "pymdownx.tilde",
            "pymdownx.critic",
            "pymdownx.details",
            "pymdownx.emoji",
            "pymdownx.highlight",
            "pymdownx.inlinehilite",
            "pymdownx.keys",
            "pymdownx.magiclink",
            "pymdownx.smartsymbols",
            "pymdownx.superfences",
            "pymdownx.tabbed",
            "pymdownx.tasklist",
        ],
        "extra": {
            "social": [
                {
                    "icon": "fontawesome/brands/github",
                    "link": "https://github.com/NewFuture/DDNS",
                },
                {
                    "icon": "fontawesome/brands/docker",
                    "link": "https://hub.docker.com/r/newfuture/ddns",
                },
                {
                    "icon": "fontawesome/brands/python",
                    "link": "https://pypi.org/project/ddns/",
                },
            ],
            "version": {
                "provider": "mike"
            },
        },
        "nav": build_navigation(doc_structure),
    }

    # Write configuration
    import yaml

    try:
        with open("mkdocs.yml", "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
        print("Generated mkdocs.yml configuration")
        return True
    except Exception as e:
        print("Error writing mkdocs.yml: {}".format(e))
        # Fallback: write minimal config without i18n plugin
        config["plugins"] = ["search"]
        with open("mkdocs.yml", "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
        print("Generated mkdocs.yml configuration (minimal)")
        return True


def scan_docs():
    """Scan doc directory to understand structure."""
    structure = {"zh": {}, "en": {}}

    for root, dirs, files in os.walk("doc"):
        for filename in files:
            if not filename.endswith(".md"):
                continue

            rel_path = os.path.relpath(os.path.join(root, filename), "doc")
            is_english = filename.endswith(".en.md")
            lang = "en" if is_english else "zh"

            # Categorize by directory
            parts = rel_path.split(os.sep)
            if len(parts) > 1:
                category = parts[0]
                if category not in structure[lang]:
                    structure[lang][category] = []
                structure[lang][category].append(rel_path)
            else:
                if "root" not in structure[lang]:
                    structure[lang]["root"] = []
                structure[lang]["root"].append(rel_path)

    return structure


def build_navigation(structure):
    """Build navigation structure for mkdocs.yml."""
    nav = [
        {"首页": "README.md"},
        {"Docker": "doc/docker.md"},
        {"安装": "doc/install.md"},
        {
            "配置方式": [
                {"命令行参数": "doc/config/cli.md"},
                {"环境变量": "doc/config/env.md"},
                {"JSON配置": "doc/config/json.md"},
            ]
        },
        {
            "DNS服务商": [
                {"概述": "doc/providers/README.md"},
                {"阿里DNS": "doc/providers/alidns.md"},
                {"阿里云ESA": "doc/providers/aliesa.md"},
                {"51DNS": "doc/providers/51dns.md"},
                {"Cloudflare": "doc/providers/cloudflare.md"},
                {"DNSPod": "doc/providers/dnspod.md"},
                {"DNSPod国际版": "doc/providers/dnspod_com.md"},
                {"腾讯云DNS": "doc/providers/tencentcloud.md"},
                {"腾讯云EdgeOne": "doc/providers/edgeone.md"},
                {"华为云DNS": "doc/providers/huaweidns.md"},
                {"HE.net": "doc/providers/he.md"},
                {"NameSilo": "doc/providers/namesilo.md"},
                {"No-IP": "doc/providers/noip.md"},
                {"回调API": "doc/providers/callback.md"},
                {"调试模式": "doc/providers/debug.md"},
            ]
        },
        {
            "开发文档": [
                {"配置文档": "doc/dev/config.md"},
                {"Provider开发": "doc/dev/provider.md"},
            ]
        },
    ]

    return nav


def prepare_docs():
    """Prepare documentation files for MkDocs."""
    # Create docs directory for MkDocs
    docs_dir = "docs"
    if os.path.exists(docs_dir):
        shutil.rmtree(docs_dir)
    os.makedirs(docs_dir)

    # Copy README as index
    if os.path.exists("README.md"):
        shutil.copy("README.md", os.path.join(docs_dir, "index.md"))

    # Copy doc directory
    if os.path.exists("doc"):
        shutil.copytree("doc", os.path.join(docs_dir, "doc"))

    print("Prepared documentation files")


def build_site():
    """Build the documentation site using MkDocs."""
    print("Building documentation website with MkDocs...")
    try:
        subprocess.check_call(["mkdocs", "build", "--clean"])
        print("\nBuild complete!")
        print("Output directory: site/")
        print("To preview locally: mkdocs serve")
        return True
    except subprocess.CalledProcessError as e:
        print("Error building site: {}".format(e))
        return False
    except FileNotFoundError:
        print("Error: mkdocs command not found")
        return False


def main():
    """Main build function."""
    print("=" * 60)
    print("DDNS Documentation Builder")
    print("Using MkDocs with Material theme")
    print("=" * 60)
    print()

    # Check and install dependencies
    if not check_dependencies():
        print("Required dependencies not found.")
        response = input("Install MkDocs and Material theme? (y/n): ")
        if response.lower() != "y":
            print("Aborted. Please install manually:")
            print("  pip install mkdocs-material")
            return False

        if not install_dependencies():
            return False

    # Check if PyYAML is available
    try:
        import yaml
    except ImportError:
        print("Installing PyYAML...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pyyaml"])

    # Generate configuration
    if not generate_mkdocs_config():
        return False

    # Prepare documentation files
    prepare_docs()

    # Build the site
    if not build_site():
        return False

    print()
    print("=" * 60)
    print("Documentation built successfully!")
    print("=" * 60)
    print()
    print("Preview locally:")
    print("  mkdocs serve")
    print()
    print("Deploy to GitHub Pages:")
    print("  mkdocs gh-deploy")
    print()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
