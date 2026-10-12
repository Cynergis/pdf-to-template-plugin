---
name: setup
description: >-
  Check that the pdf-to-template tools can run on this machine and fix what can be fixed, without the
  person typing an install command: uv, the scripts' Python packages, Chromium for rendering, the
  reports/ folder, and optionally the example report to try. Use when the user says "set up
  pdf-to-template", "check my setup", "is everything installed", "try the example", or when a script
  fails to start.
---

# Set up, from inside the editor

The person works in VS Code with the Claude Code extension and does not use a terminal. You run the
commands; they read the result.

## 1. Check and fix

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py --fix --project <project root>
```

Each script declares its own dependencies, so this first run installs the Python packages into uv's
cache (a minute); `--fix` downloads Chromium once (about 100 MB). Report the lines marked `MISSING`
in plain words and what you did about each.

- `uv` missing: it is the one thing the scripts need. Install it for the person (macOS:
  `brew install uv` when Homebrew exists, otherwise `curl -LsSf https://astral.sh/uv/install.sh | sh`;
  Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`), then run the doctor again.
  Say that VS Code may need a restart so the new PATH is seen.
- Chromium still missing after `--fix`: show the download error; a proxy or a blocked network is the
  usual cause.

## 2. The reports folder

A report lives in `reports/<report-id>/` under the project root; create `reports/` when it does not
exist. The sample PDF goes to `reports/<report-id>/source/`; the person can drop it there from the
VS Code explorer, or name a file anywhere and you copy it.

## 3. Try the example (optional)

When the person wants to see a finished template before bringing a PDF:

```bash
cp -R ${CLAUDE_PLUGIN_ROOT}/assets/example reports/fund-profile
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/render.py reports/fund-profile reports/fund-profile/data/bluewater_A_en.json --lang en --out reports/fund-profile/out/
```

Then open `reports/fund-profile/out/bluewater_A_en.png` in the editor for them (VS Code shows PNGs
and PDFs in a tab) and say what the folder holds: templates, config, data, out. From here the
`pdf-to-template` skill builds a template from their own PDF.

## 4. The report ontology server (optional)

The plugin's `report-ontology` MCP server clones `Cynergis/report-ontology` into the user's cache on
first start and needs no environment variable. If `/mcp` shows it failed, the cause is `uv` or `git`
not on the PATH of the editor, or no network for the clone; the template work does not need it.
