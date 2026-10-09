---
name: pdf-to-template
description: Reverse-engineer the layout and design of an existing PDF report (fact sheet, statement, one-pager) into a reusable, data-driven HTML/CSS + Jinja2 template that renders new data to PDF and looks like the original. Use when the user wants to "extract the design/layout/template from a PDF", "recreate this report with different data", "make a template from this PDF", or build a family of report templates (layouts × series × languages) from sample PDFs.
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

Each report type has its own folder, `reports/<report-id>/`, in the project. Define the report first with the
`new-report` skill: it creates that folder, records the sample PDF and captures what the report is, where its data
comes from and how it runs. This skill then builds the template inside the same folder.

## Setup (once)

```bash
pip install -r ${CLAUDE_PLUGIN_ROOT}/requirements-render.txt
playwright install chromium
```

## 1. Inspect — find out what you actually have

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/inspect_pdf.py source.pdf --out work/
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
python ${CLAUDE_PLUGIN_ROOT}/scripts/inspect_pdf.py aug.pdf --diff sep.pdf --out work/   # -> work/slots.json
```

## 2. Palette

Vector: take colors from `spans.json` / `drawings.json`. Raster:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/sample_colors.py work/page_0_img_0.png --k 8
python ${CLAUDE_PLUGIN_ROOT}/scripts/sample_colors.py work/page_0_img_0.png --crop 280,150,490,250   # one element (a bar)
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
python ${CLAUDE_PLUGIN_ROOT}/scripts/render.py <project> <project>/data/doc.json --lang en --out out/
```

Writes `out/doc.html|pdf|png` and checks **every `.box` / `[data-slot]` element** for width/height
overflow and anything pushed below the page. Exit code 1 on any overflow.

## 5. Diff against the source and iterate

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/diff.py work/page_0.png out/doc.png --out work/diff.png --threshold 0.80
```

Reference image: `page_N.png` for a vector source; for a raster source use the extracted
`page_N_img_K.png` (the page render would include whatever surrounds the image).

Prints a layout-level SSIM (blurred so font substitution doesn't dominate) and the **5 worst grid
cells** with their position. Open `work/diff.png` (reference | render | heatmap), fix the boxes in
the worst cells, re-render, repeat. Look at the render image yourself every iteration — the score
says where, your eyes say what.

Typical fixes, in order of payoff: grid column widths → box order/height → font size/line-height →
table column alignment → chart proportions → spacing.

Gate (agree with the user; defaults):
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

**Record the status as the report moves on.** `semantic/provenance.yaml` keeps the report's status history in its
`lifecycle` list: append an entry (`status`, `by`, `at`), never rewrite one. Append `in_validation` when the template
goes to visual sign-off, with the name of whoever sends it. `in_production` is appended at deployment, by whoever
deploys, with the date; it needs a frozen release. A report sent back from validation gets a new `saved` entry.

## 7. Semantic layer (lives in the report folder, next to the template)

```
semantic/report.yaml      what the report is, what each section is for, what each field means (per locale)
semantic/lineage.yaml     data source, table, and the column that supplies each field (unmapped | proposed | verified)
semantic/provenance.yaml  the report's status history, the sample PDF, and later the build runs and approvals
manifest.json             schedule, parameter values, verification/approval/publish policy, observability
```

These files are written with the `new-report` skill and read with the `ask-reports` skill. What they must contain is
decided by the report ontology, a separate package this plugin queries and holds no copy of. Before freezing, call the
ontology's `gaps` tool on the report: nothing may be blocking, and the warnings it lists (unmapped fields, a missing
locale) are what still stands between the template and a production release. When the template changes a section or
a field, change `semantic/report.yaml` in the same edit and call `gaps` again.

Structured fields (lists, series, values with named parts) arrive from the report's table as JSON text in one column;
single-valued fields arrive as the column's value. `data/<doc>.json` has the shape the template reads either way.
