"""Offline contracts for V5 CI separation and artifact-only Rust preparation."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from os import environ
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github/workflows"
STABLE_REFS = "(github.ref == 'refs/heads/master' || github.ref == 'refs/heads/main')"
STABLE_PUSH = "github.event_name == 'push' && " + STABLE_REFS
RUST_ONLY_PATHS = (
    "rust/**",
    ".github/workflows/rust.yml",
    ".github/workflows/rust-python-checks.yml",
    ".github/workflows/publish-rust.yml",
    ".github/instructions/rust.instructions.md",
    "docker/rust.Dockerfile",
    "docs/public/install-rust.sh",
    "tests/scripts/test-install-rust.sh",
    "docs/dev/rust.md",
    "docs/en/dev/rust.md",
    "docs/install.md",
    "docs/en/install.md",
    "docs/docker.md",
    "docs/en/docker.md",
    "README.md",
    "README.en.md",
)
NATIVE_MATRIX = (
    ("ubuntu-latest", "ddns-rs-linux-x64", "x86_64-unknown-linux-musl"),
    ("ubuntu-24.04-arm", "ddns-rs-linux-arm64", "aarch64-unknown-linux-musl"),
    ("windows-latest", "ddns-rs-windows-x64.exe", "x86_64-pc-windows-msvc"),
    ("macos-15-intel", "ddns-rs-macos-x64", "x86_64-apple-darwin"),
    ("macos-latest", "ddns-rs-macos-arm64", "aarch64-apple-darwin"),
)
REQUIRED_JOBS = ("lint", "python", "e2e", "pypi", "nuitka", "linux-binary", "prepare-docker", "docker")
PREVIEW_JOBS = ("preview-pypi", "preview-docker")


def workflow(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def block(text: str, name: str) -> str:
    """Extract a fixed two-space trigger/job block, not a general YAML parser."""
    match = re.search(rf"(?ms)^  {re.escape(name)}:\n(.*?)(?=^\S|^  \S|\Z)", text)
    if match is None:
        raise AssertionError("Missing workflow block: " + name)
    return match[1]


def inline_list(text: str, key: str) -> tuple[str, ...]:
    match = re.search(rf"(?m)^    {re.escape(key)}: \[([^\]]*)\]$", text)
    if match is None:
        raise AssertionError("Missing workflow list: " + key)
    return tuple(value.strip(" \"'") for value in match[1].split(","))


def inline_script(text: str, step_name: str) -> str:
    """Extract the executable run block from one known six-space named step."""
    _, marker, step = text.partition("      - name: " + step_name + "\n")
    if not marker:
        raise AssertionError("Missing workflow step: " + step_name)
    step = step.split("\n      - ", 1)[0]
    match = re.search(r"(?m)^        run: \|\n((?:(?:          .*)?\n)+)", step)
    if match is None:
        raise AssertionError("Missing inline script: " + step_name)
    return dedent(match[1])


def run_python(source: str, root: Path, values: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", source],
        cwd=root,
        env={**environ, **(values or {})},
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )


class V5WorkflowTests(unittest.TestCase):
    def test_v5_ci_triggers_preserve_existing_branches_and_paths(self) -> None:
        for name in ("rust.yml", "rust-python-checks.yml", "build.yml"):
            for event, branches in (
                ("push", ("master", "main", "v5")),
                ("pull_request", ("master", "main", "abc", "v5")),
            ):
                with self.subTest(workflow=name, event=event):
                    trigger = block(workflow(name), event)
                    self.assertEqual(inline_list(trigger, "branches"), branches)
                    paths = tuple(re.findall(r"""(?m)^      - ["']([^"']+)["']$""", trigger))
                    self.assertEqual(paths, RUST_ONLY_PATHS)
                    self.assertIn("    paths-ignore:" if name == "build.yml" else "    paths:", trigger)
        for name, events in (("build-docs.yml", ("push", "pull_request")), ("update-agents.yml", ("pull_request",))):
            for event in events:
                with self.subTest(workflow=name, event=event):
                    self.assertEqual(inline_list(block(workflow(name), event), "branches"), ("master", "main", "v5"))

    def test_rust_only_classification_does_not_mask_mixed_python_changes(self) -> None:
        text = workflow("rust-python-checks.yml")
        changes = block(text, "changes")
        case_paths = "|".join(path.replace("rust/**", "rust/*") for path in RUST_ONLY_PATHS)
        self.assertIn(case_paths + ")", changes)
        self.assertIn('echo "pure_rust=false"', changes)
        self.assertIn("*)\n                pure_rust=false", changes)
        self.assertIn("if: needs.changes.outputs.pure_rust == 'true'", block(text, "not-applicable"))
        for job in REQUIRED_JOBS:
            with self.subTest(job=job):
                self.assertNotRegex(block(workflow("build.yml"), job), r"(?m)^    if:")
        self.assertIn("run unit tests", block(workflow("build.yml"), "python"))

    def test_previews_and_python_cache_writes_remain_stable_push_only(self) -> None:
        text = workflow("build.yml")
        for name in PREVIEW_JOBS:
            with self.subTest(job=name):
                preview = block(text, name)
                self.assertIn("    if: " + STABLE_PUSH + "\n", preview)
                self.assertIn("    environment:\n      name: preview\n", preview)
        cache = re.search(r"CACHE_WRITE: \$\{\{(.*?)\}\}", text, re.DOTALL)
        self.assertIsNotNone(cache)
        self.assertEqual(" ".join(cache[1].split()), STABLE_PUSH)
        self.assertIn("actions/cache/restore@v6", text)
        self.assertIn("      id-token: write", block(text, "preview-pypi"))
        self.assertIn("      packages: write", block(text, "preview-docker"))

    def test_pages_deploys_only_from_stable_push_or_manual_refs(self) -> None:
        text = workflow("build-docs.yml")
        deploy = text.split("    - name: Deploy to GitHub Pages\n", 1)[1]
        guard = "(github.event_name == 'push' || github.event_name == 'workflow_dispatch') && " + STABLE_REFS
        self.assertIn("      if: " + guard + "\n", deploy)
        self.assertIn("  workflow_dispatch:", text)
        build = block(text, "build")
        self.assertNotRegex(build, r"(?m)^    if:")
        self.assertIn("run: npm run build", build)
        self.assertIn("uses: actions/upload-pages-artifact@v5", build)
        self.assertIn("permissions:\n  pages: write\n  id-token: write\n", text)

    def test_rust_caches_save_only_for_trusted_branch_pushes(self) -> None:
        policy = (
            "github.event_name == 'push' && "
            "(github.ref == 'refs/heads/master' || github.ref == 'refs/heads/main' || github.ref == 'refs/heads/v5')"
        )
        for name in ("rust.yml", "publish-rust.yml"):
            caches = re.findall(r"(?ms)^      - uses: Swatinem/rust-cache@\S+\n(.*?)(?=^      - |\Z)", workflow(name))
            self.assertTrue(caches, name)
            for cache in caches:
                with self.subTest(workflow=name, cache=cache):
                    self.assertIn("          workspaces: rust\n", cache)
                    self.assertIn("          save-if: ${{ " + policy + " }}\n", cache)

    def test_workflow_passes_full_ref_to_strict_merge_gate(self) -> None:
        gate = block(workflow("build.yml"), "merge-gate")
        self.assertEqual(inline_list(gate, "needs"), REQUIRED_JOBS + PREVIEW_JOBS)
        self.assertIn("    if: always()", gate)
        self.assertIn("          WORKFLOW_REF: ${{ github.ref }}", gate)
        shell = inline_script(workflow("build.yml"), "Enforce required job policy")
        source = shell.split("python3 - <<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
        results = {job: {"result": "success"} for job in REQUIRED_JOBS}
        results.update({job: {"result": "skipped"} for job in PREVIEW_JOBS})
        for ref, expected_code in (("refs/heads/v5", 0), ("refs/heads/master", 1), ("refs/tags/v5", 1)):
            with self.subTest(ref=ref):
                result = run_python(
                    source, ROOT, {"NEEDS_JSON": json.dumps(results), "EVENT_NAME": "push", "WORKFLOW_REF": ref}
                )
                self.assertEqual(result.returncode, expected_code, result.stdout + result.stderr)

    def test_native_and_container_matrices_and_locked_checks_are_preserved(self) -> None:
        for name in ("rust.yml", "publish-rust.yml"):
            with self.subTest(workflow=name):
                text = workflow(name)
                binary = block(text, "binary")
                matrix = tuple(
                    re.findall(
                        r"(?m)^          - os: (\S+)\n            (?:asset|artifact): (\S+)\n            target: (\S+)$",
                        binary,
                    )
                )
                expected = NATIVE_MATRIX
                if name == "rust.yml":
                    expected = tuple((os, asset.removesuffix(".exe"), target) for os, asset, target in expected)
                self.assertEqual(matrix, expected)
                self.assertIn("fail-fast: false", binary)
                self.assertIn("cargo test --manifest-path rust/Cargo.toml --locked", text)
                self.assertIn(
                    "cargo build --manifest-path rust/Cargo.toml --release --locked --target ${{ matrix.target }}",
                    binary,
                )
                self.assertIn('"$binary" --version', binary)
                self.assertIn("& $binary --version", binary)
                self.assertIn("--dns debug --no-cache", binary)
                self.assertIn("if-no-files-found: error", binary)
        self.assertIn('lto = "thin"', (ROOT / "rust/Cargo.toml").read_text(encoding="utf-8"))
        container_matrix = re.findall(
            r"(?m)^          - os: (\S+)\n            platform: (\S+)$", block(workflow("rust.yml"), "container")
        )
        self.assertEqual(container_matrix, [("ubuntu-latest", "linux/amd64"), ("ubuntu-24.04-arm", "linux/arm64")])
        container = block(workflow("publish-rust.yml"), "container")
        self.assertIn("      platforms: linux/amd64,linux/arm64\n", container)
        self.assertIn("uses: docker/setup-qemu-action@v4", container)
        self.assertIn("uses: docker/setup-buildx-action@v4", container)
        self.assertIn("          platforms: ${{ env.platforms }}", container)
        self.assertIn("          push: false", container)
        self.assertIn("          outputs: type=oci,dest=./ddns-rs-oci.tar", container)
        self.assertIn("uses: actions/upload-artifact@v7", container)
        self.assertIn("          path: ddns-rs-oci.tar\n", container)
        self.assertIn("          if-no-files-found: error", container)

    def test_rust_preparation_has_only_read_permissions_and_artifact_outputs(self) -> None:
        text = "\n".join(
            line for line in workflow("publish-rust.yml").splitlines() if not line.lstrip().startswith("#")
        )
        self.assertIn("name: Prepare Rust V5\n", text)
        triggers = text.split("\non:\n", 1)[1].split("\npermissions:\n", 1)[0]
        self.assertEqual(re.findall(r"(?m)^  (\w+):", triggers), ["push", "workflow_dispatch"])
        self.assertEqual(inline_list(block(text, "push"), "tags"), ("v5.*",))
        self.assertEqual(inline_list(block(text, "push"), "branches"), ("v5",))
        self.assertEqual(
            tuple(re.findall(r'(?m)^      - "([^"]+)"$', block(text, "push"))),
            ("rust/Cargo.toml", "rust/Cargo.lock", ".github/workflows/publish-rust.yml"),
        )
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("    needs: preflight\n", block(text, "binary"))
        for name, dependency in (("release-assets", "binary"), ("container", "release-assets")):
            job = block(text, name)
            self.assertIn("    needs: " + dependency + "\n", job)
            self.assertIn("    environment:\n      name: publish\n", job)
            self.assertIn("    permissions:\n      contents: read\n", job)
        preflight = block(text, "preflight")
        self.assertIn("uses: actions/setup-python@v7", preflight)
        self.assertIn('python-version: "3.12"', preflight)
        self.assertIn("SELECTED_REF: ${{ github.ref }}", preflight)
        self.assertIn("shell: python", preflight)
        bundle = block(text, "release-assets")
        self.assertIn("uses: actions/upload-artifact@v7", bundle)
        self.assertIn("          name: rust-v5-native-bundle\n", bundle)
        self.assertIn("          path: dist/\n", bundle)
        self.assertIn("          if-no-files-found: error", bundle)
        for forbidden in (
            r":\s*write\b",
            r"\b(?:gh|curl|wget)\s",
            r"\bgit\s+(?:push|tag)\b",
            r"\bcargo\s+publish\b",
            r"\bdocker\s+(?:login|push|manifest\s+push|buildx\s+imagetools\s+create)\b",
            r"\bpush:\s*true\b|type=registry|push=true",
            r"\bsecrets\.|\bgithub\.token\b|\b(?:GH_TOKEN|GITHUB_TOKEN)\b",
            r"--clobber|latest=|value=next|:latest\b|:next\b",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotRegex(text, forbidden)
        actions = set(re.findall(r"(?m)^\s+(?:- )?uses: (\S+)", text))
        self.assertLessEqual(
            actions,
            {
                "actions/checkout@v7",
                "actions/setup-python@v7",
                "dtolnay/rust-toolchain@stable",
                "Swatinem/rust-cache@v2",
                "actions/upload-artifact@v7",
                "actions/download-artifact@v8",
                "docker/setup-qemu-action@v4",
                "docker/setup-buildx-action@v4",
                "docker/build-push-action@v7",
            },
        )


class RustPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "rust").mkdir()
        self.source = inline_script(workflow("publish-rust.yml"), "Validate Rust V5 preparation source")

    def run_preflight(
        self,
        version: str = "5.0.0-alpha1",
        event: str = "workflow_dispatch",
        ref: str = "refs/heads/v5",
        locked_versions: tuple[str, ...] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        (self.root / "rust/Cargo.toml").write_text(
            '[package]\nname = "ddns-rs"\nversion = ' + json.dumps(version) + "\n", encoding="utf-8"
        )
        versions = (version,) if locked_versions is None else locked_versions
        lock = 'version = 4\n[[package]]\nname = "unrelated"\nversion = "1.2.3"\n'
        lock += "".join('[[package]]\nname = "ddns-rs"\nversion = ' + json.dumps(value) + "\n" for value in versions)
        (self.root / "rust/Cargo.lock").write_text(lock, encoding="utf-8")
        return run_python(self.source, self.root, {"EVENT_NAME": event, "SELECTED_REF": ref})

    def test_canonical_v5_prereleases_accept_manual_rehearsals_and_exact_tags(self) -> None:
        for version in (
            "5.0.0-alpha1",
            "5.0.0-beta2",
            "5.0.0-rc10",
            "5.12.34-alpha123",
            "5.12.34-beta12",
            "5.12.34-rc1",
        ):
            for event, ref in (
                ("workflow_dispatch", "refs/heads/v5"),
                ("push", "refs/heads/v5"),
                ("push", "refs/tags/v" + version),
            ):
                with self.subTest(version=version, event=event, ref=ref):
                    result = self.run_preflight(version, event, ref)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("artifacts only", result.stdout)

    def test_stable_v5_versions_are_rejected_for_all_preparation_refs(self) -> None:
        for version in ("5.0.0", "5.12.34"):
            for event, ref in (
                ("workflow_dispatch", "refs/heads/v5"),
                ("push", "refs/heads/v5"),
                ("push", "refs/tags/v" + version),
            ):
                with self.subTest(version=version, event=event, ref=ref):
                    result = self.run_preflight(version, event, ref)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("canonical version", result.stderr)

    def test_noncanonical_or_non_v5_manifest_versions_are_rejected(self) -> None:
        for version in (
            "0.1.0",
            "4.2.0",
            "6.0.0",
            "05.0.0",
            "5.00.0",
            "5.0.00",
            "05.0.0-alpha1",
            "5.00.0-beta2",
            "5.0.00-rc10",
            "5.0",
            "v5.0.0",
            "5.0.0-alpha",
            "5.0.0-alpha0",
            "5.0.0-alpha01",
            "5.0.0-alpha.1",
            "5.0.0-beta01",
            "5.0.0-rc0",
            "5.0.0-rc01",
            "5.0.0-preview1",
            "5.0.0+build",
            "5.0.0\n",
            " 5.0.0",
        ):
            with self.subTest(version=version):
                result = self.run_preflight(version)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("canonical version", result.stderr)

    def test_manual_rehearsal_requires_the_full_v5_branch_ref(self) -> None:
        for ref in ("refs/heads/master", "refs/heads/main", "refs/heads/v4", "refs/tags/v5.0.0-alpha1", "v5", ""):
            with self.subTest(ref=ref):
                result = self.run_preflight(ref=ref)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("must run from the v5 branch", result.stderr)

    def test_push_requires_a_tag_exactly_matching_the_manifest(self) -> None:
        for ref in (
            "refs/heads/master",
            "refs/heads/main",
            "refs/heads/v4",
            "refs/heads/feature",
            "refs/tags/v5.0.0",
            "refs/tags/v5.0.0-alpha2",
            "refs/tags/v5.00.0-alpha1",
            "refs/tags/v4.2.0",
            "refs/tags/v5.0.0-alpha1+build",
            "v5.0.0-alpha1",
        ):
            with self.subTest(ref=ref):
                result = self.run_preflight(event="push", ref=ref)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("push tag must exactly match", result.stderr)

    def test_other_events_and_missing_mismatched_or_duplicate_lock_packages_fail(self) -> None:
        for event in ("pull_request", "schedule", ""):
            with self.subTest(event=event):
                result = self.run_preflight(event=event)
                self.assertNotEqual(result.returncode, 0)
        for versions in ((), ("0.1.0",), ("5.0.0-alpha2",), ("5.0.0-alpha1", "5.0.0-alpha1")):
            with self.subTest(locked_versions=versions):
                result = self.run_preflight(locked_versions=versions)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Cargo.lock", result.stderr)


class RustBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.dist = self.root / "dist"
        self.dist.mkdir()
        self.source = inline_script(workflow("publish-rust.yml"), "Verify complete Rust artifact set")
        for _, asset, _ in NATIVE_MATRIX:
            content = ("Offline binary fixture: " + asset).encode()
            (self.dist / asset).write_bytes(content)
            newline = "" if asset.endswith(".exe") else "\n"
            (self.dist / (asset + ".sha256")).write_text(
                hashlib.sha256(content).hexdigest() + "  " + asset + newline, encoding="utf-8"
            )

    def test_complete_native_bundle_verifies_without_mutating_files_on_rerun(self) -> None:
        before = {path.name: path.read_bytes() for path in self.dist.iterdir()}
        for _ in range(2):
            result = run_python(self.source, self.root)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({path.name: path.read_bytes() for path in self.dist.iterdir()}, before)

    def test_every_binary_and_checksum_is_mandatory(self) -> None:
        for path in list(self.dist.iterdir()):
            with self.subTest(file=path.name):
                content = path.read_bytes()
                path.unlink()
                result = run_python(self.source, self.root)
                path.write_bytes(content)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("artifact set mismatch", result.stderr)

    def test_unexpected_artifacts_are_rejected(self) -> None:
        (self.dist / "unexpected").write_bytes(b"unexpected")
        result = run_python(self.source, self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("artifact set mismatch", result.stderr)

    def test_tampered_binaries_and_wrong_checksum_filenames_are_rejected(self) -> None:
        for _, asset, _ in NATIVE_MATRIX:
            with self.subTest(asset=asset):
                binary = self.dist / asset
                original = binary.read_bytes()
                binary.write_bytes(b"tampered")
                result = run_python(self.source, self.root)
                binary.write_bytes(original)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("SHA-256", result.stderr)
                checksum = self.dist / (asset + ".sha256")
                original_checksum = checksum.read_bytes()
                checksum.write_text(hashlib.sha256(original).hexdigest() + "  wrong-filename", encoding="utf-8")
                result = run_python(self.source, self.root)
                checksum.write_bytes(original_checksum)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("filename mismatch", result.stderr)

    def test_empty_binary_is_rejected_even_with_matching_checksum(self) -> None:
        asset = NATIVE_MATRIX[0][1]
        (self.dist / asset).write_bytes(b"")
        (self.dist / (asset + ".sha256")).write_text(hashlib.sha256(b"").hexdigest() + "  " + asset, encoding="utf-8")
        result = run_python(self.source, self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("empty Rust binary", result.stderr)


class PythonReleasePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bash = shutil.which("bash")
        if cls.bash is None:
            raise RuntimeError("Bash is required to test the executable Python release preflight")
        cls.source = inline_script(workflow("publish.yml"), "Validate selected branch, tag, and immutable source")

    def run_preflight(
        self, tag: str, branch: str = "master", ref_type: str = "branch", sha: str = "a" * 40
    ) -> tuple[subprocess.CompletedProcess[str], str]:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = subprocess.run(
                [self.bash, "--noprofile", "--norc", "-c", self.source],
                cwd=directory,
                env={
                    **environ,
                    "RELEASE_TAG": tag,
                    "SELECTED_REF_NAME": branch,
                    "SELECTED_REF_TYPE": ref_type,
                    "SELECTED_SHA": sha,
                    "GITHUB_OUTPUT": output.as_posix(),
                },
                text=True,
                capture_output=True,
                check=False,
                timeout=15,
            )
            return result, output.read_text(encoding="utf-8") if output.exists() else ""

    def test_existing_canonical_tags_and_master_v4_allowlist_are_preserved(self) -> None:
        for branch in ("master", "v4"):
            for tag in ("v4.2.0", "v4.2.0-alpha1", "v4.2.0-beta2", "v4.2.0-rc1", "v50.0.0"):
                with self.subTest(branch=branch, tag=tag):
                    result, output = self.run_preflight(tag, branch)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(output, "release_tag=" + tag + "\n")

    def test_v5_tags_are_rejected_explicitly_before_canonical_validation(self) -> None:
        for branch in ("master", "v4"):
            for tag in ("v5.0.0", "v5.0.0-alpha1", "v5.1.2-beta3", "v5.1.2-rc1", "v5.not-canonical"):
                with self.subTest(branch=branch, tag=tag):
                    result, output = self.run_preflight(tag, branch)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("V5 release tags are reserved for Rust", result.stderr)
                    self.assertEqual(output, "")

    def test_other_refs_invalid_tags_and_nonimmutable_shas_still_fail(self) -> None:
        for arguments in (
            ("v4.2.0", "v5"),
            ("v4.2.0", "main"),
            ("v4.2.0", "feature"),
            ("v4.2.0", "master", "tag"),
            ("v04.2.0",),
            ("v4.02.0",),
            ("v4.2.00",),
            ("v4.2.0-beta01",),
            ("v4.2.0+build",),
            ("v4.2.0", "master", "branch", "deadbeef"),
        ):
            with self.subTest(arguments=arguments):
                result, output = self.run_preflight(*arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(output, "")

    def test_python_publication_remains_manual_and_immutable_draft_based(self) -> None:
        text = workflow("publish.yml")
        triggers = text.split("\non:\n", 1)[1].split("\npermissions:\n", 1)[0]
        self.assertEqual(re.findall(r"(?m)^  (\w+):", triggers), ["workflow_dispatch"])
        self.assertIn("  cancel-in-progress: false", text)
        publication = block(text, "publish-github")
        self.assertIn("    environment:\n      name: publish\n", publication)
        self.assertIn('--draft --verify-tag --generate-notes --title "$RELEASE_TAG"', publication)
        self.assertIn('test "$tag_sha" = "$TARGET_SHA"', publication)
        self.assertIn("require_draft", publication)
        self.assertIn("immutable releases are not modified by this workflow", publication)


if __name__ == "__main__":
    unittest.main()
