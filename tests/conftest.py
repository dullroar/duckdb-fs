from __future__ import annotations

from pathlib import Path

import pytest

from duckdb_fs.catalog import GXCatalog
from duckdb_fs.query import GXQuery


@pytest.fixture
def fixture_root() -> Path:
    return Path(__file__).parent / "fixtures" / "demo_weather_output"


@pytest.fixture
def catalog(fixture_root: Path):
    value = GXCatalog.from_input_root(fixture_root)
    try:
        yield value
    finally:
        value.close()


@pytest.fixture
def query(catalog: GXCatalog) -> GXQuery:
    return GXQuery(catalog)
