# Authoring rules — turning a page into components

Lessons from building `assets/example/` (a fund fact sheet). Read before writing templates.

## Decompose before you write

Write this table first (in your head or in a scratch file), from the page image:

| box | component | data shape | repeats? | varies by layout? |
|---|---|---|---|---|
| Compound Annualized Returns | `returns_table` | `[[label, pct]]` | rows vary | no |
| Regional Allocation | `grouped_alloc` | `groups[{name, rows}]` | groups + rows vary | no |
| Sector / Credit Allocation | `two_col_alloc` | `[[label, pct]]` flowed into 2 columns | rows vary | credit only in balanced/FI |
| Calendar Year Returns | `calendar_bars` (SVG filter) | `[[year, pct]]` | | |

Same visual pattern with different titles = one component with a title parameter
(sector and credit share `two_col_alloc`).

## CSS that survives real data

- Grid columns as `minmax(0, X%)` and children `min-width:0` — otherwise one long unbreakable cell
  widens its column and pushes the neighbour into overlap (this happened; it's the #1 bug).
- Never `white-space:nowrap` on label cells; only on numeric cells (`td.n`).
- Font sizes in `pt`, page in `in` — matches print, and spans.json sizes map 1:1 for vector sources.
- `@page{size:Letter;margin:0}` (or A4) and the body sized to the page; render.py uses the CSS page size.
- Condensed sans fonts matter for dense fact sheets; `font-stretch:condensed` on a family that has
  a condensed face, or the licensed brand font via `@font-face` from `work/fonts/` (vector sources).

## Measuring from a vector source

From `page_N_spans.json`:
- Title size/color: the largest span's `size` and `color`.
- Body size: the most common `size`.
- Column x-positions: cluster span `bbox[0]` values — clusters are your grid columns.
- Box rules: `page_N_drawings.json` rects with a `stroke` and no `fill` are box borders;
  thin filled rects are rules or bands.
PDF units are points (1/72 in); CSS `pt` is the same unit — copy numbers directly.

## Charts

Regenerate from data with the plugin's chart filters (`bar_svg`, `line_svg`), configured in
`config/charts.json`: axis range and tick, label rotation, decimals. Colors come from tokens
(`fill="var(--brand)"` works inside inline SVG). Axes auto-extend when data exceeds the configured range.
A chart the filters cannot draw is a library gap: extend the plugin, never write code into the project.

## i18n

French fact sheets: `4,1 %` (non-breaking space before %), `1,4 milliard $`, dates `23/12/2025`.
Labels are typically 15–30% longer in French — always stress-test the FR render for overflow.

## When the source is a raster

- State the cap on fidelity to the user up front.
- Annotation marks in spec documents (red boxes, callouts) are not design — ignore them, and crop
  around them when sampling colors.
- Fonts: identify the style (serif headings, condensed sans body), use available stand-ins in
  tokens, and list the licensed fonts needed as an open gap.
