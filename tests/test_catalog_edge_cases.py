from __future__ import annotations

import csv
from pathlib import Path

from duckdb_fs.catalog import GXCatalog
from duckdb_fs.query import GXQuery


def test_run_date_normalization_and_error_status(tmp_path: Path) -> None:
    path = tmp_path / "one_summary.csv"
    fields = [
        "source", "expectation_type", "column", "table", "severity", "test_category",
        "success", "result_type", "rule_kind", "run_date", "environment_name",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "source": "one", "expectation_type": "expect_column_values_to_not_be_null",
                "column": "MISSING", "table": "EXAMPLE", "success": "False",
                "result_type": "error", "run_date": "2026-09-23T12:03:11.123456+00:00",
                "severity": "critical", "test_category": "DQ", "rule_kind": "single_column", "environment_name": "test",
            }
        )
    catalog = GXCatalog.from_input_root(tmp_path)
    try:
        query = GXQuery(catalog)
        listing = query.listing("summary", (("status", "ERROR"),))
        assert [source.name for source in listing.sources] == ["one_summary.csv"]
        assert ("run_date", "2026-09-23") in {(entry.facet, entry.value) for entry in listing.facets}
    finally:
        catalog.close()
