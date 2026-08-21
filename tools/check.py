#!/usr/bin/env python3
"""Run deterministic DDNS project contracts and lane-specific checks."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_LANES = ("Core", "Config", "Provider", "Web", "Scheduler", "MCP", "Docs", "Build/Release", "Agent/Workflow")
MERGE_GATE_REQUIRED = ("lint", "python", "e2e", "pypi", "nuitka", "linux-binary", "prepare-docker", "docker")
MERGE_GATE_TRUSTED_ONLY = ("preview-pypi", "preview-docker")
REQUIRED_AGENT_PATHS = ("AGENTS.md", "tools/AGENTS.md", "ddns/provider/AGENTS.md", "docs/AGENTS.md")


class CheckError(RuntimeError):
    """Raised when a required repository surface or command is unavailable."""


@dataclass(frozen=True)
class Command:
    """A deterministic command selected for one or more development lanes."""

    label: str
    arguments: tuple[str, ...]


def normalize_path(path: str) -> str:
    """Return a repository-relative path with POSIX separators."""
    path = path.replace("\\", "/")
    return path[2:] if path.startswith("./") else path


def lanes_for_path(path: str) -> tuple[str, ...]:
    """Classify a changed path into every lane whose contract it can affect."""
    path = normalize_path(path)
    lanes = []

    if path in ("run.py",) or path.startswith(
        ("ddns/ip.py", "ddns/cache.py", "ddns/util/", "tests/test_ip", "tests/test_cache", "tests/test_util")
    ):
        lanes.append("Core")
    if path.startswith(("ddns/config/", "schema/", "tests/test_config", "tests/config/")):
        lanes.append("Config")
    if path.startswith(("ddns/provider/", "tests/test_provider", "docs/providers/", "docs/en/providers/")) or path in (
        "ddns/config/cli.py",
        "ddns/config/field-model.json",
        "docs/.vitepress/config.mts",
        "docs/llms.txt",
        "schema/v4.1.json",
    ):
        lanes.append("Provider")
    if path.startswith(("ddns/web/", "tests/test_web", "web/")) or path in (
        "tests/e2e.py",
        "tests/test_config_cli_web.py",
    ):
        lanes.append("Web")
    if path.startswith(("ddns/scheduler/", "tests/test_scheduler", "tests/scripts/test-task")):
        lanes.append("Scheduler")
    if path in ("ddns/mcp.py", "tests/test_mcp.py", "tests/test_config_cli_mcp.py"):
        lanes.append("MCP")
    if path.startswith(("docs/", "schema/", "tests/config/")) or path in (
        "README.md",
        "README.en.md",
        "ddns/config/field-model.json",
    ):
        lanes.append("Docs")
    if path.startswith(("docker/", ".github/workflows/", ".github/patch.py")) or path in (
        "pyproject.toml",
        "setup.cfg",
        "requirements.txt",
        "docs/public/install.sh",
        "docs/esa.js",
    ):
        lanes.append("Build/Release")
    if (
        path == "AGENTS.md"
        or path.endswith("/AGENTS.md")
        or path.startswith(
            (".agents/", ".github/agents/", ".github/instructions/", ".github/scripts/", ".github/workflows/", "tools/")
        )
    ):
        lanes.append("Agent/Workflow")

    return tuple(lanes)


def select_lanes(paths: Iterable[str]) -> tuple[tuple[str, ...], dict[str, list[str]]]:
    """Select lanes and their changed paths, conservatively falling back to all."""
    reasons: dict[str, list[str]] = defaultdict(list)
    unknown = []
    for path in sorted({normalize_path(path) for path in paths if path.strip()}):
        lanes = lanes_for_path(path)
        if not lanes:
            unknown.append(path)
            continue
        for lane in lanes:
            reasons[lane].append(path)

    if unknown:
        for lane in CANONICAL_LANES:
            reasons[lane].extend("unknown path: {}".format(path) for path in unknown)

    selected = tuple(lane for lane in CANONICAL_LANES if lane in reasons)
    return selected, dict(reasons)


def _git_output(repo: Path, arguments: Sequence[str]) -> str:
    result = subprocess.run(["git", *arguments], cwd=repo, text=True, capture_output=True, check=False)
    if result.returncode:
        raise CheckError("git {} failed: {}".format(" ".join(arguments), result.stderr.strip()))
    return result.stdout.strip()


def _base_ref_candidates() -> tuple[str, ...]:
    """Return explicit, GitHub, then conventional base references."""
    explicit = os.environ.get("DDNS_CHECK_BASE_REF", "").strip()
    github_base = os.environ.get("GITHUB_BASE_REF", "").strip()
    candidates = []
    for value in (explicit, github_base):
        if not value:
            continue
        candidates.append(value)
        if not value.startswith("origin/"):
            candidates.append("origin/{}".format(value))
    candidates.extend(("origin/master", "master", "origin/main", "main"))
    return tuple(dict.fromkeys(candidates))


def changed_paths(repo: Path) -> list[str]:
    """List merge-base, staged, unstaged, and untracked changes in *repo*."""
    base_ref = next(
        (
            ref
            for ref in _base_ref_candidates()
            if ref
            and subprocess.run(
                ["git", "rev-parse", "--verify", "--quiet", ref], cwd=repo, capture_output=True, check=False
            ).returncode
            == 0
        ),
        None,
    )
    if base_ref is None:
        raise CheckError(
            "could not find a merge-base reference (set DDNS_CHECK_BASE_REF, GITHUB_BASE_REF, or fetch master/main)"
        )

    merge_base = _git_output(repo, ("merge-base", "HEAD", base_ref))
    outputs = (
        _git_output(repo, ("diff", "--name-only", merge_base, "HEAD")),
        _git_output(repo, ("diff", "--name-only")),
        _git_output(repo, ("diff", "--cached", "--name-only")),
        _git_output(repo, ("ls-files", "--others", "--exclude-standard")),
    )
    return sorted({normalize_path(path) for output in outputs for path in output.splitlines() if path.strip()})


def _relative_path(path: Path, repo: Path) -> str:
    """Return a stable repository-relative path for diagnostics."""
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> object:
    if not path.is_file():
        raise CheckError("required file is missing: {}".format(_relative_path(path, REPO_ROOT)))
    return json.loads(path.read_text(encoding="utf-8"))


def _frontmatter_fields(content: str) -> dict[str, str] | None:
    """Parse simple top-level YAML scalar fields without a runtime dependency."""
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def _literal_mapping_keys(path: Path) -> set[str]:
    """Read provider mapping keys without importing Python 2-compatible runtime code."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "get_provider_class":
            for child in ast.walk(node):
                if isinstance(child, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id == "mapping" for target in child.targets
                ):
                    if not isinstance(child.value, ast.Dict):
                        continue
                    return {
                        key.value
                        for key in child.value.keys
                        if isinstance(key, ast.Constant) and isinstance(key.value, str)
                    }
    raise CheckError("could not find get_provider_class mapping in {}".format(_relative_path(path, REPO_ROOT)))


