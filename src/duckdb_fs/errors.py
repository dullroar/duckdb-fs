"""Errors with a stable boundary between catalog, query, and FUSE layers."""


class CatalogError(ValueError):
    """The supplied GX output tree does not meet the duckdb-fs input contract."""


class InputChangedError(RuntimeError):
    """An input file changed after mount; remount to establish a new snapshot."""
