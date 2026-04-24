#!/usr/bin/env python3
"""Run the local study note pipeline end to end from source files to AFFiNE bundle."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_STYLE_EXAMPLE = Path("/Users/Madu/Downloads/Week2_Preferences_Utility_Notes(1).md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", required=True, help="Course or unit name for the notes")
    parser.add_argument("--slides", action="append", default=[], help="Slide file or directory")
    parser.add_argument("--textbook", action="append", default=[], help="Textbook file or directory")
    parser.add_argument("--transcripts", action="append", default=[], help="Transcript file or directory")
    parser.add_argument(
        "--practice",
        action="append",
        default=[],
        help="Exercises, problem sets, or exam-style file/directory. Directories are scanned recursively.",
    )
    parser.add_argument(
        "--practice-dir",
        action="append",
        default=[],
        help="Folder containing exercises/problem sets. All supported files inside are ingested recursively.",
    )
    parser.add_argument("--workdir", required=True, help="Pipeline working directory")
    parser.add_argument("--workspace", default=".", help="Workspace root for the Codex run")
    parser.add_argument("--model", default="", help="Optional Codex model override")
    parser.add_argument("--style-example", default=str(DEFAULT_STYLE_EXAMPLE), help="Markdown example to imitate")
    parser.add_argument(
        "--skip-codex",
        action="store_true",
        help="Only prepare corpus and prompt files without invoking codex exec",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parent
    skill_dir = root.parent
    workspace = Path(args.workspace).expanduser().resolve()
    workdir = Path(args.workdir).expanduser().resolve()
    corpus_dir = workdir / "corpus"
    analysis_dir = workdir / "analysis"
    notes_dir = workdir / "notes"
    html_dir = workdir / "html"
    affine_dir = workdir / "affine-import"
    prompt_dir = workdir / "prompts"
    log_dir = workdir / "logs"

    for path in [workdir, notes_dir, html_dir, prompt_dir, log_dir]:
        path.mkdir(parents=True, exist_ok=True)

    run(
        [
            sys.executable,
            str(root / "prepare_note_job.py"),
            *flatten_flag("--slides", args.slides),
            *flatten_flag("--textbook", args.textbook),
            *flatten_flag("--transcripts", args.transcripts),
            *flatten_flag("--practice", args.practice + args.practice_dir),
            "--workdir",
            str(workdir),
        ]
    )

    style_example_path = Path(args.style_example).expanduser().resolve()
    style_example_text = ""
    if style_example_path.exists():
        style_example_text = style_example_path.read_text(encoding="utf-8", errors="ignore")

    prompt = render_prompt(
        course=args.course,
        skill_dir=skill_dir,
        corpus_dir=corpus_dir,
        analysis_dir=analysis_dir,
        notes_dir=notes_dir,
        html_dir=html_dir,
        style_example_path=style_example_path,
        style_example_text=style_example_text,
    )
    prompt_path = prompt_dir / "note-generation-prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    if not args.skip_codex:
        codex_bin = shutil.which("codex")
        if not codex_bin:
            raise RuntimeError("`codex` CLI was not found in PATH.")

        cmd = [
            codex_bin,
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "--cd",
            str(workspace),
            "--add-dir",
            str(workdir),
            "--output-last-message",
            str(log_dir / "codex-last-message.txt"),
            "-",
        ]
        if args.model:
            cmd[2:2] = ["--model", args.model]
        run(cmd, input_text=prompt)

        markdown_files = sorted(notes_dir.rglob("*.md"))
        html_path = html_dir / "study-pack.html"
        if not markdown_files:
            raise RuntimeError(f"Codex completed but produced no Markdown notes in {notes_dir}")
        if not html_path.exists():
            raise RuntimeError(f"Codex completed but did not create the HTML study pack at {html_path}")

        run(
            [
                sys.executable,
                str(root / "package_affine_import.py"),
                "--notes",
                str(notes_dir),
                "--out",
                str(affine_dir),
            ]
        )

    summary = [
        "Pipeline complete.",
        f"Notes: {notes_dir}",
        f"HTML: {html_dir / 'study-pack.html'}",
        f"Prompt: {prompt_path}",
    ]
    if args.skip_codex:
        summary.append("Codex generation was skipped. No AFFiNE bundle was created.")
    else:
        summary.append(f"AFFiNE import bundle: {affine_dir}")
    print("\n".join(summary))
    return 0


def flatten_flag(flag: str, values: list[str]) -> list[str]:
    flattened: list[str] = []
    for value in values:
        flattened.extend([flag, value])
    return flattened


def render_prompt(
    *,
    course: str,
    skill_dir: Path,
    corpus_dir: Path,
    analysis_dir: Path,
    notes_dir: Path,
    html_dir: Path,
    style_example_path: Path,
    style_example_text: str,
) -> str:
    notes_dir_abs = notes_dir.resolve()
    html_path = (html_dir / "study-pack.html").resolve()
    example_block = ""
    if style_example_text:
        example_block = f"""
Style anchor:
- The user wants the notes to sound and read like this exact example: {style_example_path}
- Use its depth, pacing, sectioning, proof style, and explanatory tone as the primary template.

Example note content to imitate:

```markdown
{style_example_text}
```
"""
    return f"""Use the local study-note pipeline in this workspace to create final study notes.

Read these files first:
- {skill_dir / 'SKILL.md'}
- {skill_dir / 'references' / 'output-contract.md'}
- {skill_dir / 'references' / 'make-notes-pretty.md'}
- {corpus_dir / 'manifest.md'}
- {analysis_dir / 'topic-clusters.md'}
- {analysis_dir / 'gap-report.md'}
- {analysis_dir / 'note-brief.md'}
{example_block}

Task:
- Course name: {course}
- Create exam-ready Markdown notes in: {notes_dir_abs}
- Create one self-contained styled HTML study pack in: {html_path}
- Use the analysis outputs to cluster by topic/week and explicitly recover points emphasized in transcripts but missing from slides.
- Use any practice materials in the corpus as strong evidence for what answer structures, derivations, and proof sequences matter on the exam.
- Follow the Markdown structure in output-contract.md for the AFFiNE import files.
- Follow make-notes-pretty.md for the HTML file styling and layout.
- Assume the reader may as well be learning the course from scratch from these notes.
- Prioritise equations, proof logic, derivation flow, and the sequence of steps needed to solve exam-style questions.
- Use more diagrams, visual aids, and flowcharts where they materially improve understanding.
- In the HTML version, apply the user-provided palette from make-notes-pretty.md and make the document suitable for AFFiNE HTML import as well.
- Use the preferred example as the actual template:
  - explanatory honours-level prose, not terse summaries
  - formal definitions, propositions, intuition, and proof sketches where useful
  - explicit `Exam tip` callouts
  - comparison tables when they clarify assumptions or concepts
  - no citations or references section unless explicitly required
  - phrasing should feel like polished study notes written by a strong student

Output requirements:
- Create one or more Markdown files inside {notes_dir_abs}
- Create exactly one HTML file at {html_path}
- Use ASCII-safe filenames for Markdown notes
- Do not ask follow-up questions; make reasonable assumptions and proceed from the available corpus and analysis files

Before finishing:
- Verify that every Markdown file has a top-level `#` heading
- Verify that the HTML file is self-contained
- If any source quality issues materially limit the notes, mention them briefly in the final message
"""


def run(cmd: list[str], input_text: str | None = None) -> None:
    subprocess.run(cmd, check=True, text=True, input=input_text)


if __name__ == "__main__":
    raise SystemExit(main())
