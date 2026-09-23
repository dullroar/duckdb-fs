"""Immutable types shared by catalog, query, and FUSE layers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

Collection = Literal["summary", "details"]
Predicate: TypeAlias = tuple[str, str]
PredicateKey: TypeAlias = tuple[Predicate, ...]


@dataclass(frozen=True, slots=True)
class Fingerprint:
    size: int
    mtime_ns: int


@dataclass(frozen=True, slots=True)
class SourceFile:
    collection: Collection
    name: str
    path: Path
    fingerprint: Fingerprint


@dataclass(frozen=True, slots=True)
class FacetEntry:
    facet: str
    value: str
    count: int


@dataclass(frozen=True, slots=True)
class DirectoryListing:
    collection: Collection
    predicates: PredicateKey
    facets: tuple[FacetEntry, ...]
    sources: tuple[SourceFile, ...]
