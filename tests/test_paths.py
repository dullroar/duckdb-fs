from __future__ import annotations

import pytest

from duckdb_fs.paths import PathError, canonicalize, decode_component, encode_component


def test_component_round_trip_handles_filesystem_significant_values() -> None:
    rendered = encode_component("table/name", "A=B / snowman ☃")
    assert rendered == "table%2Fname=A%3DB%20%2F%20snowman%20%E2%98%83"
    assert decode_component(rendered) == ("table/name", "A=B / snowman ☃")


@pytest.mark.parametrize("component", ["noequals", "a=b=c", "=value", "facet=", "a=%ZZ"])
def test_invalid_components_fail(component: str) -> None:
    with pytest.raises(PathError):
        decode_component(component)


def test_canonicalization_is_order_independent_and_rejects_reuse() -> None:
    assert canonicalize((("table", "CUSTOMERS"), ("status", "FAIL"))) == canonicalize(
        (("status", "FAIL"), ("table", "CUSTOMERS"))
    )
    with pytest.raises(PathError):
        canonicalize((("table", "CUSTOMERS"), ("table", "READINGS")))
