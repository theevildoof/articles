#!/usr/bin/env python3
"""Normalize the Markdown front matter for the provided files or directories."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from frontmatter import normalize_front_matter


def iter_markdown_paths(targets: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for target in targets:
        path = Path(target)
        if not path.exists():
            print(f"Skipping missing path: {path}", file=sys.stderr)
            continue
        if path.is_dir():
            paths.extend(sorted(p for p in path.rglob("*.md") if p.is_file()))
        elif path.suffix.lower() == ".md":
            paths.append(path)
        else:
            print(f"Skipping non-Markdown path: {path}", file=sys.stderr)
    return paths


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: cleanup_frontmatter.py <path> [<path> ...]", file=sys.stderr)
        return 1

    markdown_paths = iter_markdown_paths(argv[1:])
    if not markdown_paths:
        print("No Markdown files found to process.")
        return 0

    changes = 0
    for md_path in markdown_paths:
        original = md_path.read_text(encoding="utf-8")
        normalized = normalize_front_matter(original)
        if normalized != original:
            md_path.write_text(normalized, encoding="utf-8")
            print(f"Normalized front matter in {md_path}")
            changes += 1

    if changes == 0:
        print("Front matter already normalized.")
    else:
        print(f"Normalized {changes} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
