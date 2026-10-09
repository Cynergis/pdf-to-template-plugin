# pdf-to-template plugin

A Claude Code plugin for report analysts and the engineers who support them. It does three things:

| Skill | Use it to |
|---|---|
| `ask-reports` | Ask about the report catalogue: which reports exist, what a report shows and what its fields mean, which table and column each value comes from, when it runs, which reports are similar. |
| `new-report` | Define a new report type from a sample PDF: capture its requirements with the analyst, draft its sections, fields and column mapping, and check the result until nothing is blocking. |
| `pdf-to-template` | Turn the sample PDF into a data-driven HTML/CSS + Jinja2 template that renders new data to PDF. |

The plugin holds no copy of the report ontology. It starts the ontology's MCP server and asks it what a report
must contain, what a draft still lacks and what the catalogue knows. A new ontology version changes what the
plugin asks without changing the plugin.

## What you need

| Requirement | Why |
|---|---|
| A checkout of the `report-ontology` repository | It holds the ontology, the questions and the MCP server. |
| `uv` on the PATH | It runs the MCP server with the ontology's own dependencies. |
| `REPORT_ONTOLOGY_HOME` set to that checkout | The plugin starts the server from there. |
| A project with a `reports/` folder | One folder per report type. Set `REPORTS_ROOT` to use another location. |

```bash
export REPORT_ONTOLOGY_HOME=/path/to/report-ontology     # in your shell profile
claude --plugin-dir /path/to/pdf-to-template-plugin      # from the project that holds reports/
```

`claude plugin validate /path/to/pdf-to-template-plugin` checks the plugin; `claude mcp list` should show
`plugin:pdf-to-template:report-ontology` as connected.

To render templates, also install the rendering dependencies once:

```bash
pip install -r requirements-render.txt && playwright install chromium
```

## A report folder

```
reports/<report-id>/
  source/                    the sample PDF
  work/                      inspection output
  semantic/report.yaml       what the report is, its sections and fields
  semantic/lineage.yaml      data source, table, column per field
  semantic/provenance.yaml   the report's status history and the sample PDF's record; later the build runs and approvals
  manifest.json              schedule, parameter values, policies, observability
  templates/ config/ data/   the template, written by the pdf-to-template skill
```

`assets/example/` is a complete report folder (a fund fact sheet) and the skeleton new reports start from.

## Layout

| Path | Contents |
|---|---|
| `.claude-plugin/plugin.json` | Plugin manifest. |
| `.mcp.json` | Starts the ontology's MCP server through `uv`. |
| `skills/` | The three skills. |
| `scripts/` | PDF inspection, palette sampling, rendering, visual diff, chart filters. |
| `assets/example/` | The example report folder. |

## Not in this plugin

- **The ontology, schemas and competency questions.** They live in `report-ontology`.
- **The build and run flow.** `flow/flow.json` and its step scripts stay where they are until the software
  factory contract decides their home. To ask flow questions, set `FLOW_ROOT` to the folder that holds
  `flow/flow.json`.
