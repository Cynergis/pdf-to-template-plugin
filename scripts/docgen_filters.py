"""Plugin-owned Jinja filters: locale formatting and chart rendering, parameterized by configuration.

Templates never ship code. A template project carries config/charts.json (which series, axis rules,
label placement) and the templates call these filters with that configuration:
    {{ d.series | bar_svg(charts.calendar) }}
The same functions serve every report type; they are tested once, in the plugin.
"""
import math


# ───────────────────────────── locale formatting ─────────────────────────────
LOCALES = {
    "en": {"pct_sep": ".", "pct_suffix": "%", "thousands": ",", "currency": "${v}", "date": "{m:02d}/{d:02d}/{y}"},
    "fr": {"pct_sep": ",", "pct_suffix": " %", "thousands": " ", "currency": "{v} $", "date": "{d:02d}/{m:02d}/{y}"},
}


def make_locale_filters(lang):
    L = LOCALES.get(lang, LOCALES["en"])

    def pct(v, d=1):
        return "" if v is None else f"{v:.{d}f}".replace(".", L["pct_sep"]) + L["pct_suffix"]

    def num(v, d=0):
        if v is None:
            return ""
        s = f"{v:,.{d}f}".replace(",", "\u0000").replace(".", L["pct_sep"]).replace("\u0000", L["thousands"])
        return s

    def currency(v, d=0):
        return "" if v is None else L["currency"].format(v=num(v, d))

    def date(iso):
        if not iso:
            return ""
        y, m, d = (int(x) for x in str(iso)[:10].split("-"))
        return L["date"].format(y=y, m=m, d=d)

    return {"pct": pct, "num": num, "currency": currency, "date": date}


# ───────────────────────────── charts (inline SVG from data) ─────────────────────────────
def bar_svg(series, cfg=None):
    """Vertical bars with rotated value labels. cfg: w, h, y_min, y_max, tick, label_rotate, value_decimals."""
    cfg = cfg or {}
    w, h = cfg.get("w", 200), cfg.get("h", 118)
    vals = [v for _, v in series]
    lo = min(min(vals), cfg.get("y_min", -15)); hi = max(max(vals), cfg.get("y_max", 20))
    tick = cfg.get("tick", 5)
    pad_l, pad_b, pad_t = cfg.get("pad_l", 14), cfg.get("pad_b", 14), cfg.get("pad_t", 16)
    ih = h - pad_b - pad_t
    y = lambda v: pad_t + (hi - v) / (hi - lo) * ih
    bw = (w - pad_l) / len(series)
    dec = cfg.get("value_decimals", 1)
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" font-size="{cfg.get("font_size", 5.5)}">']
    for t in range(int(math.floor(lo / tick) * tick), int(hi) + 1, tick):
        out.append(f'<text x="0" y="{y(t)+2:.1f}" fill="#555">{t}</text>')
    for i, (lab, v) in enumerate(series):
        x = pad_l + i * bw + bw * 0.25
        top, bot = (y(v), y(0)) if v >= 0 else (y(0), y(v))
        out.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw*0.5:.1f}" height="{bot-top:.1f}" fill="var(--brand)"/>')
        ly = top - 3 if v >= 0 else bot + 3
        anchor = "start" if v >= 0 else "end"
        label = f"{v:.{dec}f}"
        if cfg.get("label_rotate", True):
            out.append(f'<text transform="translate({x+bw*0.25+2:.1f},{ly:.1f}) rotate(-90)" text-anchor="{anchor}">{label}</text>')
        else:
            out.append(f'<text x="{x+bw*0.25:.1f}" y="{ly:.1f}" text-anchor="middle">{label}</text>')
        out.append(f'<text x="{x+bw*0.25:.1f}" y="{h-2}" text-anchor="middle" fill="#555">{lab}</text>')
    out.append("</svg>")
    return "".join(out)


def line_svg(g, cfg=None):
    """Growth line with end-value callout. g: {points[], x_labels[], y_ticks[], end_label}. cfg: w, h, tick_step, pads."""
    cfg = cfg or {}
    w, h = cfg.get("w", 200), cfg.get("h", 118)
    pts = g["points"]
    step = cfg.get("tick_step", 5000)
    top = max(max(g.get("y_ticks", [step])), math.ceil(max(pts) / step) * step)       # auto-extend axis
    ticks = list(range(step, top + 1, step))
    lo, hi = min(ticks), max(ticks)
    pad_l, pad_b, pad_t, pad_r = cfg.get("pad_l", 26), cfg.get("pad_b", 16), cfg.get("pad_t", 8), cfg.get("pad_r", 4)
    iw, ih = w - pad_l - pad_r, h - pad_b - pad_t
    X = lambda i: pad_l + i / (len(pts) - 1) * iw
    Y = lambda v: pad_t + (hi - v) / (hi - lo) * ih
    path = " ".join(f"{'M' if i == 0 else 'L'}{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(pts))
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" font-size="{cfg.get("font_size", 5.5)}">']
    for t in ticks:
        out.append(f'<text x="0" y="{Y(t)+2:.1f}" fill="#555">${t:,}</text>')
    n = len(g.get("x_labels", []))
    for k, lab in enumerate(g.get("x_labels", [])):
        out.append(f'<text x="{pad_l + (k + 0.6) / (n + 0.2) * iw:.1f}" y="{h-3}" text-anchor="middle" fill="#555">{lab}</text>')
    out.append(f'<path d="{path}" fill="none" stroke="var(--brand)" stroke-width="{cfg.get("stroke", 0.9)}"/>')
    if g.get("end_label"):
        out.append(f'<text x="{w-2}" y="{Y(pts[-1])-5:.1f}" text-anchor="end" font-size="8" font-weight="700" fill="var(--brand)" text-decoration="underline">{g["end_label"]}</text>')
    out.append("</svg>")
    return "".join(out)


CHART_FILTERS = {"bar_svg": bar_svg, "line_svg": line_svg, "growth_svg": line_svg}


def filters_for(lang):
    f = dict(CHART_FILTERS)
    f.update(make_locale_filters(lang))
    return f
