---
id: 03-verify-integration
status: pending
depends_on: [02-build-and-test]
touches:
  - plans/ralphify/steps/03-verify-integration.md
lane: none
requirements: [R3]
gate: python3 scripts/check_context.py && bash scripts/test_docker.sh && git diff --check
evidence: ""
---

# 03-verify-integration

Depends on `02-build-and-test`. Update only the step file. Rerun the context and Docker gate from the integrated worktree as the driver would. Check the template and runner links in `AGENTS.md` and the structural-change rule. Verify README commands and the existing entry points. Record the worktree base commit, exact commands, build result, test counts or concrete smoke assertions, expected opt-in skips, real FUSE result where required, and UTC date. Keep logs outside Git. Gate: `python3 scripts/check_context.py && bash scripts/test_docker.sh && git diff --check`.

The driver writes its own `evidence` field. Put detailed test evidence in the body of the verification step and commit it. The parent verifies the final child commit and result. A green build alone cannot satisfy R2 or R3.

## Repository gate

Use `uv.lock` and the existing FUSE 3 build dependencies. Run `uv run --locked pytest -m 'not integration'` and run `DUCKDB_FS_RUN_FUSE_TESTS=1 uv run --locked pytest -m integration` in a FUSE-capable Docker invocation. Verify actual reads through the mounted filesystem using the committed GX fixture. Gate on a passing test with no mount-test skip. Keep the core test run device-free. Give the mount run its own disposable mountpoint and remove it on exit. Document `/dev/fuse` and the minimum container permissions that the tested host needs. Preserve the host CLI and output schema.

Run `git merge-base HEAD plan/ralphify` to identify the integrated base commit. Replace each pending value in the results below. For each passing check, put details after `PASS`. Include the actual Docker commands or image reference and test counts or concrete smoke results. Record `n/a` in the FUSE field for other repos. If a required test fails or skips, record that in resume notes and leave the result pending.

## Results

- Base commit: PENDING
- Commands: PENDING
- Docker build: PENDING
- Tests: PENDING
- Skips: PENDING
- FUSE: PENDING
- UTC date: PENDING
