# Local Study Notes Pipeline

This repo contains a Codex-powered pipeline that turns local course materials into:

- exam-style Markdown study notes
- a styled HTML study pack
- an AFFiNE-importable Markdown bundle

## What Your Friend Needs

1. VS Code
2. Python 3
3. Codex CLI available in the terminal
4. Their own local course files

They should organise their files like this:

```text
/path/to/Course Folder/
  Slides/
  Textbook/
  Transcripts/
  Exercises/
```

## How To Run

1. Clone this repo.
2. Open the repo folder in VS Code.
3. Open `Terminal` -> `New Terminal`.
4. Copy the command from [example-command.txt](/Users/Madu/Documents/New%20project/example-command.txt).
5. Replace the example paths with their own paths.
6. Run the command.

## Output

The pipeline writes to the chosen `--workdir` folder and creates:

- `notes/`
- `html/study-pack.html`
- `affine-import/`
- `corpus/`
- `analysis/`

## Important

Do not upload lecture slides, textbooks, transcripts, exercise sheets, or generated notes to a public repo unless you have permission. Share only the pipeline code.
