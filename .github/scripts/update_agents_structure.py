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


def generate_full_structure(repo_root):
    # type: (str) -> str
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


def main():
    # type: () -> None
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
