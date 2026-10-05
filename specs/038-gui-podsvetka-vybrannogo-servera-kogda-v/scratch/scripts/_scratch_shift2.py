"""Measure how far a widget-grab image shifted between two shots (fast).

Brute-force search for the (dx, dy) that minimises mean absolute difference over
a crop; low residual = the image really moved by that offset. numpy when present,
otherwise a coarsely sampled pure-Python path.
"""
import sys

from PIL import Image

S = 4  # downscale factor for the search

b = Image.open(sys.argv[1]).convert("L")
a = Image.open(sys.argv[2]).convert("L")
print("sizes", b.size, a.size)
if b.size != a.size:
    raise SystemExit("size mismatch")
W0, H0 = b.size
b = b.resize((W0 // S, H0 // S))
a = a.resize((W0 // S, H0 // S))
W, H = b.size
x0, y0, x1, y1 = int(W * 0.16), int(H * 0.30), int(W * 0.98), int(H * 0.95)
R = 20  # search radius in downscaled px (= 4*R real px)

try:
    import numpy as np
    B = np.asarray(b, dtype=np.int16)
    A = np.asarray(a, dtype=np.int16)
    ref = B[y0:y1, x0:x1]
    best = None
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            cand = A[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
            if cand.shape != ref.shape:
                continue
            d = float(np.abs(cand - ref).mean())
            if best is None or d < best[0]:
                best = (d, dx, dy)
    print("numpy: residual=%.3f  dx=%d  dy=%d (real px)" % (best[0], best[1] * S, best[2] * S))
except ImportError:
    bp = list(b.getdata())
    ap = list(a.getdata())
    ref = [(x, y) for y in range(y0, y1, 3) for x in range(x0, x1, 3)]
    best = None
    for dy in range(-R, R + 1, 2):
        for dx in range(-R, R + 1, 2):
            s = 0
            for (x, y) in ref:
                s += abs(bp[y * W + x] - ap[(y + dy) * W + (x + dx)])
            d = s / float(len(ref))
            if best is None or d < best[0]:
                best = (d, dx, dy)
    print("pure-python: residual=%.3f  dx=%d  dy=%d (real px)" % (best[0], best[1] * S, best[2] * S))
