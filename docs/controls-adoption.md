---
gist: "Read me when: you change or debug the pinned deterministic-controls library, the check_context.py shim, the controls CI job or the Docker shim cache."
---

# Controls adoption

This repository uses the pinned `deterministic-controls` library in advisory mode.
The `controls` CI job is not a required check yet.

## How it works

- `scripts/check_context.py` is a shim. It runs the library `check` command with the
  `ci` profile. It keeps the old output lines (`ok  <script>` or `FAIL <script>`) and
  the exit codes `0` (pass) and `1` (a check failed).
- `scripts/controls-requirements.txt` holds the pin: the install line with the full
  commit of the library. The shim reads the commit from this file.
- `controls.toml` lists the enabled checks.
- Cache path: `$XDG_CACHE_HOME/deterministic-controls/<commit>/`. The default is
  `~/.cache/deterministic-controls/<commit>/`. It holds a virtual environment.
- The first run for a commit needs the network, to build the cache.
- If the library cannot run, the shim exits `2`. It never passes without a result.
  It never falls back to the old check scripts.

## How the adoption was made

1. Audit: step `a01-audit` wrote `docs/controls-audit.json`.
2. Plan: `adopt plan` made a dry run with the pinned commit. A person read the result.
3. Apply: `adopt apply` wrote the shim, the pin file, `controls.toml` and the
   `controls` job. It ran on a clean tree, before any other edit.

The old check scripts, `scripts/build_indexes.py` and `scripts/test_docker.sh` stay.
The `check` job and the `docker` job stay.

## Where the tools did not fit

- **Docker runs have no network.** Both Docker runs use `--network none`. The shim
  needs the network once to build its cache, so the core run would exit `2`.
  Fix: the `Dockerfile` builds the shim cache at image build time, as user
  `tester`, because the cache is under that user's home. The build has network.
- **Extra packages.** The image now has `git` and `python3-venv`. The shim needs
  `venv`. `tests/test_secret_guard.py` needs `git`, and the core run collects it.
- **Pin file header.** `adopt apply` wrote a `Run me when:` line, so no manual
  change was needed.
- **Files outside `touches`.** The re-run of `apply` for the `v0.1.2` pin also
  rewrote `scripts/install_hooks.sh` (a `secretguard.path` fallback). That file is
  outside `touches`, so the change was reverted. A later step or the operator can
  take that change.
- **Stricter index check.** With `v0.1.1`, `context.index-freshness` failed on
  `memory/README.md` and `scripts/README.md`. `v0.1.2` skips folder `README.md`
  files, so the pin moved and no file edit was needed.
- **No Git metadata in the image.** The test image is built from a tar of tracked
  files, with no `.git`. Without a repository the library secret scan reads the
  whole tree, including `.venv` (a generated C file gave a false finding). Fix: the
  `Dockerfile` makes a local Git commit of the copied files before `uv sync`, so
  the scan reads only tracked files, as on the host.

## Secret guard exceptions

none

## Probes

Date of all runs: 2026-11-24 (UTC). Each probe ran in a throwaway Git clone of
`HEAD`, outside the tracked tree. The command was
`python3 -m deterministic_controls check --root <copy> --profile ci --format json`
with the library at the pinned commit. The rule ID comes from the JSON.

| Probe | Expected rule ID | Exit code | Result |
| --- | --- | --- | --- |
| Broken relative link in a new Markdown file | `markdown.local-links` | 1 | Failed with `markdown.local-links.missing-file`. |
| Stale generated index (a script `Run me when:` line changed, index not rebuilt) | `context.index-freshness` | 1 | Failed with `context.index-freshness.stale` on `scripts/AGENTS.md`. |
| Plan step with no `gate` key | `plans.schema` | 1 | Failed with `plans.schema.missing-gate`. |
| Synthetic GitHub-style token in a committed Markdown file | `security.secrets` | 1 | Failed with `security.secrets.github-token`. `security.personal-data.token` also failed. |
| Tracked `driver.out` file | `repo.forbidden-artifacts` | 1 | Failed with `repo.forbidden-artifacts.tracked`. |
| Unreadable file (`chmod 000` on a tracked Markdown file) | none (must not pass) | 3 | Status `error`. Two checks reported `PermissionError`. The run did not pass. |
| Restored clean copy | none | 0 | All seven checks passed. |
| Shim `python3 scripts/check_context.py` with the plan step that has no `gate` | none | 1 | Printed `FAIL check_plan.py`. The shim exit code is `1`. |

Notes:

- The token was built at run time in the shell from random characters. It is not in
  any tracked file or in this table.
- `security.secrets` scans the files at `HEAD`. The token file had to be committed
  in the copy before the check found it. A staged file was not enough.
