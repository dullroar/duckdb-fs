---
id: 02-build-and-test
status: done
depends_on: [01-adopt-context]
touches:
  - Dockerfile
  - .dockerignore
  - README.md
  - scripts/test_docker.sh
  - scripts/AGENTS.md
  - .github/workflows/context.yml
  - plans/ralphify/steps/02-build-and-test.md
lane: none
requirements: [R2]
gate: bash scripts/test_docker.sh && python3 scripts/check_context.py && git diff --check
evidence: "2026-11-22 UTC. Docker build, context checks, 23 core tests, and 1 FUSE mount test passed. See Validation evidence."
---

# 02-build-and-test

Depends on `01-adopt-context`. Add a project Dockerfile, an appropriate `.dockerignore`, and `scripts/test_docker.sh`. Use project dependencies and current lockfiles. Run project tests as a normal container user where supported. Use synthetic fixtures, a temporary output directory, and no developer credentials. Put any new operational or test artifacts under the repo's existing conventions. Document build, test, and any device or platform requirements in `README.md`. Keep existing host usage working. Arrange for CI to call the same entry point wherever the runner supports that gate.

The Docker test script builds the image from the current step worktree and runs the repo-specific gates inside it. For context checks, use a complete source snapshot or an appropriate read-only checkout that works with linked Git worktrees. A linked worktree's `.git` pointer alone does not provide its Git metadata in the container. Keep the image usable without a sibling checkout, host venv, or mutable shared volume. Use repo- and run-specific names for any image tags, container names, and writable paths. Build dependencies can use package registries. The default test runtime uses local fixtures and an isolated container network. The FUSE mount gate is required for the two FUSE lanes, with the host requirements in their repo briefs.

Touches `Dockerfile`, `.dockerignore`, `README.md`, `scripts/test_docker.sh`, generated indexes, any necessary workflow updates, focused test/support paths from the repo brief, and this step file. Gate: `bash scripts/test_docker.sh && python3 scripts/check_context.py && git diff --check`.

## Repository gate

Use `uv.lock` and the existing FUSE 3 build dependencies. Run `uv run --locked pytest -m 'not integration'` and run `DUCKDB_FS_RUN_FUSE_TESTS=1 uv run --locked pytest -m integration` in a FUSE-capable Docker invocation. Verify actual reads through the mounted filesystem using the committed GX fixture. Gate on a passing test with no mount-test skip. Keep the core test run device-free. Give the mount run its own disposable mountpoint and remove it on exit. Document `/dev/fuse` and the minimum container permissions that the tested host needs. Preserve the host CLI and output schema.

## Validation evidence

- The protected gate passed on 2026-11-22 UTC. The image built from the linked
  worktree with `uv sync --locked`. The in-container and host context checks
  passed, and `git diff --check` reported no errors.
- The device-free run passed 23 core tests and deselected the mount test.
  The FUSE run passed the real mount test, deselected the 23 core tests, and
  reported zero skips. The test verified the bytes of the mounted GX CSV.
- The tested Linux Docker host provided `/dev/fuse` and used the default
  seccomp profile. The mount test used the device and `SYS_ADMIN` and
  ran as the image's normal user. The host did not use AppArmor.
