---
name: build-release-maintenance
description: Maintain DDNS GitHub Actions, Docker and Nuitka builds, packaging, installer validation, and release preparation while preserving matrices, caches, and protected publishing.
---

# Build and Release Maintenance

1. Read the root `AGENTS.md` and the current files involved in the task:
   `.github/workflows/`, `docker/`, `.github/patch.py`, `run.py`,
   `pyproject.toml`, and relevant test scripts.
2. Treat current workflow inputs, Dockerfiles, lockfiles, and pinned settings as
   the source of truth. Do not rely on remembered versions, images, runners, or
   matrices.
3. Identify the affected artifact and platform set before editing. Preserve
   Python source, wheel/sdist, native binaries, Linux libc variants, containers,
   installers, and scheduled-task validation unless the task explicitly changes
   support.
4. Keep pull-request cache access restore-only and write shared caches only from
   trusted branches.
5. Make the narrowest coherent change. Do not disable compression, LTO, tests,
   caching, or a platform globally to solve one architecture failure without
   evidence that the policy should change.
6. Reuse existing build and offline E2E scripts. Keep required pull-request
   checks independent of deployed websites and external mutable services.
7. For release preparation, verify version transformations, expected artifact
   names, checksums, release notes, and rerun idempotency.
8. Run the affected package, binary, container, installer, and platform checks,
   then report any matrix entries not exercised.

Do not publish to PyPI, container registries, or GitHub Releases. Do not access
release credentials, modify repository settings, bypass protected environments,
or weaken required checks.