- A root that is not a directory gives exit `2` (configuration error).
- All probe copies were deleted before the gate ran.

## Rollback

Date of the test: 2026-11-24 (UTC). There is no earlier pin, so the test used the
pre-adoption scripts.

1. The base commit is the parent of the commit that applied the adoption. It has no
   `controls.toml` and no `scripts/controls-requirements.txt`.
2. In a temporary clone, at the base commit, on a clean tree,
   `python3 scripts/check_context.py` passed (exit `0`). It ran the old scripts.
3. In a temporary clone of `HEAD`, on a clean tree, the new shim passed (exit `0`).

To roll back:

1. Option A, change the pin: edit `scripts/controls-requirements.txt` and put the
   earlier commit in the install line. Run `python3 scripts/check_context.py` once
   to build its cache.
2. Option B, remove the adoption: make a new branch. Run `git revert` on the adoption
   commits. Then run `python3 scripts/check_context.py`.

Files that the adoption added: `controls.toml`, `scripts/controls-requirements.txt`,
`docs/controls-adoption.md`.

Files that the adoption changed: `scripts/check_context.py` (now a shim),
`.github/workflows/context.yml` (new `controls` job), `Dockerfile` (shim cache, `git`,
`python3-venv`, a local commit before `uv sync`), `AGENTS.md`, `docs/README.md`,
`scripts/AGENTS.md`.

Files that the adoption kept: `scripts/build_indexes.py`, `scripts/build_context_indexes.py`,
`scripts/check_links.py`, `scripts/check_plan.py`, `scripts/ctx_common.py`,
`scripts/scan_context_secrets.py`, `scripts/scan_secrets.py`, `scripts/test_docker.sh`,
the `check` job and the `docker` job, and the tests.

The cache under `$XDG_CACHE_HOME/deterministic-controls/<commit>/` is safe to delete.
The shim builds it again on the next run, and that run needs the network.

## Receipt

Date of the run: 2026-11-24 (UTC). The command was
`python3 -m deterministic_controls adopt receipt --root <clean clone> --commit 3a2e9f3d95136958c54f73c831e84b971fc9a054`,
run in a clean clone of `HEAD`.

`repository` is the name of the temporary clone, not of the project.
`enforcement_state` is `advisory`: the `controls` CI job is not a required check.
`files_added` and `files_changed` are empty because the clone was made after the
adoption was committed.

```json
{
  "base_revision": "e98c7dd4a542aaa20d8c41749498f2d7f2aa54dd",
  "checks_run": [
    {"check_id": "context.index-freshness", "status": "passed"},
    {"check_id": "markdown.local-links", "status": "passed"},
    {"check_id": "plans.graph", "status": "passed"},
    {"check_id": "plans.schema", "status": "passed"},
    {"check_id": "repo.forbidden-artifacts", "status": "passed"},
    {"check_id": "security.personal-data", "status": "passed"},
    {"check_id": "security.secrets", "status": "passed"}
  ],
  "commands_kept": [
    "scripts/build_context_indexes.py",
    "scripts/build_indexes.py",
    "scripts/check_links.py",
    "scripts/check_plan.py",
    "scripts/ctx_common.py",
    "scripts/scan_context_secrets.py",
    "scripts/scan_secrets.py",
    "scripts/test_docker.sh",
    "test: python3 -m unittest discover -s tests",
    "test: docker build (Dockerfile)",
    "ci-job: check",
    "ci-job: docker"
  ],
  "control_pin": "3a2e9f3d95136958c54f73c831e84b971fc9a054",
  "date": "2026-11-24",
  "enabled_checks": [
    "context.index-freshness",
    "markdown.local-links",
    "plans.graph",
    "plans.schema",
    "repo.forbidden-artifacts",
    "security.personal-data",
    "security.secrets"
  ],
  "enforcement_state": "advisory",
  "files_added": [],
  "files_changed": [],
  "profile": "ci",
  "repository": "base",
  "rollback": [
    "To restore the previous pin: edit scripts/controls-requirements.txt, put the previous commit in the install line, and run scripts/check_context.py once to build its environment.",
    "To remove the adoption: run 'git revert' on the adoption commit, or restore these files from the base revision e98c7dd4a542aaa20d8c41749498f2d7f2aa54dd with 'git checkout e98c7dd4a542aaa20d8c41749498f2d7f2aa54dd -- <file>' and delete the files that were added: scripts/check_context.py, scripts/controls-requirements.txt, controls.toml, scripts/secret_guard.py, scripts/install_hooks.sh, .github/workflows/context.yml.",
    "The cached environment is in the user cache directory under deterministic-controls/<commit>/. It is safe to delete."
  ],
  "schema_version": 1
}
```
