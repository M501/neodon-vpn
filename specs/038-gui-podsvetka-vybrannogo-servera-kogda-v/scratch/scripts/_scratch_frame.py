"""Locate the accent (selected) card frame in a window grab.

Prints: bbox, centre, and whether the centre sits in the left or the right
column of the two-column server grid.
"""
import sys

import numpy as np
from PIL import Image

im = Image.open(sys.argv[1]).convert("RGB")
arr = np.asarray(im).astype(np.int16)
H, W, _ = arr.shape
D = 4
ACCENT = (51, 115, 247)


def full_mask(color, tol=10):
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
            out.append((box, fill, len(pts)))
    return out


blobs = components(block_any(full_mask(ACCENT)), 20)
frames = [b for b in blobs if b[1] < 0.45 and (b[0][2] - b[0][0]) > W * 0.25]
print("grab %s  size=%dx%d  accent blobs=%d  frame-like=%d" % (sys.argv[1], W, H, len(blobs), len(frames)))
for box, fill, n in frames:
    xc = (box[0] + box[2]) / 2.0
    yc = (box[1] + box[3]) / 2.0
    mid = (W * 0.10 + W) / 2.0
    print("FRAME bbox=%s centre=(%.0f,%.0f) column=%s width=%d height=%d fill=%.2f" % (
        box, xc, yc, "LEFT" if xc < mid else "RIGHT", box[2] - box[0], box[3] - box[1], fill))
for box, fill, n in blobs:
    if (box, fill, n) not in frames:
        print("solid  bbox=%s fill=%.2f px=%d" % (box, fill, n))
