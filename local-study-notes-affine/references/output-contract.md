# Output Contract

Default to one Markdown file per topic, week, or lecture block unless the user asks for a single master file. When the user asks for polished presentation, also generate one HTML study pack using `references/make-notes-pretty.md`.

The default note style should match polished honours lecture notes:

- explanatory, not skeletal
- formal when giving definitions and propositions
- rich intuition after each formal statement
- proof sketches or logic walkthroughs when useful
- no source citations unless the user explicitly asks for them
- assume the reader may need to relearn the course from the notes alone
- foreground the equations, proof moves, and logic sequences needed to solve problem-set and exam questions
- merge shared concepts across sources by enriching them, not flattening them
- read like course notes written carefully after class, not like cram notes
- teach the process of solving the course's problem types, not just the content statements

## Required structure

```markdown
# Week X: Topic Title
**Course code / course name | lecturer if known**

---

## 1. Roadmap and Motivation

Short orienting paragraph plus a numbered roadmap if useful.

## 2. Main Concept Block

### 2.1 Definition / Setup

Formal definition in prose or display math.

### 2.2 Intuition

Explain what the formal object means and why it matters.

### 2.3 Cross-Source Enrichment

For any concept present in multiple sources, combine them deliberately:

- slide wording: compact/formal statement
- transcript wording: professor phrasing, emphasis, examples, warnings
- textbook wording: added rigor, missing derivation steps, formal distinctions

If two phrasings differ, compare them and use the stronger combined explanation.

### 2.4 Proposition / Result

State key result clearly.

### 2.5 Proof Sketch / Logic

Walk through the argument if it helps.

## 3. Assumptions / Geometry / Economic Meaning

## 4. Equations and Derivations

$$
\text{equation here}
$$

Interpret each term in words.

### 4.1 How To Use This In A Question

Give the sequence of steps needed to deploy the result in a worked problem.

## 5. Subtleties and Clarifications

## 6. Summary Table / Comparison

## 7. Problem-Solving Context

- Problem types this topic appears in: [list]
- Opening move when this topic is the focus:
  1. [concrete step]
  2. [concrete step]
- What the student is usually asked to do with this concept:
  - derive
  - prove
  - compare
  - interpret
- Worked example skeleton:
  1. [state the object / assumptions]
  2. [apply the defining theorem or method]
  3. [derive the key relation]
  4. [interpret or conclude]

## 8. Key Takeaways
```

## Style rules

- Prefer dense but readable prose over bare bullet lists.
- Use numbered subsections like `2.1`, `2.2`, `3.1` when the topic has internal structure.
- Use blockquotes sparingly for remarks such as `Important distinction`, `Interpretation`, or `Remark`.
- Use tables for comparisons of assumptions, estimators, equilibrium concepts, or risk notions.
- Use plain Markdown and standard LaTeX delimiters so the files remain portable.
- Do not include a `Sources` section by default.
- If the analysis stage reports lecturer-only concepts, fold them naturally into the exposition rather than adding a citation-heavy section.
- Preserve the user's preferred tone: polished lecture-note prose, not robotic summaries.
- When practice sheets are available, use them to identify where fuller derivations or logical development are needed, but do not let the notes sound like exam coaching notes.
- Include explicit step-by-step logic when a proof, derivation, or equilibrium argument is central to understanding the material.
- Use Mermaid more aggressively when it clarifies the logic better than prose.
- For each major topic, ask whether a flowchart, theorem map, or decision tree would help a student solve exam questions faster.
- Do not treat overlap across slide, transcript, and textbook as redundancy to remove. Treat it as multiple explanatory layers to merge.
- If the transcript and slide cover the same concept, preserve the lecturer's wording, examples, and emphasis rather than reducing it to "confirmed by transcript".
- Avoid repetitive coaching phrases such as `exam tip`, `what to memorise`, or `how to score marks` unless the user explicitly asks for that tone.
- Use a teaching register:
  - explain why each non-obvious step is taken
  - explain what problem a concept solves before defining it
  - when stating an assumption, say what breaks without it
  - use third person
- Every concept that appears in at least one practice problem must end with a `Problem-Solving Context` block.
- The opening move for a problem type must be concrete enough that a student could write it immediately on a blank page before reading further details.
- Worked example skeletons should preserve the logical structure of a full solution while leaving content-specific entries as placeholders.

## AFFiNE packaging rules

- Keep filenames ASCII-safe and stable, for example `week-03-ols-assumptions.md`.
- Keep linked assets relative to the Markdown file.
- Avoid custom Markdown extensions that AFFiNE may not preserve.