def _cli_provider_choices(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument" or not node.args:
            continue
        if not isinstance(node.args[0], ast.Constant) or node.args[0].value != "--dns":
            continue
        for keyword in node.keywords:
            if keyword.arg == "choices":
                choices = ast.literal_eval(keyword.value)
                if isinstance(choices, list) and all(isinstance(choice, str) for choice in choices):
                    return set(choices)
    raise CheckError("could not find --dns choices in {}".format(_relative_path(path, REPO_ROOT)))


def _typescript_config_block(config: str, key: str, occurrence: int) -> str:
    """Return one balanced array or object assigned to a TypeScript config key."""
    matches = list(re.finditer(r"(?m)^\s*{}\s*:\s*([\[\{{])".format(re.escape(key)), config))
    if len(matches) <= occurrence:
        return ""

    match = matches[occurrence]
    opening = match.group(1)
    closing = "]" if opening == "[" else "}"
    start = match.start(1)
    depth = 0
    quote = None
    escaped = False
    for index in range(start, len(config)):
        character = config[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in ("'", '"', "`"):
            quote = character
        elif character == opening:
            depth += 1
        elif character == closing:
            depth -= 1
            if depth == 0:
                return config[start : index + 1]
    return ""


def _provider_docs_in_config_section(config: str, locale: str, section: str) -> set[str]:
    occurrence = 1 if locale == "en" else 0
    block = _typescript_config_block(config, section, occurrence)
    prefix = "/en/providers/" if locale == "en" else "/providers/"
    return set(re.findall(r"link:\s*['\"]{}([^/'\"]+)['\"]".format(re.escape(prefix)), block))


def _provider_metadata(repo: Path) -> tuple[set[str], set[str], list[str]]:
    """Read field-model IDs and documentation slugs."""
    errors = []
    model = _load_json(repo / "ddns" / "config" / "field-model.json")
    if not isinstance(model, dict) or not isinstance(model.get("providers"), list):
        return set(), set(), ["ddns/config/field-model.json must contain a providers list"]

    providers = model["providers"]
    if not providers:
        errors.append("ddns/config/field-model.json providers must not be empty")
        return set(), set(), errors
    if not all(isinstance(provider, dict) for provider in providers):
        return set(), set(), ["ddns/config/field-model.json providers must be objects"]
    provider_ids = [provider.get("id") for provider in providers]
    provider_docs = [provider.get("docs") for provider in providers]
    if not all(isinstance(provider_id, str) for provider_id in provider_ids) or not all(
        isinstance(doc, str) for doc in provider_docs
    ):
        return set(), set(), ["every field-model provider requires string id and docs values"]
    ids = set(provider_ids)
    docs = set(provider_docs)
    if len(ids) != len(providers):
        errors.append("field-model provider ids must be unique")
    return ids, docs, errors


def _provider_runtime_errors(repo: Path, ids: set[str]) -> list[str]:
    """Compare field-model IDs with runtime and command-line provider surfaces."""
    errors = []
    registry = _literal_mapping_keys(repo / "ddns" / "provider" / "__init__.py")
    missing_registry = sorted(ids - registry)
    if missing_registry:
        errors.append("runtime registry missing canonical IDs: {}".format(", ".join(missing_registry)))

    cli_choices = _cli_provider_choices(repo / "ddns" / "config" / "cli.py")
    if cli_choices != ids:
        errors.append("CLI --dns choices differ from field-model IDs")
    return errors


def _provider_schema_errors(repo: Path, ids: set[str]) -> list[str]:
    """Compare the two latest schema provider enums with canonical IDs."""
    errors = []
    schema = _load_json(repo / "schema" / "v4.1.json")
    if not isinstance(schema, dict):
        return ["schema/v4.1.json must be an object"]
    try:
        schema_dns = set(schema["properties"]["dns"]["enum"])
        schema_provider = set(schema["properties"]["providers"]["items"]["properties"]["provider"]["enum"])
    except (KeyError, TypeError):
        errors.append("schema/v4.1.json must expose dns and providers[].provider enums")
    else:
        if schema_dns != ids:
            errors.append("schema dns enum differs from field-model IDs")
        if schema_provider != ids:
            errors.append("schema providers[].provider enum differs from field-model IDs")
    return errors


def _provider_doc_file_errors(repo: Path, docs: set[str]) -> list[str]:
    """Return missing bilingual provider documentation files."""
    errors = []
    for doc in sorted(docs):
        for locale in ("docs/providers", "docs/en/providers"):
            path = repo / locale / "{}.md".format(doc)
            if not path.is_file():
                errors.append("missing provider documentation: {}".format(_relative_path(path, repo)))
    return errors


def _provider_navigation_errors(repo: Path, docs: set[str]) -> list[str]:
    """Return provider documentation missing from VitePress navigation."""
    nav = repo / "docs" / ".vitepress" / "config.mts"
    if not nav.is_file():
        return ["missing VitePress provider navigation"]
    config = nav.read_text(encoding="utf-8")
    errors = []
    for locale in ("zh", "en"):
        for section, label in (("nav", "navigation"), ("sidebar", "sidebar")):
            missing = sorted(docs - _provider_docs_in_config_section(config, locale, section))
            if missing:
                errors.append("{} provider {} missing: {}".format(locale, label, ", ".join(missing)))
    return errors


def _provider_overview_errors(repo: Path, ids: set[str]) -> list[str]:
    """Return provider IDs missing from bilingual overview pages."""
    errors = []
    for overview in (repo / "docs" / "providers" / "README.md", repo / "docs" / "en" / "providers" / "README.md"):
        if not overview.is_file():
            errors.append("missing provider overview: {}".format(_relative_path(overview, repo)))
            continue
        content = overview.read_text(encoding="utf-8")
        missing = sorted(
            provider_id
            for provider_id in ids
            if not re.search(r"(?<![a-z0-9_-]){}(?![a-z0-9_-])".format(re.escape(provider_id)), content, re.IGNORECASE)
        )
        if missing:
            errors.append("{} missing provider IDs: {}".format(_relative_path(overview, repo), ", ".join(missing)))
    return errors


def _provider_llms_errors(repo: Path, docs: set[str]) -> list[str]:
    """Return stale or missing provider links in the LLM index."""
    llms = repo / "docs" / "llms.txt"
    if not llms.is_file():
        return ["missing docs/llms.txt"]
    links = set(re.findall(r"/providers/([a-z0-9_]+)\.md", llms.read_text(encoding="utf-8")))
    errors = []
    invalid_links = sorted(links - docs)
    missing_links = sorted(docs - links)
    if invalid_links:
        errors.append("docs/llms.txt links unknown provider docs: {}".format(", ".join(invalid_links)))
    if missing_links:
        errors.append("docs/llms.txt missing provider docs: {}".format(", ".join(missing_links)))
    return errors


def _provider_documentation_errors(repo: Path, ids: set[str], docs: set[str]) -> list[str]:
    """Compare canonical provider documentation, navigation, overviews, and llms links."""
    return (
        _provider_doc_file_errors(repo, docs)
        + _provider_navigation_errors(repo, docs)
        + _provider_overview_errors(repo, ids)
        + _provider_llms_errors(repo, docs)
    )


def provider_parity_errors(repo: Path = REPO_ROOT) -> list[str]:
    """Return provider metadata, runtime, schema, and documentation drift."""
    ids, docs, errors = _provider_metadata(repo)
    if not ids or not docs:
        return errors
    errors.extend(_provider_runtime_errors(repo, ids))
    errors.extend(_provider_schema_errors(repo, ids))
    errors.extend(_provider_documentation_errors(repo, ids, docs))
    return errors


def _instruction_errors(repo: Path) -> list[str]:
    """Return missing root and lane-specific instruction documents."""
    return [
        "missing required instructions: {}".format(relative_path)
        for relative_path in REQUIRED_AGENT_PATHS
        if not (repo / relative_path).is_file()
    ]


def _skill_errors(repo: Path) -> list[str]:
    """Return portable skill metadata violations."""
    errors = []
    skills = sorted((repo / ".agents" / "skills").glob("*/SKILL.md"))
    if not skills:
        errors.append("no portable skills found under .agents/skills")
    for skill in skills:
        content = skill.read_text(encoding="utf-8")
        relative = _relative_path(skill, repo)
        fields = _frontmatter_fields(content)
        if not fields or not fields.get("name") or not fields.get("description"):
            errors.append("{} requires name and description front matter".format(relative))
            continue
        if fields["name"] != skill.parent.name:
            errors.append("{} front-matter name must match its directory".format(relative))
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", fields["name"]):
            errors.append("{} has an invalid skill name".format(relative))
        if len(fields["description"]) > 1024:
            errors.append("{} description exceeds 1024 characters".format(relative))
        if "allowed-tools" in fields:
            errors.append("{} must not pre-approve tools in the portable skill".format(relative))
    return errors


def _profile_errors(repo: Path) -> list[str]:
    """Return thin-profile metadata and portable-skill-reference violations."""
    errors = []
    profiles = sorted((repo / ".github" / "agents").glob("*.agent.md"))
    if not profiles:
        errors.append("no thin Copilot profiles found under .github/agents")
    for profile in profiles:
        content = profile.read_text(encoding="utf-8")
        relative = _relative_path(profile, repo)
        fields = _frontmatter_fields(content)
        if not fields or not fields.get("name") or not fields.get("description") or not fields.get("tools"):
            errors.append("{} requires name, description, and tools front matter".format(relative))
        skill_references = re.findall(r"\.agents/skills/[-a-z0-9_]+/SKILL\.md", content)
        if not skill_references:
            errors.append("{} must delegate workflow details to a portable Skill".format(relative))
        for reference in skill_references:
            if not (repo / reference).is_file():
                errors.append("{} references missing portable Skill: {}".format(relative, reference))
    return errors


def portable_contract_errors(repo: Path = REPO_ROOT) -> list[str]:
    """Return portable skill and thin-agent profile contract violations."""
    return _instruction_errors(repo) + _skill_errors(repo) + _profile_errors(repo)


def merge_gate_failures(results: dict[str, object], event_name: str) -> list[str]:
    """Return failed, cancelled, or policy-invalid workflow prerequisites."""
    failures = []
    for job in MERGE_GATE_REQUIRED:
        result = results.get(job)
        status = result.get("result") if isinstance(result, dict) else None
        if status != "success":
            failures.append("{} finished with {!r}; expected success".format(job, status))

    for job in MERGE_GATE_TRUSTED_ONLY:
        result = results.get(job)
        status = result.get("result") if isinstance(result, dict) else None
        if event_name == "pull_request":
            if status not in ("success", "skipped"):
                failures.append("{} finished with {!r}; expected success or PR skip".format(job, status))
        elif status != "success":
            failures.append("{} finished with {!r}; expected success".format(job, status))
    return failures


def _python_format_arguments(repo: Path = REPO_ROOT) -> tuple[str, ...]:
    """Return tracked Python sources without Markdown code blocks."""
    paths = []
    for directory in ("ddns", "tests", "tools"):
        paths.extend(path.relative_to(repo).as_posix() for path in (repo / directory).rglob("*.py"))
    for relative in (".github/patch.py", ".github/scripts/update_agents_structure.py", "run.py"):
        if (repo / relative).is_file():
            paths.append(relative)
    return ("ruff", "format", "--check", *sorted(set(paths)))


def _commands_for_lanes(lanes: Iterable[str], repo: Path = REPO_ROOT) -> list[Command]:
    commands = {
        "Core": (Command("Core unit tests", (sys.executable, "-m", "unittest", "discover", "tests", "-v")),),
        "Config": (
            Command(
                "Configuration unit tests",
                (sys.executable, "-m", "unittest", "discover", "tests", "-p", "test_config*.py", "-v"),
            ),
        ),
        "Provider": (
            Command(
                "Provider unit tests",
                (sys.executable, "-m", "unittest", "discover", "tests", "-p", "test_provider_*.py", "-v"),
            ),
        ),
        "Web": (
            Command(
                "Web unit tests",
                (sys.executable, "-m", "unittest", "tests.test_web", "tests.test_config_cli_web", "-v"),
            ),
            Command("Offline E2E tests", (sys.executable, "-m", "unittest", "tests.e2e", "-v")),
        ),
        "Scheduler": (
            Command(
                "Scheduler unit tests",
                (sys.executable, "-m", "unittest", "discover", "tests", "-p", "test_scheduler_*.py", "-v"),
            ),
        ),
        "MCP": (
            Command(
                "MCP unit tests",
                (sys.executable, "-m", "unittest", "tests.test_mcp", "tests.test_config_cli_mcp", "-v"),
            ),
            Command("Offline E2E tests", (sys.executable, "-m", "unittest", "tests.e2e", "-v")),
        ),
        "Docs": (
            Command("Install documentation dependencies", ("npm", "--prefix", "docs", "ci")),
            Command("Build documentation", ("npm", "--prefix", "docs", "run", "build")),
        ),
        "Build/Release": (
            Command("Ruff lint", ("ruff", "check", ".")),
            Command("Ruff format check", _python_format_arguments(repo)),
        ),
        "Agent/Workflow": (
            Command(
                "Tooling contract tests",
                (sys.executable, "-m", "unittest", "discover", "tools/tests", "-p", "test_*.py", "-v"),
            ),
            Command("Ruff tooling lint", ("ruff", "check", "tools", ".github/scripts")),
            Command("Ruff tooling format check", _python_format_arguments(repo)),
        ),
    }

    result = []
    seen = set()
    for lane in lanes:
        for command in commands[lane]:
            if command.arguments not in seen:
                result.append(command)
                seen.add(command.arguments)
    return result


def _all_commands(repo: Path = REPO_ROOT) -> tuple[Command, ...]:
    """Return the non-duplicative command set for the complete project check."""
    return (
        Command("Ruff lint", ("ruff", "check", ".")),
        Command("Ruff Python format check", _python_format_arguments(repo)),
        Command("Unit tests", (sys.executable, "-m", "unittest", "discover", "tests", "-v")),
        Command("Offline E2E tests", (sys.executable, "-m", "unittest", "tests.e2e", "-v")),
        Command(
            "Tooling contract tests",
            (sys.executable, "-m", "unittest", "discover", "tools/tests", "-p", "test_*.py", "-v"),
        ),
        Command("Install documentation dependencies", ("npm", "--prefix", "docs", "ci")),
        Command("Build documentation", ("npm", "--prefix", "docs", "run", "build")),
    )


def _run_command(command: Command, repo: Path) -> None:
    executable = command.arguments[0]
    arguments = command.arguments
    if Path(executable).name == executable:
        resolved = shutil.which(executable)
        if resolved is None:
            raise CheckError("required tool is unavailable for {}: {}".format(command.label, executable))
        arguments = (resolved, *command.arguments[1:])
    print("+ {}  # {}".format(" ".join(command.arguments), command.label))
    result = subprocess.run(arguments, cwd=repo, check=False)
    if result.returncode:
        raise CheckError("{} failed with exit code {}".format(command.label, result.returncode))


def _run_contracts(repo: Path, providers: bool, portable: bool) -> None:
    checks = []
    if providers:
        checks.append(("Provider parity", provider_parity_errors(repo)))
    if portable:
        checks.append(("Portable agent contracts", portable_contract_errors(repo)))
    for label, errors in checks:
        if errors:
            for error in errors:
                print("ERROR: {}: {}".format(label, error), file=sys.stderr)
            raise CheckError("{} failed".format(label))
        print("PASS: {}".format(label))


def run_changed(repo: Path) -> None:
    paths = changed_paths(repo)
    lanes, reasons = select_lanes(paths)
    if not lanes:
        print("No changed files; no lane checks selected.")
        return
    print("Changed files:")
    for path in paths:
        print("  - {}".format(path))
    print("Selected lanes:")
    for lane in lanes:
        print("  - {} ({})".format(lane, "; ".join(reasons[lane])))
    _run_contracts(repo, providers="Provider" in lanes, portable="Agent/Workflow" in lanes)
    for command in _commands_for_lanes(lanes, repo):
        _run_command(command, repo)


def run_all(repo: Path) -> None:
    print("Selected lanes: {}".format(", ".join(CANONICAL_LANES)))
    _run_contracts(repo, providers=True, portable=True)
    for command in _all_commands(repo):
        _run_command(command, repo)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--changed",
        action="store_true",
        help="check merge-base, staged, and unstaged changes (DDNS_CHECK_BASE_REF overrides the base)",
    )
    mode.add_argument("--all", action="store_true", help="run every deterministic project check")
    mode.add_argument("--providers", action="store_true", help="validate provider metadata and documentation parity")
    arguments = parser.parse_args(argv)
    try:
        if arguments.changed:
            run_changed(REPO_ROOT)
        elif arguments.all:
            run_all(REPO_ROOT)
        else:
            _run_contracts(REPO_ROOT, providers=True, portable=False)
    except CheckError as error:
        print("CHECK FAILED: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
