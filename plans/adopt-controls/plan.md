---
gist: "Read me when: you adopt the pinned deterministic-controls library and the secret guard in duckdb-fs, in advisory mode, with the Docker core run and the FUSE mount run kept."
---

# Plan: adopt the pinned controls in duckdb-fs

This file is the high-level plan. State requirements in [spec.md](./spec.md). The detail is in `steps/`. Every step is self-contained. Read this file for the shared facts.

## Approach

The repository came from `repo-template`. It has the old context checks (`scripts/check_context.py` and the scripts that it runs), a Dockerfile, `scripts/test_docker.sh` and a CI workflow with two jobs (`check` and `docker`). The library `deterministic-controls` gives the same checks from one pinned release. `scripts/check_context.py` becomes a shim that runs the library. The adoption is advisory: the CI job is not required yet. Keep all existing scripts, gates and CI job names. Do not delete the old check scripts in this plan.

Order: secret guard first (a00), then a read-only audit (a01), then the adoption (a02), then probes, rollback and receipt (a03), then verification from a clean clone with the Docker gate (a04).

## Facts

- Library: `deterministic-controls` `v0.1.1`. Install line: `python3 -m pip install "deterministic-controls @ git+https://github.com/dullroar/deterministic-controls@0323de273a158608f7280867e12994141bccd1e6"`. The commit is `0323de273a158608f7280867e12994141bccd1e6`. Pass it as `--commit` to `adopt plan`.
- Commands: `python3 -m deterministic_controls {list,check,explain,version,adopt}`. `adopt` has `audit`, `plan`, `apply` and `receipt`. `check --root DIR --profile quick|ci|full [--format text|json] [--report FILE]`. Exit codes: `0` pass, `1` defects, `2` bad configuration, invocation or no result, `3` internal error. Use `--help` for details.
- **No installs in agent steps.** An agent session has no network and no install right. Do not create a virtual environment and do not run `pip install`. The operator puts a checkout of the pinned release on `PYTHONPATH`, so `python3 -m deterministic_controls ...` works in a step. If it does not work, write that under "Resume notes" and stop.
- The shim (`scripts/check_context.py`) runs the library from a cached virtual environment for the pinned commit, under `$XDG_CACHE_HOME/deterministic-controls/<commit>/` (default `~/.cache/...`). The first run for a commit needs the network. If the library cannot run, the shim exits `2`. It never passes without a result and never falls back to the old scripts.
- `adopt apply` works only on a clean tree and on the current branch. It never pushes. It is idempotent. Run it before any other edit of the step.
- `adopt apply` writes `scripts/controls-requirements.txt`. If that file has no `Run me when:` line in its first 25 lines, add one. Then `python3 scripts/build_indexes.py --check` passes.
- `adopt apply` does not write `docs/controls-adoption.md`. Write it by hand.
- `adopt apply` adds a `controls` job next to the existing jobs. Keep the `check` job and the `docker` job and their steps. Do not delete the old jobs in this plan.
- Do not compare literal versions or wheel digests in tests or docs. Assert behavior and exit codes.
- Run the full test suite that the step names before each commit, not only one test file.
- Routing in one sentence (for `AGENTS.md`): send each piece of work to the cheapest executor that can do it, and let the gate decide if the work is done.
- Base branch: `main`.

## Repository brief

This text is copied from the archived repository-specific Docker gates.

> Use `uv.lock` and the existing FUSE 3 build dependencies. Run `uv run --locked pytest -m 'not integration'` and run `DUCKDB_FS_RUN_FUSE_TESTS=1 uv run --locked pytest -m integration` in a FUSE-capable Docker invocation. Verify actual reads through the mounted filesystem using the committed GX fixture. Gate on a passing test with no mount-test skip. Keep the core test run device-free. Give the mount run its own disposable mountpoint and remove it on exit. Document `/dev/fuse` and the minimum container permissions that the tested host needs. Preserve the host CLI and output schema.

The Docker gate in the repository today is `bash scripts/test_docker.sh`. It builds the image from the tracked files (`Dockerfile`: Ubuntu 24.04, FUSE 3 build packages, `uv sync --locked`). Then it runs two containers, both with `--network none`:

```bash
# core run (no device)
bash -ec "python3 scripts/check_context.py && uv run --offline --locked pytest -m 'not integration'"
# mount run (--device /dev/fuse --cap-add SYS_ADMIN, DUCKDB_FS_RUN_FUSE_TESTS=1)
/work/.venv/bin/python -m pytest -m integration --basetemp "$test_dir/pytest" --junitxml "$test_dir/results.xml"
```

The script then fails unless the mount test `test_real_mount_exposes_gx_fixture` ran and nothing skipped. Keep both runs, their commands and the no-skip rule unchanged.

Local rules:

- Keep the device-free core run separate from the mount run.
- Keep the host CLI and the output schema. The tests in `tests/` use the pinned fixture `tests/fixtures/demo_weather_output/`.
- `pytest` collects `tests/` (see `testpaths` in `pyproject.toml`). A new file in `tests/` joins the core run inside the container.

## Steps

| Step | Executor | Goal | Depends on |
| --- | --- | --- | --- |
| [a00-secret-guard](./steps/a00-secret-guard.md) | cloud agent, light | Secret guard, hooks and a blocking CI step. | none |
| [a01-audit](./steps/a01-audit.md) | script | Read-only audit with the pinned library. | a00 |
| [a02-apply](./steps/a02-apply.md) | cloud agent | Adopt the library in advisory mode. Keep all gates. | a01 |
| [a03-probes](./steps/a03-probes.md) | cloud agent | Known-bad probes, rollback test and receipt. | a02 |
| [a04-verify](./steps/a04-verify.md) | cloud agent, light | Full gates from a clean clone, including Docker and FUSE. | a03 |

## Parallelism

None. The steps run one after the other. Each step changes files that the next step reads.

## Risks

- **A secret is committed.** `a00` installs the guard first. Do not add an exception to pass a step. A new exception needs a reason and a fingerprint, and the owner reviews it.
- **The shim cannot get the library (no network).** Write that under "Resume notes" and stop. Do not change the gate. Do not use the old scripts as a replacement.
- **The Docker runs have no network.** The shim cannot build its cache in the container. The guard test needs `git`. `a02` fixes both at image build time.
- **The audit says `blocked`.** `a01` fails. Stop for review. Do not force it.
- **The mount test skips.** The gate then fails. Do not weaken the check. Record the host facts and stop.
