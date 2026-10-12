# pdf-to-template plugin

A Claude Code plugin for report analysts and the engineers who support them, made to be used from
the Claude Code panel in VS Code without a terminal: Claude runs the tools and opens the results.
It does two things:

| Skill | Use it to |
|---|---|
| `setup` | Check that the tools can run here and fix what is missing; copy the example report to try. |
| `pdf-to-template` | Turn a sample PDF into a data-driven HTML/CSS + Jinja2 template that renders new data to PDF. |

New to the plugin? [HOWTO.md](HOWTO.md) takes you from the example report to a PDF, then from your own
sample PDF to a template, in VS Code.

The plugin holds no report definition. A report's definition (its sections, fields and what each means per
language, the column behind each value, its thresholds and status) lives in an OTO project, defined with the
report pack's `report:new-report` and asked with `report:ask-reports`. The template skill reads it from there and
records the sample PDF, the build and the release back through OTO's gates. Until 0.3.0 the plugin carried its own
`new-report` and `ask-reports` over YAML files and a separate ontology server; the report pack replaces them.

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
| `uv` on the PATH | It runs the scripts, each of which declares its own dependencies (inline script metadata). The `setup` skill installs it when it is missing. |
| The `oto` plugin and the `report` pack | The report's definition: an OTO project in the same folder, started with `/report:start`, the report defined with `/report:new-report`. Not needed to render the example. |
| A project with a `reports/` folder | One folder per report type, beside the OTO project's files. |

Chromium for rendering is downloaded once by the renderer or by `setup`. `requirements-render.txt` lists the
same packages for anyone who prefers a virtual environment of their own.

`starter/` is a workspace to copy for a team: a `reports/` folder, a `CLAUDE.md` that tells Claude how to
work there, and a project setting that registers the marketplace when the folder is trusted.

## A report folder

```text
reports/<report-id>/
  source/                    the sample PDF
  work/                      inspection output
  templates/ config/ data/   the template, written by the pdf-to-template skill
  out/                       rendered documents
```

`assets/example/` is a complete report folder (a fund fact sheet) and the skeleton new reports start from.

## Layout

| Path | Contents |
|---|---|
| `.claude-plugin/plugin.json` | Plugin manifest. |
| `skills/` | The two skills. |
| `scripts/` | PDF inspection, palette sampling, rendering, visual diff, chart filters, the doctor. |
| `assets/example/` | The example report folder. |
| `starter/` | A workspace to copy. |

## Not in this plugin

- **The report's definition, its vocabulary and its questions.** They live in OTO's `report` pack and the
  project's knowledge graph.
- **The build and run flow.** It is described with OTO's `flow` pack; `flow:implement-step` writes each step.
