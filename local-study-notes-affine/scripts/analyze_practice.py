#!/usr/bin/env python3
"""Analyze practice materials into problem types, opening moves, and note dependencies."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


TYPE_RULES = [
    {
        "id": "prove-equivalence-or-implication",
        "label": "Prove equivalence or implication",
        "keywords": ["prove", "show that", "if and only if", "equivalent", "implies", "implication", "iff"],
        "opening_move": [
            "Write the exact statement to be shown, including both directions if it is an equivalence.",
            "List the definitions and assumptions that the statement depends on.",
            "Choose the proof route explicitly: direct proof, contradiction, contrapositive, or two-direction proof.",
        ],
        "usually_asked": ["prove", "show equivalence", "establish implication", "justify each logical step"],
    },
    {
        "id": "check-assumptions-or-properties",
        "label": "Check assumptions or properties",
        "keywords": ["satisfies", "check", "verify", "complete", "transitive", "convex", "continuous", "monotonic", "rational"],
        "opening_move": [
            "Write the property to be checked as a formal condition, not in prose.",
            "State the candidate object clearly: preference, utility function, correspondence, strategy profile, or allocation.",
            "Test the condition against the object point by point, or choose a counterexample if the property fails.",
        ],
        "usually_asked": ["verify", "check whether", "test assumptions", "find where the property fails"],
    },
    {
        "id": "construct-example-or-counterexample",
        "label": "Construct example or counterexample",
        "keywords": ["counterexample", "construct", "give an example", "find an example"],
        "opening_move": [
            "Write the target properties that must hold and the single property that must fail.",
            "Choose the simplest domain and object that can exhibit that pattern.",
            "State the object explicitly before checking each required property in turn.",
        ],
        "usually_asked": ["construct", "exhibit", "show failure", "separate assumptions"],
    },
    {
        "id": "solve-optimization-problem",
        "label": "Solve optimization problem",
        "keywords": ["maximize", "minimize", "lagrangian", "first-order", "foc", "ump", "emp", "budget", "subject to"],
        "opening_move": [
            "Write the objective and constraints in full notation before doing any algebra.",
            "State which assumptions guarantee interiority, existence, or binding constraints.",
            "Set up the Lagrangian or Kuhn-Tucker system and identify the candidate first-order conditions.",
        ],
        "usually_asked": ["solve", "derive first-order conditions", "characterize optimum", "check interior vs corner"],
    },
    {
        "id": "derive-demand-or-duality",
        "label": "Derive demand or duality object",
        "keywords": ["walrasian", "hicksian", "roy", "shephard", "slutsky", "indirect utility", "expenditure", "duality", "demand"],
        "opening_move": [
            "Write the relevant primal or dual problem in notation.",
            "State the object to be derived: demand, indirect utility, expenditure function, or derivative identity.",
            "Choose the theorem or route that connects the object to the optimization problem, such as FOCs, Roy's identity, or Shephard's lemma.",
        ],
        "usually_asked": ["derive", "compute", "recover from duality", "compare primal and dual objects"],
    },
    {
        "id": "equilibrium-or-welfare-analysis",
        "label": "Equilibrium or welfare analysis",
        "keywords": ["equilibrium", "pareto", "efficiency", "core", "contract curve", "welfare", "allocation", "market clearing"],
        "opening_move": [
            "Write the equilibrium or welfare definition that the question is using.",
            "List the agents, endowments, feasible set, and prices or transfers if present.",
            "State the conditions to be checked: optimality, feasibility, and market-clearing or Pareto-improvement conditions.",
        ],
        "usually_asked": ["characterize equilibrium", "check efficiency", "compare allocations", "show welfare property"],
    },
    {
        "id": "uncertainty-or-risk-analysis",
        "label": "Uncertainty or risk analysis",
        "keywords": ["lottery", "expected utility", "risk", "certainty equivalent", "risk premium", "stochastic dominance", "bernoulli"],
        "opening_move": [
            "Write the risky objects explicitly: lotteries, outcomes, probabilities, or utility over money.",
            "State the comparison criterion: expected utility, certainty equivalent, risk premium, or dominance order.",
            "Reduce the question to the exact inequality or expectation that must be evaluated.",
        ],
        "usually_asked": ["compare lotteries", "compute expected utility", "rank risk attitudes", "apply dominance test"],
    },
    {
        "id": "game-solution-concept",
        "label": "Game solution concept",
        "keywords": ["nash", "dominant strategy", "best response", "subgame", "backward induction", "extensive form", "mixed strategy"],
        "opening_move": [
            "Write the game in the representation that best fits the question: payoff matrix, strategy sets, or game tree.",
            "State the solution concept being tested: dominant strategy, Nash equilibrium, or subgame perfection.",
            "List the candidate best responses or continuation actions before solving for equilibrium.",
        ],
        "usually_asked": ["solve game", "find equilibrium", "eliminate strategies", "check sequential rationality"],
    },
    {
        "id": "interpretation-or-comparison",
        "label": "Interpretation or comparison",
        "keywords": ["interpret", "compare", "intuition", "explain", "difference between", "why"],
        "opening_move": [
            "Write the two objects, concepts, or cases being compared in parallel notation.",
            "State the single dimension of comparison first: assumptions, behavior, welfare effect, or geometry.",
            "Organize the answer as matched points rather than free-form commentary.",
        ],
        "usually_asked": ["interpret", "compare", "explain intuition", "state economic meaning"],
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, help="Path to corpus.json")
    parser.add_argument("--analysis-dir", required=True, help="Directory containing clusters.json and other analysis outputs")
    parser.add_argument("--out", required=True, help="Directory for practice-analysis outputs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_path = Path(args.corpus).expanduser().resolve()
    analysis_dir = Path(args.analysis_dir).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    chunks = payload["chunks"]
    clusters = json.loads((analysis_dir / "clusters.json").read_text(encoding="utf-8"))["clusters"]

    practice_chunks = [chunk for chunk in chunks if chunk["role"] == "practice"]
    problems = segment_practice(practice_chunks)
    enriched = enrich_problems(problems, clusters)
    type_index = index_by_type(enriched)

    write_json(out_dir / "practice-analysis.json", {"problems": enriched, "type_index": type_index})
    write_markdown(out_dir / "practice-problem-analysis.md", render_problem_analysis_md(enriched))
    write_markdown(out_dir / "problem-type-playbook.md", render_type_playbook_md(type_index))
    write_markdown(out_dir / "problem-identification-flowchart.md", render_decision_tree_md())
    write_markdown(out_dir / "topic-dependency-map.md", render_dependency_map_md(enriched))
    return 0


def segment_practice(chunks: list[dict]) -> list[dict]:
    by_file: dict[str, list[dict]] = defaultdict(list)
    for chunk in chunks:
        by_file[chunk["source_file"]].append(chunk)

    problems: list[dict] = []
    for source_file, file_chunks in sorted(by_file.items()):
        file_chunks.sort(key=lambda item: item["order"])
        current: list[dict] = []
        current_label = ""
        counter = 1
        saw_start = False

        for chunk in file_chunks:
            text = chunk["text"]
            start = extract_problem_label(text)
            if start and current:
                problems.append(build_problem(source_file, file_chunks[0]["source_name"], current_label or f"Problem {counter}", current))
                counter += 1
                current = [chunk]
                current_label = start
                saw_start = True
            elif start:
                current = [chunk]
                current_label = start
                saw_start = True
            else:
                current.append(chunk)

        if current:
            label = current_label or f"Problem {counter if saw_start else 1}"
            problems.append(build_problem(source_file, file_chunks[0]["source_name"], label, current))

        if not saw_start and not problems_for_file(problems, source_file):
            problems.append(build_problem(source_file, file_chunks[0]["source_name"], "Problem 1", file_chunks))

    return problems


def problems_for_file(problems: list[dict], source_file: str) -> list[dict]:
    return [problem for problem in problems if problem["source_file"] == source_file]


def build_problem(source_file: str, source_name: str, label: str, chunks: list[dict]) -> dict:
    text = "\n\n".join(chunk["text"] for chunk in chunks)
    return {
        "problem_id": slugify(f"{source_name}-{label}"),
        "source_file": source_file,
        "source_name": source_name,
        "label": label,
        "locator_start": chunks[0]["locator"],
        "text": text,
    }


def extract_problem_label(text: str) -> str:
    first_line = text.splitlines()[0].strip()
    patterns = [
        r"^(Problem|Question|Exercise)\s+([0-9IVXivxA-Za-z\.\-]+)",
        r"^([0-9]{1,2}[A-Za-z]?)\s*[\.\)]\s+",
    ]
    for pattern in patterns:
        match = re.match(pattern, first_line)
        if match:
            return first_line[:80]
    return ""


def enrich_problems(problems: list[dict], clusters: list[dict]) -> list[dict]:
    enriched: list[dict] = []
    for problem in problems:
        problem_types = classify_problem(problem["text"])
        dependencies = map_problem_to_topics(problem["text"], clusters, problem["source_name"])
        actions = sorted({action for item in problem_types for action in item["usually_asked"]})
        opening_moves = [
            {
                "type_id": item["id"],
                "type_label": item["label"],
                "steps": item["opening_move"],
            }
            for item in problem_types
        ]
        enriched.append(
            {
                **problem,
                "problem_types": [{"id": item["id"], "label": item["label"]} for item in problem_types],
                "opening_moves": opening_moves,
                "usually_asked": actions,
                "dependencies": dependencies,
            }
        )
    return enriched


def classify_problem(text: str) -> list[dict]:
    text_low = text.lower()
    matched = []
    for rule in TYPE_RULES:
        if any(keyword in text_low for keyword in rule["keywords"]):
            matched.append(rule)
    if not matched:
        matched.append(
            {
                "id": "general-structured-analysis",
                "label": "General structured analysis",
                "keywords": [],
                "opening_move": [
                    "Write down exactly what object the question gives and what object it asks for.",
                    "Translate the prompt into formal notation before doing interpretation.",
                    "List the assumptions or definitions that the question seems to invoke.",
                ],
                "usually_asked": ["define", "derive", "explain", "check conditions"],
            }
        )
    return matched


def map_problem_to_topics(text: str, clusters: list[dict], source_name: str) -> list[dict]:
    text_tokens = tokenize(text)
    text_counter = Counter(text_tokens)
    week_hint = infer_week(source_name)
    scored = []
    for cluster in clusters:
        score = sum(text_counter.get(keyword, 0) for keyword in cluster["keywords"])
        score += sum(text.lower().count(keyword.lower()) for keyword in cluster["keywords"])
        if cluster["week"] == week_hint:
            score += 3
        if score > 0:
            scored.append((score, cluster))
    scored.sort(key=lambda item: (-item[0], item[1]["week"], item[1]["topic"]))
    return [
        {
            "week": cluster["week"],
            "topic": cluster["topic"],
            "cluster_id": cluster["cluster_id"],
        }
        for _, cluster in scored[:4]
    ]


def index_by_type(problems: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for rule in TYPE_RULES:
        grouped[rule["id"]] = {
            "type_id": rule["id"],
            "type_label": rule["label"],
            "opening_move": rule["opening_move"],
            "usually_asked": rule["usually_asked"],
            "problems": [],
        }
    grouped.setdefault(
        "general-structured-analysis",
        {
            "type_id": "general-structured-analysis",
            "type_label": "General structured analysis",
            "opening_move": [
                "Write down exactly what object the question gives and what object it asks for.",
                "Translate the prompt into formal notation before doing interpretation.",
                "List the assumptions or definitions that the question seems to invoke.",
            ],
            "usually_asked": ["define", "derive", "explain", "check conditions"],
            "problems": [],
        },
    )
    for problem in problems:
        for item in problem["problem_types"]:
            grouped[item["id"]]["problems"].append(
                {
                    "label": problem["label"],
                    "source_name": problem["source_name"],
                    "dependencies": problem["dependencies"],
                }
            )
    return [entry for entry in grouped.values() if entry["problems"]]


def render_problem_analysis_md(problems: list[dict]) -> str:
    lines = ["# Practice Problem Analysis", ""]
    for problem in problems:
        lines.extend(
            [
                f"## {problem['source_name']} - {problem['label']}",
                "",
                f"- Problem types: {', '.join(item['label'] for item in problem['problem_types'])}",
                f"- Topic dependencies: {', '.join(dep['week'] + ' ' + dep['topic'] for dep in problem['dependencies']) or 'None mapped'}",
                f"- Usually asked to do: {', '.join(problem['usually_asked'])}",
                "",
                "### Opening moves",
                "",
            ]
        )
        for move in problem["opening_moves"]:
            lines.append(f"#### {move['type_label']}")
            for idx, step in enumerate(move["steps"], start=1):
                lines.append(f"{idx}. {step}")
            lines.append("")
        snippet = shorten(problem["text"], 900)
        lines.extend(["### Prompt snapshot", "", snippet, ""])
    return "\n".join(lines)


def render_type_playbook_md(type_index: list[dict]) -> str:
    lines = ["# Problem Type Playbook", "", "This file lists the reusable opening move for each identified problem type.", ""]
    for entry in type_index:
        lines.extend(
            [
                f"## {entry['type_label']}",
                "",
                "### Standard opening move",
                "",
            ]
        )
        for idx, step in enumerate(entry["opening_move"], start=1):
            lines.append(f"{idx}. {step}")
        lines.extend(
            [
                "",
                f"### What problems of this type usually ask for",
                "",
                f"- {', '.join(entry['usually_asked'])}",
                "",
                "### Seen in",
                "",
            ]
        )
        for problem in entry["problems"]:
            lines.append(f"- {problem['source_name']} - {problem['label']}")
        lines.append("")
    return "\n".join(lines)


def render_decision_tree_md() -> str:
    return """# Problem Identification Flowchart

