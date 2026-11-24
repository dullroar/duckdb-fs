FROM ghcr.io/astral-sh/uv:0.11.7 AS uv
FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates fuse3 gcc git libc6-dev libfuse3-dev pkg-config python3-dev python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never

RUN useradd --create-home --shell /bin/bash tester \
    && install -d -o tester -g tester /work
WORKDIR /work
COPY --chown=tester:tester . .
USER tester
RUN uv sync --locked
# Prepare the check_context.py shim cache. The build has network. The runs have none.
RUN python3 -c "import sys; sys.path.insert(0, 'scripts'); import check_context as c; s, k = c.pinned(); c.ensure_environment(s, k)"
