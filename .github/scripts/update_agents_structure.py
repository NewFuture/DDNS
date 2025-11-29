#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to update the directory structure section in AGENTS.md.

This script dynamically scans the repository and generates an updated directory
structure that can be used to update the AGENTS.md file.
All file listings are generated from the actual filesystem.
"""

import os
import re
import sys
from datetime import datetime

# File descriptions for known files (used as fallback for better descriptions)
# New files will automatically be discovered and get auto-generated descriptions
FILE_DESCRIPTIONS = {
    # Root level
    "run.py": "Direct run script",
    "install.sh": "One-click install script",
    "pyproject.toml": "Python project configuration",
    "setup.cfg": "Setup configuration",
    ".gitignore": "Git ignore rules",
    "LICENSE": "MIT License",
    "README.md": "Main README (Chinese)",
    "README.en.md": "Main README (English)",
    # ddns main files
    "ddns/__init__.py": "Package initialization and version info",
    "ddns/__main__.py": "Entry point for module execution",
    "ddns/cache.py": "Cache management",
    "ddns/ip.py": "IP address detection logic",
    # ddns/config
    "ddns/config/__init__.py": "",
    "ddns/config/cli.py": "Command-line argument parsing",
    "ddns/config/config.py": "Configuration loading and merging",
    "ddns/config/env.py": "Environment variable parsing",
    "ddns/config/file.py": "JSON file configuration",
    # ddns/provider - base files only, providers are auto-generated
    "ddns/provider/__init__.py": "Provider registry",
    "ddns/provider/_base.py": "Abstract base classes (SimpleProvider, BaseProvider)",
    "ddns/provider/_signature.py": "HMAC signature utilities",
    # ddns/scheduler
    "ddns/scheduler/__init__.py": "",
    "ddns/scheduler/_base.py": "Base scheduler class",
    "ddns/scheduler/cron.py": "Cron-based scheduler (Linux/macOS)",
    "ddns/scheduler/launchd.py": "macOS launchd scheduler",
    "ddns/scheduler/schtasks.py": "Windows Task Scheduler",
    "ddns/scheduler/systemd.py": "Linux systemd timer",
    # ddns/util
    "ddns/util/__init__.py": "",
    "ddns/util/comment.py": "Comment handling",
    "ddns/util/fileio.py": "File I/O operations",
    "ddns/util/http.py": "HTTP client with proxy support",
    "ddns/util/try_run.py": "Safe command execution",
    # tests
    "tests/__init__.py": "Test initialization (path setup)",
    "tests/base_test.py": "Shared test utilities and base classes",
    "tests/README.md": "Testing documentation",
    # docker
    "docker/Dockerfile": "Main Dockerfile",
    "docker/glibc.Dockerfile": "glibc-based build",
    "docker/musl.Dockerfile": "musl-based build",
    "docker/entrypoint.sh": "Container entrypoint script",
    # doc files
    "doc/docker.md": "Docker documentation (Chinese)",
    "doc/docker.en.md": "Docker documentation (English)",
    "doc/install.md": "Installation guide (Chinese)",
    "doc/install.en.md": "Installation guide (English)",
    "doc/release.md": "Release notes",
    # doc/config files
    "doc/config/cli.md": "CLI usage (Chinese)",
    "doc/config/cli.en.md": "CLI usage (English)",
    "doc/config/env.md": "Environment variables (Chinese)",
    "doc/config/env.en.md": "Environment variables (English)",
    "doc/config/json.md": "JSON config (Chinese)",
    "doc/config/json.en.md": "JSON config (English)",
    # doc/dev files
    "doc/dev/provider.md": "Provider development guide (Chinese)",
    "doc/dev/provider.en.md": "Provider development guide (English)",
    "doc/dev/config.md": "Config system (Chinese)",
    "doc/dev/config.en.md": "Config system (English)",
    # doc/providers - README only, provider docs are auto-generated
    "doc/providers/README.md": "Provider list (Chinese)",
    "doc/providers/README.en.md": "Provider list (English)",
}

# Provider name mappings for nice display names
PROVIDER_NAMES = {
    "alidns": "AliDNS",
    "aliesa": "AliESA",
    "cloudflare": "Cloudflare",
    "dnscom": "DNS.COM",
    "dnspod": "DNSPod (China)",
    "dnspod_com": "DNSPod International",
    "edgeone": "EdgeOne",
    "edgeone_dns": "EdgeOne DNS",
    "he": "Hurricane Electric",
    "huaweidns": "Huawei Cloud DNS",
    "namesilo": "NameSilo",
    "noip": "No-IP",
    "tencentcloud": "Tencent Cloud",
    "callback": "Callback",
    "debug": "Debug",
    "51dns": "51DNS",
}


def extract_current_structure(agents_content):
    # type: (str) -> str | None
    """Extract the current directory structure section from AGENTS.md."""
    pattern = r"### Directory Structure\s*\n\n```text\n(.*?)```"
    match = re.search(pattern, agents_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def update_agents_structure(agents_content, new_structure):
    # type: (str, str) -> str
    """Update the directory structure section in AGENTS.md content."""
    pattern = r"(### Directory Structure\s*\n\n```text\n)(.*?)(```)"
    replacement = r"\g<1>" + new_structure + "\n" + r"\g<3>"
    return re.sub(pattern, replacement, agents_content, flags=re.DOTALL)


def update_version_and_date(agents_content, version, date_str):
    # type: (str, str, str) -> str
    """Update the version and date at the bottom of AGENTS.md."""
    agents_content = re.sub(r"\*\*Version\*\*\s*:\s*[\d.]+", "**Version**: " + version, agents_content)
    agents_content = re.sub(r"\*\*Last Updated\*\*\s*:\s*[\d-]+", "**Last Updated**: " + date_str, agents_content)
    return agents_content


def _parse_provider_init(repo_root):
    # type: (str) -> dict
    """Parse ddns/provider/__init__.py to extract provider name mappings."""
    provider_init_path = os.path.join(repo_root, "ddns", "provider", "__init__.py")
    provider_mapping = {}

    if not os.path.exists(provider_init_path):
        return provider_mapping

    try:
        with open(provider_init_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse the mapping dictionary to extract provider names
        # Match patterns like: "dnspod": DnspodProvider,
        pattern = r'"([^"]+)":\s*(\w+Provider)'
        matches = re.findall(pattern, content)

        for provider_key, class_name in matches:
            # Extract base name from class name (e.g., DnspodProvider -> Dnspod)
            # Remove 'Provider' suffix and format nicely
            if class_name.endswith("Provider"):
                base_class_name = class_name[:-8]  # Remove 'Provider'
                # Only add the primary provider name (first occurrence of each class)
                if provider_key not in provider_mapping:
                    provider_mapping[provider_key] = base_class_name
    except (OSError, IOError):
        pass

    return provider_mapping


# Cache for provider init parsing
_PROVIDER_INIT_CACHE = {}


def get_provider_name(base_name, repo_root=None):
    # type: (str, str | None) -> str
    """Get nice display name for a provider.

    First checks PROVIDER_NAMES, then reads from ddns/provider/__init__.py.
    """
    # Check static mapping first
    if base_name in PROVIDER_NAMES:
        return PROVIDER_NAMES[base_name]

    # Try to read from provider __init__.py if repo_root is provided
    if repo_root:
        global _PROVIDER_INIT_CACHE
        if not _PROVIDER_INIT_CACHE:
            _PROVIDER_INIT_CACHE = _parse_provider_init(repo_root)

        if base_name in _PROVIDER_INIT_CACHE:
            return _PROVIDER_INIT_CACHE[base_name]

    # Fallback to title case
    return base_name.title()


def get_provider_doc_description(filename, repo_root=None):
    # type: (str, str | None) -> str
    """Generate description for provider documentation files."""
    is_english = filename.endswith(".en.md")
    base_name = filename.replace(".en.md", "").replace(".md", "")

    if base_name == "README":
        return "Provider list (English)" if is_english else "Provider list (Chinese)"

    provider_name = get_provider_name(base_name, repo_root)
    lang = "English" if is_english else "Chinese"
    return provider_name + " guide (" + lang + ")"


def get_provider_code_description(filename, repo_root=None):
    # type: (str, str | None) -> str
    """Generate description for provider Python files."""
    base_name = filename.replace(".py", "")
    provider_name = get_provider_name(base_name, repo_root)
    return provider_name + " DNS provider"


def version_sort_key(filename):
    # type: (str) -> list
    """Sort key for version-named files like v2.json, v2.8.json, v4.0.json."""
    name = filename.rsplit(".", 1)[0]
    if name.startswith("v"):
        name = name[1:]
    parts = name.split(".")
    result = []
    for part in parts:
        try:
            result.append(int(part))
        except ValueError:
            result.append(0)
    return result


def get_sorted_files(directory, extensions=None, version_sort=False, exclude_dirs=True):
    # type: (str, list | None, bool, bool) -> list
    """Get sorted list of files from a directory."""
    result = []
    if os.path.isdir(directory):
        for f in os.listdir(directory):
            filepath = os.path.join(directory, f)
            if exclude_dirs and os.path.isdir(filepath):
                continue
            if extensions:
                if any(f.endswith(ext) for ext in extensions):
                    result.append(f)
            else:
                result.append(f)
    if version_sort:
        result.sort(key=version_sort_key)
    else:
        result.sort()
    return result


def get_subdirs(directory):
    # type: (str) -> list
    """Get sorted list of subdirectories."""
    result = []
    if os.path.isdir(directory):
        for f in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, f)):
                result.append(f)
    result.sort()
    return result


def get_file_description(filepath, filename):
    # type: (str, str) -> str
    """Get description for a file, using FILE_DESCRIPTIONS or auto-generating."""
    desc = FILE_DESCRIPTIONS.get(filepath, "")
    if desc:
        return desc

    # Auto-generate description based on file type and location
    if filename == "__init__.py":
        return ""
    if filename.startswith("_"):
        return ""
    if filename.endswith(".py"):
        name = filename[:-3]
        return name.title().replace("_", " ") + " module"
    if filename.endswith(".md"):
        name = filename[:-3]
        is_english = filename.endswith(".en.md")
        if is_english:
            name = name[:-3]
        lang = " (English)" if is_english else " (Chinese)"
        return name.title().replace("_", " ") + " documentation" + lang
    if filename.endswith(".json"):
        return "JSON configuration"
    if filename.endswith(".sh"):
        return "Shell script"

    return ""


def _generate_files_dynamic(lines, repo_root, rel_dir, prefix_base, extensions=None, version_sort=False):
    # type: (list, str, str, str, list | None, bool) -> None
    """Dynamically generate file entries for a directory."""
    abs_dir = os.path.join(repo_root, rel_dir)
    files = get_sorted_files(abs_dir, extensions, version_sort)

    for i, f in enumerate(files):
        filepath = rel_dir + "/" + f
        desc = get_file_description(filepath, f)

        is_last = i == len(files) - 1
        prefix = prefix_base + ("\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 ")

        if desc:
            padded_name = f.ljust(20)
            lines.append(prefix + padded_name + "# " + desc)
        else:
            lines.append(prefix + f)


def _generate_provider_files(lines, repo_root):
    # type: (list, str) -> None
    """Generate provider file entries dynamically."""
    lines.append("\u2502   \u251c\u2500\u2500 provider/               # DNS provider implementations")
    provider_dir = os.path.join(repo_root, "ddns", "provider")
    provider_files = get_sorted_files(provider_dir, [".py"])

    for i, f in enumerate(provider_files):
        filepath = "ddns/provider/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")

        is_last = i == len(provider_files) - 1
        prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "

        if desc:
            padded_name = f.ljust(20)
            lines.append(prefix + padded_name + "# " + desc)
        elif f == "__init__.py" or f.startswith("_"):
            lines.append(prefix + f)
        else:
            # Auto-generate description for unknown providers
            padded_name = f.ljust(20)
            lines.append(prefix + padded_name + "# " + get_provider_code_description(f, repo_root))
    lines.append("\u2502   \u2502")


def _generate_scheduler_files(lines, repo_root):
    # type: (list, str) -> None
    """Generate scheduler file entries dynamically."""
    lines.append("\u2502   \u251c\u2500\u2500 scheduler/              # Task scheduling implementations")
    scheduler_dir = os.path.join(repo_root, "ddns", "scheduler")
    scheduler_files = get_sorted_files(scheduler_dir, [".py"])

    for i, f in enumerate(scheduler_files):
        filepath = "ddns/scheduler/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")

        is_last = i == len(scheduler_files) - 1
        prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "

        if desc:
            padded_name = f.ljust(20)
            lines.append(prefix + padded_name + "# " + desc)
        elif f == "__init__.py" or f.startswith("_"):
            lines.append(prefix + f)
        else:
            padded_name = f.ljust(20)
            name = f[:-3]
            lines.append(prefix + padded_name + "# " + name.title() + " scheduler")
    lines.append("\u2502   \u2502")


def _generate_util_files(lines, repo_root):
    # type: (list, str) -> None
    """Generate util file entries dynamically."""
    lines.append("\u2502   \u2514\u2500\u2500 util/                   # Utility modules")
    util_dir = os.path.join(repo_root, "ddns", "util")
    util_files = get_sorted_files(util_dir, [".py"])

    for i, f in enumerate(util_files):
        filepath = "ddns/util/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")

        is_last = i == len(util_files) - 1
        prefix = "\u2502       \u2514\u2500\u2500 " if is_last else "\u2502       \u251c\u2500\u2500 "

        if desc:
            padded_name = f.ljust(20)
            lines.append(prefix + padded_name + "# " + desc)
        elif f == "__init__.py" or f.startswith("_"):
            lines.append(prefix + f)
        else:
            padded_name = f.ljust(20)
            name = f[:-3]
            lines.append(prefix + padded_name + "# " + name.title().replace("_", " ") + " utilities")
    lines.append("\u2502")


def _generate_config_files(lines, repo_root):
    # type: (list, str) -> None
    """Generate ddns/config file entries dynamically."""
    lines.append("\u2502   \u251c\u2500\u2500 config/                 # Configuration management")
    config_dir = os.path.join(repo_root, "ddns", "config")
    config_files = get_sorted_files(config_dir, [".py"])

    for i, f in enumerate(config_files):
        filepath = "ddns/config/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")

        is_last = i == len(config_files) - 1
        prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "

        if desc:
            padded_name = f.ljust(20)
            lines.append(prefix + padded_name + "# " + desc)
        elif f == "__init__.py" or f.startswith("_"):
            lines.append(prefix + f)
        else:
            padded_name = f.ljust(20)
            name = f[:-3]
            lines.append(prefix + padded_name + "# " + name.title() + " configuration")
    lines.append("\u2502   \u2502")


def _generate_ddns_main_files(lines, repo_root):
    # type: (list, str) -> None
    """Generate main ddns files dynamically."""
    ddns_dir = os.path.join(repo_root, "ddns")
    # Get only Python files (exclude .pyi stub files), not directories
    main_files = get_sorted_files(ddns_dir, [".py"])

    for f in main_files:
        filepath = "ddns/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")

        if desc:
            padded_name = f.ljust(20)
            lines.append("\u2502   \u251c\u2500\u2500 " + padded_name + "# " + desc)
        elif f == "__init__.py":
            lines.append("\u2502   \u251c\u2500\u2500 " + f.ljust(20) + "# Package initialization")
        elif f.startswith("_"):
            lines.append("\u2502   \u251c\u2500\u2500 " + f)
        else:
            padded_name = f.ljust(20)
            name = f.rsplit(".", 1)[0]
            lines.append("\u2502   \u251c\u2500\u2500 " + padded_name + "# " + name.title() + " module")
    lines.append("\u2502   \u2502")


def _generate_doc_config_section(lines, repo_root):
    # type: (list, str) -> None
    """Generate doc/config section dynamically."""
    lines.append("\u2502   \u251c\u2500\u2500 config/                 # Configuration documentation")
    config_dir = os.path.join(repo_root, "doc", "config")
    config_files = get_sorted_files(config_dir, [".md"])

    for i, f in enumerate(config_files):
        filepath = "doc/config/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        if not desc:
            is_english = f.endswith(".en.md")
            base_name = f.replace(".en.md", "").replace(".md", "")
            lang = " (English)" if is_english else " (Chinese)"
            desc = base_name.upper() + " documentation" + lang

        is_last = i == len(config_files) - 1
        prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "

        padded_name = f.ljust(20)
        lines.append(prefix + padded_name + "# " + desc)
    lines.append("\u2502   \u2502")


def _generate_doc_dev_section(lines, repo_root):
    # type: (list, str) -> None
    """Generate doc/dev section dynamically."""
    lines.append("\u2502   \u251c\u2500\u2500 dev/                    # Developer documentation")
    dev_dir = os.path.join(repo_root, "doc", "dev")
    dev_files = get_sorted_files(dev_dir, [".md"])

    for i, f in enumerate(dev_files):
        filepath = "doc/dev/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        if not desc:
            is_english = f.endswith(".en.md")
            base_name = f.replace(".en.md", "").replace(".md", "")
            lang = " (English)" if is_english else " (Chinese)"
            desc = base_name.title() + " development guide" + lang

        is_last = i == len(dev_files) - 1
        prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "

        padded_name = f.ljust(20)
        lines.append(prefix + padded_name + "# " + desc)
    lines.append("\u2502   \u2502")


def _generate_doc_providers_section(lines, repo_root):
    # type: (list, str) -> None
    """Generate doc/providers section dynamically."""
    lines.append("\u2502   \u251c\u2500\u2500 providers/              # Provider-specific documentation")
    providers_dir = os.path.join(repo_root, "doc", "providers")
    provider_docs = get_sorted_files(providers_dir, [".md"])

    for i, f in enumerate(provider_docs):
        filepath = "doc/providers/" + f
        desc = FILE_DESCRIPTIONS.get(filepath)
        if not desc:
            desc = get_provider_doc_description(f, repo_root)

        is_last = i == len(provider_docs) - 1
        prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "

        padded_name = f.ljust(20)
        lines.append(prefix + padded_name + "# " + desc)
    lines.append("\u2502   \u2502")


def _generate_doc_examples_section(lines, repo_root):
    # type: (list, str) -> None
    """Generate doc/examples section dynamically."""
    lines.append("\u2502   \u251c\u2500\u2500 examples/               # Example configuration files")
    examples_dir = os.path.join(repo_root, "doc", "examples")
    example_files = get_sorted_files(examples_dir)

    for i, f in enumerate(example_files):
        filepath = "doc/examples/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        if not desc:
            if f.endswith(".json"):
                desc = "Example configuration"
            else:
                desc = "Example file"

        is_last = i == len(example_files) - 1
        prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "

        padded_name = f.ljust(24)
        lines.append(prefix + padded_name + "# " + desc)
    lines.append("\u2502   \u2502")


def _generate_doc_root_files(lines, repo_root):
    # type: (list, str) -> None
    """Generate doc root level files dynamically."""
    doc_dir = os.path.join(repo_root, "doc")
    # Get files only (not directories) at doc root
    doc_files = get_sorted_files(doc_dir, [".md"])

    for f in doc_files:
        filepath = "doc/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        if not desc:
            is_english = f.endswith(".en.md")
            base_name = f.replace(".en.md", "").replace(".md", "")
            lang = " (English)" if is_english else " (Chinese)"
            desc = base_name.title() + " documentation" + lang

        padded_name = f.ljust(24)
        lines.append("\u2502   \u251c\u2500\u2500 " + padded_name + "# " + desc)

    lines.append("\u2502   \u2514\u2500\u2500 img/                    # Images and diagrams")
    lines.append("\u2502")


def _generate_doc_section(lines, repo_root):
    # type: (list, str) -> None
    """Generate entire doc section dynamically."""
    lines.append("\u251c\u2500\u2500 doc/                        # Documentation")
    _generate_doc_config_section(lines, repo_root)
    _generate_doc_dev_section(lines, repo_root)
    _generate_doc_providers_section(lines, repo_root)
    _generate_doc_examples_section(lines, repo_root)
    _generate_doc_root_files(lines, repo_root)


def _generate_docker_section(lines, repo_root):
    # type: (list, str) -> None
    """Generate docker section dynamically."""
    lines.append("\u251c\u2500\u2500 docker/                     # Docker configuration")
    docker_dir = os.path.join(repo_root, "docker")
    docker_files = get_sorted_files(docker_dir)

    for i, f in enumerate(docker_files):
        filepath = "docker/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        if not desc:
            if f.endswith("Dockerfile") or f == "Dockerfile":
                desc = f + " build"
            elif f.endswith(".sh"):
                desc = "Shell script"
            else:
                desc = "Docker file"

        is_last = i == len(docker_files) - 1
        prefix = "\u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u251c\u2500\u2500 "

        padded_name = f.ljust(20)
        lines.append(prefix + padded_name + "# " + desc)
    lines.append("\u2502")


def _generate_schema_section(lines, repo_root):
    # type: (list, str) -> None
    """Generate schema section dynamically."""
    lines.append("\u251c\u2500\u2500 schema/                     # JSON schemas")
    schema_dir = os.path.join(repo_root, "schema")
    schema_files = get_sorted_files(schema_dir, [".json"], version_sort=True)

    for i, f in enumerate(schema_files):
        is_last = i == len(schema_files) - 1
        prefix = "\u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u251c\u2500\u2500 "

        version = f[:-5]  # Remove .json
        # Determine description based on position in list
        if i == 0:
            desc = "Legacy schema " + version
        elif i == len(schema_files) - 1:
            desc = "Latest schema " + version
        elif i == len(schema_files) - 2:
            desc = "Previous schema " + version
        else:
            desc = "Schema " + version

        padded_name = f.ljust(24)
        lines.append(prefix + padded_name + "# " + desc)
    lines.append("\u2502")


def _generate_tests_section(lines, repo_root):
    # type: (list, str) -> None
    """Generate tests section dynamically."""
    lines.append("\u251c\u2500\u2500 tests/                      # Unit tests")
    tests_dir = os.path.join(repo_root, "tests")

    # Get specific files first
    specific_files = ["__init__.py", "base_test.py", "README.md"]
    for f in specific_files:
        if os.path.exists(os.path.join(tests_dir, f)):
            filepath = "tests/" + f
            desc = FILE_DESCRIPTIONS.get(filepath, "")
            if desc:
                padded_name = f.ljust(20)
                lines.append("\u2502   \u251c\u2500\u2500 " + padded_name + "# " + desc)
            else:
                lines.append("\u2502   \u251c\u2500\u2500 " + f)

    # Get subdirectories
    subdirs = get_subdirs(tests_dir)
    for d in subdirs:
        lines.append("\u2502   \u251c\u2500\u2500 " + (d + "/").ljust(20) + "# Test " + d + " files")

    # Get test file patterns - group by category
    test_files = get_sorted_files(tests_dir, [".py"])
    test_categories = set()
    standalone_tests = []  # Tests without category suffix like test_cache.py, test_ip.py

    for f in test_files:
        if f.startswith("test_") and f not in specific_files:
            # Extract category like "provider", "config", etc.
            name_without_ext = f[5:-3]  # Remove "test_" prefix and ".py" suffix
            parts = name_without_ext.split("_")
            if len(parts) >= 2:
                # Has underscore, so it's like test_provider_xxx.py
                category = parts[0]
                test_categories.add(category)
            else:
                # No underscore, so it's like test_cache.py
                standalone_tests.append(f)

    # Generate pattern lines for each category
    sorted_categories = sorted(test_categories)
    for category in sorted_categories:
        pattern = "test_" + category + "_*.py"
        lines.append("\u2502   \u251c\u2500\u2500 " + pattern.ljust(24) + "# " + category.title() + " tests")

    # Generate lines for standalone tests
    for i, f in enumerate(standalone_tests):
        is_last = i == len(standalone_tests) - 1 and not sorted_categories
        prefix = "\u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u251c\u2500\u2500 "
        name = f[5:-3].title()  # Remove test_ and .py
        lines.append(prefix + f.ljust(20) + "# " + name + " tests")

    lines.append("\u2502")


def _generate_root_files(lines, repo_root):
    # type: (list, str) -> None
    """Generate root level files dynamically."""
    # Priority files to show
    root_files = [
        "run.py",
        "install.sh",
        "pyproject.toml",
        "setup.cfg",
        ".gitignore",
        "LICENSE",
        "README.md",
        "README.en.md",
    ]

    for i, f in enumerate(root_files):
        if not os.path.exists(os.path.join(repo_root, f)):
            continue

        desc = FILE_DESCRIPTIONS.get(f, "")
        if not desc:
            if f.endswith(".py"):
                desc = "Python script"
            elif f.endswith(".sh"):
                desc = "Shell script"
            elif f.endswith(".md"):
                is_english = f.endswith(".en.md")
                desc = "README (English)" if is_english else "README (Chinese)"
            else:
                desc = "Configuration file"

        is_last = i == len(root_files) - 1
        prefix = "\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 "

        padded_name = f.ljust(28)
        lines.append(prefix + padded_name + "# " + desc)


def generate_full_structure(repo_root):
    # type: (str) -> str
    """Generate the full directory structure dynamically from filesystem."""
    lines = []

    # Root
    lines.append("DDNS/")

    # .github section (static - internal config)
    lines.append("\u251c\u2500\u2500 .github/                    # GitHub configuration")
    lines.append("\u2502   \u251c\u2500\u2500 workflows/              # CI/CD workflows (build, publish, test)")
    lines.append("\u2502   \u251c\u2500\u2500 instructions/           # Agent instructions (python.instructions.md)")
    lines.append("\u2502   \u2514\u2500\u2500 copilot-instructions.md # GitHub Copilot instructions")
    lines.append("\u2502")

    # ddns section - dynamic
    lines.append("\u251c\u2500\u2500 ddns/                       # Main application code")
    _generate_ddns_main_files(lines, repo_root)
    _generate_config_files(lines, repo_root)
    _generate_provider_files(lines, repo_root)
    _generate_scheduler_files(lines, repo_root)
    _generate_util_files(lines, repo_root)

    # tests section - dynamic
    _generate_tests_section(lines, repo_root)

    # doc section - dynamic
    _generate_doc_section(lines, repo_root)

    # docker section - dynamic
    _generate_docker_section(lines, repo_root)

    # schema section - dynamic
    _generate_schema_section(lines, repo_root)

    # Root files - dynamic
    _generate_root_files(lines, repo_root)

    return "\n".join(lines)


def main():
    # type: () -> None
    """Main function to update AGENTS.md directory structure."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))

    agents_file = os.path.join(repo_root, "AGENTS.md")

    if not os.path.exists(agents_file):
        print("Error: AGENTS.md not found at " + agents_file)
        sys.exit(1)

    with open(agents_file, "r", encoding="utf-8") as f:
        agents_content = f.read()

    current_structure = extract_current_structure(agents_content)
    if current_structure is None:
        print("Error: Could not find directory structure section in AGENTS.md")
        sys.exit(1)

    new_structure = generate_full_structure(repo_root)

    if current_structure.strip() == new_structure.strip():
        print("No changes detected in directory structure.")
        sys.exit(0)

    updated_content = update_agents_structure(agents_content, new_structure)

    version_match = re.search(r"\*\*Version\*\*\s*:\s*([\d.]+)", agents_content)
    if version_match:
        current_version = version_match.group(1)
        version_parts = current_version.split(".")
        while len(version_parts) < 3:
            version_parts.append("0")
        version_parts[2] = str(int(version_parts[2]) + 1)
        new_version = ".".join(version_parts)
    else:
        new_version = "1.0.0"

    today = datetime.now().strftime("%Y-%m-%d")
    updated_content = update_version_and_date(updated_content, new_version, today)

    with open(agents_file, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("AGENTS.md directory structure has been updated.")
    print("\nChanges detected:")
    print("Old structure lines: " + str(len(current_structure.strip().split("\n"))))
    print("New structure lines: " + str(len(new_structure.strip().split("\n"))))
    print("Version: " + new_version)
    print("Date: " + today)

    sys.exit(0)


if __name__ == "__main__":
    main()
