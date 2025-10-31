#!/usr/bin/env python3
"""Convert notebooks in ./notebooks into Markdown pages for Just the Docs."""
from __future__ import annotations

import sys
from pathlib import Path
import shutil

import nbformat
from nbconvert import MarkdownExporter
from traitlets.config import Config

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
NOTEBOOK_DIR = ROOT / "notebooks"
OUTPUT_DIR = ROOT / "docs" / "notebooks"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from frontmatter import normalize_front_matter


def ensure_unique_output_filenames(nb_node: nbformat.NotebookNode) -> None:
    """Adjust output metadata so extracted files always have unique names."""

    used: set[str] = set()

    def allocate(original: str) -> str:
        path = Path(original)
        stem = path.stem
        suffix = path.suffix
        parent = path.parent

        candidate = original
        index = 1
        while candidate in used:
            candidate = str(parent / f"{stem}-{index}{suffix}")
            index += 1
        used.add(candidate)
        return candidate

    for cell in nb_node.cells:
        for output in getattr(cell, "outputs", []):
            metadata = getattr(output, "metadata", {})
            if not isinstance(metadata, dict):
                continue

            filenames: dict[str, list[tuple[str, str | None]]] = {}

            filename = metadata.get("filename")
            if isinstance(filename, str):
                filenames.setdefault(filename, []).append(("filename", None))

            names_by_mime = metadata.get("filenames")
            if isinstance(names_by_mime, dict):
                for mime, name in names_by_mime.items():
                    if isinstance(name, str):
                        filenames.setdefault(name, []).append(("filenames", mime))

            if not filenames:
                continue

            for original, entries in filenames.items():
                new_name = allocate(original)
                for target, key in entries:
                    if target == "filename":
                        metadata["filename"] = new_name
                    else:
                        assert key is not None
                        metadata.setdefault("filenames", {})[key] = new_name


def convert_notebooks() -> None:
    if not NOTEBOOK_DIR.exists():
        print("No notebooks directory found; skipping conversion.")
        return

    notebooks = sorted(path for path in NOTEBOOK_DIR.glob("*.ipynb") if path.is_file())
    if not notebooks:
        print("No notebooks to convert.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    expected_stems = {path.stem for path in notebooks}

    # Remove Markdown files whose notebooks no longer exist.
    for md_path in sorted(OUTPUT_DIR.glob("*.md")):
        if md_path.stem not in expected_stems:
            print(f"Removing stale export: {md_path.relative_to(ROOT)}")
            md_path.unlink()

    # Remove asset directories for deleted notebooks.
    for assets_dir in sorted(OUTPUT_DIR.glob("*_files")):
        stem = assets_dir.name.removesuffix("_files")
        if stem not in expected_stems:
            print(f"Removing stale assets: {assets_dir.relative_to(ROOT)}")
            shutil.rmtree(assets_dir)

    config = Config()
    config.MarkdownExporter.preprocessors = ["nbconvert.preprocessors.ExtractOutputPreprocessor"]
    exporter = MarkdownExporter(config=config)
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True

    for nb_path in notebooks:
        print(f"Converting {nb_path.relative_to(ROOT)}")
        nb_node = nbformat.read(nb_path, as_version=4)
        ensure_unique_output_filenames(nb_node)

        if nb_node.cells:
            first_cell = nb_node.cells[0]
            source = first_cell.source if isinstance(first_cell.source, str) else "".join(first_cell.source)
            if source.lstrip().startswith("---"):
                if first_cell.cell_type != "raw":
                    nb_node.cells[0] = nbformat.v4.new_raw_cell(source)
                nb_node.cells[0].metadata.setdefault("raw_mimetype", "text/markdown")
            else:
                print(f"Warning: {nb_path.name} does not start with a front matter cell", file=sys.stderr)

        body, resources = exporter.from_notebook_node(nb_node)
        body = normalize_front_matter(body)

        output_md = OUTPUT_DIR / nb_path.with_suffix(".md").name
        previous = output_md.read_text(encoding="utf-8") if output_md.exists() else None
        if previous != body:
            output_md.write_text(body, encoding="utf-8")
            print(f"Wrote {output_md.relative_to(ROOT)}")

        output_dir_name = resources.get("output_files_dir") if resources else None
        if output_dir_name:
            assets_dir = OUTPUT_DIR / output_dir_name
        else:
            assets_dir = OUTPUT_DIR / f"{nb_path.stem}_files"

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

    print("Notebook conversion complete.")


if __name__ == "__main__":
    convert_notebooks()
