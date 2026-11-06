---
gist: "Read when: asked for a custom search UI, changing how paths express queries, or explaining the File | Open design rationale."
---

# The File | Open dialog is the query UI

**Decision.** Pipeline: GX extractor CSVs -> DuckDB query catalog -> FUSE -> File | Open. The intended interface is the File | Open dialog already embedded in nearly every desktop application, not a custom search page. Filesystems are a mature protocol for enumerate, open, read, seek and stat; projecting faceted queries through it lets someone narrow by failure, table, column and expectation without SQL or a catalog-specific client. The path is a portable serialized query rather than transient checkbox state.
