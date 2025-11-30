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


def extract_current_structure(agents_content):
    # type: (str) -> str | None
    """Extract the current directory structure section from AGENTS.md."""
    pattern = r"### Directory Structure\s*\n\n```text\n(.*?)```"
    match = re.search(pattern, agents_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


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
        rest = line[connector_pos:]
        name_match = re.match(r"^[\u251c\u2514\u2500]+\s*", rest)
        if name_match:
            name_part = rest[name_match.end() :]
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
    """Get all actual files in the monitored directories (ddns/ and doc/ only)."""
    files = set()

    # Scan ddns/ and doc/ directories fully
    files.update(scan_directory_files(repo_root, "ddns", [".py", ".pyi"]))
    files.update(scan_directory_files(repo_root, "doc", [".md", ".png", ".svg", ".json"]))

    return files


def get_documented_ddns_doc_files(documented_files):
    # type: (set) -> set
    """Filter documented files to only include ddns/ and doc/ paths."""
    return {f for f in documented_files if f.startswith("ddns/") or f.startswith("doc/")}


def compare_structures(documented_files, actual_files):
    # type: (set, set) -> tuple
    """Compare documented files with actual files and return differences."""
    added_files = actual_files - documented_files
    deleted_files = documented_files - actual_files
    return (sorted(added_files), sorted(deleted_files))


def main():
    # type: () -> None
    """Main function to compare AGENTS.md directory structure with actual files."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))

    agents_file = os.path.join(repo_root, "AGENTS.md")

    if not os.path.exists(agents_file):
        print("Error: AGENTS.md not found at " + agents_file)
        sys.exit(1)

    # Read current AGENTS.md
    with open(agents_file, "r", encoding="utf-8") as f:
        agents_content = f.read()

    # Extract current structure from AGENTS.md
    current_structure = extract_current_structure(agents_content)
    if current_structure is None:
        print("Error: Could not find directory structure section in AGENTS.md")
        sys.exit(1)

    # Get actual files in monitored directories (ddns/ and doc/ only)
    actual_files = get_actual_files(repo_root)

    # Extract files from the current structure in AGENTS.md
    all_documented_files = extract_files_from_structure(current_structure)

    # Filter to only compare ddns/ and doc/ directories
    documented_files = get_documented_ddns_doc_files(all_documented_files)

    # Compare and find differences
    added_files, deleted_files = compare_structures(documented_files, actual_files)

    # Check if there are any differences
    if not added_files and not deleted_files:
        print("changed=false")
        print("No changes detected in directory structure.")
        sys.exit(0)

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
