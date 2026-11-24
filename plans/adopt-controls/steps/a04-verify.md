---
id: a04-verify
status: pending
depends_on: [a03-probes]
touches:
  - plans/adopt-controls/steps/a04-verify.md
lane: none
tier: light
gate: d=$(mktemp -d) && trap 'rm -rf "$d"' EXIT && git clone -q . "$d/clone" && cd "$d/clone" && python3 scripts/check_context.py && python3 scripts/build_indexes.py --check && python3 scripts/secret_guard.py --tracked && bash scripts/install_hooks.sh --self-test && python3 -m unittest discover -s tests -p 'test_secret_guard.py' && bash scripts/test_docker.sh && cd - >/dev/null && grep -q 'history-findings=[0-9]' plans/adopt-controls/steps/a04-verify.md
requirements: [R4]
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Verify the full gates from a clean clone

## Change

This step changes only its own step file. The gate clones the committed `HEAD` of this worktree into a temporary directory and runs the checks there.

- Do the same checks yourself first. Clone this worktree into a temporary directory outside the repository (`git clone`). In the clone run: `python3 scripts/check_context.py`, `python3 scripts/build_indexes.py --check`, `python3 scripts/secret_guard.py --tracked`, `bash scripts/install_hooks.sh --self-test`, `python3 -m unittest discover -s tests -p 'test_secret_guard.py'` and `bash scripts/test_docker.sh`.
- The Docker gate runs the core tests (`pytest -m 'not integration'`, no device, no network) and then the real FUSE mount run. The mount run needs `/dev/fuse` and the container rights that `scripts/test_docker.sh` sets. It must run the test `test_real_mount_exposes_gx_fixture` with zero skips. The script fails if the test did not run or if one test skipped. Record the test counts of both runs.
- Run `python3 scripts/secret_guard.py --history` in the clone. Record the count of findings. If the count is more than `0`, do not hide it: list the findings by rule and path (never the secret) under "Resume notes", set the status to `blocked` and stop. The owner decides.
- In `evidence`, write each command, its result, the test counts and the UTC date. Also write the token `history-findings=<count>` with the real count (`0` if none) under "Resume notes", in place of `(none)`, before you run the gate. The gate looks for it in this file.
- If the Docker gate or `/dev/fuse` is not available in your session, say so under "Resume notes". Do not claim a pass. The driver runs the whole gate.

## Do not change

- Files outside `touches`. The `gate` command. Any other file in this repository.

## Already done by earlier steps

- a03-probes: the probes, the rollback test and the receipt in `docs/controls-adoption.md`.

## Done when

- The gate passes. The evidence has the commands, the results, the counts, the date and the history count.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

After the operator merges this plan, the operator runs `bash scripts/install_hooks.sh` in the canonical clone.

## Operator change (2026-11-23)

Do not clone, use `mktemp`, or run Docker yourself: agent sessions may not. The gate does all of that: it makes the clean clone in a temporary directory, runs every check and `bash scripts/test_docker.sh` (including the real FUSE mount where the repository has one). Your part:

1. In this worktree, run `python3 scripts/secret_guard.py --history`. Write its finding count on its own line in this file as `history-findings=<count>`. A real secret means stop and set `status: blocked`.
2. Run `python3 scripts/check_context.py` and the repository's host tests that run without Docker. Record the commands and counts below.
3. Commit. The driver then runs the gate, and its log records the Docker and clean-clone results.

## Resume notes

history-findings=0

Host checks run in this worktree on 2026-11-23 (UTC). I did not clone or run Docker, as the operator change says. The gate does that.

- `python3 scripts/secret_guard.py --history`: 0 findings, 0 allowed, 0 unscanned.
- `python3 scripts/check_context.py`: pass (5 checks ok).
- `python3 scripts/build_indexes.py --check`: pass.
- `python3 -m unittest discover -s tests -p 'test_secret_guard.py'`: 21 tests, OK.
