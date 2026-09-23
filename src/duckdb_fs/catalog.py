"""DuckDB-backed, mount-time catalog for GX extractor CSV output."""

from __future__ import annotations

import csv
import os
import threading
from collections.abc import Iterable
from pathlib import Path

import duckdb

from .errors import CatalogError, InputChangedError
from .model import Collection, FacetEntry, Fingerprint, PredicateKey, SourceFile

SUMMARY_REQUIRED = frozenset({"source", "expectation_type", "column", "table", "severity", "test_category", "success", "result_type", "rule_kind", "run_date", "environment_name"})
DETAIL_REQUIRED = frozenset({"source", "expectation_type", "column", "table", "run_date", "environment_name"})

FACETS: dict[Collection, tuple[str, ...]] = {
    "summary": (
        "status", "table", "column", "expectation_type", "severity", "test_category",
        "result_type", "rule_kind", "environment_name", "run_date",
    ),
    "details": ("table", "column", "expectation_type", "environment_name", "run_date"),
}


def _fingerprint(path: Path) -> Fingerprint:
    stat = path.stat()
    return Fingerprint(stat.st_size, stat.st_mtime_ns)


def _header(path: Path) -> set[str]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            row = next(csv.reader(handle), None)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise CatalogError(f"cannot read CSV header: {path}") from exc
    if not row:
        return set()
    return {value.strip() for value in row if value.strip()}


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


