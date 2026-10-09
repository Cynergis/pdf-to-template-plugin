"""Step 1 — Inspect a source PDF and extract everything a template author needs.

Usage:
  python inspect_pdf.py source.pdf --out work/            # inspect all pages
  python inspect_pdf.py source.pdf --page 0 --out work/
  python inspect_pdf.py issue_aug.pdf --diff issue_sep.pdf --out work/   # find data slots

Writes to --out:
  page_N.png          page rendered at 2x (always — this is what you look at)
  page_N_spans.json   every text span: text, bbox, font, size, color, bold/italic   (vector pages)
  page_N_drawings.json rules, boxes, fills with colors                               (vector pages)
  page_N_img_K.png    embedded raster images ≥ 30% of page area                    (raster pages)
  fonts/              embedded font files (vector pages)
  report.json         per-page verdict: "vector" | "raster" | "mixed" + summary
  slots.json          (--diff) spans whose text differs between the two issues = data slots
"""
import argparse, json, pathlib
import pymupdf


def span_list(page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                if not s["text"].strip():
                    continue
                out.append({
                    "text": s["text"], "bbox": [round(v, 1) for v in s["bbox"]],
                    "font": s["font"], "size": round(s["size"], 2),
                    "color": f"#{s['color']:06x}",
                    "bold": bool(s["flags"] & 16), "italic": bool(s["flags"] & 2),
                })
    return out


def drawing_list(page):
    out = []
    for d in page.get_drawings():
        hexc = lambda c: None if c is None else "#%02x%02x%02x" % tuple(int(x * 255) for x in c[:3])
        out.append({"rect": [round(v, 1) for v in d["rect"]], "stroke": hexc(d.get("color")),
                    "fill": hexc(d.get("fill")), "width": d.get("width")})
    return out


def inspect(pdf_path, out, pages=None, dpi=144):
    doc = pymupdf.open(pdf_path)
    out.mkdir(parents=True, exist_ok=True)
    report = {"source": str(pdf_path), "pages": []}
    for i, page in enumerate(doc):
        if pages is not None and i not in pages:
            continue
        area = page.rect.width * page.rect.height
        page.get_pixmap(dpi=dpi).save(out / f"page_{i}.png")
        spans, draws = span_list(page), drawing_list(page)
        big_imgs = []
        for k, img in enumerate(page.get_images(full=True)):
            for r in page.get_image_rects(img[0]):
                if r.width * r.height >= 0.3 * area:
                    pix = pymupdf.Pixmap(doc, img[0])
                    if pix.n - pix.alpha >= 4:
                        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                    p = out / f"page_{i}_img_{k}.png"
                    pix.save(p)
                    # how much text actually sits on top of the image?
                    on_img = sum(1 for s in spans if pymupdf.Rect(s["bbox"]).intersects(r))
                    big_imgs.append({"file": p.name, "bbox": [round(v, 1) for v in r],
                                     "px": [pix.width, pix.height], "text_spans_over_image": on_img})
        if spans:
            (out / f"page_{i}_spans.json").write_text(json.dumps(spans, indent=1, ensure_ascii=False))
        if draws:
            (out / f"page_{i}_drawings.json").write_text(json.dumps(draws, indent=1))
        raster_only = any(b["text_spans_over_image"] == 0 for b in big_imgs)
        verdict = "raster" if big_imgs and (raster_only or not spans) else ("mixed" if big_imgs else "vector")
        fonts = sorted({s["font"] for s in spans})
        report["pages"].append({
            "page": i, "size_pt": [page.rect.width, page.rect.height], "verdict": verdict,
            "spans": len(spans), "drawings": len(draws), "fonts": fonts,
            "font_sizes": sorted({s["size"] for s in spans}),
            "text_colors": sorted({s["color"] for s in spans}), "large_images": big_imgs,
        })
    # embedded fonts (only meaningful for vector content)
    fdir = out / "fonts"
    for xref, ext, _type, name, *_ in {f for p in doc for f in p.get_fonts(full=True)}:
        try:
            fname, fext, _, buf = doc.extract_font(xref)
            if buf:
                fdir.mkdir(exist_ok=True)
                (fdir / f"{fname or name}.{fext}").write_bytes(buf)
        except Exception:
            pass
    (out / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    return report


def diff_slots(pdf_a, pdf_b, out, page=0, tol=2.0):
    """Spans at (about) the same position whose text changed between two issues = data slots."""
    a = span_list(pymupdf.open(pdf_a)[page])
    b = span_list(pymupdf.open(pdf_b)[page])
    slots, static = [], 0
    for s in a:
        x0, y0 = s["bbox"][:2]
        match = next((t for t in b if abs(t["bbox"][0] - x0) < tol and abs(t["bbox"][1] - y0) < tol), None)
        if match is None:
            slots.append({**s, "kind": "moved_or_missing"})
        elif match["text"] != s["text"]:
            slots.append({**s, "kind": "changed", "other": match["text"]})
        else:
            static += 1
    (out / "slots.json").write_text(json.dumps(slots, indent=1, ensure_ascii=False))
    print(f"slots: {len(slots)} variable spans, {static} static spans -> {out/'slots.json'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out", default="work")
    ap.add_argument("--page", type=int)
    ap.add_argument("--diff", help="second issue of the same report, to discover data slots")
    ap.add_argument("--dpi", type=int, default=144, help="page image resolution (the flow uses 300)")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    rep = inspect(a.pdf, out, None if a.page is None else {a.page}, dpi=a.dpi)
    for p in rep["pages"]:
        print(f"page {p['page']}: {p['verdict']:6}  spans={p['spans']:4} drawings={p['drawings']:4} "
              f"fonts={p['fonts'][:4]}{'…' if len(p['fonts']) > 4 else ''} "
              f"images={[(i['px'], i['text_spans_over_image']) for i in p['large_images']]}")
    if a.diff:
        diff_slots(a.pdf, a.diff, out, page=a.page or 0)
