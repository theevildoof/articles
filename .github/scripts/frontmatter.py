#!/usr/bin/env python3
"""Utilities for normalizing Markdown front matter blocks."""
from __future__ import annotations

from typing import Optional, Tuple


def _find_front_matter(lines: list[str]) -> Tuple[Optional[int], Optional[int]]:
    """Return the start and end indices (inclusive) of the front matter block."""
    start: Optional[int] = None
    for idx, line in enumerate(lines):
        if line.strip() == "---":
            if start is None:
                start = idx
            else:
                return start, idx
    return start, None


def normalize_front_matter(text: str) -> str:
    """Ensure that a Markdown document starts with a tidy front matter block.

    The function performs the following adjustments:
    - removes leading blank lines before the first `---` marker
    - trims trailing whitespace on front matter lines
    - guarantees a blank line between the front matter and body content
    - ensures the result ends with a single newline when content exists
    """
    if not text:
        return text

    lines = text.splitlines()
    start, end = _find_front_matter(lines)

    if start is None or end is None:
        # No complete front matter block; just trim trailing whitespace/newlines.
        cleaned = "\n".join(line.rstrip() for line in lines).strip("\n")
        return (cleaned + "\n") if cleaned else ""

    # Determine if anything except whitespace appears before the front matter.
    prefix = lines[:start]
    if any(line.strip() for line in prefix):
        cleaned = "\n".join(line.rstrip() for line in lines).strip("\n")
        return cleaned + "\n"

    front = [line.rstrip() for line in lines[start : end + 1]]
    remainder = [line.rstrip() for line in lines[end + 1 :]]

    # Remove blank lines immediately following the front matter.
    while remainder and not remainder[0].strip():
        remainder.pop(0)

    normalized_lines = front + [""]
    normalized_lines.extend(remainder)

    normalized = "\n".join(normalized_lines).strip("\n")
    return (normalized + "\n") if normalized else ""


__all__ = ["normalize_front_matter"]
