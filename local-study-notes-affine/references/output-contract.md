# Output Contract

Default to one Markdown file per topic, week, or lecture block unless the user asks for a single master file. When the user asks for polished presentation, also generate one HTML study pack using `references/make-notes-pretty.md`.

The default note style should match a high-quality honours revision sheet:

- explanatory, not skeletal
- formal when giving definitions and propositions
- rich intuition after each formal statement
- explicit exam tips and common mistakes
- proof sketches or logic walkthroughs when useful
- no source citations unless the user explicitly asks for them
- assume the reader may need to relearn the course from the notes alone
- foreground the equations, proof moves, and logic sequences needed to solve problem-set and exam questions

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

> ⚠️ Exam tip: short high-value note

### 2.2 Intuition

Explain what the formal object means and why it matters.

### 2.3 Proposition / Result

State key result clearly.

### 2.4 Proof Sketch / Logic

Walk through the argument if it helps.

## 3. Assumptions / Geometry / Economic Meaning

## 4. Equations and Derivations

$$
\text{equation here}
$$

Interpret each term in words.

### 4.1 How To Use This In A Question

Give the sequence of steps needed to deploy the result in a worked problem.

## 5. Standard Pitfalls

## 6. Summary Table / Comparison

## 7. Key Takeaways
```

## Style rules

- Prefer dense but readable prose over bare bullet lists.
- Use numbered subsections like `2.1`, `2.2`, `3.1` when the topic has internal structure.
- Use blockquotes for `Exam tip` callouts.
- Use tables for comparisons of assumptions, estimators, equilibrium concepts, or risk notions.
- Use plain Markdown and standard LaTeX delimiters so the files remain portable.
- Do not include a `Sources` section by default.
- If the analysis stage reports lecturer-only concepts, fold them naturally into the exposition rather than adding a citation-heavy section.
- Preserve the user's preferred tone: polished lecture-note prose, not robotic summaries.
- When practice sheets are available, explain how the abstract theory becomes an answer structure.
- Include explicit step-by-step logic when a proof, derivation, or equilibrium argument is likely to appear on an exam.
- Use Mermaid more aggressively when it clarifies the logic better than prose.
- For each major topic, ask whether a flowchart, theorem map, or decision tree would help a student solve exam questions faster.

## AFFiNE packaging rules

- Keep filenames ASCII-safe and stable, for example `week-03-ols-assumptions.md`.
- Keep linked assets relative to the Markdown file.
- Avoid custom Markdown extensions that AFFiNE may not preserve.
