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
- **Files outside `touches`.** `apply` wrote none.
- **Stricter index check.** The library `context.index-freshness` check finds two
  files that the old `build_indexes.py --check` accepts: `memory/README.md` (no
  `gist` front matter) and `scripts/README.md` (no `Run me when:` line). The old
  scripts did not scan these files. They must be fixed before the shim passes.

## Secret guard exceptions

none
