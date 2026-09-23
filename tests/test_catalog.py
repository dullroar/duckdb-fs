from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from duckdb_fs.catalog import GXCatalog
from duckdb_fs.errors import CatalogError, InputChangedError
from duckdb_fs.paths import PathError
from duckdb_fs.query import GXQuery


def _count(catalog: GXCatalog, collection: str, predicates: tuple[tuple[str, str], ...] = ()) -> int:
    where, values = catalog._where(collection, predicates)  # type: ignore[arg-type]
    return int(catalog._connection.execute(f"SELECT count(*) FROM {collection}{where}", values).fetchone()[0])


def test_demo_weather_corpus_and_facets(catalog: GXCatalog, query: GXQuery) -> None:
    assert _count(catalog, "summary") == 50
    assert _count(catalog, "details") == 34
    assert _count(catalog, "summary", (("status", "FAIL"),)) == 29
    customers = query.listing("summary", (("status", "FAIL"), ("table", "CUSTOMERS")))
    assert _count(catalog, "summary", customers.predicates) == 6
    assert [source.name for source in customers.sources] == ["CUSTOMERS_summary.csv"]
    assert {entry.facet for entry in customers.facets}.isdisjoint({"status", "table"})
    assert ("column", "LAST_NAME") in {(entry.facet, entry.value) for entry in customers.facets}
    assert all(entry.count > 0 for entry in customers.facets)


def test_predicate_order_is_equivalent(query: GXQuery) -> None:
    forward = query.listing("summary", (("status", "FAIL"), ("table", "CUSTOMERS")))
    reverse = query.listing("summary", (("table", "CUSTOMERS"), ("status", "FAIL")))
    assert forward == reverse


def test_details_keep_only_reliable_facets(query: GXQuery) -> None:
    listing = query.listing("details")
    assert {entry.facet for entry in listing.facets}.isdisjoint({"status", "severity", "test_category"})
    assert "CUSTOMERS_details.csv" in {source.name for source in listing.sources}


def test_source_file_is_visible_when_any_row_matches(fixture_root: Path, query: GXQuery) -> None:
    predicates = (("status", "FAIL"), ("table", "CUSTOMERS"), ("column", "LAST_NAME"))
    listing = query.listing("summary", predicates)
    assert [source.name for source in listing.sources] == ["CUSTOMERS_summary.csv"]
    source = query.catalog.source("summary", "CUSTOMERS_summary.csv")
    assert source.path.read_bytes() == (fixture_root / "CUSTOMERS" / "CUSTOMERS_summary.csv").read_bytes()
    assert query.catalog.source_matches("summary", source.name, listing.predicates)


def test_unknown_or_nonmatching_predicates_fail(query: GXQuery) -> None:
    with pytest.raises(PathError):
        query.listing("summary", (("status", "FAIL"), ("status", "PASS")))
    with pytest.raises(PathError):
        query.listing("summary", (("status", "NOT_A_STATUS"),))


def test_catalog_rejects_bad_header_and_duplicate_basenames(tmp_path: Path, fixture_root: Path) -> None:
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "broken_summary.csv").write_text("table,column\nA,B\n", encoding="utf-8")
    with pytest.raises(CatalogError, match="lacks required"):
        GXCatalog.from_input_root(bad)

    copied = tmp_path / "copied"
    shutil.copytree(fixture_root, copied)
    duplicate = copied / "duplicate"
    duplicate.mkdir()
    shutil.copy(copied / "CUSTOMERS" / "CUSTOMERS_summary.csv", duplicate / "CUSTOMERS_summary.csv")
    with pytest.raises(CatalogError, match="duplicate"):
        GXCatalog.from_input_root(copied)


def test_zero_byte_details_are_ignored(tmp_path: Path, fixture_root: Path) -> None:
    root = tmp_path / "output"
    root.mkdir()
    shutil.copy(fixture_root / "CUSTOMERS" / "CUSTOMERS_summary.csv", root / "CUSTOMERS_summary.csv")
    (root / "CUSTOMERS_details.csv").touch()
    catalog = GXCatalog.from_input_root(root)
    try:
        assert _count(catalog, "summary") == 10
        assert _count(catalog, "details") == 0
    finally:
        catalog.close()


def test_input_fingerprint_requires_remount(tmp_path: Path, fixture_root: Path) -> None:
    root = tmp_path / "output"
    shutil.copytree(fixture_root, root)
    catalog = GXCatalog.from_input_root(root)
    try:
        path = root / "CUSTOMERS" / "CUSTOMERS_summary.csv"
        path.write_bytes(path.read_bytes() + b"\n")
        with pytest.raises(InputChangedError, match="remount"):
            catalog.assert_unchanged()
    finally:
        catalog.close()
