---
gist: "Read when: changing path semantics, listing behavior, file contents served, or source-corpus handling and remount rules."
---

# Read-only mount and facet-path invariants

- The mount is read-only; every mutation returns `EROFS`.
- A collection path is an AND of its facet/value pairs. Predicate order does not alter the result, and a facet cannot recur below itself.
- Only remaining facets with matching rows are shown.
- Source CSV files are evidence artifacts, not row payloads. A file appears when at least one of its rows matches the path, but opens with its complete original bytes.
- The input corpus is fingerprinted at mount. A changed or missing source requires a remount rather than silently mixing data from separate GX runs.
- Directory listings are immutable per open directory handle, preventing paged FUSE reads from recomputing a large listing repeatedly.
