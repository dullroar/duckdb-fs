"""Command-line entry point for mounting metadata-driven-gx output."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

import pyfuse3
import trio

from .catalog import GXCatalog
from .fuse.operations import DuckDBFSOperations
from .query import GXQuery


def _mount(args: argparse.Namespace) -> int:
    catalog = GXCatalog.from_input_root(args.input_root)
    query = GXQuery(catalog, cache_size=args.cache_size, cache_max_files=args.cache_max_files)
    operations = DuckDBFSOperations(query, stat_path=args.input_root)
    options = set(pyfuse3.default_options)
    options.add("fsname=duckdb-fs")
    if args.debug:
        options.add("debug")
    pyfuse3.init(operations, os.fspath(args.mountpoint), options)
    try:
        trio.run(pyfuse3.main)
    finally:
        pyfuse3.close(unmount=False)
        catalog.close()
    return 0


def _unmount(args: argparse.Namespace) -> int:
    subprocess.run(["fusermount3", "-u", os.fspath(args.mountpoint)], check=True)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="duckdb-fs", description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    mount = commands.add_parser("mount", help="mount GX extractor CSVs as a read-only faceted filesystem")
    mount.add_argument("--input-root", type=Path, required=True)
    mount.add_argument("--mountpoint", type=Path, required=True)
    mount.add_argument("--cache-size", type=int, default=1024)
    mount.add_argument("--cache-max-files", type=int, default=10_000)
    mount.add_argument("--debug", action="store_true")
    mount.set_defaults(handler=_mount)
    unmount = commands.add_parser("unmount", help="unmount a duckdb-fs mount")
    unmount.add_argument("--mountpoint", type=Path, required=True)
    unmount.set_defaults(handler=_unmount)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
