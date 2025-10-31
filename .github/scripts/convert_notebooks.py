#!/usr/bin/env python3
"""Convert notebooks in ./notebooks into Markdown pages for Just the Docs."""
from __future__ import annotations

import sys
from pathlib import Path
import shutil

import nbformat
from nbconvert import MarkdownExporter

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
NOTEBOOK_DIR = ROOT / "notebooks"
OUTPUT_DIR = ROOT / "docs" / "notebooks"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from frontmatter import normalize_front_matter


def iter_notebooks() -> list[Path]:
    """Return the notebooks under NOTEBOOK_DIR in a predictable order."""
    return sorted(path for path in NOTEBOOK_DIR.rglob("*.ipynb") if path.is_file())


def _relative_base(path: Path) -> Path:
    """Return the notebook path relative to NOTEBOOK_DIR without the .ipynb suffix."""
    relative = path.relative_to(NOTEBOOK_DIR)
    return relative.parent / path.stem


def _remove_empty_directories(root: Path) -> None:
    """Remove empty directories within ``root`` (post-order)."""
    for directory in sorted(root.rglob("*"), reverse=True):
        if directory.is_dir():
            try:
                next(directory.iterdir())
            except StopIteration:
                directory.rmdir()
                print(f"Removed empty directory: {directory.relative_to(ROOT)}")


def convert_notebooks() -> None:
    if not NOTEBOOK_DIR.exists():
        print("No notebooks directory found; skipping conversion.")
        return

    notebooks = iter_notebooks()
    if not notebooks:
        print("No notebooks to convert.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    expected_bases = {_relative_base(path) for path in notebooks}
    expected_markdown = {base.parent / f"{base.name}.md" for base in expected_bases}
    expected_assets = {base.parent / f"{base.name}_files" for base in expected_bases}

    # Remove Markdown files whose notebooks no longer exist.
    for md_path in sorted(OUTPUT_DIR.rglob("*.md")):
        relative_md = md_path.relative_to(OUTPUT_DIR)
        if relative_md not in expected_markdown:
            print(f"Removing stale export: {md_path.relative_to(ROOT)}")
            md_path.unlink()

    # Remove asset directories for deleted notebooks.
    for assets_dir in sorted(OUTPUT_DIR.rglob("*_files")):
        relative_assets = assets_dir.relative_to(OUTPUT_DIR)
        if relative_assets not in expected_assets:
            print(f"Removing stale assets: {assets_dir.relative_to(ROOT)}")
            shutil.rmtree(assets_dir)

    exporter = MarkdownExporter()
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True

    for nb_path in notebooks:
        print(f"Converting {nb_path.relative_to(ROOT)}")
        nb_node = nbformat.read(nb_path, as_version=4)

        if nb_node.cells:
            first_cell = nb_node.cells[0]
            source = first_cell.source if isinstance(first_cell.source, str) else "".join(first_cell.source)
            if source.lstrip().startswith("---"):
                if first_cell.cell_type != "raw":
                    nb_node.cells[0] = nbformat.v4.new_raw_cell(source)
                nb_node.cells[0].metadata.setdefault("raw_mimetype", "text/markdown")
            else:
                print(f"Warning: {nb_path.name} does not start with a front matter cell", file=sys.stderr)

        relative_base = _relative_base(nb_path)
        output_md = OUTPUT_DIR / relative_base.parent / f"{relative_base.name}.md"
        output_md.parent.mkdir(parents=True, exist_ok=True)

        resources_input = {
            "metadata": {"path": str(nb_path.parent)},
            "output_files_dir": str(relative_base.parent / f"{relative_base.name}_files"),
        }

        body, resources = exporter.from_notebook_node(nb_node, resources=resources_input)
        body = normalize_front_matter(body)

        previous = output_md.read_text(encoding="utf-8") if output_md.exists() else None
        if previous != body:
            output_md.write_text(body, encoding="utf-8")
            print(f"Wrote {output_md.relative_to(ROOT)}")

        output_dir_name = (
            resources.get("output_files_dir", resources_input["output_files_dir"])
            if resources
            else resources_input["output_files_dir"]
        )
        assets_dir = OUTPUT_DIR / output_dir_name
        if assets_dir.exists():
            shutil.rmtree(assets_dir)
            print(f"Cleared {assets_dir.relative_to(ROOT)}")

        outputs = resources.get("outputs", {}) if resources else {}
        for rel_path, data in outputs.items():
            asset_path = OUTPUT_DIR / rel_path
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(data, str):
                data = data.encode("utf-8")
            asset_path.write_bytes(data)
            print(f"Wrote {asset_path.relative_to(ROOT)}")

    _remove_empty_directories(OUTPUT_DIR)
    print("Notebook conversion complete.")


if __name__ == "__main__":
    convert_notebooks()
