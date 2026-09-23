"""Portable, reversible rendering of a facet predicate as one path component."""

from __future__ import annotations

import re
from urllib.parse import quote, unquote

from .model import PredicateKey


class PathError(ValueError):
    """A virtual path component is not one valid facet predicate."""


_BAD_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")


def canonicalize(predicates: tuple[tuple[str, str], ...] | PredicateKey) -> PredicateKey:
    """Canonicalize an AND predicate set and reject repeated facets."""

    normalized = tuple(sorted(predicates))
    if any(not facet or not value for facet, value in normalized):
        raise PathError("facet names and values must be non-empty")
    if len({facet for facet, _ in normalized}) != len(normalized):
        raise PathError("a facet may appear only once in a path")
    return normalized


def encode_component(facet: str, value: str) -> str:
    if not facet or not value:
        raise PathError("facet names and values must be non-empty")
    return f"{quote(facet, safe='-._~')}={quote(value, safe='-._~')}"


def decode_component(component: str) -> tuple[str, str]:
    if component.count("=") != 1 or _BAD_PERCENT.search(component):
        raise PathError("invalid facet path component")
    raw_facet, raw_value = component.split("=", 1)
    facet, value = unquote(raw_facet), unquote(raw_value)
    if not facet or not value:
        raise PathError("facet names and values must be non-empty")
    return facet, value