```mermaid
flowchart TD
    A["Read the first sentence of the problem"] --> B{"Is the task to prove, show, or establish an implication/equivalence?"}
    B -->|Yes| C["Type: Prove equivalence or implication"]
    B -->|No| D{"Does it ask whether an object satisfies completeness, transitivity, convexity, continuity, or another property?"}
    D -->|Yes| E["Type: Check assumptions or properties"]
    D -->|No| F{"Does it ask for an example or counterexample?"}
    F -->|Yes| G["Type: Construct example or counterexample"]
    F -->|No| H{"Does it give an objective + constraint or use words like maximize, minimize, UMP, EMP, or Lagrangian?"}
    H -->|Yes| I["Type: Solve optimization problem"]
    H -->|No| J{"Does it mention Walrasian/Hicksian demand, expenditure, indirect utility, Roy, Shephard, or Slutsky?"}
    J -->|Yes| K["Type: Derive demand or duality object"]
    J -->|No| L{"Does it mention equilibrium, Pareto efficiency, feasibility, or market clearing?"}
    L -->|Yes| M["Type: Equilibrium or welfare analysis"]
    L -->|No| N{"Does it mention lotteries, expected utility, certainty equivalents, risk premium, or stochastic dominance?"}
    N -->|Yes| O["Type: Uncertainty or risk analysis"]
    N -->|No| P{"Does it mention strategies, best responses, Nash, dominant strategy, subgames, or backward induction?"}
    P -->|Yes| Q["Type: Game solution concept"]
    P -->|No| R["Type: Interpretation or comparison / general structured analysis"]
```
"""


def render_dependency_map_md(problems: list[dict]) -> str:
    lines = ["# Topic Dependency Map", "", "This map shows which note topics are actually drawn on by each practice problem.", ""]
    topic_to_problems: dict[tuple[str, str], list[str]] = defaultdict(list)
    for problem in problems:
        for dep in problem["dependencies"]:
            topic_to_problems[(dep["week"], dep["topic"])].append(f"{problem['source_name']} - {problem['label']}")
    for (week, topic), refs in sorted(topic_to_problems.items()):
        lines.extend([f"## {week}: {topic}", ""])
        for ref in refs:
            lines.append(f"- {ref}")
        lines.append("")
    return "\n".join(lines)


def shorten(text: str, limit: int) -> str:
    flat = re.sub(r"\s+", " ", text).strip()
    if len(flat) <= limit:
        return flat
    return flat[: limit - 3].rstrip() + "..."


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9\-]{1,}", text.lower())


def infer_week(source_name: str) -> str:
    match = re.search(r"(?:week|w)[\s_-]?(\d{1,2})", source_name.lower())
    if match:
        return f"week-{int(match.group(1)):02d}"
    return "week-unknown"


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "problem"


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_markdown(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
