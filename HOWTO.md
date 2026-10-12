# How to: from a sample PDF to a template, and from the template to a new PDF, in VS Code

This guide is for someone who has never used the `pdf-to-template` plugin and works in VS Code
with the Claude Code extension. There is no terminal in it: you type in the Claude panel, Claude
runs the tools and opens the results in the editor for you to look at. In about an hour you will
have rendered a report from data, built a template from a PDF of your own, and compared it with
the original side by side.

What you end up with, per report:

```text
reports/<report-id>/
  source/sample.pdf        the PDF you started from
  work/                    what the inspection found: page images, text, fonts, the diff image
  templates/               the template: tokens.css, components.j2, base.html.j2
  config/                  layouts, charts, labels per language
  data/<doc>.json          the facts of one document, nothing else
  out/<doc>.pdf|png|html   a rendered document
```

The idea in one sentence: a PDF is glyphs at coordinates, so nothing "extracts" a template; the
tools gather the evidence and grade the result, and Claude writes the template, renders it,
compares it with the source and fixes the worst cells until the gate passes.

## 1. Install (once, a few clicks)

**The workspace.** In VS Code, open the folder your reports will live in. The quickest start is
the starter folder that ships with the plugin: copy `starter/` from
https://github.com/Cynergis/pdf-to-template-plugin to a folder of your own (or use the Command
Palette, **Git: Clone**, and open its `starter` folder). It holds a `reports/` folder, a
`CLAUDE.md` that tells Claude how to work here, and a project setting that registers the
`cynergis` marketplace when you accept the workspace trust dialog. An empty folder works too; the
marketplace is then added in the next step.

**The plugin.** Open the Claude Code panel and type `/plugins` in the prompt box. In the
**Marketplaces** tab add `Cynergis/oto-registry` if it is not listed. In the **Plugins** tab
search for `pdf-to-template` and click **Install**, then choose **Install for you**. Or open this
link, which does the same in one step:

```text
vscode://anthropic.claude-code/install-plugin?plugin=pdf-to-template&marketplace=Cynergis/oto-registry
```

Check: type `/` in the prompt box; the list shows `/pdf-to-template:setup`,
`/pdf-to-template:pdf-to-template`, `/pdf-to-template:new-report` and
`/pdf-to-template:ask-reports`.

**The tools.** Nothing to install by hand. Type:

```text
/pdf-to-template:setup
```

Claude runs the plugin's doctor: it fetches the tools' Python packages into a cache the first
time (a minute) and downloads a headless Chromium once (about 100 MB), then reports a line per
item, `ok` or `MISSING`, and what it did about each. The one thing it cannot do silently is
install `uv`, the runner the tools use; if it is missing, Claude installs it and tells you to
restart VS Code once.

## 2. First run: a PDF from data, no PDF of your own needed

The plugin ships a complete report folder, a fund fact sheet, as its example. Render it first: it
proves the setup and shows what a finished template looks like.

```text
/pdf-to-template:setup copy the example report into reports/fund-profile, render it with its English data and open the result
```

Claude copies the example, renders it and opens `reports/fund-profile/out/bluewater_A_en.png` in
an editor tab. What you see: a one page fact sheet with a returns table, bar and line charts drawn
from the data, allocation tables, holdings and a footer. The charts are not pictures: the plugin's
filters draw them from the numbers. The PDF is next to the PNG; click it in the Explorer to open it.

Now transform it. Change a fact and render again:

```text
in reports/fund-profile/data/bluewater_A_en.json set the 1 Year return to 7.2 and the total fund assets to $3.4 billion, re-render and open the result
```

Then the same template in another language, with the other data file:

```text
render reports/fund-profile with data/demo_equity_F_fr.json in French and open it
```

French numbers come out as `4,1 %`: labels and number formats live in `config/i18n.json`, never
in the template. Those three runs are the whole production idea: one template, many documents,
no model in the loop once the template is frozen.

When a box overflows its width or height or is pushed below the page, the renderer says which
box, and Claude reports it. That is the first gate.

## 3. Your own report: build the template from a sample PDF

Bring one real report as a PDF. Two issues of the same report (two months, same fund, same
language) are better than one: what changed between them is data, the rest is design, and the
inspection finds the data slots for you.

Drag the PDF into `reports/<report-id>/source/` in the VS Code Explorer (create the folders, or
ask Claude to), or just tell Claude where the file is. Use a short id in lower case with hyphens,
such as `equity-fact-sheet`. Then:

