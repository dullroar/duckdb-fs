# duckdb-fs

`duckdb-fs` is a read-only FUSE filesystem over the CSV output of
[metadata-driven-gx](https://github.com/dullroar/metadata_driven_gx). A directory
represents a faceted query. For example:

```text
/summary/status=FAIL/table=CUSTOMERS/column=LAST_NAME/
```

means the conjunction `status = FAIL AND table = CUSTOMERS AND column = LAST_NAME`.
The directory contains every remaining, nonempty facet and every original summary
CSV with at least one matching row. Opening `CUSTOMERS_summary.csv` returns that
original, unfiltered CSV artifact.

## Why a filesystem?

The goal is to make the ordinary **File | Open** dialog the ultimate searchable data
access UI. Every desktop application, shell, script, and file browser already knows
how to enumerate folders and open files; duckdb-fs gives that universal interface a
faceted-query vocabulary. A user can drill from `status=FAIL` to a table, column, and
expectation without knowing SQL, DuckDB, Great Expectations, or a bespoke data-catalog
application. The resulting path is also a portable, addressable serialized query that
can be pasted into a terminal, passed to another program, or reopened later.

`summary/` and `details/` are deliberately separate collections. Summary rows are
one expectation result each; detail rows are exploded failure evidence and can have
different natural-key columns from suite to suite.

## Mount

```bash
uv sync --all-groups
mkdir /tmp/duckdb-fs-mount
uv run duckdb-fs mount \
  --input-root ../metadata_driven_gx/environments/demo_weather/output \
  --mountpoint /tmp/duckdb-fs-mount
```

In another terminal:

```bash
ls /tmp/duckdb-fs-mount/summary/status=FAIL/table=CUSTOMERS
cat /tmp/duckdb-fs-mount/summary/status=FAIL/table=CUSTOMERS/CUSTOMERS_summary.csv
```

Unmount with `uv run duckdb-fs unmount --mountpoint /tmp/duckdb-fs-mount`.
If a process does not exit normally, `fusermount3 -u /tmp/duckdb-fs-mount` is the
normal recovery command; `fusermount3 -uz` is the deliberate lazy-unmount fallback.

## GX input contract

`--input-root` is the extractor's `output/` directory. duckdb-fs discovers
`**/*_summary.csv` and `**/*_details.csv` beneath it. It requires a non-empty
summary corpus and ignores zero-byte details CSVs, which the extractor intentionally
emits when a suite has no detail failures.

The file set, size, and modification times are captured at mount. If GX rewrites a
source CSV, the mount reports an I/O error for subsequent catalog/evidence access;
remount it to establish a new corpus. Do not run GX against an output tree while it
is mounted.

Summary facets are `status` (`PASS`, `FAIL`, or `ERROR`), `table`, `column`,
`expectation_type`, `severity`, `test_category`, `result_type`, `rule_kind`,
`environment_name`, and day-normalized `run_date`. Details expose only reliable
fields: `table`, `column`, `expectation_type`, `environment_name`, and `run_date`.

## Development and FUSE prerequisites

```bash
uv run pytest
DUCKDB_FS_RUN_FUSE_TESTS=1 uv run pytest -m integration
```

The integration test requires a working FUSE 3 device. On the observed Ubuntu WSL2
environment, install `fuse3`, `libfuse3-dev`, and `pkg-config`; if `/dev/fuse` is
absent, an administrator must load the FUSE module and create the device before a
normal user can mount.

## Docker build and test

Use a Linux Docker Engine with access to the package registries for the build.
From the repository root, build the image from the current worktree:

```bash
git ls-files --cached -z |
  tar --create --file=- --no-recursion --owner=0 --group=0 --numeric-owner \
    --null --files-from=- |
  docker build --tag "duckdb-fs:build-$$" -
```

The snapshot uses the worktree contents of the paths in the Git index. Stage
new files or deletions before building. The build also works in a linked Git
worktree.

```bash
bash scripts/test_docker.sh
```

The script builds its own image and runs the context checks and core tests as
a normal user, with the network disabled and no FUSE device. A second offline
container mounts the committed GX fixture at a temporary path and verifies
that the mounted CSV matches the fixture. A skipped mount test fails the gate.

The mount container requires a readable and writable `/dev/fuse` on the Docker
host and the `SYS_ADMIN` capability for `fusermount3`. On a Docker Engine that
uses AppArmor, the script also sets `apparmor=unconfined` for the mount container
so it can mount the filesystem. Both containers and the test image tag are
removed after the run.

## Run the Ralph plan

With `ralph-looper` installed, run from the repository root:

```bash
ralph-looper --repo "$PWD" --plan ralphify --status
ralph-looper --repo "$PWD" --plan ralphify --agent codex --jobs 1
```

See [docs/design/](docs/design/README.md) for the constraints and non-goals.
