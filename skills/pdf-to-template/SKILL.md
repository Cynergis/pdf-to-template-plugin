---
name: pdf-to-template
description: Reverse-engineer the layout and design of an existing PDF report (fact sheet, statement, one-pager) into a reusable, data-driven HTML/CSS + Jinja2 template that renders new data to PDF and looks like the original. Use when the user wants to "extract the design/layout/template from a PDF", "recreate this report with different data", "make a template from this PDF", or build a family of report templates (layouts × series × languages) from sample PDFs. Reads the report's definition from an OTO project (the report pack's new-report) and records the sample, the build and the release there.
---

# PDF → reusable report template

A PDF holds glyphs at coordinates, not a template. Nothing extracts "the template". This skill
makes **you** the author: scripts gather the evidence and grade the result; you write the template.

```
source.pdf ─► 1 INSPECT ─► 2 PALETTE ─► 3 AUTHOR (you) ─► 4 RENDER ─► 5 DIFF ─┐
                 │                          ▲                                   │
                 └─ verdict, spans, fonts   └──────── fix worst cells ◄─────────┘
                                                      until gate passes ─► 6 FREEZE
```

Scripts are in the plugin's `scripts/` folder (`${CLAUDE_PLUGIN_ROOT}/scripts/...`).
A complete worked example (Mackenzie-style fund fact sheet, 12 components, 3 layouts, EN/FR)
is in `${CLAUDE_PLUGIN_ROOT}/assets/example/` — it is the starting skeleton for a new report folder.

Each report type has its own folder, `reports/<report-id>/`, in the project, for its template. What the report *is*
(its sections, its fields and what each means per language, the column behind each value, its thresholds, its
status) lives in the project's OTO knowledge graph, defined with the report pack's **report:new-report** skill. This
skill reads that definition, builds the template in the folder, and records what the build produced back in the
graph. The project is an OTO project (`oto status --project <root>`); define the report first, so the template has
fields to be checked against.

## 0. Read the definition

The report id is the `reportId` the definition was recorded under (`kg_ask Q1` lists them). Ask the graph; do not
work from the interview's notes:

| Question | What the template takes from it |
|---|---|
| `kg_ask Q7 REPORT=<id>` | the sections in order (one component each, and the `Macro` that renders it when one is named), the fields of each, and which appear only in some layouts (`presentWhen` → `config/layouts.json`) |
| `kg_ask Q3 FIELD=<field>`, for each field | the label per language (→ `config/i18n.json`) |
| `kg_ask Q4 REPORT=<id>` | the column behind each field, with its type and row structure (→ the shape of `data/<doc>.json`, keyed by field id) |
| `kg_ask Q9 REPORT=<id>` | the sample document and the verification thresholds (→ the gate in step 5) |
| `kg_ask Q17 REPORT=<id>` | where the report is in its lifecycle |

A box on the page that no field explains is a question for the analyst, not a field you invent: the definition
changes first, through report:new-report, then the template.

## Setup

Nothing to install by hand. Each script declares its own dependencies (inline script metadata), so
`uv run <script>` fetches them into a cached environment the first time; the renderer downloads
Chromium itself on the first render. The one requirement is `uv` on the PATH. When in doubt, or when a
script fails to start, run the `setup` skill (`uv run ${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py --fix`): it
reports what is missing and installs what it can.

## 1. Inspect — find out what you actually have

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/inspect_pdf.py source.pdf --out work/
```

Read `work/report.json` and look at `work/page_N.png`. The verdict decides the path:

| verdict | meaning | what you get | path |
|---|---|---|---|
| `vector` | real text + drawings | exact fonts (`work/fonts/`), sizes, colors, bboxes in `page_N_spans.json`, rules/fills in `page_N_drawings.json` | measure, don't guess: copy font sizes, colors, box positions from the JSON |
| `raster` | page is a picture (screenshot, scan, spec doc) | `page_N_img_K.png` only | vision reconstruction from the image; tell the user fidelity is capped, and **ask for the production PDF** — it is usually vector |
| `mixed` | text plus large images (photos, charts as images) | both | vector path for text, treat images as assets or chart slots |

If the user has **two issues of the same report** (same fund, same language, different months),
discover data slots automatically — spans that changed are data, the rest is static design:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/inspect_pdf.py aug.pdf --diff sep.pdf --out work/   # -> work/slots.json
```

## 2. Palette

