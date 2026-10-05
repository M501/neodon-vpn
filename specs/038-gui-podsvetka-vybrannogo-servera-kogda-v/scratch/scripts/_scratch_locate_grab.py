"""Locate a window grab inside a full-screen screenshot -> client origin on screen."""
import sys

import numpy as np
from PIL import Image

screen = Image.open(sys.argv[1]).convert("L")
grab = Image.open(sys.argv[2]).convert("L")
S = 4
sc = np.asarray(screen.resize((screen.width // S, screen.height // S)), dtype=np.int16)
gr = np.asarray(grab.resize((grab.width // S, grab.height // S)), dtype=np.int16)
gh, gw = gr.shape
sh, sw = sc.shape
print("screen small", sc.shape, "grab small", gr.shape)

# compare only the central band of the grab (fast, still discriminative)
band = slice(gh // 4, gh // 4 * 3)
ref = gr[band, :]
best = None
for oy in range(0, sh - ref.shape[0] + 1):
    for ox in range(0, sw - gw + 1):
        cand = sc[oy + band.start:oy + band.stop, ox:ox + gw]
        if cand.shape != ref.shape:
            continue
        d = float(np.abs(cand - ref).mean())
        if best is None or d < best[0]:
            best = (d, ox, oy)
print("best residual=%.2f  origin_small=(%d,%d)  origin_screen=(%d,%d)"
      % (best[0], best[1], best[2], best[1] * S, best[2] * S))