class GXCatalog:
    """One explicit, private DuckDB connection over a fixed list of CSV files."""

    def __init__(self, input_root: Path, sources: dict[Collection, tuple[SourceFile, ...]]) -> None:
        self.input_root = input_root
        self.sources = sources
        self._by_name = {
            collection: {source.name: source for source in values}
            for collection, values in sources.items()
        }
        self._connection = duckdb.connect(":memory:")
        self._lock = threading.RLock()
        self._create_views()

    @classmethod
    def from_input_root(cls, input_root: Path | str) -> "GXCatalog":
        root = Path(input_root).resolve()
        if not root.is_dir():
            raise CatalogError(f"input root is not a directory: {root}")
        sources: dict[Collection, tuple[SourceFile, ...]] = {}
        for collection, required in (("summary", SUMMARY_REQUIRED), ("details", DETAIL_REQUIRED)):
            paths = sorted(root.rglob(f"*_{collection}.csv"))
            discovered: list[SourceFile] = []
            names: set[str] = set()
            for path in paths:
                if not path.is_file():
                    continue
                fingerprint = _fingerprint(path)
                if collection == "details" and fingerprint.size == 0:
                    continue
                header = _header(path)
                missing = sorted(required - header)
                if missing:
                    raise CatalogError(f"{path} lacks required {collection} columns: {', '.join(missing)}")
                if path.name in names:
                    raise CatalogError(f"duplicate {collection} CSV basename: {path.name}")
                names.add(path.name)
                discovered.append(SourceFile(collection, path.name, path.resolve(), fingerprint))
            sources[collection] = tuple(discovered)
        if not sources["summary"]:
            raise CatalogError(f"no non-empty *_summary.csv files found below {root}")
        return cls(root, sources)

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def assert_unchanged(self) -> None:
        for values in self.sources.values():
            for source in values:
                try:
                    current = _fingerprint(source.path)
                except FileNotFoundError as exc:
                    raise InputChangedError(f"GX input disappeared; remount required: {source.path}") from exc
                if current != source.fingerprint:
                    raise InputChangedError(f"GX input changed; remount required: {source.path}")

    def _create_views(self) -> None:
        self._create_raw_view("summary")
        self._create_raw_view("details")
        self._connection.execute(
            """
            CREATE VIEW summary AS
            SELECT
              source_path, "source", "table", "column", "expectation_type", "severity",
              "test_category", "result_type", "rule_kind", "environment_name",
              substr("run_date", 1, 10) AS "run_date",
              CASE "result_type"
                WHEN 'success' THEN 'PASS'
                WHEN 'failure' THEN 'FAIL'
                WHEN 'error' THEN 'ERROR'
              END AS "status"
            FROM summary_raw
            """
        )
        self._connection.execute(
            """
            CREATE VIEW details AS
            SELECT
              source_path, "source", "table", "column", "expectation_type", "environment_name",
              substr("run_date", 1, 10) AS "run_date"
            FROM details_raw
            """
        )
        invalid = self._connection.execute(
            "SELECT DISTINCT result_type FROM summary WHERE result_type NOT IN ('success', 'failure', 'error') OR result_type IS NULL"
        ).fetchall()
        if invalid:
            values = ", ".join(repr(row[0]) for row in invalid)
            raise CatalogError(f"summary result_type must be success, failure, or error; found {values}")

    def _create_raw_view(self, collection: Collection) -> None:
        sources = self.sources[collection]
        if not sources:
            # A no-failure GX run legitimately leaves only zero-byte detail CSVs.
            if collection == "details":
                self._connection.execute(
                    "CREATE VIEW details_raw AS SELECT CAST(NULL AS VARCHAR) AS source_path, "
                    "CAST(NULL AS VARCHAR) AS source, CAST(NULL AS VARCHAR) AS \"table\", "
                    "CAST(NULL AS VARCHAR) AS \"column\", CAST(NULL AS VARCHAR) AS expectation_type, "
                    "CAST(NULL AS VARCHAR) AS environment_name, CAST(NULL AS VARCHAR) AS run_date WHERE FALSE"
                )
                return
            raise CatalogError("summary input is required")
        paths = ", ".join(_sql_string(os.fspath(source.path)) for source in sources)
        self._connection.execute(
            f"CREATE VIEW {collection}_raw AS SELECT * FROM read_csv([{paths}], "
            "header = true, union_by_name = true, all_varchar = true, filename = 'source_path')"
        )

    def facets(self, collection: Collection) -> tuple[str, ...]:
        return FACETS[collection]

    def source(self, collection: Collection, name: str) -> SourceFile:
        try:
            return self._by_name[collection][name]
        except KeyError as exc:
            raise KeyError(name) from exc

    def _where(self, collection: Collection, predicates: PredicateKey) -> tuple[str, list[str]]:
        allowed = set(FACETS[collection])
        if any(facet not in allowed for facet, _ in predicates):
            raise CatalogError("unknown facet")
        if not predicates:
            return "", []
        return " WHERE " + " AND ".join(f'"{facet}" = ?' for facet, _ in predicates), [value for _, value in predicates]

    def has_match(self, collection: Collection, predicates: PredicateKey) -> bool:
        self.assert_unchanged()
        where, values = self._where(collection, predicates)
        with self._lock:
            return self._connection.execute(f"SELECT EXISTS(SELECT 1 FROM {collection}{where})", values).fetchone()[0]

    def source_matches(self, collection: Collection, name: str, predicates: PredicateKey) -> bool:
        source = self.source(collection, name)
        self.assert_unchanged()
        where, values = self._where(collection, predicates)
        prefix = " WHERE " if not where else where + " AND "
        with self._lock:
            return self._connection.execute(
                f"SELECT EXISTS(SELECT 1 FROM {collection}{prefix}source_path = ?)", [*values, os.fspath(source.path)]
            ).fetchone()[0]

    def matching_sources(self, collection: Collection, predicates: PredicateKey) -> tuple[SourceFile, ...]:
        self.assert_unchanged()
        where, values = self._where(collection, predicates)
        with self._lock:
            rows = self._connection.execute(
                f"SELECT DISTINCT source_path FROM {collection}{where} ORDER BY source_path", values
            ).fetchall()
        path_to_source = {os.fspath(source.path): source for source in self.sources[collection]}
        return tuple(path_to_source[row[0]] for row in rows)

    def remaining_facets(self, collection: Collection, predicates: PredicateKey) -> tuple[FacetEntry, ...]:
        self.assert_unchanged()
        used = {facet for facet, _ in predicates}
        where, values = self._where(collection, predicates)
        entries: list[FacetEntry] = []
        with self._lock:
            for facet in FACETS[collection]:
                if facet in used:
                    continue
                clause = " WHERE " if not where else where + " AND "
                rows = self._connection.execute(
                    f'SELECT "{facet}", count(*) FROM {collection}{clause}'
                    f'"{facet}" IS NOT NULL AND "{facet}" <> \'\' GROUP BY 1 ORDER BY 1', values
                ).fetchall()
                entries.extend(FacetEntry(facet, str(value), int(count)) for value, count in rows)
        return tuple(entries)
