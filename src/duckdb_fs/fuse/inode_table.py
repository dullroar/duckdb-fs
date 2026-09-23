"""Stable inode allocation for virtual query directories and source files."""

from __future__ import annotations

from dataclasses import dataclass

import pyfuse3

from ..model import Collection, PredicateKey, SourceFile


@dataclass(frozen=True, slots=True)
class DirectoryRef:
    collection: Collection | None
    predicates: PredicateKey
    parent_inode: int | None


@dataclass(frozen=True, slots=True)
class FileRef:
    source: SourceFile
    parent_inode: int


class InodeTable:
    def __init__(self) -> None:
        root = int(pyfuse3.ROOT_INODE)
        self._refs: dict[int, DirectoryRef | FileRef] = {root: DirectoryRef(None, (), None)}
        self._keys: dict[object, int] = {("root",): root}
        self._next = root + 1

    def get(self, inode: int) -> DirectoryRef | FileRef:
        return self._refs[inode]

    def directory(self, collection: Collection, predicates: PredicateKey, parent_inode: int) -> int:
        key = ("dir", collection, predicates, parent_inode)
        return self._allocate(key, DirectoryRef(collection, predicates, parent_inode))

    def file(self, source: SourceFile, parent_inode: int) -> int:
        key = ("file", source.collection, source.path, parent_inode)
        return self._allocate(key, FileRef(source, parent_inode))

    def _allocate(self, key: object, ref: DirectoryRef | FileRef) -> int:
        existing = self._keys.get(key)
        if existing is not None:
            return existing
        inode = self._next
        self._next += 1
        self._keys[key] = inode
        self._refs[inode] = ref
        return inode
