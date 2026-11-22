#!/usr/bin/env python3
"""Generate the routing index inside each folder README that carries index markers.

Run me when: an existing workflow uses the former command name for build_indexes.py.

Every routed Markdown file declares `gist: "Read when: ..."` in its front matter.
A README containing the BEGIN/END markers lists the Markdown files beneath its folder,
except README.md files, and except anything under a child folder whose own README has
markers (that child README is listed instead). Generated files that cannot carry front matter
can be left out with a line `<!-- index-exclude: a.md, sub/b.md -->` in the README; list them by
hand above the generated block.

Usage: build_context_indexes.py [--check] [ROOT]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from ctx_common import BEGIN, END, SKIP_DIRS, split_frontmatter


def has_markers(readme: Path) -> bool:
    return readme.is_file() and BEGIN in readme.read_text(encoding="utf-8")


def collect(folder: Path) -> list[Path]:
    found: list[Path] = []
    for child in sorted(folder.iterdir()):
        if child.name in SKIP_DIRS:
            continue
        if child.is_dir():
            if has_markers(child / "README.md"):
                found.append(child / "README.md")
            else:
                found.extend(collect(child))
        elif child.suffix == ".md" and child.name != "README.md":
            found.append(child)
    return found


def excluded(readme: Path) -> set[str]:
    found = re.search(r"<!--\s*index-exclude:\s*(.*?)\s*-->", readme.read_text(encoding="utf-8"))
    return {p.strip() for p in found.group(1).split(",")} if found else set()


def build(readme: Path, errors: list[str]) -> str:
    entries = []
    skip = excluded(readme)
    for path in sorted(collect(readme.parent), key=lambda p: p.relative_to(readme.parent).as_posix()):
        rel = path.relative_to(readme.parent).as_posix()
        if rel in skip:
            continue
        meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        gist = meta.get("gist")
        if not isinstance(gist, str) or not gist.strip():
            errors.append(f"{path}: missing gist front matter")
            continue
        entries.append(f"* [{rel}](./{rel}).\n  {gist.strip()}")
    return "\n".join(entries) if entries else "<!-- No routed files yet. -->"


def update_readme_indexes(root: Path, check: bool, errors: list[str]) -> list[str]:
    stale: list[str] = []
    for readme in sorted(root.rglob("README.md")):
        if SKIP_DIRS & set(readme.relative_to(root).parts) or not has_markers(readme):
            continue
        text = readme.read_text(encoding="utf-8")
        head, rest = text.split(BEGIN, 1)
        if END not in rest:
            errors.append(f"{readme}: BEGIN marker without END marker")
            continue
        _, tail = rest.split(END, 1)
        new = f"{head}{BEGIN}\n\n{build(readme, errors)}\n\n{END}{tail}"
        if new != text:
            stale.append(str(readme.relative_to(root)))
            if not check:
                readme.write_text(new, encoding="utf-8")
    return stale


if __name__ == "__main__":
    from build_indexes import main

    sys.exit(main(sys.argv[1:]))
