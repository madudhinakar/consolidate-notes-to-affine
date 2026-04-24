#!/usr/bin/env python3
"""Build a local study corpus from slides, textbook files, and transcripts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
from zipfile import ZipFile


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".srt", ".vtt"}
TEXTISH_EXTENSIONS = {".txt", ".md"}
TRANSCRIPT_EXTENSIONS = {".srt", ".vtt"}
WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


@dataclass
class Chunk:
    chunk_id: str
    role: str
    source_file: str
    source_name: str
    locator: str
    order: int
    text: str
    word_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slides", action="append", default=[], help="Slide file or directory")
    parser.add_argument("--textbook", action="append", default=[], help="Textbook file or directory")
    parser.add_argument("--transcripts", action="append", default=[], help="Transcript file or directory")
    parser.add_argument(
        "--practice",
        action="append",
        default=[],
        help="Exercises, problem sets, or exam-style file/directory. Directories are scanned recursively.",
    )
    parser.add_argument("--out", required=True, help="Output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    groups = {
        "slides": collect_files(args.slides),
        "textbook": collect_files(args.textbook),
        "transcripts": collect_files(args.transcripts),
        "practice": collect_files(args.practice),
    }

    if not any(groups.values()):
        print("No input files found.", file=sys.stderr)
        return 1

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    chunks: list[Chunk] = []
    manifest: dict[str, object] = {
        "source_counts": {},
        "files": [],
    }

    for role, files in groups.items():
        manifest["source_counts"][role] = len(files)
        for file_path in files:
            extracted = extract_file(role, file_path)
            chunks.extend(extracted)
            manifest["files"].append(
                {
                    "role": role,
                    "path": str(file_path),
                    "chunks": len(extracted),
                    "words": sum(chunk.word_count for chunk in extracted),
                }
            )

    write_json(out_dir / "corpus.json", {"chunks": [asdict(chunk) for chunk in chunks], "manifest": manifest})
    write_jsonl(out_dir / "chunks.jsonl", chunks)
    write_manifest(out_dir / "manifest.md", manifest, chunks)
    print(f"Wrote corpus with {len(chunks)} chunks to {out_dir}")
    return 0


def collect_files(raw_paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for raw in raw_paths:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            print(f"Skipping missing path: {path}", file=sys.stderr)
            continue
        candidates = [path]
        if path.is_dir():
            candidates = sorted(p for p in path.rglob("*") if p.is_file())
        for candidate in candidates:
            if candidate.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if candidate not in seen:
                seen.add(candidate)
                files.append(candidate)
    return sorted(files)


def extract_file(role: str, path: Path) -> list[Chunk]:
    suffix = path.suffix.lower()
    if suffix in TEXTISH_EXTENSIONS:
        parts = parse_plain_text(path.read_text(encoding="utf-8", errors="ignore"))
    elif suffix == ".docx":
        parts = parse_docx(path)
    elif suffix == ".pdf":
        parts = parse_pdf(path)
    elif suffix in TRANSCRIPT_EXTENSIONS:
        parts = parse_transcript_cues(path.read_text(encoding="utf-8", errors="ignore"))
    else:
        raise ValueError(f"Unsupported file type: {path}")

    chunks: list[Chunk] = []
    stem = slugify(path.stem)
    for index, part in enumerate(parts, start=1):
        text = normalize_text(part["text"])
        if not text:
            continue
        chunks.append(
            Chunk(
                chunk_id=f"{stem}-{index:04d}",
                role=role,
                source_file=str(path),
                source_name=path.name,
                locator=part["locator"],
                order=index,
                text=text,
                word_count=count_words(text),
            )
        )
    return chunks


def parse_plain_text(text: str) -> list[dict[str, str]]:
    blocks = split_paragraphs(text)
    return [{"locator": f"para {index}", "text": block} for index, block in enumerate(blocks, start=1)]


def parse_transcript_cues(text: str) -> list[dict[str, str]]:
    lines = [line.rstrip() for line in text.splitlines()]
    chunks: list[dict[str, str]] = []
    buffer: list[str] = []
    locator = ""

    def flush() -> None:
        nonlocal buffer, locator
        joined = " ".join(buffer).strip()
        if joined:
            chunks.append({"locator": locator or f"cue {len(chunks) + 1}", "text": joined})
        buffer = []
        locator = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.isdigit():
            continue
        if "-->" in stripped:
            flush()
            locator = stripped
            continue
        if stripped.upper().startswith("WEBVTT"):
            continue
        buffer.append(stripped)
    flush()
    return chunks


def parse_docx(path: Path) -> list[dict[str, str]]:
    with ZipFile(path) as archive:
        xml_bytes = archive.read("word/document.xml")
    root = ET.fromstring(xml_bytes)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", WORD_NS):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", WORD_NS)]
        joined = "".join(texts).strip()
        if joined:
            paragraphs.append(joined)
    return [{"locator": f"para {index}", "text": text} for index, text in enumerate(paragraphs, start=1)]


def parse_pdf(path: Path) -> list[dict[str, str]]:
    reader = import_pdf_reader()
    pdf = reader(str(path))
    parts: list[dict[str, str]] = []
    for index, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        blocks = split_paragraphs(text)
        if not blocks:
            continue
        for block_index, block in enumerate(blocks, start=1):
            parts.append({"locator": f"p.{index} block {block_index}", "text": block})
    return parts


def import_pdf_reader():
    try:
        from pypdf import PdfReader  # type: ignore

        return PdfReader
    except Exception:
        pass

    try:
        from PyPDF2 import PdfReader  # type: ignore

        return PdfReader
    except Exception as exc:
        raise RuntimeError(
            "PDF extraction requires `pypdf` or `PyPDF2`. Install one of them and rerun."
        ) from exc


def split_paragraphs(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    raw_blocks = re.split(r"\n\s*\n", normalized)
    blocks: list[str] = []
    for block in raw_blocks:
        clean = normalize_text(block)
        if clean:
            blocks.append(clean)
    return blocks


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "source"


def count_words(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, chunks: Iterable[Chunk]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")


def write_manifest(path: Path, manifest: dict[str, object], chunks: list[Chunk]) -> None:
    files = manifest["files"]
    total_words = sum(chunk.word_count for chunk in chunks)
    total_chunks = len(chunks)

    lines = [
        "# Corpus Manifest",
        "",
        f"- Total chunks: {total_chunks}",
        f"- Total words: {total_words}",
        f"- Slide files: {manifest['source_counts']['slides']}",
        f"- Textbook files: {manifest['source_counts']['textbook']}",
        f"- Transcript files: {manifest['source_counts']['transcripts']}",
        f"- Practice files: {manifest['source_counts']['practice']}",
        "",
        "## Files",
        "",
        "| Role | File | Chunks | Words |",
        "| --- | --- | ---: | ---: |",
    ]

    for item in files:
        file_name = Path(item["path"]).name
        lines.append(f"| {item['role']} | {file_name} | {item['chunks']} | {item['words']} |")

    lines.extend(
        [
            "",
            "## Suggested inspection commands",
            "",
            "- `rg 'OLS|heteroskedasticity|Nash|IS-LM' chunks.jsonl`",
            "- `rg 'lecture 3|week 3|midsem' chunks.jsonl`",
            "- `jq '.chunks[] | select(.role == \"transcripts\")' corpus.json`",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
