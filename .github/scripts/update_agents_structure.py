#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to update the directory structure section in AGENTS.md.

This script scans the repository and generates an updated directory structure
that can be used to update the AGENTS.md file.
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
}

# Directory descriptions
DIR_DESCRIPTIONS = {
    ".github/": "GitHub configuration",
    ".github/workflows/": "CI/CD workflows (build, publish, test)",
    ".github/instructions/": "Agent instructions (python.instructions.md)",
    "ddns/": "Main application code",
    "ddns/config/": "Configuration management",
    "ddns/provider/": "DNS provider implementations",
    "ddns/scheduler/": "Task scheduling implementations",
    "ddns/util/": "Utility modules",
    "tests/": "Unit tests",
    "tests/config/": "Test configuration files",
    "tests/scripts/": "Test helper scripts",
    "doc/": "Documentation",
    "doc/config/": "Configuration documentation",
    "doc/dev/": "Developer documentation",
    "doc/providers/": "Provider-specific documentation",
    "doc/img/": "Images and diagrams",
    "docker/": "Docker configuration",
    "schema/": "JSON schemas",
}

# Special file patterns for tests directory
TEST_PATTERNS = {
    "test_cache.py": "Cache tests",
    "test_config_*.py": "Configuration tests",
    "test_ip.py": "IP detection tests",
    "test_provider_*.py": "Provider-specific tests",
    "test_scheduler_*.py": "Scheduler tests",
    "test_util_*.py": "Utility tests",
}

# Directories to skip
SKIP_DIRS = {".git", "__pycache__", ".vscode", "node_modules", ".github/agents"}

# Files to skip
SKIP_FILES = {"*.pyc", "*.pyo", ".DS_Store"}


def get_file_description(filepath):
    """Get description for a file based on filepath."""
    # Check exact match first
    if filepath in FILE_DESCRIPTIONS:
        return FILE_DESCRIPTIONS[filepath]

    # Check for pattern matches in tests
    filename = os.path.basename(filepath)
    parent_dir = os.path.dirname(filepath)

    if parent_dir == "tests":
        for pattern, desc in TEST_PATTERNS.items():
            if "*" in pattern:
                prefix = pattern.split("*")[0]
                suffix = pattern.split("*")[1] if "*" in pattern else ""
                if filename.startswith(prefix) and filename.endswith(suffix):
                    return desc

    # For doc files, generate description based on filename
    if parent_dir.startswith("doc/"):
        if filename.endswith(".en.md"):
            base = filename[:-6]  # Remove .en.md
            return base.replace("_", " ").title() + " (English)"
        elif filename.endswith(".md"):
            base = filename[:-3]  # Remove .md
            return base.replace("_", " ").title() + " (Chinese)"

    # For schema files
    if parent_dir == "schema":
        if filename.endswith(".json"):
            version = filename[:-5]  # Remove .json
            return "Schema " + version

    return ""


def should_skip(name, is_dir=False):
    """Check if file/dir should be skipped."""
    if is_dir and name in SKIP_DIRS:
        return True
    if not is_dir:
        for pattern in SKIP_FILES:
            if pattern.startswith("*") and name.endswith(pattern[1:]):
                return True
            if pattern == name:
                return True
    return False


def scan_directory(root_path, rel_path="", depth=0, max_depth=3):
    """Scan directory and return structure as list of (name, is_dir, description, depth)."""
    result = []
    full_path = os.path.join(root_path, rel_path) if rel_path else root_path

    if depth > max_depth:
        return result

    try:
        entries = sorted(os.listdir(full_path))
    except OSError:
        return result

    dirs = []
    files = []

    for entry in entries:
        entry_path = os.path.join(full_path, entry)
        entry_rel = os.path.join(rel_path, entry) if rel_path else entry

        if os.path.isdir(entry_path):
            if not should_skip(entry, is_dir=True):
                dirs.append((entry, entry_rel))
        else:
            if not should_skip(entry):
                files.append((entry, entry_rel))

    # Add directories first
    for name, entry_rel in dirs:
        dir_key = entry_rel + "/"
        desc = DIR_DESCRIPTIONS.get(dir_key, "")
        result.append((name + "/", True, desc, depth))

        # Recursively scan subdirectory
        sub_entries = scan_directory(root_path, entry_rel, depth + 1, max_depth)
        result.extend(sub_entries)

    # Then add files
    for name, entry_rel in files:
        desc = get_file_description(entry_rel)
        result.append((name, False, desc, depth))

    return result


