"""Card grid analysis of a window grab: which grid cell is selected / live?

numpy, 4x block-any masks (thin 2px borders survive), cheap flood fill.
Prints the card grid in row-major order with each cell's state so the caller can
compare it with the index in selected-server.json.
"""
import json
import sys

import numpy as np
from PIL import Image

im = Image.open(sys.argv[1]).convert("RGB")
arr = np.asarray(im).astype(np.int16)
H, W, _ = arr.shape
D = 4

ACCENT = (51, 115, 247)
PLAIN = (28, 28, 34)
SELBG = (22, 32, 58)
LIVEBG = (20, 37, 30)


def full_mask(color, tol=12):
    d = np.abs(arr - np.array(color, dtype=np.int16))
    return (d.max(axis=2) <= tol)


def block_any(m):
    h, w = m.shape
    ph, pw = (-h) % D, (-w) % D
    if ph or pw:
        m = np.pad(m, ((0, ph), (0, pw)), constant_values=False)
    hh, ww = m.shape
    return m.reshape(hh // D, D, ww // D, D).any(axis=(1, 3))


def components(m, min_px=15):
    h, w = m.shape
    seen = np.zeros_like(m, dtype=bool)
    out = []
    ys, xs = np.nonzero(m)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        stack = [(int(y0), int(x0))]
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
            box = [min(pxx) * D, min(py) * D, max(pxx) * D, max(py) * D]
            fill = len(pts) / float((max(py) - min(py) + 1) * (max(pxx) - min(pxx) + 1))
            out.append({"n": len(pts), "bbox": box, "fill": round(fill, 3)})
    return out


acc = components(block_any(full_mask(ACCENT, 10)), 20)
frames = [c for c in acc if c["fill"] < 0.45 and (c["bbox"][2] - c["bbox"][0]) > W * 0.25]
solid = [c for c in acc if c not in frames]
print("accent blobs:", len(acc), "| frame-like:", len(frames), "| solid:", len(solid))
for c in frames:
    print("  FRAME bbox=%s fill=%.2f px=%d" % (c["bbox"], c["fill"], c["n"]))
for c in solid[:5]:
    print("  solid bbox=%s fill=%.2f" % (c["bbox"], c["fill"]))

# card interiors: any of the three background colours, merged into one mask
interior = block_any(full_mask(PLAIN, 6) | full_mask(SELBG, 8) | full_mask(LIVEBG, 8))
blobs = [c for c in components(interior, 60) if c["bbox"][2] - c["bbox"][0] > 150]
# only real cards: roughly equal height, two columns
blobs.sort(key=lambda c: ((c["bbox"][1] + c["bbox"][3]) / 2.0, (c["bbox"][0] + c["bbox"][2]) / 2.0))
rows = []
for c in blobs:
    yc = (c["bbox"][1] + c["bbox"][3]) / 2.0
    if rows and abs(yc - rows[-1][0]) < 40:
        rows[-1][1].append(c)
    else:
        rows.append([yc, [c]])
print("card blobs: %d -> rows: %d" % (len(blobs), len(rows)))
idx = 0
for yc, row in rows:
    row.sort(key=lambda c: (c["bbox"][0] + c["bbox"][2]) / 2.0)
    for c in row:
        cb = c["bbox"]
        inside = arr[cb[1]:cb[3], cb[0]:cb[2]]
        dd = np.abs(inside - np.array(SELBG, dtype=np.int16)).max(axis=2)
        state = "selected" if (dd <= 12).mean() > 0.5 else "other"
        print("  grid[%d] state=%-8s bbox=%s" % (idx, state, cb))
        idx += 1

res = {"size": [W, H],
       "frames": frames,
       "cards": [{"state": "?", "bbox": c["bbox"], "n": int(c["n"])} for c in blobs],
       "rows": len(rows)}
open("/home/m26/cells.json", "w").write(json.dumps(res))
print("wrote /home/m26/cells.json")
