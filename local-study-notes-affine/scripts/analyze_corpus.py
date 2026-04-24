#!/usr/bin/env python3
"""Infer week/topic clusters and detect slide-vs-transcript gaps from a built corpus."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


STOPWORDS = {
    "a", "about", "after", "all", "also", "an", "and", "are", "as", "at", "be", "because",
    "been", "being", "between", "both", "but", "by", "can", "could", "did", "do", "does",
    "doing", "for", "from", "had", "has", "have", "if", "in", "into", "is", "it", "its",
    "just", "more", "most", "not", "of", "on", "or", "our", "so", "that", "the", "their",
    "them", "then", "there", "these", "they", "this", "those", "to", "too", "under", "up",
    "use", "using", "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "with", "would", "you", "your", "lecture", "week", "slide", "slides", "transcript",
    "textbook", "chapter", "page", "pages", "topic", "topics", "model", "models",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, help="Path to corpus.json")
    parser.add_argument("--out", required=True, help="Directory for analysis outputs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_path = Path(args.corpus).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    chunks = payload["chunks"]

    files = index_files(chunks)
    clusters = build_clusters(files)
    gaps = build_gap_report(clusters, chunks)

    write_json(out_dir / "clusters.json", {"clusters": clusters})
    write_markdown(out_dir / "topic-clusters.md", render_clusters_md(clusters))
    write_markdown(out_dir / "gap-report.md", render_gap_md(gaps))
    write_markdown(out_dir / "note-brief.md", render_brief_md(clusters, gaps))
    return 0


def index_files(chunks: list[dict]) -> dict[str, dict]:
    files: dict[str, dict] = {}
    for chunk in chunks:
        source = chunk["source_file"]
        entry = files.setdefault(
            source,
            {
                "source_file": source,
                "source_name": chunk["source_name"],
                "role": chunk["role"],
                "week": infer_week(source, chunk["source_name"], chunk["text"]),
                "text": [],
            },
        )
        entry["text"].append(chunk["text"])
    for entry in files.values():
        joined = "\n".join(entry["text"])
        entry["full_text"] = joined
        entry["keywords"] = top_keywords(joined, limit=12)
    return files


def build_clusters(files: dict[str, dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for file_info in files.values():
        grouped[file_info["week"]].append(file_info)

    clusters: list[dict] = []
    for week, members in sorted(grouped.items(), key=week_sort_key):
        topic = infer_topic_label(members)
        role_map: dict[str, list[str]] = defaultdict(list)
        for member in sorted(members, key=lambda item: (item["role"], item["source_name"])):
            role_map[member["role"]].append(member["source_name"])
        combined_text = "\n".join(member["full_text"] for member in members)
        clusters.append(
            {
                "cluster_id": slugify(f"{week}-{topic}"),
                "week": week,
                "topic": topic,
                "keywords": top_keywords(combined_text, limit=10),
                "files": {role: names for role, names in sorted(role_map.items())},
            }
        )
    return clusters


def build_gap_report(clusters: list[dict], chunks: list[dict]) -> list[dict]:
    by_week_role: dict[tuple[str, str], list[str]] = defaultdict(list)
    for chunk in chunks:
        week = infer_week(chunk["source_file"], chunk["source_name"], chunk["text"])
        by_week_role[(week, chunk["role"])].append(chunk["text"])

    gaps: list[dict] = []
    for cluster in clusters:
        week = cluster["week"]
        slide_text = "\n".join(by_week_role.get((week, "slides"), []))
        transcript_text = "\n".join(by_week_role.get((week, "transcripts"), []))
        textbook_text = "\n".join(by_week_role.get((week, "textbook"), []))

        slide_terms = weighted_terms(slide_text)
        transcript_terms = weighted_terms(transcript_text)
        textbook_terms = weighted_terms(textbook_text)

        lecturer_only = diff_terms(transcript_terms, slide_terms)
        slide_only = diff_terms(slide_terms, transcript_terms)
        textbook_support = overlap_terms(lecturer_only, textbook_terms)

        gaps.append(
            {
                "week": week,
                "topic": cluster["topic"],
                "lecturer_only_terms": lecturer_only[:10],
                "slide_only_terms": slide_only[:8],
                "textbook_supported_terms": textbook_support[:8],
                "coverage_score": coverage_score(slide_terms, transcript_terms),
            }
        )
    return gaps


def infer_week(path: str, name: str, sample_text: str) -> str:
    haystack = f"{path} {name} {sample_text[:400]}".lower()
    patterns = [
        r"week[\s_-]*(\d{1,2})(?!\d)",
        r"(?:^|[^a-z0-9])w[\s_-]?(\d{1,2})(?!\d)",
        r"lec(?:ture)?[\s_-]*(\d{1,2})(?!\d)",
        r"class[\s_-]*(\d{1,2})(?!\d)",
    ]
    for pattern in patterns:
        match = re.search(pattern, haystack)
        if match:
            return f"week-{int(match.group(1)):02d}"
    return "week-unknown"


def infer_topic_label(members: list[dict]) -> str:
    counter: Counter[str] = Counter()
    for member in members:
        counter.update(member["keywords"])
    words = [word for word, _ in counter.most_common(3)]
    return " / ".join(words) if words else "general-topic"


def top_keywords(text: str, limit: int) -> list[str]:
    counter = weighted_terms(text)
    return [term for term, _ in counter.most_common(limit)]


def weighted_terms(text: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for token in tokenize(text):
        if token in STOPWORDS or len(token) < 3 or token.isdigit():
            continue
        counter[token] += 1
    return counter


def diff_terms(primary: Counter[str], reference: Counter[str]) -> list[str]:
    scored: list[tuple[str, float]] = []
    for term, count in primary.items():
        reference_count = reference.get(term, 0)
        score = count - reference_count
        if score >= 2:
            scored.append((term, score))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return [term for term, _ in scored]


def overlap_terms(primary_terms: list[str], supporting_counter: Counter[str]) -> list[str]:
    overlap = [term for term in primary_terms if supporting_counter.get(term, 0) > 0]
    return overlap


def coverage_score(slide_terms: Counter[str], transcript_terms: Counter[str]) -> float:
    transcript_vocab = {term for term, count in transcript_terms.items() if count >= 2}
    if not transcript_vocab:
        return 1.0
    covered = sum(1 for term in transcript_vocab if slide_terms.get(term, 0) > 0)
    return covered / len(transcript_vocab)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9\-]{1,}", text.lower())


def week_sort_key(item: tuple[str, list[dict]]) -> tuple[int, str]:
    week = item[0]
    match = re.search(r"(\d+)$", week)
    if match:
        return (int(match.group(1)), week)
    return (math.inf, week)


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "cluster"


def render_clusters_md(clusters: list[dict]) -> str:
    lines = ["# Topic Clusters", ""]
    for cluster in clusters:
        lines.extend(
            [
                f"## {cluster['week']}: {cluster['topic']}",
                "",
                f"- Keywords: {', '.join(cluster['keywords'])}",
            ]
        )
        for role, names in cluster["files"].items():
            lines.append(f"- {role.title()}: {', '.join(names)}")
        lines.append("")
    return "\n".join(lines) + "\n"


def render_gap_md(gaps: list[dict]) -> str:
    lines = ["# Gap Report", "", "Use this to prioritize what the final notes should recover from speech rather than slides.", ""]
    for gap in gaps:
        coverage_pct = round(gap["coverage_score"] * 100)
        lines.extend(
            [
                f"## {gap['week']}: {gap['topic']}",
                "",
                f"- Slide coverage of transcript vocabulary: {coverage_pct}%",
                f"- Lecturer-emphasized terms missing or underrepresented on slides: {', '.join(gap['lecturer_only_terms']) or 'None detected'}",
                f"- Slide-heavy terms not emphasized in transcript: {', '.join(gap['slide_only_terms']) or 'None detected'}",
                f"- Lecturer-only terms also supported by textbook wording: {', '.join(gap['textbook_supported_terms']) or 'None detected'}",
                "",
            ]
        )
    return "\n".join(lines)


def render_brief_md(clusters: list[dict], gaps: list[dict]) -> str:
    gap_map = {gap["week"]: gap for gap in gaps}
    lines = [
        "# Note Brief",
        "",
        "Draft notes topic-by-topic using the clusters below. For each topic, explicitly include the lecturer-only concepts where they change intuition, derivation steps, or exam framing.",
        "",
    ]
    for cluster in clusters:
        gap = gap_map.get(cluster["week"], {})
        lines.extend(
            [
                f"## Draft Target: {cluster['week']} - {cluster['topic']}",
                "",
                f"- Source files: {', '.join(sum(cluster['files'].values(), []))}",
                f"- Anchor terms: {', '.join(cluster['keywords'])}",
                f"- Must recover from transcript: {', '.join(gap.get('lecturer_only_terms', [])[:6]) or 'None detected'}",
                f"- Check textbook support for: {', '.join(gap.get('textbook_supported_terms', [])[:5]) or 'None detected'}",
                "",
            ]
        )
    return "\n".join(lines)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_markdown(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