def generate_tree_structure(entries, base_name="DDNS"):
    """Generate tree structure string from entries."""
    lines = [base_name + "/"]

    # Filter and organize entries by depth
    for i, (name, is_dir, desc, depth) in enumerate(entries):
        # Determine prefix based on depth
        prefix_parts = []
        for d in range(depth):
            # Check if there are more items at this level after current
            has_more_at_level = False
            for j, (_, _, _, check_depth) in enumerate(entries[i + 1 :], i + 1):
                if check_depth == d:
                    has_more_at_level = True
                    break
                if check_depth < d:
                    break
            if has_more_at_level:
                prefix_parts.append("\u2502   ")
            else:
                prefix_parts.append("    ")

        # Check if this is the last item at its depth
        is_last = True
        for j in range(i + 1, len(entries)):
            if entries[j][3] == depth:
                is_last = False
                break
            if entries[j][3] < depth:
                break

        if is_last:
            prefix_parts.append("\u2514\u2500\u2500 ")
        else:
            prefix_parts.append("\u251c\u2500\u2500 ")

        prefix = "".join(prefix_parts)

        # Format description
        if desc:
            # Pad name to align descriptions
            padded_name = name.ljust(24 - len(prefix) + len(name))
            line = prefix + padded_name + "# " + desc
        else:
            line = prefix + name

        lines.append(line)

    return "\n".join(lines)


