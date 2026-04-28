#!/usr/bin/env python3
"""Run the local study-note preparation pipeline up to the note-writing stage."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


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
    parser.add_argument("--workdir", required=True, help="Pipeline working directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parent
    workdir = Path(args.workdir).expanduser().resolve()
    corpus_dir = workdir / "corpus"
    analysis_dir = workdir / "analysis"
    workdir.mkdir(parents=True, exist_ok=True)

    run(
        [
            sys.executable,
            str(root / "build_corpus.py"),
            *flatten_flag("--slides", args.slides),
            *flatten_flag("--textbook", args.textbook),
            *flatten_flag("--transcripts", args.transcripts),
            *flatten_flag("--practice", args.practice),
            "--out",
            str(corpus_dir),
        ]
    )
    run(
        [
            sys.executable,
            str(root / "analyze_corpus.py"),
            "--corpus",
            str(corpus_dir / "corpus.json"),
            "--out",
            str(analysis_dir),
        ]
    )
    run(
        [
            sys.executable,
            str(root / "analyze_practice.py"),
            "--corpus",
            str(corpus_dir / "corpus.json"),
            "--analysis-dir",
            str(analysis_dir),
            "--out",
            str(analysis_dir),
        ]
    )
    print("Prepared corpus and analysis:")
    print(f"- {corpus_dir}")
    print(f"- {analysis_dir}")
    return 0


def flatten_flag(flag: str, values: list[str]) -> list[str]:
    flattened: list[str] = []
    for value in values:
        flattened.extend([flag, value])
    return flattened


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    raise SystemExit(main())
