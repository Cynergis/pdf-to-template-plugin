"""Step 4 — Render data through a template project to HTML/PDF/PNG and check every box for overflow.

Project layout (see assets/example):
  <project>/templates/base.html.j2   page shell; receives f (data), t (labels), lang, layout, brand
  <project>/templates/components.j2  one macro per box
  <project>/templates/tokens.css     design tokens
  <project>/config/charts.json       optional: per-chart configuration for the plugin's chart filters (no code)
  <project>/config/layouts.json      optional: {"layout_name": {...}}; data picks one via "layout"
  <project>/config/i18n.json         optional: {"en": {...labels, "pct_sep": "."}, "fr": {...}}

Usage:
  python render.py <project> data/fund.json [data/other.json ...] --lang en --out out/
Exit code 1 if any page or box overflows (use it as a gate).
"""
import argparse, json, pathlib, sys
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from playwright.sync_api import sync_playwright

OVERFLOW_JS = """() => {
  const H = document.documentElement.clientHeight, issues = [];
  if (document.body.scrollHeight > document.body.clientHeight + 2)
    issues.push({where: 'page', detail: `content ${document.body.scrollHeight}px > page ${document.body.clientHeight}px`});
  document.querySelectorAll('[data-slot], .box').forEach(el => {
    const name = el.dataset.slot || (el.querySelector('h2')?.innerText.split('\\n')[0]) || el.className;
    if (el.scrollWidth > el.clientWidth + 1) issues.push({where: name, detail: `overflows width by ${el.scrollWidth - el.clientWidth}px`});
    if (el.scrollHeight > el.clientHeight + 1 && getComputedStyle(el).overflowY !== 'visible')
      issues.push({where: name, detail: `overflows height by ${el.scrollHeight - el.clientHeight}px`});
    const r = el.getBoundingClientRect();
    if (r.bottom > H + 1) issues.push({where: name, detail: `extends ${Math.round(r.bottom - H)}px below page`});
  });
  return issues;
}"""


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from docgen_filters import filters_for  # plugin-owned filters: locale formatting + charts


def load_project(proj):
    """A template project is data only: templates, CSS and JSON config. Code in it is refused."""
    code = [str(x.relative_to(proj)) for x in proj.rglob("*") if x.suffix in (".py", ".js", ".sh") and x.is_file()]
    if code:
        raise SystemExit(f"template project contains code, which onboarding must never produce: {code}")
    cfg = lambda n: json.loads((proj / "config" / n).read_text()) if (proj / "config" / n).exists() else {}
    return cfg("layouts.json"), cfg("i18n.json"), cfg("charts.json")


def make_env(proj, lang):
    env = Environment(loader=FileSystemLoader(proj / "templates"), undefined=StrictUndefined)
    env.filters.update(filters_for(lang))
    return env


def render(proj, data_paths, lang, out, brand=None):
    layouts, i18n, charts = load_project(proj)
    t = i18n.get(lang, {})
    env = make_env(proj, lang)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for dp in data_paths:
            f = json.loads(pathlib.Path(dp).read_text())
            html = env.get_template("base.html.j2").render(
                f=f, t=t, lang=lang, layout=layouts.get(f.get("layout"), {}), charts=charts, brand=brand or {"logo": None})
            stem = pathlib.Path(dp).stem
            (out / f"{stem}.html").write_text(html)
            page = browser.new_page(viewport={"width": 816, "height": 1056})   # Letter @96dpi
            page.set_content(html, wait_until="networkidle")
            issues = page.evaluate(OVERFLOW_JS)
            page.pdf(path=str(out / f"{stem}.pdf"), prefer_css_page_size=True, print_background=True)
            page.screenshot(path=str(out / f"{stem}.png"))
            page.close()
            status = "OK" if not issues else f"{len(issues)} OVERFLOW"
            print(f"{stem}: {status}  -> {out/stem}.pdf")
            for i in issues:
                print(f"   - [{i['where']}] {i['detail']}")
            results.append({"doc": stem, "pdf": str(out / f"{stem}.pdf"), "png": str(out / f"{stem}.png"),
                            "html": str(out / f"{stem}.html"), "issues": issues})
        browser.close()
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("data", nargs="+")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    results = render(pathlib.Path(a.project), a.data, a.lang, pathlib.Path(a.out))
    sys.exit(0 if all(not r["issues"] for r in results) else 1)
