---
gist: "Read when: proposing a persistent .duckdb catalog, Parquet conversion, an LMDB index, automatic refresh, or a different result producer."
---

# DuckDB as the v1 execution layer

**Decision.** DuckDB reads a fixed set of CSVs selected at mount and evaluates the facet queries; it is not a stored database. There is no persistent `.duckdb` catalog, Parquet conversion, LMDB index, or automatic source refresh in this release. DuckDB replaces the inverted-index backend of lmdb-fs for the GX corpus because it already supplies CSV scanning, relational filters, distinct-value discovery and grouping.

**Reconsider when.** Measurement shows direct CSV querying is inadequate; a Parquet materialization command or another result producer then belongs behind the catalog boundary.
