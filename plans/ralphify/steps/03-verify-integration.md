---
id: 03-verify-integration
status: done
depends_on: [02-build-and-test]
touches:
  - plans/ralphify/steps/03-verify-integration.md
lane: none
requirements: [R3]
gate: python3 scripts/check_context.py && bash scripts/test_docker.sh && git diff --check
evidence: gate passed 2026-11-22 (driver-verified)
claimed_by: codex cli-default
claimed_at: "2026-11-22T20:24:04Z"
---

# 03-verify-integration

Depends on `02-build-and-test`. Update only the step file. Rerun the context and Docker gate from the integrated worktree as the driver would. Check the template and runner links in `AGENTS.md` and the structural-change rule. Verify README commands and the existing entry points. Record the worktree base commit, exact commands, build result, test counts or concrete smoke assertions, expected opt-in skips, real FUSE result where required, and UTC date. Keep logs outside Git. Gate: `python3 scripts/check_context.py && bash scripts/test_docker.sh && git diff --check`.

The driver writes its own `evidence` field. Put detailed test evidence in the body of the verification step and commit it. The parent verifies the final child commit and result. A green build alone cannot satisfy R2 or R3.

## Repository gate

Use `uv.lock` and the existing FUSE 3 build dependencies. Run `uv run --locked pytest -m 'not integration'` and run `DUCKDB_FS_RUN_FUSE_TESTS=1 uv run --locked pytest -m integration` in a FUSE-capable Docker invocation. Verify actual reads through the mounted filesystem using the committed GX fixture. Gate on a passing test with no mount-test skip. Keep the core test run device-free. Give the mount run its own disposable mountpoint and remove it on exit. Document `/dev/fuse` and the minimum container permissions that the tested host needs. Preserve the host CLI and output schema.

Run `git merge-base HEAD plan/ralphify` to identify the integrated base commit. Replace each pending value in the results below. For each passing check, put details after `PASS`. Include the actual Docker commands or image reference and test counts or concrete smoke results. Record `n/a` in the FUSE field for other repos. If a required test fails or skips, record that in resume notes and leave the result pending.

## Results

- Base commit: `15809e3a572d64bc86376f5c0faec8428ccccadd` from
  `git merge-base HEAD plan/ralphify`.
- Commands: PASS. `python3 scripts/check_context.py && bash scripts/test_docker.sh && git diff --check`.
  The host and container context checks passed. `git diff --check` reported no errors.
- Docker build: PASS. The linked worktree built `duckdb-fs-test:RokhXGPu`
  with FUSE 3 dependencies and `uv sync --locked`. The standalone README
  build command also built `duckdb-fs:build-15285`.
- Tests: PASS. `uv run --offline --locked pytest -m 'not integration'`
  passed 23 tests in an offline container with no FUSE device. The FUSE
  container passed 1 test with `DUCKDB_FS_RUN_FUSE_TESTS=1` and
  `uv run --offline --locked pytest -m integration`.
- Skips: PASS. The core run deselected 1 test and the FUSE run deselected
  23 tests. The gate reported zero skips. A separate `uv run pytest -rs`
  passed 23 tests and skipped only the real mount test because the opt-in
  variable was unset.
- FUSE: PASS. The mount test read
  `summary/status=FAIL/table=CUSTOMERS/CUSTOMERS_summary.csv` from the mount
  and matched its bytes to the committed GX fixture. The container used
  `--network none --device /dev/fuse --cap-add SYS_ADMIN`, the image's normal
  user, and the host's default seccomp profile. The Docker host did not use
  AppArmor. The test script removed the temporary test directory on exit.
- UTC date: 2026-11-22.

## Entry points

- Both upstream links in `AGENTS.md` resolved, and the pinned runner guide
  in `docs/README.md` resolved. `AGENTS.md` requires a review of both upstream
  repositories before a structure change and lists the topics to account for.
- `uv run duckdb-fs mount --help` and `uv run duckdb-fs unmount --help`
  passed in the README build image. The mount test also used the
  `python -m duckdb_fs.cli` entry point to mount and unmount the fixture.
  The migration left the package configuration, lockfile, product source,
  and test suite unchanged.
- The Ralph runner help lists the README options `--repo`, `--plan`,
  `--status`, `--agent codex`, and `--jobs 1`. Its status helper read the
  integrated plan and reported two done steps and one pending step. The full
  `--status` command from this linked worktree used the step directory name
  as the repository name and could not reuse the existing plan worktree.
  Verification of the launch command was limited to its documented syntax
  because the driver was already running this plan.
