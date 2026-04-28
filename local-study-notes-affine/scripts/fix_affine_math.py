#!/usr/bin/env python3
"""Convert markdown math-like spans into AFFiNE-friendly $$...$$ wrappers."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


FENCE_RE = re.compile(r"^(```|~~~)")
INLINE_CODE_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
INLINE_DOLLAR_RE = re.compile(r"(?<!\$)\$([^\$\n]+)\$(?!\$)")
INLINE_PAREN_RE = re.compile(r"\\\((.+?)\\\)")
DISPLAY_BRACKET_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Markdown file or directory to rewrite")
    parser.add_argument(
        "--out",
        help="Optional output directory. If omitted, files are rewritten in place.",
    )
    parser.add_argument(
        "--suffix",
        default="",
        help="Optional suffix for rewritten filenames when using --out, e.g. '-affine'.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = Path(args.target).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve() if args.out else None

    files = collect_markdown(target)
    if not files:
        raise SystemExit("No markdown files found.")

    for file_path in files:
        relative = file_path.relative_to(target) if target.is_dir() else Path(file_path.name)
        output_path = file_path
        if out_dir:
            stem = relative.stem + args.suffix
            output_path = out_dir / relative.with_name(stem + relative.suffix)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, output_path)

        original = output_path.read_text(encoding="utf-8", errors="ignore")
        rewritten = rewrite_markdown(original)
        output_path.write_text(rewritten, encoding="utf-8")
        print(f"Rewrote {output_path}")

    return 0


def collect_markdown(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() == ".md" else []
    return sorted(file for file in path.rglob("*.md") if file.is_file())


def rewrite_markdown(text: str) -> str:
    lines = text.splitlines(keepends=True)
    rewritten: list[str] = []
    in_fence = False

    for line in lines:
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            rewritten.append(line)
            continue

        if in_fence:
            rewritten.append(line)
            continue

        updated = line
        updated = DISPLAY_BRACKET_RE.sub(lambda m: wrap_math(m.group(1)), updated)
        updated = INLINE_PAREN_RE.sub(lambda m: wrap_math(m.group(1)), updated)
        updated = INLINE_DOLLAR_RE.sub(lambda m: wrap_math(m.group(1)), updated)
        updated = INLINE_CODE_RE.sub(lambda m: wrap_math(m.group(1)) if looks_math_like(m.group(1)) else m.group(0), updated)
        rewritten.append(updated)

    return "".join(rewritten)


def wrap_math(content: str) -> str:
    inner = content.strip()
    if inner.startswith("$$") and inner.endswith("$$"):
        return inner
    return f"$${inner}$$"


def looks_math_like(content: str) -> bool:
    stripped = content.strip()
    if not stripped:
        return False

    math_markers = [
        "\\",
        "^",
        "_",
        "{",
        "}",
        "=",
        "<",
        ">",
        "+",
        "-",
        "*",
        "/",
        "(",
        ")",
        "[",
        "]",
    ]
    if any(marker in stripped for marker in math_markers):
        return True

    if re.fullmatch(r"[A-Za-z]\w*", stripped):
        return True

    return False


if __name__ == "__main__":
    raise SystemExit(main())
