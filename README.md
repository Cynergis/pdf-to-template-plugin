# pdf-to-template plugin

A Claude Code plugin for report analysts and the engineers who support them, made to be used from
the Claude Code panel in VS Code without a terminal: Claude runs the tools and opens the results.
It does four things:

| Skill | Use it to |
|---|---|
| `setup` | Check that the tools can run here and fix what is missing; copy the example report to try. |
| `pdf-to-template` | Turn a sample PDF into a data-driven HTML/CSS + Jinja2 template that renders new data to PDF. |
| `new-report` | Define a new report type from a sample PDF: capture its requirements with the analyst, draft its sections, fields and column mapping, and check the result until nothing is blocking. |
| `ask-reports` | Ask about the report catalogue: which reports exist, what a report shows and what its fields mean, which table and column each value comes from, when it runs, which reports are similar. |

New to the plugin? [HOWTO.md](HOWTO.md) takes you from the example report to a PDF, then from your own
sample PDF to a template, in VS Code.

The plugin holds no copy of the report ontology. It starts the ontology's MCP server and asks it what a report
must contain, what a draft still lacks and what the catalogue knows. A new ontology version changes what the
plugin asks without changing the plugin.

## Install

In the Claude Code panel in VS Code, type `/plugins`, add the marketplace `Cynergis/oto-registry` in the
**Marketplaces** tab and install `pdf-to-template` from the **Plugins** tab; or open this link:

```text
vscode://anthropic.claude-code/install-plugin?plugin=pdf-to-template&marketplace=Cynergis/oto-registry
```

Then `/pdf-to-template:setup`. From a terminal, the same is `claude plugin install pdf-to-template
--marketplace Cynergis/oto-registry`, or `claude --plugin-dir /path/to/pdf-to-template-plugin` for a checkout.

## What you need

| Requirement | Why |
|---|---|
| `uv` on the PATH | It runs the scripts, each of which declares its own dependencies (inline script metadata), and the ontology's MCP server. The `setup` skill installs it when it is missing. |
| `git` | The MCP server keeps a clone of `Cynergis/report-ontology` in your user cache (`~/.cache/pdf-to-template/`). Set `REPORT_ONTOLOGY_HOME` to use a checkout of your own instead. |
| A project with a `reports/` folder | One folder per report type. Set `REPORTS_ROOT` to use another location. |

Chromium for rendering is downloaded once by the renderer or by `setup`. `requirements-render.txt` lists the
same packages for anyone who prefers a virtual environment of their own.

`starter/` is a workspace to copy for a team: a `reports/` folder, a `CLAUDE.md` that tells Claude how to
work there, and a project setting that registers the marketplace when the folder is trusted.

## A report folder

```text
reports/<report-id>/
  source/                    the sample PDF
  work/                      inspection output
  semantic/report.yaml       what the report is, its sections and fields
  semantic/lineage.yaml      data source, table, column per field
  semantic/provenance.yaml   the report's status history and the sample PDF's record; later the build runs and approvals
  manifest.json              schedule, parameter values, policies, observability
  templates/ config/ data/   the template, written by the pdf-to-template skill
  out/                       rendered documents
```

`assets/example/` is a complete report folder (a fund fact sheet) and the skeleton new reports start from.

## Layout

| Path | Contents |
|---|---|
| `.claude-plugin/plugin.json` | Plugin manifest. |
| `.mcp.json` | Starts the ontology's MCP server through `scripts/report_ontology_mcp.sh`. |
| `skills/` | The four skills. |
| `scripts/` | PDF inspection, palette sampling, rendering, visual diff, chart filters, the doctor, the server launcher. |
| `assets/example/` | The example report folder. |
| `starter/` | A workspace to copy. |

## Not in this plugin

- **The ontology, schemas and competency questions.** They live in `report-ontology`.
- **The build and run flow.** `flow/flow.json` and its step scripts stay where they are until the software
  factory contract decides their home. To ask flow questions, set `FLOW_ROOT` to the folder that holds
  `flow/flow.json`.
