"""Pure faceted listings over a GXCatalog; intentionally independent of FUSE."""

from __future__ import annotations

from .cache import BoundedLRU
from .catalog import GXCatalog
from .model import Collection, DirectoryListing, PredicateKey
from .paths import PathError, canonicalize, encode_component


class GXQuery:
    def __init__(self, catalog: GXCatalog, *, cache_size: int = 1024, cache_max_files: int = 10_000) -> None:
        if cache_max_files < 0:
            raise ValueError("cache_max_files cannot be negative")
        self.catalog = catalog
        self.cache_max_files = cache_max_files
        self._cache: BoundedLRU[tuple[Collection, PredicateKey], DirectoryListing] = BoundedLRU(cache_size)

    def listing(self, collection: Collection, predicates: PredicateKey = ()) -> DirectoryListing:
        predicates = canonicalize(predicates)
        key = (collection, predicates)
        cached = self._cache.get(key)
        if cached is not None:
            self.catalog.assert_unchanged()
            return cached
        if not self.catalog.has_match(collection, predicates):
            raise PathError("no rows match this predicate path")
        listing = DirectoryListing(
            collection=collection,
            predicates=predicates,
            facets=self.catalog.remaining_facets(collection, predicates),
            sources=self.catalog.matching_sources(collection, predicates),
        )
        if len(listing.sources) <= self.cache_max_files:
            self._cache.put(key, listing)
        return listing

    def child_predicates(self, predicates: PredicateKey, facet: str, value: str) -> PredicateKey:
        if facet in {name for name, _ in predicates}:
            raise PathError("a facet may appear only once in a path")
        return canonicalize((*predicates, (facet, value)))

    @staticmethod
    def facet_component(facet: str, value: str) -> str:
        return encode_component(facet, value)
