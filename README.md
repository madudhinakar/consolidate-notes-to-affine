# Local Study Notes Pipeline

This repo contains a study-note pipeline that turns local course materials into:

- exam-style Markdown study notes
- a styled HTML study pack
- an AFFiNE-importable Markdown bundle

## What You Need

1. VS Code
2. Python 3
3. Your own local course files

Optional:

- Codex CLI in the terminal for full automation
- ChatGPT or another LLM for the manual fallback flow

Organise your files like this:

```text
/path/to/Course Folder/
  Slides/
  Textbook/
  Transcripts/
  Exercises/
```

## How To Run With Codex

1. Clone this repo.
2. Open the repo folder in VS Code.
3. Open `Terminal` -> `New Terminal`.
4. Copy the command from [example-command.txt](/Users/Madu/Documents/New%20project/example-command.txt).
5. Replace the example paths with your own paths.
6. Run the command.

## How To Run Without Codex

1. Clone this repo.
2. Open the repo folder in VS Code.
3. Open `Terminal` -> `New Terminal`.
4. Copy the command from [example-command-manual.txt](/Users/Madu/Documents/New%20project/example-command-manual.txt).
5. Replace the example paths with your own paths.
6. Run the command.
7. Open the generated file `output/prompts/manual-chatgpt-prompt.md`.
8. Upload your course files to ChatGPT or another LLM.
9. Paste the contents of `manual-chatgpt-prompt.md`.
10. Ask the model to generate the Markdown notes and the HTML study pack.

## Output

The pipeline writes to the chosen `--workdir` folder and creates:

- `notes/`
- `html/study-pack.html`
- `affine-import/`
- `corpus/`
- `analysis/`
- `prompts/manual-chatgpt-prompt.md`

## Important

Do not upload lecture slides, textbooks, transcripts, exercise sheets, or generated notes to a public repo unless you have permission. Share only the pipeline code.