```text
/pdf-to-template:pdf-to-template build a template from reports/<report-id>/source/sample.pdf
```

Claude follows the skill's six steps. What happens, and what you are asked at each one:

1. **Inspect.** The verdict for each page is read from `work/report.json`:
   - `vector`: real text and drawings. Fonts, sizes, colors and box positions are measured, not
     guessed. This is the good case.
   - `raster`: the page is a picture (a scan or a screenshot). Claude tells you fidelity is capped
     and asks for the production PDF. Give it one if you can; it is usually vector.
   - `mixed`: text plus images; photos and image charts become assets or chart slots.

   Claude opens `work/page_0.png`: that is the reference everything is compared against.
2. **Palette.** Brand colors from the text and drawings, or sampled from the page image. You may
   be asked to confirm a color when a title and a chart bar disagree.
3. **Author.** Claude copies the example's `templates/`, `config/` and `data/` into your report
   folder and rewrites them: one macro per kind of visual box, layouts that arrange them, every
   color and size as a CSS variable, every label in `i18n.json`, and a data file that holds the
   source's own numbers. It shows you the list of boxes it found and what each one is; correct it
   there, before any CSS is written.
4. **Render.** As in section 2, with the source's own data. Zero overflow is required.
5. **Diff.** Claude opens `work/diff.png`: three panels, the source page, the render, and a
   heatmap. It reports a layout similarity score and the five worst grid cells by position, fixes
   those boxes, re-renders and repeats. Look at the diff image at every round; the score says
   where, your eyes say what. The default gate for a vector source is a score of 0.85 or more
   with zero overflow; for a raster source the gate is zero overflow plus your sign-off on the
   side by side.
6. **Freeze.** Claude renders one alternate data file (longer names, more rows, the other
   language) as a stress test, then hands over the folder, the side by side image, both PDFs and
   the list of what is still open: licensed fonts, logo files, boxes the diff still flags.

You can drive any step yourself in the same words: "inspect the PDF again at 300 dpi", "sample the
colors of the header band", "diff the render against the source", "re-render with the French data".

## 4. Transform a report: new data in, a new PDF out

Once the template is frozen, a document is a data file. Ask:

```text
make a data file for the same report as of September 2026 with these numbers: ... then render it and open the PDF
```

A data file holds facts only, no positions and no styling. A list or a table is an array of rows
in the shape the template reads; the renderer is strict, so a missing field fails loudly instead
of printing a blank. The PNG is the quick check; the PDF is the real thing.

## 5. Before production: what the report ontology checks

The folder also holds `semantic/report.yaml` (what the report is, its sections and what each
field means), `semantic/lineage.yaml` (the table and column behind each field) and
`semantic/provenance.yaml` (the report's status history). They are written with
`/pdf-to-template:new-report`, which interviews you as the analyst, and read with
`/pdf-to-template:ask-reports`. The plugin's report ontology server starts by itself (it keeps a
copy of the ontology in your user cache). Before freezing, ask:

```text
run the ontology's gaps check on reports/<report-id>
```

Nothing may be blocking; the warnings (a field with no column, a missing language) are what still
stands between the template and a production release.

## 6. When something goes wrong

| Claude reports | It means | Do |
|---|---|---|
| a script could not start, a package is missing | the tools' cache is incomplete | `/pdf-to-template:setup` again; it reinstalls what is missing |
| `uv` is not found | the runner is not on the editor's PATH | let Claude install it, then restart VS Code once |
| the browser is missing | Chromium was not downloaded | `/pdf-to-template:setup`, which downloads it; a proxy is the usual cause when it fails |
| a box overflows (the renderer names it) | the box does not fit its cell | ask Claude to fix that box; usually a column width or a label that may not wrap |
| verdict `raster` | the PDF is a picture | ask for the production PDF; otherwise accept capped fidelity and sign off on the side by side |
| the diff score stays low while the render looks right | the fonts differ | the score tolerates that; a licensed brand font from `work/fonts/` closes the gap |
| the `report-ontology` server failed (`/mcp`) | `git` or `uv` is not on the editor's PATH, or no network for the first clone | ignore for template work; needed only for section 5 |

## 7. Where to go next

- Define the report as facts before the template: `/pdf-to-template:new-report`, with the same
  sample PDF, so the catalogue can answer what the report is, where its data comes from and when
  it runs.
- Build and run it as a flow, with Claude writing each step from its brief: the `flow` plugin from
  the same marketplace, installed from the same `/plugins` dialog.
