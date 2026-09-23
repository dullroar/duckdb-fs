# duckdb-fs

`duckdb-fs` is a read-only FUSE filesystem over the CSV output of
[metadata-driven-gx](../metadata_driven_gx). Directories are faceted queries, not
physical containment. For example:

```text
/summary/status=FAIL/table=CUSTOMERS/column=LAST_NAME/
```

means the conjunction `status = FAIL AND table = CUSTOMERS AND column = LAST_NAME`.
The directory contains every remaining, nonempty facet and every original summary
CSV with at least one matching row. Opening `CUSTOMERS_summary.csv` returns that
original, unfiltered CSV artifact.

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

See [DESIGN.md](DESIGN.md) for the constraints and non-goals.
