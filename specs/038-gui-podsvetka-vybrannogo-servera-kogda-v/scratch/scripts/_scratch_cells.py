"""Card grid analysis of a window grab: which cell is selected/live?

numpy + a cheap flood fill on a 4x-downsampled mask. Prints the card grid in
row-major order with each cell's state, so the caller can compare it with the
index in selected-server.json.
"""
import json
import sys

import numpy as np
from PIL import Image

im = Image.open(sys.argv[1]).convert("RGB")
arr = np.asarray(im)
H, W, _ = arr.shape
D = 4
small = arr[::D, ::D]

ACCENT = (51, 115, 247)
PLAIN = (28, 28, 34)
SELBG = (22, 32, 58)
LIVEBG = (20, 37, 30)


def mask(color, tol=12):
    d = np.abs(small.astype(np.int16) - np.array(color, dtype=np.int16))
    return (d.max(axis=2) <= tol)


def components(m, min_px=40):
    h, w = m.shape
    seen = np.zeros_like(m, dtype=bool)
    out = []
    ys, xs = np.nonzero(m)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        stack = [(y0, x0)]
        seen[y0, x0] = True
        pts = []
        while stack:
            y, x = stack.pop()
            pts.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        if len(pts) >= min_px:
            py = [p[0] for p in pts]
            pxx = [p[1] for p in pts]
            out.append({"n": len(pts),
                        "bbox": [min(pxx) * D, min(py) * D, max(pxx) * D, max(py) * D],
                        "fill": len(pts) / float((max(py) - min(py) + 1) * (max(pxx) - min(pxx) + 1))})
    return out


acc = components(mask(ACCENT, 10), 40)
frames = [c for c in acc if c["fill"] < 0.35 and (c["bbox"][2] - c["bbox"][0]) > W * 0.25]
solid = [c for c in acc if c not in frames]
print("accent components:", len(acc), "| frame-like:", len(frames), "| solid:", len(solid))
for c in frames:
    print("  FRAME bbox=%s fill=%.2f" % (c["bbox"], c["fill"]))
for c in solid[:4]:
    print("  solid bbox=%s fill=%.2f" % (c["bbox"], c["fill"]))

cards = []
for name, col in (("selected", SELBG), ("live", LIVEBG), ("plain", PLAIN)):
    for c in components(mask(col, 6), 60):
        cards.append({"state": name, "bbox": c["bbox"], "n": c["n"]})
# merge the same card's segments (bg colour differs by row) into grid rows/cols
print("card-coloured blobs:", len(cards))
for c in sorted(cards, key=lambda c: (c["bbox"][1], c["bbox"][0])):
    print("   %-8s bbox=%s" % (c["state"], c["bbox"]))

res = {"size": [W, H],
       "frames": [{k: (v if k == "fill" else [int(x) for x in v]) for k, v in c.items()} for c in frames],
       "cards": [{k: (v if k == "state" else ([int(x) for x in v] if k == "bbox" else int(v)))
                  for k, v in c.items()} for c in cards]}
open("/home/m26/cells.json", "w").write(json.dumps(res))
print("wrote /home/m26/cells.json")