def extract_current_structure(agents_content):
    """Extract the current directory structure section from AGENTS.md."""
    # Find the directory structure section
    pattern = r"### Directory Structure\s*\n\n```text\n(.*?)```"
    match = re.search(pattern, agents_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def update_agents_structure(agents_content, new_structure):
    """Update the directory structure section in AGENTS.md content."""
    pattern = r"(### Directory Structure\s*\n\n```text\n)(.*?)(```)"
    replacement = r"\g<1>" + new_structure + "\n" + r"\g<3>"
    return re.sub(pattern, replacement, agents_content, flags=re.DOTALL)


# (Function `generate_structure_for_section()` removed)
def version_sort_key(filename):
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


def generate_full_structure(repo_root):
    """Generate the full directory structure matching AGENTS.md format."""
    lines = []

    # Root
    lines.append("DDNS/")

    # .github section
    lines.append("\u251c\u2500\u2500 .github/                    # GitHub configuration")
    lines.append("\u2502   \u251c\u2500\u2500 workflows/              # CI/CD workflows (build, publish, test)")
    lines.append("\u2502   \u251c\u2500\u2500 instructions/           # Agent instructions (python.instructions.md)")
    lines.append("\u2502   \u2514\u2500\u2500 copilot-instructions.md # GitHub Copilot instructions")
    lines.append("\u2502")

    # ddns section
    lines.append("\u251c\u2500\u2500 ddns/                       # Main application code")
    lines.append("\u2502   \u251c\u2500\u2500 __init__.py             # Package initialization and version info")
    lines.append("\u2502   \u251c\u2500\u2500 __main__.py             # Entry point for module execution")
    lines.append("\u2502   \u251c\u2500\u2500 cache.py                # Cache management")
    lines.append("\u2502   \u251c\u2500\u2500 ip.py                   # IP address detection logic")
    lines.append("\u2502   \u2502")

    # ddns/config
    lines.append("\u2502   \u251c\u2500\u2500 config/                 # Configuration management")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 __init__.py")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 cli.py              # Command-line argument parsing")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 config.py           # Configuration loading and merging")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 env.py              # Environment variable parsing")
    lines.append("\u2502   \u2502   \u2514\u2500\u2500 file.py             # JSON file configuration")
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
                if f == "__init__.py":
                    lines.append(prefix + f)
                else:
                    lines.append(prefix + f)
            else:
                name = f[:-3]  # Remove .py
                lines.append(prefix + f.ljust(20) + "# " + name.title() + " DNS provider")
    lines.append("\u2502   \u2502")

    # ddns/scheduler
    lines.append("\u2502   \u251c\u2500\u2500 scheduler/              # Task scheduling implementations")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 __init__.py")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 _base.py            # Base scheduler class")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 cron.py             # Cron-based scheduler (Linux/macOS)")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 launchd.py          # macOS launchd scheduler")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 schtasks.py         # Windows Task Scheduler")
    lines.append("\u2502   \u2502   \u2514\u2500\u2500 systemd.py          # Linux systemd timer")
    lines.append("\u2502   \u2502")

    # ddns/util
    lines.append("\u2502   \u2514\u2500\u2500 util/                   # Utility modules")
    lines.append("\u2502       \u251c\u2500\u2500 __init__.py")
    lines.append("\u2502       \u251c\u2500\u2500 comment.py          # Comment handling")
    lines.append("\u2502       \u251c\u2500\u2500 fileio.py           # File I/O operations")
    lines.append("\u2502       \u251c\u2500\u2500 http.py             # HTTP client with proxy support")
    lines.append("\u2502       \u2514\u2500\u2500 try_run.py          # Safe command execution")
    lines.append("\u2502")

    # tests section
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

    # doc section
    lines.append("\u251c\u2500\u2500 doc/                        # Documentation")
    lines.append("\u2502   \u251c\u2500\u2500 config/                 # Configuration documentation")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 cli.md              # CLI usage (Chinese)")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 cli.en.md           # CLI usage (English)")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 env.md              # Environment variables (Chinese)")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 env.en.md           # Environment variables (English)")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 json.md             # JSON config (Chinese)")
    lines.append("\u2502   \u2502   \u2514\u2500\u2500 json.en.md          # JSON config (English)")
    lines.append("\u2502   \u2502")
    lines.append("\u2502   \u251c\u2500\u2500 dev/                    # Developer documentation")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 provider.md         # Provider development guide (Chinese)")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 provider.en.md      # Provider development guide (English)")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 config.md           # Config system (Chinese)")
    lines.append("\u2502   \u2502   \u2514\u2500\u2500 config.en.md        # Config system (English)")
    lines.append("\u2502   \u2502")
    lines.append("\u2502   \u251c\u2500\u2500 providers/              # Provider-specific documentation")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 README.md           # Provider list (Chinese)")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 README.en.md        # Provider list (English)")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 alidns.md           # AliDNS guide (Chinese)")
    lines.append("\u2502   \u2502   \u251c\u2500\u2500 alidns.en.md        # AliDNS guide (English)")
    lines.append(
        "\u2502   \u2502   \u2514\u2500\u2500 ...                 # Other providers (Chinese & English versions)"
    )
    lines.append("\u2502   \u2502")
    lines.append("\u2502   \u251c\u2500\u2500 docker.md               # Docker documentation (Chinese)")
    lines.append("\u2502   \u251c\u2500\u2500 docker.en.md            # Docker documentation (English)")
    lines.append("\u2502   \u251c\u2500\u2500 install.md              # Installation guide (Chinese)")
    lines.append("\u2502   \u251c\u2500\u2500 install.en.md           # Installation guide (English)")
    lines.append("\u2502   \u2514\u2500\u2500 img/                    # Images and diagrams")
    lines.append("\u2502")

    # docker section
    lines.append("\u251c\u2500\u2500 docker/                     # Docker configuration")
    lines.append("\u2502   \u251c\u2500\u2500 Dockerfile              # Main Dockerfile")
    lines.append("\u2502   \u251c\u2500\u2500 glibc.Dockerfile        # glibc-based build")
    lines.append("\u2502   \u251c\u2500\u2500 musl.Dockerfile         # musl-based build")
    lines.append("\u2502   \u2514\u2500\u2500 entrypoint.sh           # Container entrypoint script")
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
            desc = "Current schema v4.0"
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


def main():
    """Main function to update AGENTS.md directory structure."""
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
        print("No changes detected in directory structure.")
        sys.exit(0)

    # Update AGENTS.md content
    updated_content = update_agents_structure(agents_content, new_structure)

    # Write updated content
    with open(agents_file, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("AGENTS.md directory structure has been updated.")
    print("\nChanges detected:")
    print("Old structure lines: " + str(len(current_structure.strip().split("\n"))))
    print("New structure lines: " + str(len(new_structure.strip().split("\n"))))

    sys.exit(0)


if __name__ == "__main__":
    main()
