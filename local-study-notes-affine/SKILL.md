---
name: local-study-notes-affine
description: Use this skill when the user wants Codex to turn local lecture slides, textbook chapters, and lecture transcripts into exam-ready study notes for AFFiNE. This skill is for offline source ingestion, cross-referencing what appears on slides against what the lecturer actually said, extracting equations and formal definitions from dense economics or econometrics material, and exporting the final notes as structured Markdown files that AFFiNE can import.
---

# Local Study Notes To AFFiNE

## Overview

This skill builds a local-first study-note pipeline for dense university subjects where slides are incomplete without lecture audio and textbook detail. It uses helper scripts to extract source text into a corpus, then has Codex synthesize high-signal Markdown notes with equations, diagrams, source citations, and an AFFiNE-ready export bundle.

AFFiNE's public import guidance still supports Markdown import, so default the importable deliverable to Markdown files plus any local assets referenced by those files. Also produce a styled HTML study pack by following `references/make-notes-pretty.md`.

## Workflow

1. Collect source paths from the user.
2. Run `scripts/build_corpus.py` to extract text from local source files into a machine-readable corpus.
3. Run `scripts/analyze_corpus.py` to infer week and topic clusters, and to detect what the lecturer emphasized that the slides understate or omit.
4. Run `scripts/analyze_practice.py` to classify practice problems, infer opening moves, build a problem-identification flowchart, and map problems back to note topics.
5. Read `corpus/manifest.md` first, then inspect only the relevant chunks in `corpus/chunks.jsonl` or `corpus/corpus.json`.
6. Read `analysis/topic-clusters.md`, `analysis/gap-report.md`, `analysis/note-brief.md`, `analysis/practice-problem-analysis.md`, `analysis/problem-type-playbook.md`, and `analysis/topic-dependency-map.md` before drafting notes.
7. Synthesize notes by topic, not by file order.
8. Package the final Markdown into an AFFiNE import directory with `scripts/package_affine_import.py`.

## Input Expectations

Preferred source groupings:

- `slides/`: lecture PDFs
- `textbook/`: textbook PDF or chapter extracts
- `transcripts/`: `.txt`, `.md`, `.docx`, `.srt`, `.vtt`, or PDF transcripts

If the user provides a mixed directory, use file extensions and path names to infer the role. Treat transcripts as the best signal for lecturer emphasis, slides as the best signal for lecture structure, and textbook content as the best signal for formal derivations, definitions, and notation.

## Commands

Build the corpus:

```bash
python3 local-study-notes-affine/scripts/build_corpus.py \
  --slides "/absolute/path/to/slides" \
  --textbook "/absolute/path/to/textbook" \
  --transcripts "/absolute/path/to/transcripts" \
  --out "/absolute/path/to/workdir/corpus"
```

Package notes for AFFiNE import:

```bash
python3 local-study-notes-affine/scripts/package_affine_import.py \
  --notes "/absolute/path/to/workdir/notes" \
  --out "/absolute/path/to/workdir/affine-import"
```

Analyze the corpus for clustering and gaps:

```bash
python3 local-study-notes-affine/scripts/analyze_corpus.py \
  --corpus "/absolute/path/to/workdir/corpus/corpus.json" \
  --out "/absolute/path/to/workdir/analysis"
```

Run the full pipeline end to end:

```bash
bash local-study-notes-affine/run-study-notes.sh \
  --course "ECON4040 Honours Econometrics" \
  --slides "/absolute/path/to/slides" \
  --textbook "/absolute/path/to/textbook" \
  --transcripts "/absolute/path/to/transcripts" \
  --practice-dir "/absolute/path/to/exercises-and-problem-sets" \
  --workdir "/absolute/path/to/workdir"
```

## Synthesis Rules

- Start from transcript emphasis: repeated verbal explanations, caveats, intuitions, exam hints, and worked examples matter more than slide brevity.
- Use slides to recover the lecture sequence and anchor claims to page numbers where possible.
- Use the textbook to enrich every shared concept with missing steps in proofs, derivations, model assumptions, notation conventions, and extra explanatory detail.
- Use the topic clusters to decide note boundaries. Prefer one note per coherent lecture block or econometric topic, not one note per raw file.
- Use the gap report as a priority list for "What the slides missed" and "How the lecturer framed it".
- Do not collapse overlap into a single "same point" summary. If the slide, transcript, and textbook all cover a concept, merge them into a richer explanation that preserves what each source adds.
- Treat the transcript as a second explanatory source, not just confirmation of the slides. Ask:
  - what wording did the professor use that differs from the slide?
  - what intuition, warning, or example appeared verbally?
  - what did the slide state more formally or compactly?
  - what extra depth or rigor does the textbook add?
- If two sources say roughly the same thing in different language, keep both signals and either compare the phrasings or combine them into a stronger explanation.
- If a concept appears in only one of the three sources, keep it.
- Nothing should be dropped just because it seems obvious or already mentioned elsewhere.
- Treat practice problems as a fourth source: not for factual content, but for what operations the student is expected to perform with the concepts.
- For every concept that appears in at least one problem, enrich the notes so they teach the problem-solving process:
  - classify the problem type
  - extract the opening move
  - map the concept to the parts of a solution where it is actually used
  - show the skeleton of a correct argument
- Do not collapse different problem types just because they use the same concept. "derive the object" and "test a claim about the object" must remain distinct if the required opening moves differ.
- When the material is mathematically dense, render equations in LaTeX blocks and explain each term in plain language.
- Use Mermaid when a process or concept map is clearer than prose.
- Flag disagreements or ambiguities explicitly. If the lecturer's framing differs from the textbook, say so.
- Produce two final artifacts when the user asks for polished notes:
  - AFFiNE import Markdown files following `references/output-contract.md`
  - a single styled HTML study pack following `references/make-notes-pretty.md`

## Output Contract

Read `references/output-contract.md` before drafting the final notes. The notes should usually include:

- a one-paragraph topic summary
- core definitions
- theorem or model statements
- derivations or equation walkthroughs
- intuition and economic interpretation
- lecturer-only clarifications and slide omissions
- common traps or examiner-style misconceptions
- short recall questions or mini problem prompts
- problem-solving context blocks for every tested concept

## Inspection Strategy

Do not load the entire corpus into context if it is large.

- Read `corpus/manifest.md` to identify relevant files and chunk counts.
- Read `analysis/topic-clusters.md` to map source files into weeks and topics.
- Read `analysis/gap-report.md` to see transcript concepts missing from slides.
- Read `analysis/practice-problem-analysis.md` and `analysis/problem-type-playbook.md` to identify how problems operationalize the concepts.
- Read `analysis/problem-identification-flowchart.md` to see the decision logic for unseen problems.
- Read `analysis/topic-dependency-map.md` to identify which note sections must receive problem-solving enrichment.
- Use `rg` on `chunks.jsonl` to pull only the weeks, models, or keywords needed for the current notes.
- If one lecture's transcript is noisy, prioritize slide structure and textbook clarification, and say that you are inferring missing detail.
- If using the full runner, inspect `workdir/prompts/note-generation-prompt.md` and `workdir/logs/codex-last-message.txt` if generation fails or needs refinement.
- When comparing sources for one concept, inspect at least one chunk from each available source before drafting that concept explanation.

## Failure Modes

- If PDF extraction is poor, note it and ask the user for OCR'd PDFs or transcript text.
- If a transcript lacks timestamps or speaker markers, treat paragraph boundaries as the citation unit.
- If textbook extraction is too large, summarize only the sections directly tied to the lecture topics under review.
