"""Focused tests for deterministic project check selection and contracts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from os import environ
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check  # noqa: E402

STRUCTURE_SCRIPT = Path(__file__).resolve().parents[2] / ".github" / "scripts" / "update_agents_structure.py"
STRUCTURE_SPEC = importlib.util.spec_from_file_location("update_agents_structure", STRUCTURE_SCRIPT)
if STRUCTURE_SPEC is None or STRUCTURE_SPEC.loader is None:
    raise RuntimeError("Unable to load update_agents_structure.py")
update_agents_structure = importlib.util.module_from_spec(STRUCTURE_SPEC)
STRUCTURE_SPEC.loader.exec_module(update_agents_structure)


class LaneSelectionTests(unittest.TestCase):
    def test_provider_documentation_selects_provider_and_docs(self) -> None:
        self.assertEqual(check.lanes_for_path("docs/providers/cloudflare.md"), ("Provider", "Docs"))

    def test_unknown_path_selects_full_conservative_set(self) -> None:
        selected, reasons = check.select_lanes(["new-root-file.txt"])
        self.assertEqual(selected, check.CANONICAL_LANES)
        self.assertTrue(all(reasons[lane] == ["unknown path: new-root-file.txt"] for lane in selected))

    def test_dot_directories_are_preserved_for_agent_lane(self) -> None:
        self.assertEqual(check.normalize_path("./.github/workflows/build.yml"), ".github/workflows/build.yml")
        self.assertEqual(check.lanes_for_path(".github/workflows/build.yml"), ("Build/Release", "Agent/Workflow"))
        self.assertEqual(check.normalize_path(".agents/skills/example/SKILL.md"), ".agents/skills/example/SKILL.md")
        self.assertEqual(check.lanes_for_path(".agents/skills/example/SKILL.md"), ("Agent/Workflow",))

    def test_nearest_agent_instructions_select_agent_lane(self) -> None:
        self.assertEqual(check.lanes_for_path("docs/AGENTS.md"), ("Docs", "Agent/Workflow"))
        self.assertEqual(check.lanes_for_path("ddns/provider/AGENTS.md"), ("Provider", "Agent/Workflow"))

    def test_executable_docs_are_build_changes(self) -> None:
        self.assertEqual(check.lanes_for_path("docs/public/install.sh"), ("Docs", "Build/Release"))
        self.assertEqual(check.lanes_for_path("docs/esa.js"), ("Docs", "Build/Release"))

    def test_run_entrypoint_selects_core_and_build_release(self) -> None:
        self.assertEqual(check.lanes_for_path("run.py"), ("Core", "Build/Release"))

    def test_schema_changes_also_validate_docs(self) -> None:
        self.assertEqual(check.lanes_for_path("schema/v4.1.json"), ("Config", "Provider", "Docs"))

    def test_generated_docs_inputs_select_docs(self) -> None:
        self.assertEqual(check.lanes_for_path("ddns/config/field-model.json"), ("Config", "Provider", "Docs"))
        self.assertEqual(check.lanes_for_path("tests/config/debug.json"), ("Config", "Docs"))

    def test_provider_contract_inputs_select_provider(self) -> None:
        self.assertEqual(check.lanes_for_path("ddns/config/cli.py"), ("Config", "Provider"))
        self.assertEqual(check.lanes_for_path("schema/v4.1.json"), ("Config", "Provider", "Docs"))
        self.assertEqual(check.lanes_for_path("docs/.vitepress/config.mts"), ("Provider", "Docs"))

    def test_explicit_base_precedes_github_and_default_refs(self) -> None:
        with patch.dict(
            environ, {"DDNS_CHECK_BASE_REF": "origin/stack-base", "GITHUB_BASE_REF": "master"}, clear=False
        ):
            self.assertEqual(check._base_ref_candidates()[:3], ("origin/stack-base", "master", "origin/master"))


class ChangedPathsTests(unittest.TestCase):
    def _git(self, root: Path, *arguments: str) -> None:
        subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True, text=True)

    def test_changed_paths_collects_every_git_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init", "-b", "master")
            self._git(root, "config", "user.email", "tests@example.invalid")
            self._git(root, "config", "user.name", "DDNS Tests")
            self._write(root / "base.txt", "base\n")
            self._write(root / "renamed-source.txt", "rename\n")
            self._write(root / "unstaged.txt", "base\n")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")
            self._git(root, "switch", "-c", "feature")

            self._write(root / "committed.txt", "committed\n")
            self._git(root, "mv", "renamed-source.txt", "renamed-destination.txt")
            self._git(root, "add", "committed.txt")
            self._git(root, "commit", "-m", "feature")
            self._write(root / "staged.txt", "staged\n")
            self._git(root, "add", "staged.txt")
            self._write(root / "unstaged.txt", "changed\n")
            self._write(root / "untracked.txt", "untracked\n")

            with patch.dict(environ, {"DDNS_CHECK_BASE_REF": "master", "GITHUB_BASE_REF": ""}, clear=False):
                self.assertEqual(
                    check.changed_paths(root),
                    [
                        "committed.txt",
                        "renamed-destination.txt",
                        "renamed-source.txt",
                        "staged.txt",
                        "unstaged.txt",
                        "untracked.txt",
                    ],
                )

    def test_changed_paths_fails_without_base(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init", "-b", "feature")
            with patch.object(check, "_base_ref_candidates", return_value=("missing-ref",)):
                with self.assertRaisesRegex(check.CheckError, "could not find a merge-base reference"):
                    check.changed_paths(root)

    def test_format_arguments_respect_git_ignores_and_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init", "-b", "master")
            self._write(root / ".gitignore", ".venv/\n")
            self._write(root / "tools/check.py", "tracked = True\n")
            self._write(root / "tools/deleted.py", "deleted = True\n")
            self._write(root / "tools/untracked.py", "untracked = True\n")
            self._write(root / "tools/.venv/lib/site.py", "ignored = True\n")
            self._write(root / "docs/example.py", "out_of_scope = True\n")
            self._git(root, "add", ".gitignore", "tools/check.py", "tools/deleted.py", "docs/example.py")
            (root / "tools/deleted.py").unlink()

            arguments = set(check._python_format_arguments(root)[3:])
            self.assertIn("tools/check.py", arguments)
            self.assertIn("tools/untracked.py", arguments)
            self.assertNotIn("tools/deleted.py", arguments)
            self.assertNotIn("tools/.venv/lib/site.py", arguments)
            self.assertNotIn("docs/example.py", arguments)

    @staticmethod
    def _write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class ContractTests(unittest.TestCase):
    def _write(self, root: Path, relative: str, content: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _vitepress_config(self, doc: str) -> str:
        return """themeConfig: {
  nav: [{ link: '/providers/%s' }],
  sidebar: { '/providers/': [{ link: '/providers/%s' }] }
},
locales: {
  en: {
    themeConfig: {
      nav: [{ link: '/en/providers/%s' }],
      sidebar: { '/en/providers/': [{ link: '/en/providers/%s' }] }
    }
  }
}
""" % (doc, doc, doc, doc)

    def _llms_provider_index(self, doc: str) -> str:
        return (
            "- Multiple DNS provider support (1 providers)\n\n"
            "### DNS Provider Guides\n"
            "- https://ddns.newfuture.cc/providers/{0} "
            "([.md](https://ddns.newfuture.cc/providers/{0}.md))\n\n"
            "### Developer Documentation\n\n"
            "## Supported DNS Providers\n"
            "Canonical provider IDs: `{0}`.\n".format(doc)
        )

    def _provider_repo(self) -> Path:
        root = Path(tempfile.mkdtemp())
        model = {"providers": [{"id": "example", "docs": "example"}]}
        schema = {
            "properties": {
                "dns": {"enum": ["example"]},
                "providers": {"items": {"properties": {"provider": {"enum": ["example"]}}}},
            }
        }
        self._write(root, "ddns/config/field-model.json", json.dumps(model))
        self._write(root, "schema/v4.1.json", json.dumps(schema))
        self._write(
            root,
            "ddns/provider/__init__.py",
            "def get_provider_class(name):\n    mapping = {'example': object}\n    return mapping.get(name)\n",
        )
        self._write(root, "ddns/config/cli.py", "def cli(arg):\n    arg.add_argument('--dns', choices=['example'])\n")
        self._write(root, "docs/providers/example.md", "# Example\n")
        self._write(root, "docs/en/providers/example.md", "# Example\n")
        self._write(root, "docs/providers/README.md", "| Provider |\n| --- |\n| `example` |\n")
        self._write(root, "docs/en/providers/README.md", "| Provider |\n| --- |\n| `example` |\n")
        self._write(root, "docs/.vitepress/config.mts", self._vitepress_config("example"))
        self._write(root, "docs/llms.txt", self._llms_provider_index("example"))
        return root

    def test_provider_parity_accepts_consistent_surfaces(self) -> None:
        self.assertEqual(check.provider_parity_errors(self._provider_repo()), [])

    def test_provider_parity_reports_schema_drift(self) -> None:
        root = self._provider_repo()
        schema = json.loads((root / "schema/v4.1.json").read_text(encoding="utf-8"))
        schema["properties"]["dns"]["enum"] = []
        (root / "schema/v4.1.json").write_text(json.dumps(schema), encoding="utf-8")
        self.assertIn("schema dns enum differs from field-model IDs", check.provider_parity_errors(root))

    def test_provider_navigation_requires_nav_and_sidebar(self) -> None:
        root = self._provider_repo()
        config_path = root / "docs/.vitepress/config.mts"
        config = config_path.read_text(encoding="utf-8")
        config_path.write_text(config.replace("nav: [{ link: '/providers/example' }]", "nav: []", 1), encoding="utf-8")
        self.assertIn("zh provider navigation missing: example", check.provider_parity_errors(root))

        root = self._provider_repo()
        config_path = root / "docs/.vitepress/config.mts"
        config = config_path.read_text(encoding="utf-8")
        config_path.write_text(
            config.replace(
                "sidebar: { '/providers/': [{ link: '/providers/example' }] }", "sidebar: { '/providers/': [] }", 1
            ),
            encoding="utf-8",
        )
        self.assertIn("zh provider sidebar missing: example", check.provider_parity_errors(root))

    def test_provider_navigation_ignores_commented_links(self) -> None:
        root = self._provider_repo()
        config_path = root / "docs/.vitepress/config.mts"
        config = config_path.read_text(encoding="utf-8")
        config = config.replace(
            "nav: [{ link: '/providers/example' }]", "nav: [\n// { link: '/providers/example' }\n]", 1
        )
        config = config.replace(
            "sidebar: { '/providers/': [{ link: '/providers/example' }] }",
            "sidebar: { '/providers/': [/* { link: '/providers/example' } */] }",
            1,
        )
        config_path.write_text(config, encoding="utf-8")
        errors = check.provider_parity_errors(root)
        self.assertIn("zh provider navigation missing: example", errors)
        self.assertIn("zh provider sidebar missing: example", errors)

    def test_provider_navigation_rejects_unknown_links(self) -> None:
        root = self._provider_repo()
        config_path = root / "docs/.vitepress/config.mts"
        config = config_path.read_text(encoding="utf-8")
        config_path.write_text(
            config.replace(
                "nav: [{ link: '/providers/example' }]",
                "nav: [{ link: '/providers/example' }, { link: '/providers/stale' }]",
                1,
            ),
            encoding="utf-8",
        )
        self.assertIn("zh provider navigation links unknown docs: stale", check.provider_parity_errors(root))

    def test_provider_parity_rejects_empty_metadata(self) -> None:
        root = self._provider_repo()
        (root / "ddns/config/field-model.json").write_text(json.dumps({"providers": []}), encoding="utf-8")
        self.assertIn("ddns/config/field-model.json providers must not be empty", check.provider_parity_errors(root))

    def test_runtime_provider_class_requires_canonical_id(self) -> None:
        root = self._provider_repo()
        (root / "ddns/provider/__init__.py").write_text(
            "def get_provider_class(name):\n"
            "    mapping = {'example': object, 'runtime-only': RuntimeOnlyProvider}\n"
            "    return mapping.get(name)\n",
            encoding="utf-8",
        )
        self.assertIn(
            "runtime provider classes lack canonical IDs: RuntimeOnlyProvider", check.provider_parity_errors(root)
        )

    def test_llms_provider_index_rejects_duplicates_and_comments(self) -> None:
        root = self._provider_repo()
        llms_path = root / "docs/llms.txt"
        link = "https://ddns.newfuture.cc/providers/example.md\n"
        llms_path.write_text(
            "### DNS Provider Guides\n" + link + link + "\n### Developer Documentation\n", encoding="utf-8"
        )
        self.assertIn("docs/llms.txt duplicate provider docs: example", check.provider_parity_errors(root))

        llms_path.write_text(
            "### DNS Provider Guides\n<!-- {} -->\n\n### Developer Documentation\n".format(link.strip()),
            encoding="utf-8",
        )
        self.assertIn("docs/llms.txt missing provider docs: example", check.provider_parity_errors(root))

    def test_llms_provider_count_and_inventory_match_metadata(self) -> None:
        root = self._provider_repo()
        llms_path = root / "docs/llms.txt"
        content = llms_path.read_text(encoding="utf-8")
        content = content.replace("(1 providers)", "(2 providers)")
        content = content.replace("Canonical provider IDs: `example`", "Canonical provider IDs: `stale`")
        llms_path.write_text(content, encoding="utf-8")
        errors = check.provider_parity_errors(root)
        self.assertIn("docs/llms.txt provider count is 2; expected 1", errors)
        self.assertIn("docs/llms.txt supported provider IDs missing: example", errors)
        self.assertIn("docs/llms.txt supported provider IDs unknown: stale", errors)

    def test_missing_temporary_surface_raises_check_error(self) -> None:
        root = Path(tempfile.mkdtemp())
        with self.assertRaisesRegex(check.CheckError, "required file is missing.*field-model.json"):
            check.provider_parity_errors(root)

    def test_provider_overview_requires_table_row(self) -> None:
        root = self._provider_repo()
        (root / "ddns/config/field-model.json").write_text(
            json.dumps({"providers": [{"id": "he", "docs": "he"}]}), encoding="utf-8"
        )
        schema = json.loads((root / "schema/v4.1.json").read_text(encoding="utf-8"))
        schema["properties"]["dns"]["enum"] = ["he"]
        schema["properties"]["providers"]["items"]["properties"]["provider"]["enum"] = ["he"]
        (root / "schema/v4.1.json").write_text(json.dumps(schema), encoding="utf-8")
        (root / "ddns/provider/__init__.py").write_text(
            "def get_provider_class(name):\n    mapping = {'he': object}\n    return mapping.get(name)\n",
            encoding="utf-8",
        )
        (root / "ddns/config/cli.py").write_text(
            "def cli(arg):\n    arg.add_argument('--dns', choices=['he'])\n", encoding="utf-8"
        )
        for relative in ("docs/providers/he.md", "docs/en/providers/he.md"):
            self._write(root, relative, "# HE\n")
        for relative in ("docs/providers/README.md", "docs/en/providers/README.md"):
            self._write(root, relative, "| Provider |\n| --- |\n\n- **he** is mentioned outside the table.\n")
        (root / "docs/.vitepress/config.mts").write_text(self._vitepress_config("he"), encoding="utf-8")
        (root / "docs/llms.txt").write_text(self._llms_provider_index("he"), encoding="utf-8")
        self.assertIn("docs/providers/README.md missing provider IDs: he", check.provider_parity_errors(root))

    def test_provider_overview_rejects_unknown_table_row(self) -> None:
        root = self._provider_repo()
        overview = root / "docs/providers/README.md"
        overview.write_text(overview.read_text(encoding="utf-8") + "| `stale` |\n", encoding="utf-8")
        self.assertIn("docs/providers/README.md lists unknown provider IDs: stale", check.provider_parity_errors(root))

    def test_portable_profiles_must_reference_skills(self) -> None:
        root = Path(tempfile.mkdtemp())
        self._write(root, "AGENTS.md", "# Rules\n")
        self._write(root, ".agents/skills/example/SKILL.md", "---\nname: example\ndescription: Example\n---\n")
        self._write(
            root,
            ".github/agents/example.agent.md",
            "---\nname: Example\ndescription: Example\ntools: [read]\n---\n# Example\n",
        )
        self.assertIn(
            ".github/agents/example.agent.md must delegate workflow details to a portable Skill",
            check.portable_contract_errors(root),
        )

    def test_portable_contracts_require_nearest_instruction_files(self) -> None:
        root = Path(tempfile.mkdtemp())
        self._write(root, "AGENTS.md", "# Rules\n")
        errors = check.portable_contract_errors(root)
        self.assertIn("missing required instructions: docs/AGENTS.md", errors)
        self.assertIn("missing required instructions: ddns/provider/AGENTS.md", errors)
        self.assertIn("missing required instructions: tools/AGENTS.md", errors)

    def test_current_portable_contracts_pass(self) -> None:
        self.assertEqual(check.portable_contract_errors(check.REPO_ROOT), [])

    def test_agent_contract_workflow_watches_all_workflows(self) -> None:
        workflow = (check.REPO_ROOT / ".github/workflows/update-agents.yml").read_text(encoding="utf-8")
        self.assertIn("- '.github/workflows/**'", workflow)

    def test_portable_skill_must_not_preapprove_tools(self) -> None:
        root = Path(tempfile.mkdtemp())
        for relative in check.REQUIRED_AGENT_PATHS:
            self._write(root, relative, "# Rules\n")
        self._write(
            root,
            ".agents/skills/example/SKILL.md",
            "---\nname: example\ndescription: Example\nallowed-tools: shell\n---\n",
        )
        self._write(
            root,
            ".github/agents/example.agent.md",
            "---\nname: Example\ndescription: Example\ntools: [read]\n---\nRead `.agents/skills/example/SKILL.md`.\n",
        )
        self.assertIn(
            ".agents/skills/example/SKILL.md must not pre-approve tools in the portable skill",
            check.portable_contract_errors(root),
        )

    def test_all_commands_do_not_repeat_unit_or_e2e_suites(self) -> None:
        labels = [command.label for command in check._all_commands()]
        self.assertEqual(labels.count("Unit tests"), 1)
        self.assertEqual(labels.count("Offline E2E tests"), 1)
        self.assertEqual(labels.count("Tooling contract tests"), 1)

    def test_format_check_only_targets_python_files(self) -> None:
        arguments = check._python_format_arguments()
        self.assertTrue(all(not argument.endswith(".md") for argument in arguments[3:]))
        self.assertIn("tests/test_ip.py", arguments)

    def test_docs_lane_installs_before_building(self) -> None:
        labels = [command.label for command in check._commands_for_lanes(("Docs",))]
        self.assertEqual(labels, ["Install documentation dependencies", "Build documentation"])

    def test_core_lane_runs_offline_e2e(self) -> None:
        labels = [command.label for command in check._commands_for_lanes(("Core",))]
        self.assertEqual(labels, ["Core unit tests", "Offline E2E tests"])

    @patch("check.subprocess.run")
    @patch("check.shutil.which", return_value="C:/tools/npm.cmd")
    def test_run_command_uses_resolved_executable(self, mock_which, mock_run) -> None:
        mock_run.return_value.returncode = 0
        check._run_command(check.Command("Docs", ("npm", "--version")), check.REPO_ROOT)
        mock_which.assert_called_once_with("npm")
        self.assertEqual(mock_run.call_args.args[0][0], "C:/tools/npm.cmd")

    def test_merge_gate_rejects_required_skip_and_cancellation(self) -> None:
        results = {job: {"result": "success"} for job in check.MERGE_GATE_REQUIRED}
        results["python"] = {"result": "cancelled"}
        results["preview-pypi"] = {"result": "skipped"}
        results["preview-docker"] = {"result": "skipped"}
        failures = check.merge_gate_failures(results, "pull_request")
        self.assertEqual(failures, ["python finished with 'cancelled'; expected success"])

    def test_merge_gate_allows_only_pr_policy_skips(self) -> None:
        results = {job: {"result": "success"} for job in check.MERGE_GATE_REQUIRED}
        results["preview-pypi"] = {"result": "skipped"}
        results["preview-docker"] = {"result": "skipped"}
        self.assertEqual(check.merge_gate_failures(results, "pull_request"), [])
        self.assertIn(
            "preview-pypi finished with 'skipped'; expected success", check.merge_gate_failures(results, "push")
        )


class StructureWorkflowTests(unittest.TestCase):
    @patch.object(check, "portable_contract_errors", return_value=["missing required instructions: docs/AGENTS.md"])
    @patch.object(update_agents_structure, "structure_drift", return_value=([], ["docs/AGENTS.md"]))
    def test_reporting_writes_issue_before_failing_contract(self, _mock_drift, _mock_contracts) -> None:
        with tempfile.TemporaryDirectory() as directory:
            issue_body = Path(directory) / "issue_body.md"
            with patch.object(update_agents_structure, "ISSUE_BODY_FILE", str(issue_body)):
                result = update_agents_structure.main([])

            self.assertEqual(result, 1)
            body = issue_body.read_text(encoding="utf-8")
            self.assertIn("## Contract Errors", body)
            self.assertIn("missing required instructions: docs/AGENTS.md", body)
            self.assertIn("## Missing Files", body)

    def test_contract_only_report_omits_structure_actions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            issue_body = Path(directory) / "issue_body.md"
            with patch.object(update_agents_structure, "ISSUE_BODY_FILE", str(issue_body)):
                update_agents_structure.write_issue_body([], [], ["invalid portable contract"], False)

            body = issue_body.read_text(encoding="utf-8")
            self.assertIn("1. Fix each contract error above", body)
            self.assertNotIn("Update directory structure", body)
            self.assertNotIn("Update version/date", body)


if __name__ == "__main__":
    unittest.main()
