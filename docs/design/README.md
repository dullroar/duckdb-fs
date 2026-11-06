---
gist: "Read when: changing the repository's design, boundaries or dependencies, or before simplifying a deliberate seam."
---

# Architecture premises

One durable design decision per file: the constraint, the choice, why, and what would contradict it. Open only the premise whose **Read when** line matches the task.

<!-- BEGIN GENERATED CONTEXT INDEX -->

* [duckdb-as-execution-layer.md](./duckdb-as-execution-layer.md).
  Read when: proposing a persistent .duckdb catalog, Parquet conversion, an LMDB index, automatic refresh, or a different result producer.
* [filesystem-as-query-ui.md](./filesystem-as-query-ui.md).
  Read when: asked for a custom search UI, changing how paths express queries, or explaining the File | Open design rationale.
* [read-only-facet-path-invariants.md](./read-only-facet-path-invariants.md).
  Read when: changing path semantics, listing behavior, file contents served, or source-corpus handling and remount rules.
* [scope-and-lineage.md](./scope-and-lineage.md).
  Read when: deciding whether a request fits the project, or relating it to lmdb-fs and metadata-driven-gx.

<!-- END GENERATED CONTEXT INDEX -->
