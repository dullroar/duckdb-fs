---
id: a03-probes
status: pending
depends_on: [a02-apply]
touches:
  - docs/controls-adoption.md
  - plans/adopt-controls/steps/a03-probes.md
lane: none
gate: python3 scripts/check_context.py && python3 scripts/build_indexes.py --check && python3 scripts/secret_guard.py --tracked && grep -q '^## Probes' docs/controls-adoption.md && grep -q '^## Rollback' docs/controls-adoption.md && grep -q '^## Receipt' docs/controls-adoption.md && for id in markdown.local-links context.index-freshness plans.schema security.secrets repo.forbidden-artifacts; do grep -q "$id" docs/controls-adoption.md || exit 1; done && grep -q '"control_pin": "0323de273a158608f7280867e12994141bccd1e6"' docs/controls-adoption.md && git diff --check
requirements: [R3]
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Prove the controls with known-bad probes, test the rollback and write the receipt

## Change

Work in `docs/controls-adoption.md` only. Do all probes in a temporary copy outside the repository (`mktemp -d`). Make the copy from the tracked files of `HEAD` (`git archive`) in a new Git repository with one commit. Never probe in this worktree.

- `## Probes`: a table with one row for each probe: the probe, the expected rule ID, the exit code and the result. In the copy, run `python3 -m deterministic_controls check --root <copy> --profile ci --format json` and read the rule ID from the JSON. Probes:
  - a broken relative link in a Markdown file: `markdown.local-links`.
  - a stale generated index (change a script, do not rebuild): `context.index-freshness`.
  - a plan step without `gate`: `plans.schema`.
  - a synthetic token in a Markdown file: `security.secrets`. Build the token at run time in the shell. Never write the token in any tracked file, in the step file or in the table.
  - a tracked `driver.out` file: `repo.forbidden-artifacts`.
  - an internal error (an unreadable file, or a forced exception): the check must not pass. Record the exit code (`2` or `3`).
  Each bad probe must fail with the expected rule ID. Then restore the copy and check that it passes (exit `0`). Also run `python3 scripts/check_context.py` (the shim) in the copy for the bad plan step and record that its exit code is `1`.
- `## Rollback`: test it. There is no earlier pin, so use the pre-adoption scripts. The base commit is the parent of the `adopt apply` commit (find it with `git log`). In a temporary clone, check out that commit and run its `python3 scripts/check_context.py` on the clean tree. Then run the new shim on the clean tree of `HEAD`. Record that both pass. Write the steps to roll back: change the pin, or `git revert` the adoption commits on a new branch (list the files that the adoption added, changed and kept), then run `python3 scripts/check_context.py`. Say that the cache under `$XDG_CACHE_HOME/deterministic-controls/<commit>/` is safe to delete.
- `## Receipt`: run `python3 -m deterministic_controls adopt receipt --root <clean clone> --commit 0323de273a158608f7280867e12994141bccd1e6` in a clean clone of `HEAD`. Put the JSON in a fenced `json` block. Say that `repository` is the name of the temporary clone. Say that `enforcement_state` is `advisory`.
- Record the UTC date of each run. Do not write local paths or user names in the file.

## Do not change

- Files outside `touches`. The `gate` command.
- Do not add a secret guard exception.

## Already done by earlier steps

- a02-apply: the shim, the pin, `controls.toml`, the CI job, the Dockerfile change and the first text of `docs/controls-adoption.md`.

## Done when

- The gate passes. Each bad probe fails for the expected reason. The good copy passes. The rollback result is recorded.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
