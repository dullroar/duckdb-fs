from __future__ import annotations

import asyncio
import errno
import os
import shutil
import stat
from pathlib import Path

import pyfuse3
import pytest

from duckdb_fs.catalog import GXCatalog
from duckdb_fs.fuse.operations import DuckDBFSOperations
from duckdb_fs.query import GXQuery


def _operations(root: Path) -> tuple[DuckDBFSOperations, GXCatalog]:
    catalog = GXCatalog.from_input_root(root)
    return DuckDBFSOperations(GXQuery(catalog), stat_path=root), catalog


def _entry(entries: list[tuple[bytes, int]], name: bytes) -> tuple[bytes, int]:
    return next(entry for entry in entries if entry[0] == name)


def test_root_query_directories_and_source_file(fixture_root: Path) -> None:
    ops, catalog = _operations(fixture_root)
    try:
        root = ops._children(pyfuse3.ROOT_INODE)
        _, summary_inode = _entry(root, b"summary")
        _, fail_inode = _entry(ops._children(summary_inode), b"status=FAIL")
        _, customers_inode = _entry(ops._children(fail_inode), b"table=CUSTOMERS")
        source_name, source_inode = _entry(ops._children(customers_inode), b"CUSTOMERS_summary.csv")
        assert source_name == b"CUSTOMERS_summary.csv"
        info = asyncio.run(ops.open(source_inode, os.O_RDONLY, None))
        try:
            assert asyncio.run(ops.read(info.fh, 0, 64)) == (fixture_root / "CUSTOMERS" / "CUSTOMERS_summary.csv").read_bytes()[:64]
        finally:
            asyncio.run(ops.release(info.fh))
    finally:
        catalog.close()


def test_direct_lookup_does_not_enumerate_parent(fixture_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ops, catalog = _operations(fixture_root)
    try:
        _, summary_inode = _entry(ops._children(pyfuse3.ROOT_INODE), b"summary")

        def fail_listing(*args, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("lookup must not enumerate the complete parent")

        monkeypatch.setattr(ops.query, "listing", fail_listing)
        attrs = asyncio.run(ops.lookup(summary_inode, b"status=FAIL", None))
        assert attrs.st_mode & stat.S_IFMT(attrs.st_mode) == stat.S_IFDIR
    finally:
        catalog.close()


def test_open_directory_holds_and_releases_snapshot(fixture_root: Path) -> None:
    ops, catalog = _operations(fixture_root)
    try:
        handle = asyncio.run(ops.opendir(pyfuse3.ROOT_INODE, None))
        assert int(handle) in ops._open_dirs
        asyncio.run(ops.releasedir(handle))
        assert int(handle) not in ops._open_dirs
    finally:
        catalog.close()


@pytest.mark.parametrize("operation", ["mkdir", "unlink", "rmdir"])
def test_mutations_report_erofs(fixture_root: Path, operation: str) -> None:
    ops, catalog = _operations(fixture_root)
    try:
        args = {
            "mkdir": (pyfuse3.ROOT_INODE, b"new", 0o755, None),
            "unlink": (pyfuse3.ROOT_INODE, b"new", None),
            "rmdir": (pyfuse3.ROOT_INODE, b"new", None),
        }[operation]
        with pytest.raises(pyfuse3.FUSEError) as exc:
            asyncio.run(getattr(ops, operation)(*args))
        assert exc.value.errno == errno.EROFS
    finally:
        catalog.close()


def test_changed_input_returns_eio(tmp_path: Path, fixture_root: Path) -> None:
    root = tmp_path / "output"
    shutil.copytree(fixture_root, root)
    ops, catalog = _operations(root)
    try:
        _, summary_inode = _entry(ops._children(pyfuse3.ROOT_INODE), b"summary")
        _, source_inode = _entry(ops._children(summary_inode), b"CUSTOMERS_summary.csv")
        path = root / "CUSTOMERS" / "CUSTOMERS_summary.csv"
        path.write_bytes(path.read_bytes() + b"\n")
        with pytest.raises(pyfuse3.FUSEError) as exc:
            asyncio.run(ops.getattr(source_inode))
        assert exc.value.errno == errno.EIO
    finally:
        catalog.close()
