#!/usr/bin/env python3
"""Package Markdown study notes into an AFFiNE-ready import directory."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notes", required=True, help="Markdown file or directory")
    parser.add_argument("--out", required=True, help="Output bundle directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notes_path = Path(args.notes).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    markdown_files = collect_markdown(notes_path)
    manifest = []

    for note in markdown_files:
        relative = note.relative_to(notes_path) if notes_path.is_dir() else Path(note.name)
        target = out_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(note, target)
        manifest.append(
            {
                "file": str(relative),
                "title": extract_title(note),
                "bytes": note.stat().st_size,
            }
        )

    (out_dir / "affine-import-manifest.json").write_text(
        json.dumps({"notes": manifest}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Packaged {len(markdown_files)} Markdown files into {out_dir}")
    return 0


def collect_markdown(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() == ".md" else []
    return sorted(file for file in path.rglob("*.md") if file.is_file())


def extract_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


if __name__ == "__main__":
    raise SystemExit(main())
