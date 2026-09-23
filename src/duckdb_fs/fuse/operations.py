"""Read-only pyfuse3 projection of a :class:`duckdb_fs.query.GXQuery`."""

from __future__ import annotations

import errno
import os
import stat
import time
from pathlib import Path

import pyfuse3

from ..catalog import FACETS
from ..errors import CatalogError, InputChangedError
from ..model import Collection
from ..paths import PathError, decode_component
from ..query import GXQuery
from .inode_table import DirectoryRef, FileRef, InodeTable


class DuckDBFSOperations(pyfuse3.Operations):
    """Filesystem operations deliberately limited to enumeration and read access."""

    def __init__(self, query: GXQuery, *, stat_path: Path | str) -> None:
        super().__init__()
        self.query = query
        self.inodes = InodeTable()
        self._stat_path = Path(stat_path)
        self._open_files: dict[int, int] = {}
        self._open_dirs: dict[int, list[tuple[bytes, int]]] = {}
        self._next_handle = 1
        self._next_directory_handle = 1 << 32

    def _ref(self, inode: int) -> DirectoryRef | FileRef:
        try:
            return self.inodes.get(inode)
        except KeyError as exc:
            raise pyfuse3.FUSEError(errno.ENOENT) from exc

    def _directory(self, inode: int) -> DirectoryRef:
        ref = self._ref(inode)
        if not isinstance(ref, DirectoryRef):
            raise pyfuse3.FUSEError(errno.ENOTDIR)
        return ref

    def _raise_catalog_error(self, exc: Exception) -> None:
        if isinstance(exc, InputChangedError):
            raise pyfuse3.FUSEError(errno.EIO) from exc
        raise pyfuse3.FUSEError(errno.ENOENT) from exc

    def _attrs(self, inode: int) -> pyfuse3.EntryAttributes:
        ref = self._ref(inode)
        attrs = pyfuse3.EntryAttributes()
        attrs.st_ino = inode
        attrs.st_uid = os.getuid()
        attrs.st_gid = os.getgid()
        attrs.entry_timeout = 0
        attrs.attr_timeout = 0
        if isinstance(ref, DirectoryRef):
            now = time.time_ns()
            attrs.st_mode = stat.S_IFDIR | 0o555
            attrs.st_size = 0
            attrs.st_atime_ns = attrs.st_ctime_ns = attrs.st_mtime_ns = now
            attrs.st_nlink = 2
            return attrs
        try:
            self.query.catalog.assert_unchanged()
            source_stat = ref.source.path.stat()
        except (InputChangedError, FileNotFoundError) as exc:
            raise pyfuse3.FUSEError(errno.EIO) from exc
        attrs.st_mode = stat.S_IFREG | 0o444
        attrs.st_size = source_stat.st_size
        attrs.st_atime_ns = source_stat.st_atime_ns
        attrs.st_ctime_ns = source_stat.st_ctime_ns
        attrs.st_mtime_ns = source_stat.st_mtime_ns
        attrs.st_nlink = 1
        return attrs

    def _children(self, parent_inode: int) -> list[tuple[bytes, int]]:
        directory = self._directory(parent_inode)
        if directory.collection is None:
            return [
                (name.encode("utf-8"), self.inodes.directory(name, (), parent_inode))
                for name in ("summary", "details")
            ]
        try:
            listing = self.query.listing(directory.collection, directory.predicates)
        except (CatalogError, InputChangedError, PathError) as exc:
            self._raise_catalog_error(exc)
        entries: list[tuple[bytes, int]] = []
        for facet in listing.facets:
            predicates = self.query.child_predicates(directory.predicates, facet.facet, facet.value)
            inode = self.inodes.directory(directory.collection, predicates, parent_inode)
            entries.append((self.query.facet_component(facet.facet, facet.value).encode("utf-8"), inode))
        for source in listing.sources:
            entries.append((source.name.encode("utf-8"), self.inodes.file(source, parent_inode)))
        return entries

    async def getattr(self, inode, ctx=None):  # type: ignore[no-untyped-def]
        return self._attrs(int(inode))

    async def lookup(self, parent_inode, name, ctx):  # type: ignore[no-untyped-def]
        parent_inode = int(parent_inode)
        directory = self._directory(parent_inode)
        if name == b".":
            return self._attrs(parent_inode)
        if name == b"..":
            return self._attrs(directory.parent_inode or int(pyfuse3.ROOT_INODE))
        try:
            child_name = name.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise pyfuse3.FUSEError(errno.ENOENT) from exc
        if directory.collection is None:
            if child_name in ("summary", "details"):
                inode = self.inodes.directory(child_name, (), parent_inode)
                return self._attrs(inode)
            raise pyfuse3.FUSEError(errno.ENOENT)
        collection: Collection = directory.collection
        try:
            source = self.query.catalog.source(collection, child_name)
        except KeyError:
            source = None
        if source is not None:
            try:
                if self.query.catalog.source_matches(collection, child_name, directory.predicates):
                    inode = self.inodes.file(source, parent_inode)
                    return self._attrs(inode)
            except (CatalogError, InputChangedError) as exc:
                self._raise_catalog_error(exc)
        try:
            facet, value = decode_component(child_name)
            if facet not in FACETS[collection] or facet in {facet for facet, _ in directory.predicates}:
                raise PathError("unknown or reused facet")
            predicates = self.query.child_predicates(directory.predicates, facet, value)
            if self.query.catalog.has_match(collection, predicates):
                inode = self.inodes.directory(collection, predicates, parent_inode)
                return self._attrs(inode)
        except (CatalogError, InputChangedError, PathError) as exc:
            if isinstance(exc, InputChangedError):
                self._raise_catalog_error(exc)
        raise pyfuse3.FUSEError(errno.ENOENT)

    async def opendir(self, inode, ctx):  # type: ignore[no-untyped-def]
        self._directory(int(inode))
        handle = self._next_directory_handle
        self._next_directory_handle += 1
        self._open_dirs[handle] = self._children(int(inode))
        return pyfuse3.FileHandleT(handle)

    async def readdir(self, fh, start_id, token):  # type: ignore[no-untyped-def]
        try:
            entries = self._open_dirs[int(fh)]
        except KeyError as exc:
            raise pyfuse3.FUSEError(errno.EBADF) from exc
        for index, (name, inode) in enumerate(entries[start_id:], start=start_id + 1):
            if not pyfuse3.readdir_reply(token, name, self._attrs(inode), index):
                return

    async def releasedir(self, fh):  # type: ignore[no-untyped-def]
        self._open_dirs.pop(int(fh), None)

    async def open(self, inode, flags, ctx):  # type: ignore[no-untyped-def]
        ref = self._ref(int(inode))
        if not isinstance(ref, FileRef):
            raise pyfuse3.FUSEError(errno.EISDIR)
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_TRUNC):
            raise pyfuse3.FUSEError(errno.EROFS)
        try:
            self.query.catalog.assert_unchanged()
            fd = os.open(ref.source.path, os.O_RDONLY)
        except (InputChangedError, FileNotFoundError) as exc:
            raise pyfuse3.FUSEError(errno.EIO) from exc
        handle = self._next_handle
        self._next_handle += 1
        self._open_files[handle] = fd
        return pyfuse3.FileInfo(fh=pyfuse3.FileHandleT(handle))

    async def read(self, fh, off, size):  # type: ignore[no-untyped-def]
        try:
            self.query.catalog.assert_unchanged()
            return os.pread(self._open_files[int(fh)], size, off)
        except InputChangedError as exc:
            raise pyfuse3.FUSEError(errno.EIO) from exc
        except KeyError as exc:
            raise pyfuse3.FUSEError(errno.EBADF) from exc

    async def release(self, fh):  # type: ignore[no-untyped-def]
        fd = self._open_files.pop(int(fh), None)
        if fd is not None:
            os.close(fd)

    async def statfs(self, ctx):  # type: ignore[no-untyped-def]
        source = os.statvfs(self._stat_path)
        result = pyfuse3.StatvfsData()
        result.f_bsize = source.f_bsize
        result.f_frsize = source.f_frsize
        result.f_blocks = source.f_blocks
        result.f_bfree = source.f_bfree
        result.f_bavail = source.f_bavail
        result.f_files = source.f_files
        result.f_ffree = source.f_ffree
        result.f_favail = source.f_favail
        result.f_namemax = source.f_namemax
        return result

    async def setattr(self, inode, attr, fields, fh, ctx):  # type: ignore[no-untyped-def]
        raise pyfuse3.FUSEError(errno.EROFS)

    async def mknod(self, parent_inode, name, mode, rdev, ctx):  # type: ignore[no-untyped-def]
        raise pyfuse3.FUSEError(errno.EROFS)

    async def mkdir(self, parent_inode, name, mode, ctx):  # type: ignore[no-untyped-def]
        raise pyfuse3.FUSEError(errno.EROFS)

    async def unlink(self, parent_inode, name, ctx):  # type: ignore[no-untyped-def]
        raise pyfuse3.FUSEError(errno.EROFS)

    async def rmdir(self, parent_inode, name, ctx):  # type: ignore[no-untyped-def]
        raise pyfuse3.FUSEError(errno.EROFS)

    async def symlink(self, parent_inode, name, target, ctx):  # type: ignore[no-untyped-def]
        raise pyfuse3.FUSEError(errno.EROFS)

    async def rename(self, parent_inode_old, name_old, parent_inode_new, name_new, flags, ctx):  # type: ignore[no-untyped-def]
        raise pyfuse3.FUSEError(errno.EROFS)

    async def write(self, fh, off, buf):  # type: ignore[no-untyped-def]
        raise pyfuse3.FUSEError(errno.EROFS)

    async def setxattr(self, inode, name, value, ctx):  # type: ignore[no-untyped-def]
        raise pyfuse3.FUSEError(errno.EROFS)

    async def removexattr(self, inode, name, ctx):  # type: ignore[no-untyped-def]
        raise pyfuse3.FUSEError(errno.EROFS)

    async def create(self, parent_inode, name, mode, flags, ctx):  # type: ignore[no-untyped-def]
        raise pyfuse3.FUSEError(errno.EROFS)
