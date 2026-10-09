"""Step 5 — Compare a render to the reference page and say WHERE it differs.

Usage:
  python diff.py reference.png out/fund.png [--out work/diff.png] [--grid 8x6] [--threshold 0.80]

Prints a layout-level SSIM score (blurred, so font substitution doesn't dominate) and the worst
grid cells, so you know which boxes to fix next. Writes a 3-panel image: reference | render | heatmap.
Exit code 1 if score < threshold.
"""
import argparse, sys
import cv2, numpy as np
from skimage.metrics import structural_similarity as ssim


def compare(ref_path, test_path, out_path, grid=(8, 6), blur=9):
    ref, test = cv2.imread(ref_path), cv2.imread(test_path)
    h = 1100
    ref = cv2.resize(ref, (int(ref.shape[1] * h / ref.shape[0]), h), interpolation=cv2.INTER_AREA)
    test = cv2.resize(test, (ref.shape[1], h), interpolation=cv2.INTER_AREA)
    g = lambda im: cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), (blur, blur), 0)
    score, smap = ssim(g(ref), g(test), full=True)
    heat = cv2.applyColorMap(((1 - np.clip(smap, 0, 1)) * 255).astype(np.uint8), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(test, 0.55, heat, 0.45, 0)
    cols, rows = grid
    ch, cw = h // rows, ref.shape[1] // cols
    cells = []
    for r in range(rows):
        for c in range(cols):
            s = float(smap[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw].mean())
            cells.append((s, r, c))
            cv2.rectangle(overlay, (c * cw, r * ch), ((c + 1) * cw, (r + 1) * ch), (200, 200, 200), 1)
    cells.sort()
    for s, r, c in cells[:5]:
        cv2.rectangle(overlay, (c * cw, r * ch), ((c + 1) * cw, (r + 1) * ch), (0, 0, 255), 3)
    cv2.imwrite(out_path, np.hstack([ref, test, overlay]))
    return score, cells


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("reference"); ap.add_argument("render")
    ap.add_argument("--out", default="diff.png")
    ap.add_argument("--grid", default="8x6")
    ap.add_argument("--threshold", type=float, default=0.0)
    a = ap.parse_args()
    cols, rows = map(int, a.grid.split("x"))
    score, cells = compare(a.reference, a.render, a.out, (cols, rows))
    print(f"layout SSIM: {score:.3f}   (diff image: {a.out})")
    print("worst cells (row, col from top-left; 1.0 = identical):")
    for s, r, c in cells[:5]:
        print(f"   row {r} col {c}: {s:.3f}   ≈ {int(100*c/cols)}–{int(100*(c+1)/cols)}% across, {int(100*r/rows)}–{int(100*(r+1)/rows)}% down")
    sys.exit(0 if score >= a.threshold else 1)
