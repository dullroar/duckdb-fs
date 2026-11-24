# Goal: adopt the pinned controls in duckdb-fs

## Ralph loop prompt

Use this prompt for each loop iteration. It has no chat history, so keep it complete.

> You work on plan `adopt-controls` in this repository. Read `AGENTS.md`, then `plans/adopt-controls/goal.md` and `plan.md`.
> Open the step file you were given. Work only in the worktree you were given, on its branch.
> Do only that step. Change only the files in `touches`.
> Run the full test suite that the step names and the `gate` command. If one fails, find the cause and fix it. Do not weaken or delete the gate.
> When the gate passes, set `status: done` and write `evidence` (command, result, date). Commit.
> If you cannot finish, keep `status: in_progress`, write what remains under "Resume notes" in the step file, and commit.
> If you are blocked, set `status: blocked` and write the reason. Do not guess.
> Never push, publish, change a remote or change a GitHub setting. Never run `ralph-pusher`.
> Never write secrets or personal data in any file. Write in Simplified Technical English.

## Goal

`duckdb-fs` is a read-only FUSE projection of Great Expectations extractor facts. This plan gives it the pinned `deterministic-controls` library and a blocking secret guard. The adoption is advisory: the new CI job is not a required check yet. All existing gates, entry points and CI job names stay.

The library is `v0.1.1` at a pinned commit. Install line:

`python3 -m pip install "deterministic-controls @ git+https://github.com/dullroar/deterministic-controls@0323de273a158608f7280867e12994141bccd1e6"`

## Done when

- `python3 scripts/check_context.py` passes. It runs the pinned library through a shim.
- `bash scripts/test_docker.sh` passes. The core run has no network. The real FUSE mount test runs with zero skips.
- The secret guard runs in CI (`--tracked`, and `--range` on pull requests) and in the pre-commit and pre-push hooks.
- Known-bad probes fail with the expected rule ID. The rollback is tested.
- `docs/controls-adoption.md` has the receipt and the rollback.
- Every step of this plan is `done` with evidence.

## Out of scope

- Any other repository. Pushing, publishing, changing a remote or a GitHub setting.
- Required checks and branch protection. The operator does that later.
- Changes to product code, to the tests that exist, to the host CLI or to the output schema.
- Changes to the pinned library.
