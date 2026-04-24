# Pretty Notes Style

This reference adapts the user's attached `make-notes-pretty` skill for the local study-note pipeline.

## Purpose

When polished presentation matters, generate a single self-contained HTML file in addition to the AFFiNE Markdown notes. The HTML file is the visually rich study pack. The Markdown files remain the AFFiNE import artifact, but the HTML file should also be suitable for direct AFFiNE HTML import when the user wants that path.

## Required output

- One self-contained HTML file
- CSS embedded in a `<style>` block
- No external stylesheet framework
- Use Mermaid and MathJax from CDN when diagrams or equations are present
- Build the HTML as a document, not a web app

## Typography

Import:

```css
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:ital,wght@0,300;0,400;0,600;0,700;1,400&display=swap');
```

- `h1`: `Libre Baskerville`, serif
- `h2` to `h4`: `Source Sans 3`, sans-serif, bold
- body text and lists: `Source Sans 3`, sans-serif

## Palette

Use the user's palette directly. The base shade is `--medium-carmine-700`.

```css
:root {
  --medium-carmine-50: #fdf2f1;
  --medium-carmine-100: #f8e7e5;
  --medium-carmine-200: #f5d2ce;
  --medium-carmine-300: #f1ada7;
  --medium-carmine-400: #ea7e78;
  --medium-carmine-500: #e25b58;
  --medium-carmine-600: #cf4545;
  --medium-carmine-700: #AD3838;
  --medium-carmine-800: #932f2f;
  --medium-carmine-900: #78302e;
  --medium-carmine-950: #451313;

  --sunglow-50: #fffbe8;
  --sunglow-100: #fff2c8;
  --sunglow-200: #ffe382;
  --sunglow-300: #FFD029;
  --sunglow-400: #f4bf00;
  --sunglow-500: #e1ac00;
  --sunglow-600: #bd8c00;
  --sunglow-700: #966c00;
  --sunglow-800: #795500;
  --sunglow-900: #614800;
  --sunglow-950: #372600;

  --morning-glory-50: #ecfdff;
  --morning-glory-100: #d6f8fe;
  --morning-glory-200: #92d4e1;
  --morning-glory-300: #74e6fb;
  --morning-glory-400: #1dd0eb;
  --morning-glory-500: #0bb7cf;
  --morning-glory-600: #0094a8;
  --morning-glory-700: #037686;
  --morning-glory-800: #0d606d;
  --morning-glory-900: #184f59;
  --morning-glory-950: #05353c;

  --white-50: #FFFFFF;
  --white-100: #f5f4f4;
  --white-200: #e6e4e4;
  --white-300: #d9d2d4;
  --white-400: #a89c9f;
  --white-500: #7b6e72;
  --white-600: #5c4f53;
  --white-700: #463d3f;
  --white-800: #2a2627;
  --white-900: #1a1718;
  --white-950: #0b0809;

  --font-heading: "Libre Baskerville", serif;
  --font-body: "Source Sans 3", sans-serif;
  --radius: 0.5rem;
}
```

Suggested semantic use:

- main heading and primary emphasis: `--medium-carmine-700`
- section rules and proof markers: `--medium-carmine-600`
- exam tips and highlighted steps: `--sunglow-300`
- diagrams and intuition callouts: `--morning-glory-700`
- page background: `--white-100` or `--sunglow-50`
- body text: `--white-900`

## Layout

- `max-width: 860px`
- centered content
- `padding: 2rem`
- light warm background with strong ink contrast
- editorial rather than dashboard-like
- use callouts selectively, not everywhere
- make equations and diagrams visually prominent

## Required structural transformations

- Convert major topics to `h2`
- Convert subtopics to `h3`
- Use bullet lists for properties, examples, and definitions
- Use numbered lists for derivations, procedures, proofs, and answer algorithms
- Render assumptions as explicit numbered lists
- Use tables for model, estimator, test, and concept comparisons

## Callouts

Use these classes when the content warrants them:

- `callout-exam`
- `callout-intuition`
- `callout-definition`
- `callout-warning`
- `callout-summary`
- `callout-proof`

Recommended styling direction:

- `callout-exam`: `--medium-carmine-700`
- `callout-intuition`: `--morning-glory-700`
- `callout-definition`: `--sunglow-700`
- `callout-warning`: `--medium-carmine-800`
- `callout-summary`: `--white-300`
- `callout-proof`: `--morning-glory-600`

## Diagrams and equations

- Use MathJax for equations
- Use Mermaid for process flows, concept hierarchies, decision rules, proof maps, and causal structures
- Prefer more diagrams than before when the concept has a real logic flow
- Add a diagram when it helps show:
  - theorem proof structure
  - optimisation workflow
  - duality relationships
  - equilibrium reasoning
  - dominance / Nash / subgame refinement logic
  - risk-comparison orderings
- End the HTML with a `Key Takeaways` section containing 5 to 7 exam-ready points

## Visual guidance

- Use flowcharts for answer procedures
- Use concept maps for assumption hierarchies
- Use side-by-side cards or tables for comparison-heavy topics
- Use subtle equation panels for derivations that must be memorised
- Keep diagrams study-oriented, not decorative

## Constraints

- Do not use Inter, Roboto, or Arial
- Do not make the result look like SaaS UI
- Keep the AFFiNE import path Markdown-first even when also generating HTML
