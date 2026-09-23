# duckdb-fs design

## Purpose

duckdb-fs projects immutable Great Expectations extractor facts through the universal
filesystem interface. It is a query UI: a path is progressive set intersection, and
the backing output tree need not resemble the navigation hierarchy.

```text
GX extractor CSVs -> DuckDB query catalog -> FUSE -> File | Open
```

The intended user interface is not a custom search page: it is the File | Open dialog
already embedded in nearly every desktop application. Filesystems are a mature common
protocol for enumerate, open, read, seek, and stat. Projecting faceted queries through
that protocol lets someone progressively select the dimensions that matter—failure,
table, column, expectation—until the relevant evidence appears, without learning SQL
or adopting a catalog-specific client. The path is a portable serialized query rather
than transient checkbox state in one application's UI.

DuckDB is the v1 execution layer, not a stored database. It reads a fixed set of CSVs
selected at mount and evaluates the facet queries. There is no persistent `.duckdb`
catalog, Parquet conversion, LMDB index, or automatic source refresh in this release.

## Invariants

- The mount is read-only; every mutation returns `EROFS`.
- A collection path is an AND of its facet/value pairs. Predicate order does not alter
  the result, and a facet cannot recur below itself.
- Only remaining facets with matching rows are shown.
- Source CSV files are evidence artifacts, not row payloads. A file appears when at
  least one of its rows matches the path, but opens with its complete original bytes.
- The input corpus is fingerprinted at mount. A changed or missing source requires a
  remount rather than silently mixing data from separate GX runs.
- Directory listings are immutable for each open directory handle, preventing paged
  FUSE reads from recomputing a large listing repeatedly.

## Scope boundary

This is not a writable filesystem, data catalog, ETL platform, generalized CSV
browser, or replacement for GX. The initial compatibility contract is deliberately
the extractor output from metadata-driven-gx. A Parquet materialization command or a
different result producer belongs behind the catalog boundary only after measurement
shows that direct CSV querying is inadequate.

## Lineage

The implementation differs from [`lmdb-fs`](https://github.com/dullroar/lmdb-fs), but retains its core proposition:
metadata-rich, immutable facts can be discovered through ordinary filesystem tools by
treating directory paths as accumulated predicates. DuckDB replaces the inverted-index
backend for the GX corpus because it already supplies CSV scanning, relational filters,
distinct-value discovery, and grouping.
