# Report workspace

This folder holds report templates built with the `pdf-to-template` plugin. The people who work
here use the Claude Code panel in VS Code and no terminal: you run every command and open every
result for them.

## Layout

- `reports/<report-id>/` is one report type: `source/` (the sample PDF), `work/` (inspection
  output and the diff image), `templates/`, `config/`, `data/` (the template), `out/` (rendered
  documents), `semantic/` and `manifest.json` (what the report is, written by `new-report`).
- A report id is lower case with hyphens (`equity-fact-sheet`).

## How to work here

- First time, or when a script fails to start: the `pdf-to-template:setup` skill. It runs the
  plugin's doctor, which installs what is missing. Never ask the person to install anything.
- Build a template from a PDF: the `pdf-to-template:pdf-to-template` skill. Render a document:
  the same skill's renderer. Define the report's facts: `pdf-to-template:new-report`; ask about
  them: `pdf-to-template:ask-reports`.
- Scripts run with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py`; they carry their own
  dependencies.
- After every render or diff, open the result in the editor (the PNG, the PDF, `work/diff.png`)
  and say in one line what to look at. The person judges with their eyes; the scores say where.
- A PDF the person mentions by name but has not placed: copy it into `reports/<id>/source/`.
