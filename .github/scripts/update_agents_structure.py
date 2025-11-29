#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to compare the directory structure in AGENTS.md with actual files.

This script scans the repository and compares the directory structure with
what's documented in AGENTS.md. If differences are found, it outputs the
added and deleted files for creating an issue.
"""

import os
import re
import sys

# File descriptions for known files
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
    # ddns/provider
    "ddns/provider/__init__.py": "Provider registry",
    "ddns/provider/_base.py": "Abstract base classes (SimpleProvider, BaseProvider)",
    "ddns/provider/_signature.py": "HMAC signature utilities",
    "ddns/provider/alidns.py": "Alibaba Cloud DNS",
    "ddns/provider/aliesa.py": "Alibaba Cloud ESA",
    "ddns/provider/callback.py": "Custom webhook callbacks",
    "ddns/provider/cloudflare.py": "Cloudflare DNS",
    "ddns/provider/debug.py": "Debug provider",
    "ddns/provider/dnscom.py": "DNS.COM",
    "ddns/provider/dnspod.py": "DNSPod (China)",
    "ddns/provider/dnspod_com.py": "DNSPod International",
    "ddns/provider/edgeone.py": "Tencent EdgeOne",
    "ddns/provider/edgeone_dns.py": "Tencent EdgeOne DNS",
    "ddns/provider/he.py": "Hurricane Electric",
    "ddns/provider/huaweidns.py": "Huawei Cloud DNS",
    "ddns/provider/namesilo.py": "NameSilo",
    "ddns/provider/noip.py": "No-IP",
    "ddns/provider/tencentcloud.py": "Tencent Cloud DNS",
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
    # doc main files
    "doc/docker.md": "Docker documentation (Chinese)",
    "doc/docker.en.md": "Docker documentation (English)",
    "doc/install.md": "Installation guide (Chinese)",
    "doc/install.en.md": "Installation guide (English)",
    "doc/release.md": "Release notes",
    # doc/config
    "doc/config/cli.md": "CLI usage (Chinese)",
    "doc/config/cli.en.md": "CLI usage (English)",
    "doc/config/env.md": "Environment variables (Chinese)",
    "doc/config/env.en.md": "Environment variables (English)",
    "doc/config/json.md": "JSON config (Chinese)",
    "doc/config/json.en.md": "JSON config (English)",
    # doc/dev
    "doc/dev/provider.md": "Provider development guide (Chinese)",
    "doc/dev/provider.en.md": "Provider development guide (English)",
    "doc/dev/config.md": "Config system (Chinese)",
    "doc/dev/config.en.md": "Config system (English)",
    # doc/providers
    "doc/providers/README.md": "Provider list (Chinese)",
    "doc/providers/README.en.md": "Provider list (English)",
    # doc/img
    "doc/img/ddns.png": "Project logo",
    "doc/img/ddns.svg": "Project logo (SVG)",
    # doc/examples
    "doc/examples/config-with-extra.json": "Example configuration with extra options",
}


def extract_current_structure(agents_content):
    # type: (str) -> str | None
    """Extract the current directory structure section from AGENTS.md."""
    # Find the directory structure section
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


def version_sort_key(filename):
    # type: (str) -> list
    """Sort key for version-named files like v2.json, v2.8.json, v4.0.json."""
    # Extract version number from filename (e.g., v2.8.json -> [2, 8])
    name = filename.rsplit(".", 1)[0]  # Remove extension
    if name.startswith("v"):
        name = name[1:]  # Remove 'v' prefix
    parts = name.split(".")
    result = []
    for part in parts:
        try:
            result.append(int(part))
        except ValueError:
            result.append(0)
    return result


def get_sorted_files(directory, extensions=None, version_sort=False):
    # type: (str, list | None, bool) -> list
    """Get sorted list of files from a directory."""
    result = []
    if os.path.isdir(directory):
        for f in os.listdir(directory):
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


def scan_directory_files(repo_root, directory, extensions=None):
    # type: (str, str, list | None) -> set
    """Recursively scan a directory and return all file paths relative to repo root."""
    result = set()
    dir_path = os.path.join(repo_root, directory)
    if not os.path.isdir(dir_path):
        return result

    for root, dirs, files in os.walk(dir_path):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

        for f in files:
            # Skip hidden files and .pyc files
            if f.startswith(".") or f.endswith(".pyc"):
                continue
            if extensions and not any(f.endswith(ext) for ext in extensions):
                continue
            rel_path = os.path.relpath(os.path.join(root, f), repo_root)
            result.add(rel_path)

    return result


def extract_files_from_structure(structure_text):
    # type: (str) -> set
    """Extract file paths from the directory structure text in AGENTS.md.

    Uses a stack-based approach to track directory paths based on tree depth.
    """
    files = set()
    lines = structure_text.split("\n")

    # Stack to track current directory path at each depth level
    path_stack = []

    for line in lines:
        # Skip empty lines and the root DDNS/ line
        stripped = line.strip()
        if not stripped or stripped == "DDNS/":
            continue

        # Skip lines that only contain tree characters (like │)
        if all(c in "│ \t" for c in line):
            continue

        # Calculate depth by finding the position of ├ or └
        depth = 0
        connector_pos = -1
        for i, char in enumerate(line):
            if char in "\u251c\u2514":  # ├ or └
                connector_pos = i
                # Each level is 4 characters (│   or    )
                depth = i // 4
                break

        if connector_pos == -1:
            continue

        # Extract the name after the connector (├── or └──)
        # Find where the actual name starts
        rest = line[connector_pos:]
        # Remove tree characters at the start
        name_match = re.match(r"^[\u251c\u2514\u2500]+\s*", rest)
        if name_match:
            name_part = rest[name_match.end():]
        else:
            continue

        # Extract the file/directory name (before any # comment)
        if "#" in name_part:
            name = name_part.split("#", 1)[0].strip()
        else:
            name = name_part.strip()

        # Skip wildcard patterns and ellipsis
        if "*" in name or name == "...":
            continue

        # Skip empty names
        if not name:
            continue

        # Adjust stack to match current depth
        while len(path_stack) > depth:
            path_stack.pop()

        # Check if this is a directory (ends with /)
        if name.endswith("/"):
            dir_name = name.rstrip("/")
            # Ensure stack has enough entries
            while len(path_stack) < depth:
                path_stack.append("")
            if len(path_stack) == depth:
                path_stack.append(dir_name)
            else:
                path_stack[depth] = dir_name
        else:
            # It's a file - build the full path
            if path_stack:
                file_path = "/".join(path_stack) + "/" + name
            else:
                file_path = name
            files.add(file_path)

    return files


def get_actual_files(repo_root):
    # type: (str) -> set
    """Get all actual files in the monitored directories (ddns/ and doc/ only).

    These are the directories that should be fully listed in AGENTS.md.
    Tests, docker, schema, and root files use compact/static formats.
    """
    files = set()

    # Scan ddns/ and doc/ directories fully - these must be completely listed
    files.update(scan_directory_files(repo_root, "ddns", [".py", ".pyi"]))
    files.update(scan_directory_files(repo_root, "doc", [".md", ".png", ".svg", ".json"]))

    return files


def get_documented_ddns_doc_files(documented_files):
    # type: (set) -> set
    """Filter documented files to only include ddns/ and doc/ paths."""
    return {f for f in documented_files if f.startswith("ddns/") or f.startswith("doc/")}


def generate_directory_entry(name, desc, is_last, depth, is_dir=False):
    # type: (str, str, bool, int, bool) -> str
    """Generate a single directory tree entry line."""
    # Build the prefix based on depth
    prefix_parts = []
    for _ in range(depth):
        prefix_parts.append("\u2502   ")

    if is_last:
        prefix_parts.append("\u2514\u2500\u2500 ")
    else:
        prefix_parts.append("\u251c\u2500\u2500 ")

    prefix = "".join(prefix_parts)

    if is_dir:
        name = name + "/"

    if desc:
        padded_name = name.ljust(20)
        return prefix + padded_name + "# " + desc
    else:
        return prefix + name


def generate_full_structure(repo_root):
    # type: (str) -> str
    """Generate the full directory structure matching AGENTS.md format.

    Fully lists ddns/ and doc/ directories without omissions.
    Keeps tests/ in compact style with wildcards.
    """
    lines = []

    # Root
    lines.append("DDNS/")

    # .github section (keep compact, not monitored for changes)
    lines.append("\u251c\u2500\u2500 .github/                    # GitHub configuration")
    lines.append("\u2502   \u251c\u2500\u2500 workflows/              # CI/CD workflows (build, publish, test)")
    lines.append("\u2502   \u251c\u2500\u2500 instructions/           # Agent instructions (python.instructions.md)")
    lines.append("\u2502   \u2514\u2500\u2500 copilot-instructions.md # GitHub Copilot instructions")
    lines.append("\u2502")

    # ddns section - dynamically generate all files
    lines.append("\u251c\u2500\u2500 ddns/                       # Main application code")

    # ddns root files
    ddns_dir = os.path.join(repo_root, "ddns")
    ddns_root_files = sorted(
        [f for f in os.listdir(ddns_dir) if os.path.isfile(os.path.join(ddns_dir, f)) and f.endswith(".py")]
    )
    sorted([d for d in os.listdir(ddns_dir) if os.path.isdir(os.path.join(ddns_dir, d)) and not d.startswith("_")])

    for f in ddns_root_files:
        filepath = "ddns/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        lines.append("\u2502   \u251c\u2500\u2500 " + f.ljust(20) + ("# " + desc if desc else ""))
    lines.append("\u2502   \u2502")

    # ddns/config
    lines.append("\u2502   \u251c\u2500\u2500 config/                 # Configuration management")
    config_dir = os.path.join(ddns_dir, "config")
    config_files = get_sorted_files(config_dir, [".py"])
    for i, f in enumerate(config_files):
        filepath = "ddns/config/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        is_last = i == len(config_files) - 1
        prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "
        if desc:
            lines.append(prefix + f.ljust(20) + "# " + desc)
        else:
            lines.append(prefix + f)
    lines.append("\u2502   \u2502")

    # ddns/provider - dynamic generation
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
        else:
            # For unknown providers, generate a description
            if f.startswith("_"):
                lines.append(prefix + f)
            else:
                name = f[:-3]  # Remove .py
                lines.append(prefix + f.ljust(20) + "# " + name.title() + " DNS provider")
    lines.append("\u2502   \u2502")

    # ddns/scheduler
    lines.append("\u2502   \u251c\u2500\u2500 scheduler/              # Task scheduling implementations")
    scheduler_dir = os.path.join(ddns_dir, "scheduler")
    scheduler_files = get_sorted_files(scheduler_dir, [".py"])
    for i, f in enumerate(scheduler_files):
        filepath = "ddns/scheduler/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        is_last = i == len(scheduler_files) - 1
        prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "
        if desc:
            lines.append(prefix + f.ljust(20) + "# " + desc)
        else:
            lines.append(prefix + f)
    lines.append("\u2502   \u2502")

    # ddns/util
    lines.append("\u2502   \u2514\u2500\u2500 util/                   # Utility modules")
    util_dir = os.path.join(ddns_dir, "util")
    util_files = get_sorted_files(util_dir, [".py"])
    for i, f in enumerate(util_files):
        filepath = "ddns/util/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        is_last = i == len(util_files) - 1
        prefix = "\u2502       \u2514\u2500\u2500 " if is_last else "\u2502       \u251c\u2500\u2500 "
        if desc:
            lines.append(prefix + f.ljust(20) + "# " + desc)
        else:
            lines.append(prefix + f)
    lines.append("\u2502")

    # tests section - keep compact style with wildcards
    lines.append("\u251c\u2500\u2500 tests/                      # Unit tests")
    lines.append("\u2502   \u251c\u2500\u2500 __init__.py             # Test initialization (path setup)")
    lines.append("\u2502   \u251c\u2500\u2500 base_test.py            # Shared test utilities and base classes")
    lines.append("\u2502   \u251c\u2500\u2500 README.md               # Testing documentation")
    lines.append("\u2502   \u251c\u2500\u2500 config/                 # Test configuration files")
    lines.append("\u2502   \u251c\u2500\u2500 scripts/                # Test helper scripts")
    lines.append("\u2502   \u251c\u2500\u2500 test_cache.py           # Cache tests")
    lines.append("\u2502   \u251c\u2500\u2500 test_config_*.py        # Configuration tests")
    lines.append("\u2502   \u251c\u2500\u2500 test_ip.py              # IP detection tests")
    lines.append("\u2502   \u251c\u2500\u2500 test_provider_*.py      # Provider-specific tests")
    lines.append("\u2502   \u251c\u2500\u2500 test_scheduler_*.py     # Scheduler tests")
    lines.append("\u2502   \u2514\u2500\u2500 test_util_*.py          # Utility tests")
    lines.append("\u2502")

    # doc section - dynamically generate all files
    lines.append("\u251c\u2500\u2500 doc/                        # Documentation")
    doc_dir = os.path.join(repo_root, "doc")

    # doc/config
    lines.append("\u2502   \u251c\u2500\u2500 config/                 # Configuration documentation")
    doc_config_dir = os.path.join(doc_dir, "config")
    config_files = get_sorted_files(doc_config_dir, [".md"])
    for i, f in enumerate(config_files):
        filepath = "doc/config/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        is_last = i == len(config_files) - 1
        prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "
        if desc:
            lines.append(prefix + f.ljust(20) + "# " + desc)
        else:
            lines.append(prefix + f)
    lines.append("\u2502   \u2502")

    # doc/dev
    lines.append("\u2502   \u251c\u2500\u2500 dev/                    # Developer documentation")
    doc_dev_dir = os.path.join(doc_dir, "dev")
    dev_files = get_sorted_files(doc_dev_dir, [".md"])
    for i, f in enumerate(dev_files):
        filepath = "doc/dev/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        is_last = i == len(dev_files) - 1
        prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "
        if desc:
            lines.append(prefix + f.ljust(20) + "# " + desc)
        else:
            lines.append(prefix + f)
    lines.append("\u2502   \u2502")

    # doc/examples
    lines.append("\u2502   \u251c\u2500\u2500 examples/               # Example configurations")
    doc_examples_dir = os.path.join(doc_dir, "examples")
    if os.path.isdir(doc_examples_dir):
        example_files = get_sorted_files(doc_examples_dir)
        for i, f in enumerate(example_files):
            filepath = "doc/examples/" + f
            desc = FILE_DESCRIPTIONS.get(filepath, "")
            is_last = i == len(example_files) - 1
            prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "
            if desc:
                lines.append(prefix + f.ljust(20) + "# " + desc)
            else:
                lines.append(prefix + f)
    lines.append("\u2502   \u2502")

    # doc/img
    lines.append("\u2502   \u251c\u2500\u2500 img/                    # Images and diagrams")
    doc_img_dir = os.path.join(doc_dir, "img")
    if os.path.isdir(doc_img_dir):
        img_files = get_sorted_files(doc_img_dir)
        for i, f in enumerate(img_files):
            filepath = "doc/img/" + f
            desc = FILE_DESCRIPTIONS.get(filepath, "")
            is_last = i == len(img_files) - 1
            prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "
            if desc:
                lines.append(prefix + f.ljust(20) + "# " + desc)
            else:
                lines.append(prefix + f)
    lines.append("\u2502   \u2502")

    # doc/providers - fully list all provider documentation
    lines.append("\u2502   \u251c\u2500\u2500 providers/              # Provider-specific documentation")
    doc_providers_dir = os.path.join(doc_dir, "providers")
    provider_docs = get_sorted_files(doc_providers_dir, [".md"])
    for i, f in enumerate(provider_docs):
        filepath = "doc/providers/" + f
        # Generate description for provider docs
        if f == "README.md":
            desc = "Provider list (Chinese)"
        elif f == "README.en.md":
            desc = "Provider list (English)"
        elif f.endswith(".en.md"):
            provider_name = f[:-6]  # Remove .en.md
            desc = provider_name.title() + " guide (English)"
        else:
            provider_name = f[:-3]  # Remove .md
            desc = provider_name.title() + " guide (Chinese)"

        is_last = i == len(provider_docs) - 1
        prefix = "\u2502   \u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u2502   \u251c\u2500\u2500 "
        lines.append(prefix + f.ljust(20) + "# " + desc)
    lines.append("\u2502   \u2502")

    # doc root files
    doc_root_files = sorted([f for f in os.listdir(doc_dir) if os.path.isfile(os.path.join(doc_dir, f)) and f.endswith(".md")])
    for i, f in enumerate(doc_root_files):
        filepath = "doc/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        is_last = i == len(doc_root_files) - 1
        prefix = "\u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u251c\u2500\u2500 "
        if desc:
            lines.append(prefix + f.ljust(20) + "# " + desc)
        else:
            lines.append(prefix + f)
    lines.append("\u2502")

    # docker section
    lines.append("\u251c\u2500\u2500 docker/                     # Docker configuration")
    docker_dir = os.path.join(repo_root, "docker")
    docker_files = get_sorted_files(docker_dir)
    for i, f in enumerate(docker_files):
        filepath = "docker/" + f
        desc = FILE_DESCRIPTIONS.get(filepath, "")
        is_last = i == len(docker_files) - 1
        prefix = "\u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u251c\u2500\u2500 "
        if desc:
            lines.append(prefix + f.ljust(20) + "# " + desc)
        else:
            lines.append(prefix + f)
    lines.append("\u2502")

    # schema section - dynamic generation
    lines.append("\u251c\u2500\u2500 schema/                     # JSON schemas")
    schema_dir = os.path.join(repo_root, "schema")
    schema_files = get_sorted_files(schema_dir, [".json"], version_sort=True)
    for i, f in enumerate(schema_files):
        is_last = i == len(schema_files) - 1
        prefix = "\u2502   \u2514\u2500\u2500 " if is_last else "\u2502   \u251c\u2500\u2500 "
        version = f[:-5]  # Remove .json
        if version == "v2":
            desc = "Legacy schema v2"
        elif version == "v2.8":
            desc = "Legacy schema v2.8"
        elif version == "v4.0":
            desc = "Previous schema v4.0"
        elif version == "v4.1":
            desc = "Latest schema v4.1"
        else:
            desc = "Schema " + version
        padded_name = f.ljust(24)
        lines.append(prefix + padded_name + "# " + desc)
    lines.append("\u2502")

    # Root files
    lines.append("\u251c\u2500\u2500 run.py                      # Direct run script")
    lines.append("\u251c\u2500\u2500 install.sh                  # One-click install script")
    lines.append("\u251c\u2500\u2500 pyproject.toml              # Python project configuration")
    lines.append("\u251c\u2500\u2500 setup.cfg                   # Setup configuration")
    lines.append("\u251c\u2500\u2500 .gitignore                  # Git ignore rules")
    lines.append("\u251c\u2500\u2500 LICENSE                     # MIT License")
    lines.append("\u251c\u2500\u2500 README.md                   # Main README (Chinese)")
    lines.append("\u2514\u2500\u2500 README.en.md                # Main README (English)")

    return "\n".join(lines)


def compare_structures(documented_files, actual_files):
    # type: (set, set) -> tuple
    """Compare documented files with actual files and return differences.

    Returns:
        tuple: (added_files, deleted_files) - files that exist but not documented,
               and files that are documented but don't exist
    """
    added_files = actual_files - documented_files
    deleted_files = documented_files - actual_files
    return (sorted(added_files), sorted(deleted_files))


def main():
    # type: () -> None
    """Main function to compare AGENTS.md directory structure with actual files."""
    # Determine repository root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))

    agents_file = os.path.join(repo_root, "AGENTS.md")

    if not os.path.exists(agents_file):
        print("Error: AGENTS.md not found at " + agents_file)
        sys.exit(1)

    # Read current AGENTS.md
    with open(agents_file, "r", encoding="utf-8") as f:
        agents_content = f.read()

    # Extract current structure
    current_structure = extract_current_structure(agents_content)
    if current_structure is None:
        print("Error: Could not find directory structure section in AGENTS.md")
        sys.exit(1)

    # Generate new structure
    new_structure = generate_full_structure(repo_root)

    # Check if structure has changed
    if current_structure.strip() == new_structure.strip():
        print("changed=false")
        print("No changes detected in directory structure.")
        sys.exit(0)

    # Get actual files in monitored directories (ddns/ and doc/ only)
    actual_files = get_actual_files(repo_root)

    # Extract files from the current structure in AGENTS.md
    all_documented_files = extract_files_from_structure(current_structure)

    # Filter to only compare ddns/ and doc/ directories
    # (other directories use compact format with wildcards or static entries)
    documented_files = get_documented_ddns_doc_files(all_documented_files)

    # Compare and find differences
    added_files, deleted_files = compare_structures(documented_files, actual_files)

    # Output results for the workflow
    print("changed=true")

    # Create issue body content
    issue_body_parts = []
    issue_body_parts.append("The directory structure in AGENTS.md is out of sync with the actual repository files.\n")

    if added_files:
        issue_body_parts.append("## Added Files (not documented in AGENTS.md)\n")
        for f in added_files:
            issue_body_parts.append("- `" + f + "`")
        issue_body_parts.append("")

    if deleted_files:
        issue_body_parts.append("## Deleted Files (documented but no longer exist)\n")
        for f in deleted_files:
            issue_body_parts.append("- `" + f + "`")
        issue_body_parts.append("")

    issue_body_parts.append("## Required Updates\n")
    issue_body_parts.append("Please update AGENTS.md to:\n")
    issue_body_parts.append("1. Update the directory structure section to reflect the current file layout")
    issue_body_parts.append("2. Update the version number at the bottom of the file")
    issue_body_parts.append("3. Update the 'Last Updated' date to today's date")
    issue_body_parts.append("")
    issue_body_parts.append("---")
    issue_body_parts.append("*This issue was automatically generated by the update-agents workflow.*")

    issue_body = "\n".join(issue_body_parts)

    # Write issue body to a file for the workflow to use
    output_file = os.path.join(repo_root, ".github", "issue_body.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(issue_body)

    # Also output to stdout for debugging
    print("\nIssue body written to: " + output_file)
    print("\n" + issue_body)

    # Output counts for summary
    print("\nSummary:")
    print("Added files: " + str(len(added_files)))
    print("Deleted files: " + str(len(deleted_files)))

    sys.exit(0)


if __name__ == "__main__":
    main()
