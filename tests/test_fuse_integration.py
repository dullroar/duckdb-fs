from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


@pytest.mark.integration
def test_real_mount_exposes_gx_fixture(tmp_path: Path, fixture_root: Path) -> None:
    if os.environ.get("DUCKDB_FS_RUN_FUSE_TESTS") != "1":
        pytest.skip("set DUCKDB_FS_RUN_FUSE_TESTS=1 to perform a real FUSE mount")
    mountpoint = tmp_path / "mount"
    mountpoint.mkdir()
    process = subprocess.Popen(
        [
            sys.executable, "-m", "duckdb_fs.cli", "mount",
            "--input-root", str(fixture_root), "--mountpoint", str(mountpoint),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not (mountpoint / "summary").is_dir():
            if process.poll() is not None:
                _, stderr = process.communicate(timeout=1)
                pytest.fail(f"duckdb-fs mount exited early: {stderr}")
            time.sleep(0.05)
        assert (mountpoint / "summary" / "status=FAIL" / "table=CUSTOMERS" / "CUSTOMERS_summary.csv").read_bytes() == (
            fixture_root / "CUSTOMERS" / "CUSTOMERS_summary.csv"
        ).read_bytes()
    finally:
        subprocess.run(
            [sys.executable, "-m", "duckdb_fs.cli", "unmount", "--mountpoint", str(mountpoint)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        process.wait(timeout=10)
