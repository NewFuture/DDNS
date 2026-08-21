"""Focused tests for deterministic project check selection and contracts."""

from __future__ import annotations

import importlib.util
import json
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

    def test_executable_docs_are_build_changes(self) -> None:
        self.assertEqual(check.lanes_for_path("docs/public/install.sh"), ("Docs", "Build/Release"))
        self.assertEqual(check.lanes_for_path("docs/esa.js"), ("Docs", "Build/Release"))

    def test_schema_changes_also_validate_docs(self) -> None:
        self.assertEqual(check.lanes_for_path("schema/v4.1.json"), ("Config", "Docs"))

    def test_generated_docs_inputs_select_docs(self) -> None:
        self.assertEqual(check.lanes_for_path("ddns/config/field-model.json"), ("Config", "Provider", "Docs"))
        self.assertEqual(check.lanes_for_path("tests/config/debug.json"), ("Config", "Docs"))

    def test_explicit_base_precedes_github_and_default_refs(self) -> None:
        with patch.dict(
            environ, {"DDNS_CHECK_BASE_REF": "origin/stack-base", "GITHUB_BASE_REF": "master"}, clear=False
        ):
            self.assertEqual(check._base_ref_candidates()[:3], ("origin/stack-base", "master", "origin/master"))


class ContractTests(unittest.TestCase):
    def _write(self, root: Path, relative: str, content: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

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
        self._write(root, "docs/providers/README.md", "`example`\n")
        self._write(root, "docs/en/providers/README.md", "`example`\n")
        self._write(root, "docs/.vitepress/config.mts", "link: '/providers/example'\nlink: '/en/providers/example'\n")
        self._write(
            root,
            "docs/llms.txt",
            "https://ddns.newfuture.cc/providers/example ([.md](https://ddns.newfuture.cc/providers/example.md))\n",
        )
        return root

    def test_provider_parity_accepts_consistent_surfaces(self) -> None:
        self.assertEqual(check.provider_parity_errors(self._provider_repo()), [])

    def test_provider_parity_reports_schema_drift(self) -> None:
        root = self._provider_repo()
        schema = json.loads((root / "schema/v4.1.json").read_text(encoding="utf-8"))
        schema["properties"]["dns"]["enum"] = []
        (root / "schema/v4.1.json").write_text(json.dumps(schema), encoding="utf-8")
        self.assertIn("schema dns enum differs from field-model IDs", check.provider_parity_errors(root))

    def test_provider_parity_rejects_empty_metadata(self) -> None:
        root = self._provider_repo()
        (root / "ddns/config/field-model.json").write_text(json.dumps({"providers": []}), encoding="utf-8")
        self.assertIn("ddns/config/field-model.json providers must not be empty", check.provider_parity_errors(root))

    def test_provider_overview_uses_identifier_boundaries(self) -> None:
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
            self._write(root, relative, "The provider list does not name the short identifier.\n")
        (root / "docs/.vitepress/config.mts").write_text(
            "link: '/providers/he'\nlink: '/en/providers/he'\n", encoding="utf-8"
        )
        (root / "docs/llms.txt").write_text(
            "https://ddns.newfuture.cc/providers/he ([.md](https://ddns.newfuture.cc/providers/he.md))\n",
            encoding="utf-8",
        )
        self.assertIn("docs/providers/README.md missing provider IDs: he", check.provider_parity_errors(root))

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


if __name__ == "__main__":
    unittest.main()