Vector: take colors from `spans.json` / `drawings.json`. Raster:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/sample_colors.py work/page_0_img_0.png --k 8
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/sample_colors.py work/page_0_img_0.png --crop 280,150,490,250   # one element (a bar)
```

Global palettes include noise (annotation boxes, anti-aliasing). Crop to a specific element
(chart bar, title, header band) to get each brand color precisely.

## 3. Author the template

Rule that governs everything below: **a template project is data** (Jinja, CSS, JSON). The plugin is the only code, built once; an onboarding run never adds code, and a component missing from the library stops the run until the library is extended by its own release.

Copy `templates/`, `config/` and `data/` from `${CLAUDE_PLUGIN_ROOT}/assets/example/` into `reports/<report-id>/`
and rewrite them for the new source. Structure:

```
templates/tokens.css      colors, fonts, sizes as CSS variables — every style decision lives here
templates/components.j2   one Jinja macro per visual box (table, chart, key-value list, bullets…)
templates/base.html.j2    page shell: header, grid, footer; loops layout → components
config/charts.json        chart configuration for the plugin's filters (bar_svg, line_svg); projects carry no code
config/layouts.json       each layout = ordered component slots per column
config/i18n.json          labels per language + number format (pct_sep "." or ",")
data/<doc>.json           facts only — no positions, no styling
```

Authoring rules — read `${CLAUDE_SKILL_DIR}/references/authoring.md` before writing; the short version:
- **The definition names things.** One macro per section of `Q7`, called by the `Macro` the section is
  rendered by when the graph names one; label keys in `i18n.json` and keys in `data/<doc>.json` are the field ids.
- **Components, not pages.** Identify each repeated box type once; layouts only arrange them.
  A family of 22 templates should be ~6 layouts × a dozen components, not 22 files.
- **Flow layout, not coordinates.** CSS grid/flex + loops over rows, so 5 or 12 holdings both work.
  Absolute positioning only for elements that are truly fixed (logo, footer band).
- **Charts are regenerated from data** by the plugin's filters (`${CLAUDE_PLUGIN_ROOT}/scripts/docgen_filters.py`), configured per template in `config/charts.json`, never traced from the source and never coded per report.
- **All labels in i18n**, all numbers through a formatter filter (FR: `4,1 %`, spaces as thousands).
- Use `StrictUndefined` (already in render.py) so a missing field fails loudly.
- Don't reproduce third-party logos/marks you weren't given as files — leave a `brand.logo` slot.

## 4. Render

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/render.py <project> <project>/data/doc.json --lang en --out out/
```

Writes `out/doc.html|pdf|png` and checks **every `.box` / `[data-slot]` element** for width/height
overflow and anything pushed below the page. Exit code 1 on any overflow.

## 5. Diff against the source and iterate

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/diff.py work/page_0.png out/doc.png --out work/diff.png --threshold 0.80
```

Reference image: `page_N.png` for a vector source; for a raster source use the extracted
`page_N_img_K.png` (the page render would include whatever surrounds the image).

Prints a layout-level SSIM (blurred so font substitution doesn't dominate) and the **5 worst grid
cells** with their position. Open `work/diff.png` (reference | render | heatmap), fix the boxes in
the worst cells, re-render, repeat. Look at the render image yourself every iteration — the score
says where, your eyes say what.

Typical fixes, in order of payoff: grid column widths → box order/height → font size/line-height →
table column alignment → chart proportions → spacing.

Gate: the definition's verification policy when `Q9` returns one (`goldenStaticSsimMin`, `overflowBlocking`,
`fidelityMin`); otherwise agree it with the user from these defaults, and record it with the release (step 6):
- vector source: SSIM ≥ 0.85 rendering the **source's own data**, zero overflow
- raster source: SSIM is only indicative (annotations, resolution); gate on zero overflow + user sign-off
  on a side-by-side
- stress test: render one **alternate** data file with longer names, more rows, other language;
  must pass overflow

## 6. Freeze and hand over

Deliver: the project folder (templates, config, sample data), side-by-side PNG
(source | rebuilt | alternate data), both PDFs, and a list of open gaps (licensed fonts, logo
assets, per-slot fit rules, any box the diff still flags). After freezing, rendering is
deterministic — no model in the loop for routine runs.

**Record what the build produced**, through OTO's **capture-form** skill (a capture file with `scope` the report
id, then `oto curate propose`, `add`, `check`, `apply`), each item as `capture.json` lists it:

- the sample PDF as the report's `SourceDocument` (`derivedFrom`): where it is (`reports/<id>/source/…`) and its
  `sha256`;
- the build as a `Run` (`flow` `pdf-to-template`, `flowVersion` this plugin's version, `engineVersion` from
  `oto version`, its `result`) that `usedSource` the sample, with an `Approval` per sign-off (`gate`, `decision`,
  `reviewer`);
- at freeze, the `TemplateRelease` the report is `releasedAs` (`version`, `frozen`, its fonts, the assets still
  pending), `producedBy` the run, with the `VerificationPolicy` the gate used; and each section `renderedBy` its
  `Macro`.

`kg_ask Q14` then says which source, run and approvals produced the template, and `Q13` what its release needs.

**Record the status as the report moves on**: a `StatusChange` on the report type (`hasStatusChange`), appended,
never rewritten. `in_validation` when the template goes to visual sign-off, `changedBy` whoever sends it.
`in_production` is recorded at deployment, by whoever deploys; it needs a frozen release. A report sent back from
validation gets a new `saved`.

## 7. Before freezing: what the graph still lacks

`oto curate check --project <root>` must find nothing blocking. `oto query --project <root> questions` (or
`kg_questions`) lists what the graph cannot answer yet about the report: fields with no column (`Q4`), a meaning
missing in a language (`Q3`), what the release still needs (`Q13`). They are what stands between the template and a
production release; say them, with who can answer each. When the template changes a section or a field, change
the definition first (report:new-report), then the template.

Structured fields (lists, series, values with named parts) arrive from the report's table as JSON text in one column;
single-valued fields arrive as the column's value. `data/<doc>.json` has the shape the template reads either way.
