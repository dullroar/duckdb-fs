#!/usr/bin/env bash
# Run me when: I need to verify the project and its FUSE mount in Docker.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
security_options=$(docker info --format '{{json .SecurityOptions}}')

run_dir=$(mktemp -d /tmp/duckdb-fs-test.XXXXXXXX)
run_name=${run_dir##*/}
image="duckdb-fs-test:${run_name#duckdb-fs-test.}"
cleanup() {
    docker image rm "$image" >/dev/null 2>&1 || true
    rmdir -- "$run_dir"
}
trap cleanup EXIT

# Copy indexed paths from the current worktree, without its Git metadata.
git ls-files --cached -z |
    tar --create --file=- --no-recursion --owner=0 --group=0 --numeric-owner \
        --null --files-from=- |
    docker build --tag "$image" -

docker run --rm --name "$run_name-core" --network none "$image" \
    bash -ec "python3 scripts/check_context.py &&
        uv run --offline --locked pytest -m 'not integration'"

fuse_options=(--device /dev/fuse --cap-add SYS_ADMIN)
if [[ $security_options == *name=apparmor* ]]; then
    fuse_options+=(--security-opt apparmor=unconfined)
fi

docker run --rm --name "$run_name-fuse" --network none "${fuse_options[@]}" \
    --env DUCKDB_FS_RUN_FUSE_TESTS=1 -i "$image" bash -se <<'BASH'
test_dir=$(mktemp -d /tmp/duckdb-fs-mount-test.XXXXXXXX)
trap 'rm -rf -- "$test_dir"' EXIT
uv run --offline --locked pytest -m integration \
    --basetemp "$test_dir/pytest" --junitxml "$test_dir/results.xml"
python3 - "$test_dir/results.xml" <<'PY'
import sys
from xml.etree import ElementTree

results = ElementTree.parse(sys.argv[1])
mount_ran = any(
    case.get("name") == "test_real_mount_exposes_gx_fixture"
    for case in results.iter("testcase")
)
if not mount_ran or results.find(".//skipped") is not None:
    sys.exit("FUSE gate requires a real mount test with no skips.")
PY
BASH
