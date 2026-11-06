---
gist: "Read when: deciding whether a request fits the project, or relating it to lmdb-fs and metadata-driven-gx."
---

# Scope and lineage

**Boundary.** Not a writable filesystem, data catalog, ETL platform, generalized CSV browser, or replacement for GX. The initial compatibility contract is deliberately the extractor output of metadata-driven-gx.

**Lineage.** Different implementation from [lmdb-fs](https://github.com/dullroar/lmdb-fs) but the same proposition: metadata-rich, immutable facts discoverable through ordinary filesystem tools by treating directory paths as accumulated predicates.
