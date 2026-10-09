"""Step 2 — Sample a design palette from an image (raster sources, or to cross-check vector colors).

Usage:
  python sample_colors.py work/page_0_img_0.png [--k 8] [--crop x0,y0,x1,y1] [--out work/palette.json]

Prints dominant non-white colors (k-means in Lab space), with share of non-white pixels.
Use --crop to sample one element (a bar, a band, a heading) precisely.
"""
import argparse, json
import cv2, numpy as np


def palette(path, k=8, crop=None):
    img = cv2.imread(path)
    if crop:
        x0, y0, x1, y1 = crop
        img = img[y0:y1, x0:x1]
    px = img.reshape(-1, 3).astype(np.float32)
    px = px[px.min(1) < 235]                       # drop near-white background
    if len(px) == 0:
        return []
    lab = cv2.cvtColor(px.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    k = min(k, len(lab))
    _, labels, _ = cv2.kmeans(lab, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3, cv2.KMEANS_PP_CENTERS)
    out = []
    for c in range(k):
        members = px[labels.ravel() == c]
        if len(members) == 0:
            continue
        b, g, r = np.median(members, 0).astype(int)
        out.append({"hex": f"#{r:02x}{g:02x}{b:02x}", "share": round(len(members) / len(px), 3)})
    return sorted(out, key=lambda d: -d["share"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--crop")
    ap.add_argument("--out")
    a = ap.parse_args()
    pal = palette(a.image, a.k, [int(v) for v in a.crop.split(",")] if a.crop else None)
    for c in pal:
        print(f"{c['hex']}  {c['share']*100:5.1f}%")
    if a.out:
        open(a.out, "w").write(json.dumps(pal, indent=1))
