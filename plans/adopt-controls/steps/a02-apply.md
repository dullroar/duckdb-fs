---
id: a02-apply
status: done
depends_on: [a01-audit]
touches:
  - scripts/check_context.py
  - scripts/controls-requirements.txt
  - controls.toml
  - .github/workflows/context.yml
  - Dockerfile
  - scripts/AGENTS.md
  - plans/AGENTS.md
  - AGENTS.md
  - docs/controls-adoption.md
  - docs/README.md
  - plans/adopt-controls/steps/a02-apply.md
lane: none
gate: python3 scripts/check_context.py && python3 scripts/build_indexes.py --check && python3 scripts/secret_guard.py --tracked && grep -q '3a2e9f3d95136958c54f73c831e84b971fc9a054' scripts/controls-requirements.txt && test -s controls.toml && grep -q '^  check:' .github/workflows/context.yml && grep -q '^  docker:' .github/workflows/context.yml && grep -q 'secret_guard.py --tracked' .github/workflows/context.yml && ! grep -q 'continue-on-error' .github/workflows/context.yml && ! grep 'uses:' .github/workflows/context.yml | grep -vqE '@[0-9a-f]{40}' && grep -q 'cheapest executor' AGENTS.md && grep -q 'controls-adoption.md' docs/README.md && bash scripts/test_docker.sh && git diff --check
requirements: [R2]
claimed_by: claude cli-default
claimed_at: "2026-11-24T02:17:34Z"
evidence: gate passed 2026-11-24 (driver-verified)
---

# Adopt the pinned library in advisory mode

This is the first real use of the adoption tools in this repository. Record each place where they did not fit in `docs/controls-adoption.md`, under "Where the tools did not fit". That text goes to the lessons of the program.

## Change

- Run `python3 -m deterministic_controls adopt plan --root . --commit 3a2e9f3d95136958c54f73c831e84b971fc9a054` (a dry run). Read the plan. Then run `adopt apply` with the same `--commit`. Run `apply` before any other edit, because it needs a clean tree. Keep its commit on this step branch. Use `adopt --help` for the other options. Do not install the library (see "Facts" in `plan.md`).
- Result: `scripts/check_context.py` is the shim. `scripts/controls-requirements.txt` has the pinned install line (add a `Run me when:` line if `apply` left it out). `controls.toml` exists.
- The shim keeps the old output lines (`ok  <script>` or `FAIL <script>`) and the exit codes `0` and `1`. It gives exit `2` if the library cannot run.
- If `apply` writes a file outside `touches`, revert that file and record it under "Where the tools did not fit".
- Keep all old check scripts. Keep `scripts/build_indexes.py` and `scripts/test_docker.sh`. Run `python3 scripts/build_indexes.py` to refresh `scripts/AGENTS.md` and `plans/AGENTS.md`.
- `.github/workflows/context.yml`: keep the `check` job and the `docker` job with all their steps. Keep the workflow name `context`. The new `controls` job is advisory: it is not required in branch protection, and it must fail honestly (no `continue-on-error`). It has `permissions: contents: read`, no secrets, and every action pinned to a full 40-character SHA with the tag in a trailing comment.
- `Dockerfile`: both Docker runs have no network. The core run executes `python3 scripts/check_context.py` as user `tester`. The shim needs the network once for the pinned commit. So prepare the shim cache at image build time (the build has network), for `tester` (the cache is under that user's home). The image needs `git` (for the shim install and for `tests/test_secret_guard.py`, which `pytest` collects in the core run) and the Python `venv` module (`python3-venv`). Add them to the existing `apt-get install` line, as root, before `USER tester`. Do not change `scripts/test_docker.sh`, the run commands, `--network none`, the FUSE options or the `uv sync --locked` layer. The mount run uses `/work/.venv`. Keep it working.
- `AGENTS.md`: add this standing rule, in Simplified Technical English, and keep all existing rules: "Do not weaken the controls. You may run the local checks at any time. CI runs them in all cases. Do not change or disable the controls, the pin (`scripts/controls-requirements.txt`), `controls.toml` or the workflows to make an unrelated task pass. The driver checks the gate and `touches` of each step. A change to the gate or a file outside `touches` fails the step. Send each piece of work to the cheapest executor that can do it, and let the gate decide if the work is done. The full policy is at https://github.com/dullroar/ralph-looper/blob/main/docs/routing.md."
- `docs/controls-adoption.md`: write it by hand. Sections: "How it works" (shim, pin, cache path, first run needs the network, exit `2` if the library cannot run), "How the adoption was made" (audit, plan, apply), "Where the tools did not fit" (include the Dockerfile change and why), "Secret guard exceptions" (`none`, or a list). Add one line for it to `docs/README.md`. Step `a03-probes` adds the probes, the rollback and the receipt.
- Do not change product code (`src/` or the package), the existing tests, the host CLI or the output schema.

## Do not change

- Files outside `touches`. The `gate` command.
- Do not make the shim fall back to the old scripts. Do not add a secret guard exception.

## Already done by earlier steps

- a00-secret-guard: the guard, the hooks, the guard test and the guard steps in the workflow. a01-audit: `docs/controls-audit.json`.

## Done when

- The gate passes, including `bash scripts/test_docker.sh` (core run, and the mount run with no skip). If your session cannot run Docker or has no `/dev/fuse`, run the other parts of the gate and say so in "Resume notes". The driver runs the whole gate.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Operator change (2026-11-23)

The pin moved to `v0.1.2` (`3a2e9f3d95136958c54f73c831e84b971fc9a054`). `v0.1.2` fixes the blocker above: `context.index-freshness` now skips `README.md` in `memory/` and `scripts/`, so do not edit those files. Re-run `python3 -m deterministic_controls adopt apply --root . --commit 3a2e9f3d95136958c54f73c831e84b971fc9a054`. It changes only the pin in `scripts/controls-requirements.txt`. Keep the rest of the applied work. Then run the gate, including `bash scripts/test_docker.sh`.

## Resume notes

Resolved on 2026-11-23: pin moved to v0.1.2, `apply` re-run (reverted its `scripts/install_hooks.sh` change, outside touches), and the Dockerfile now commits the copied files so the secret scan skips `.venv`. Earlier note (obsolete): Blocked on scope. Work done: `adopt apply` (shim, pin, `controls.toml`, `controls` job), Dockerfile cache and packages, `AGENTS.md` rule, `docs/controls-adoption.md`, `docs/README.md` line.

The gate fails at `python3 scripts/check_context.py` (exit 1). The library check `context.index-freshness` reports:

- `memory/README.md` has no `gist` front matter.
- `scripts/README.md` has no `Run me when:` line in its first 25 lines.

The old `build_indexes.py --check` passes. The library is stricter. Both files are outside `touches`, so this step cannot fix them. A fix needs these two files in `touches` of this step (or a decision to exclude them in `controls.toml`, which weakens the check). Re-checked on 2026-11-23: same result. `check_context.py` still exits 1, and a search finds no `gist` in `memory/README.md` and no `Run me when:` in `scripts/README.md`. Needed decision: add `memory/README.md` and `scripts/README.md` to `touches` of this step. Not run: `bash scripts/test_docker.sh` (the core run calls `check_context.py`, which fails).
